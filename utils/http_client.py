"""
HTTP Client utilities for SEO Auditor
Handles all HTTP requests with retry logic, rate limiting, and caching
"""

import time
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, urljoin
from datetime import datetime
import random

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.exceptions import (
    RequestException,
    Timeout,
    ConnectionError,
    HTTPError,
    TooManyRedirects
)

from .cache import CacheManager

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter to control request frequency
    """

    def __init__(self, requests_per_second: float = 2, burst_size: int = 5):
        """
        Initialize rate limiter

        Args:
            requests_per_second: Maximum requests per second
            burst_size: Number of requests allowed in burst
        """
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0

    def acquire(self):
        """Wait if necessary to maintain rate limit"""
        current_time = time.time()

        # Refill tokens based on time elapsed
        time_passed = current_time - self.last_update
        self.tokens = min(
            self.burst_size,
            self.tokens + time_passed * self.requests_per_second
        )
        self.last_update = current_time

        # Wait if no tokens available
        if self.tokens < 1:
            sleep_time = (1 - self.tokens) / self.requests_per_second
            time.sleep(sleep_time)
            self.tokens = 0
            self.last_update = time.time()
        else:
            self.tokens -= 1

        # Ensure minimum interval between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_interval:
            time.sleep(self.min_interval - time_since_last)

        self.last_request_time = time.time()


class HTTPClient:
    """
    Advanced HTTP client with retry logic, rate limiting, and caching
    """

    def __init__(self, config: dict = None, cache_manager: Optional[CacheManager] = None):
        """
        Initialize HTTP client

        Args:
            config: Configuration dictionary from config.yaml
            cache_manager: Optional CacheManager instance
        """
        self.config = config or {}
        self.cache_manager = cache_manager

        # Extract configuration
        crawler_config = self.config.get('crawler', {})
        self.timeout = crawler_config.get('timeout', 30)
        self.retry_attempts = crawler_config.get('retry_attempts', 3)
        self.retry_delay = crawler_config.get('retry_delay', 2)
        self.user_agent = crawler_config.get(
            'user_agent',
            'SEO-Auditor-Bot/1.0 (+https://github.com/yourusername/py-seo-auditor)'
        )
        self.follow_redirects = crawler_config.get('follow_redirects', True)
        self.max_redirects = crawler_config.get('max_redirects', 5)
        self.crawl_delay = crawler_config.get('crawl_delay', 1)

        # Rate limiting
        rate_limit_config = self.config.get('advanced', {}).get('rate_limiting', {})
        if rate_limit_config.get('enabled', True):
            requests_per_second = rate_limit_config.get('requests_per_second', 2)
            burst_size = rate_limit_config.get('burst_size', 5)
            self.rate_limiter = RateLimiter(requests_per_second, burst_size)
        else:
            self.rate_limiter = None

        # Initialize session with retry strategy
        self.session = self._create_session()

        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cached_requests': 0,
            'total_bytes': 0,
            'start_time': datetime.now()
        }

        logger.info("HTTP client initialized")

    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry strategy

        Returns:
            Configured requests.Session object
        """
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.retry_attempts,
            backoff_factor=self.retry_delay,  # Exponential backoff: 2, 4, 8 seconds
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP codes
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            raise_on_status=False
        )

        # Mount adapter with retry strategy
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers
        session.headers.update(self._get_default_headers())

        logger.debug("Session created with retry strategy")
        return session

    def _get_default_headers(self) -> Dict[str, str]:
        """
        Get default HTTP headers

        Returns:
            Dictionary of default headers
        """
        return {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }

    def get(
            self,
            url: str,
            headers: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, Any]] = None,
            use_cache: bool = True,
            cache_ttl: Optional[int] = None,
            **kwargs
    ) -> Optional[requests.Response]:
        """
        Send GET request with caching and rate limiting

        Args:
            url: URL to request
            headers: Optional custom headers
            params: Optional URL parameters
            use_cache: Whether to use cache
            cache_ttl: Optional custom cache TTL
            **kwargs: Additional arguments passed to requests.get

        Returns:
            Response object or None on failure
        """
        # Check cache first
        if use_cache and self.cache_manager:
            cache_key = self.cache_manager.generate_key('http_get', url, params)
            cached_response = self.cache_manager.get(cache_key)

            if cached_response:
                logger.debug(f"Cache hit for: {url}")
                self.stats['cached_requests'] += 1
                return cached_response

        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.acquire()

        # Prepare request
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)

        try:
            self.stats['total_requests'] += 1

            # Make request
            response = self.session.get(
                url,
                headers=request_headers,
                params=params,
                timeout=self.timeout,
                allow_redirects=self.follow_redirects,
                **kwargs
            )

            # Update statistics
            self.stats['total_bytes'] += len(response.content)

            # Check response status
            if response.status_code == 200:
                self.stats['successful_requests'] += 1

                # Cache successful response
                if use_cache and self.cache_manager:
                    self.cache_manager.set(cache_key, response, cache_ttl)

                logger.debug(f"GET {url} - Status: {response.status_code}")
                return response

            elif response.status_code == 429:
                # Rate limited - apply exponential backoff
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    wait_time = int(retry_after)
                else:
                    wait_time = self.retry_delay * 2

                logger.warning(f"Rate limited on {url}, waiting {wait_time}s")
                time.sleep(wait_time)

                # Retry once after waiting
                return self.get(url, headers, params, use_cache=False, **kwargs)

            else:
                self.stats['failed_requests'] += 1
                logger.warning(f"GET {url} - Status: {response.status_code}")
                return response

        except Timeout:
            self.stats['failed_requests'] += 1
            logger.error(f"Timeout requesting {url}")
            return None

        except ConnectionError as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Connection error for {url}: {e}")
            return None

        except TooManyRedirects:
            self.stats['failed_requests'] += 1
            logger.error(f"Too many redirects for {url}")
            return None

        except RequestException as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Request exception for {url}: {e}")
            return None

    def post(
            self,
            url: str,
            data: Optional[Dict] = None,
            json: Optional[Dict] = None,
            headers: Optional[Dict[str, str]] = None,
            **kwargs
    ) -> Optional[requests.Response]:
        """
        Send POST request

        Args:
            url: URL to request
            data: Form data
            json: JSON data
            headers: Optional custom headers
            **kwargs: Additional arguments

        Returns:
            Response object or None on failure
        """
        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.acquire()

        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)

        try:
            self.stats['total_requests'] += 1

            response = self.session.post(
                url,
                data=data,
                json=json,
                headers=request_headers,
                timeout=self.timeout,
                **kwargs
            )

            self.stats['total_bytes'] += len(response.content)

            if response.status_code in [200, 201]:
                self.stats['successful_requests'] += 1
            else:
                self.stats['failed_requests'] += 1

            logger.debug(f"POST {url} - Status: {response.status_code}")
            return response

        except RequestException as e:
            self.stats['failed_requests'] += 1
            logger.error(f"POST request failed for {url}: {e}")
            return None

    def head(
            self,
            url: str,
            headers: Optional[Dict[str, str]] = None,
            **kwargs
    ) -> Optional[requests.Response]:
        """
        Send HEAD request (efficient for checking resource existence)

        Args:
            url: URL to request
            headers: Optional custom headers
            **kwargs: Additional arguments

        Returns:
            Response object or None on failure
        """
        if self.rate_limiter:
            self.rate_limiter.acquire()

        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)

        try:
            self.stats['total_requests'] += 1

            response = self.session.head(
                url,
                headers=request_headers,
                timeout=self.timeout,
                allow_redirects=self.follow_redirects,
                **kwargs
            )

            if response.status_code == 200:
                self.stats['successful_requests'] += 1
            else:
                self.stats['failed_requests'] += 1

            logger.debug(f"HEAD {url} - Status: {response.status_code}")
            return response

        except RequestException as e:
            self.stats['failed_requests'] += 1
            logger.error(f"HEAD request failed for {url}: {e}")
            return None

    def download_file(
            self,
            url: str,
            output_path: str,
            chunk_size: int = 8192
    ) -> bool:
        """
        Download file from URL

        Args:
            url: URL to download
            output_path: Path to save file
            chunk_size: Download chunk size in bytes

        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.get(url, stream=True, use_cache=False)

            if not response or response.status_code != 200:
                return False

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)

            logger.info(f"Downloaded {url} to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Download failed for {url}: {e}")
            return False

    def get_robots_txt(self, base_url: str) -> Optional[str]:
        """
        Fetch robots.txt for a domain

        Args:
            base_url: Base URL of the website

        Returns:
            robots.txt content or None
        """
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        response = self.get(robots_url, use_cache=True, cache_ttl=86400)  # Cache for 24h

        if response and response.status_code == 200:
            return response.text

        return None

    def get_sitemap(self, base_url: str) -> Optional[str]:
        """
        Fetch sitemap.xml for a domain

        Args:
            base_url: Base URL of the website

        Returns:
            sitemap.xml content or None
        """
        parsed = urlparse(base_url)
        sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"

        response = self.get(sitemap_url, use_cache=True, cache_ttl=86400)  # Cache for 24h

        if response and response.status_code == 200:
            return response.text

        return None

    def check_url_status(self, url: str) -> Dict[str, Any]:
        """
        Check URL status and get metadata

        Args:
            url: URL to check

        Returns:
            Dictionary with status information
        """
        response = self.head(url)

        if not response:
            return {
                'url': url,
                'status_code': None,
                'accessible': False,
                'redirect_url': None,
                'content_type': None,
                'content_length': None
            }

        return {
            'url': url,
            'status_code': response.status_code,
            'accessible': response.status_code == 200,
            'redirect_url': response.url if response.url != url else None,
            'content_type': response.headers.get('Content-Type'),
            'content_length': response.headers.get('Content-Length'),
            'is_redirect': response.status_code in [301, 302, 303, 307, 308]
        }

    def set_user_agent(self, user_agent: str):
        """Update user agent"""
        self.user_agent = user_agent
        self.session.headers.update({'User-Agent': user_agent})
        logger.info(f"User agent updated to: {user_agent}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get client statistics

        Returns:
            Dictionary with statistics
        """
        runtime = (datetime.now() - self.stats['start_time']).total_seconds()

        return {
            'total_requests': self.stats['total_requests'],
            'successful_requests': self.stats['successful_requests'],
            'failed_requests': self.stats['failed_requests'],
            'cached_requests': self.stats['cached_requests'],
            'total_mb_downloaded': round(self.stats['total_bytes'] / (1024 * 1024), 2),
            'success_rate': round(
                (self.stats['successful_requests'] / self.stats['total_requests'] * 100)
                if self.stats['total_requests'] > 0 else 0,
                2
            ),
            'requests_per_second': round(
                self.stats['total_requests'] / runtime if runtime > 0 else 0,
                2
            ),
            'runtime_seconds': round(runtime, 2)
        }

    def close(self):
        """Close session and cleanup"""
        self.session.close()
        logger.info("HTTP client closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# User agent rotation utility
class UserAgentRotator:
    """
    Rotate user agents to avoid detection
    """

    # Common real user agents (updated for 2025)
    USER_AGENTS = [
        # Chrome on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        # Chrome on Mac
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        # Firefox on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
        # Firefox on Mac
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0',
        # Safari on Mac
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15',
        # Edge on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
    ]

    @classmethod
    def get_random(cls) -> str:
        """Get random user agent"""
        return random.choice(cls.USER_AGENTS)

    @classmethod
    def get_chrome(cls) -> str:
        """Get Chrome user agent"""
        return cls.USER_AGENTS[0]

    @classmethod
    def get_firefox(cls) -> str:
        """Get Firefox user agent"""
        return cls.USER_AGENTS[2]

    @classmethod
    def get_safari(cls) -> str:
        """Get Safari user agent"""
        return cls.USER_AGENTS[4]

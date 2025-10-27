"""
Website crawler for SEO Auditor
Implements breadth-first crawling with robots.txt compliance
"""

import time
import logging
from typing import Dict, List, Optional, Set, Any
from urllib.parse import urlparse, urljoin
from collections import deque
from datetime import datetime
import threading
from urllib.robotparser import RobotFileParser

from utils.http_client import HTTPClient
from utils.parsers import HTMLParser, RobotsParser
from utils.cache import CacheManager
from utils.logger import log_execution_time

logger = logging.getLogger(__name__)


class CrawlResult:
    """
    Data class for storing crawl results for a single page
    """

    def __init__(self, url: str):
        self.url = url
        self.status_code = None
        self.title = None
        self.meta_description = None
        self.meta_keywords = None
        self.meta_robots = None
        self.canonical_url = None
        self.h1_tags = []
        self.headers = {}
        self.images = []
        self.internal_links = []
        self.external_links = []
        self.word_count = 0
        self.structured_data = []
        self.open_graph = {}
        self.twitter_card = {}
        self.hreflang = []
        self.response_time = 0
        self.content_size = 0
        self.crawl_timestamp = datetime.now()
        self.errors = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'url': self.url,
            'status_code': self.status_code,
            'title': self.title,
            'meta_description': self.meta_description,
            'meta_keywords': self.meta_keywords,
            'meta_robots': self.meta_robots,
            'canonical_url': self.canonical_url,
            'h1_tags': self.h1_tags,
            'headers': self.headers,
            'image_count': len(self.images),
            'images': self.images,
            'internal_link_count': len(self.internal_links),
            'external_link_count': len(self.external_links),
            'word_count': self.word_count,
            'structured_data_count': len(self.structured_data),
            'structured_data': self.structured_data,
            'open_graph': self.open_graph,
            'twitter_card': self.twitter_card,
            'hreflang': self.hreflang,
            'response_time': self.response_time,
            'content_size': self.content_size,
            'crawl_timestamp': self.crawl_timestamp.isoformat(),
            'errors': self.errors
        }


class SEOCrawler:
    """
    Main crawler class for SEO auditing
    Implements breadth-first search with configurable depth and page limits
    """

    def __init__(self, config: Dict = None, cache_manager: Optional[CacheManager] = None):
        """
        Initialize SEO crawler

        Args:
            config: Configuration dictionary from config.yaml
            cache_manager: Optional cache manager instance
        """
        self.config = config or {}
        self.cache_manager = cache_manager

        # Extract crawler configuration
        crawler_config = self.config.get('crawler', {})
        self.max_pages = crawler_config.get('max_pages', 100)
        self.max_depth = crawler_config.get('max_depth', 3)
        self.respect_robots = crawler_config.get('respect_robots_txt', True)
        self.crawl_delay = crawler_config.get('crawl_delay', 1)
        self.exclude_patterns = crawler_config.get('exclude_patterns', [])

        # Initialize HTTP client
        self.http_client = HTTPClient(config, cache_manager)

        # Crawl state
        self.visited_urls: Set[str] = set()
        self.url_queue: deque = deque()
        self.crawl_results: List[CrawlResult] = []
        self.robots_parsers: Dict[str, RobotFileParser] = {}

        # Thread safety
        self.lock = threading.Lock()

        # Statistics
        self.stats = {
            'pages_crawled': 0,
            'pages_skipped': 0,
            'errors': 0,
            'total_links_found': 0,
            'start_time': None,
            'end_time': None
        }

        logger.info(f"Crawler initialized: max_pages={self.max_pages}, max_depth={self.max_depth}")

    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL for comparison

        Args:
            url: URL to normalize

        Returns:
            Normalized URL
        """
        parsed = urlparse(url)

        # Remove fragment
        url_no_fragment = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        # Remove trailing slash for consistency (except root)
        if url_no_fragment.endswith('/') and parsed.path != '/':
            url_no_fragment = url_no_fragment[:-1]

        return url_no_fragment

    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain"""
        domain1 = urlparse(url1).netloc
        domain2 = urlparse(url2).netloc
        return domain1 == domain2

    def _should_skip_url(self, url: str) -> bool:
        """
        Check if URL should be skipped based on patterns

        Args:
            url: URL to check

        Returns:
            True if should skip
        """
        # Skip non-HTTP(S) URLs
        if not url.startswith(('http://', 'https://')):
            return True

        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if pattern in url:
                logger.debug(f"Skipping URL matching exclude pattern: {url}")
                return True

        # Skip common non-HTML extensions
        skip_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip',
                           '.exe', '.dmg', '.mp4', '.mp3', '.css', '.js']
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return True

        return False

    def _get_robots_parser(self, base_url: str) -> Optional[RobotFileParser]:
        """
        Get or create robots.txt parser for domain

        Args:
            base_url: Base URL of the website

        Returns:
            RobotFileParser instance or None
        """
        parsed = urlparse(base_url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        # Check cache
        if domain in self.robots_parsers:
            return self.robots_parsers[domain]

        # Fetch and parse robots.txt
        try:
            robots_url = f"{domain}/robots.txt"
            response = self.http_client.get(robots_url, use_cache=True, cache_ttl=86400)

            if response and response.status_code == 200:
                rp = RobotFileParser()
                rp.parse(response.text.splitlines())
                self.robots_parsers[domain] = rp
                logger.info(f"Loaded robots.txt for {domain}")
                return rp
            else:
                logger.info(f"No robots.txt found for {domain}, allowing all")
                # Create permissive parser
                rp = RobotFileParser()
                self.robots_parsers[domain] = rp
                return rp

        except Exception as e:
            logger.error(f"Error fetching robots.txt for {domain}: {e}")
            return None

    def _is_allowed_by_robots(self, url: str) -> bool:
        """
        Check if URL is allowed by robots.txt

        Args:
            url: URL to check

        Returns:
            True if allowed
        """
        if not self.respect_robots:
            return True

        parser = self._get_robots_parser(url)
        if not parser:
            return True

        user_agent = self.http_client.user_agent
        return parser.can_fetch(user_agent, url)

    def _extract_links(self, html_content: str, base_url: str, current_depth: int) -> List[tuple]:
        """
        Extract and queue links from HTML

        Args:
            html_content: HTML content
            base_url: Base URL for resolving relative links
            current_depth: Current crawl depth

        Returns:
            List of (url, depth) tuples
        """
        links = []

        try:
            parser = HTMLParser(html_content, base_url)
            all_links = parser.get_internal_links()

            for link_data in all_links:
                url = link_data['href']
                normalized_url = self._normalize_url(url)

                # Skip if already visited or queued
                if normalized_url in self.visited_urls:
                    continue

                # Skip if should be excluded
                if self._should_skip_url(normalized_url):
                    continue

                # Skip if not same domain
                if not self._is_same_domain(normalized_url, base_url):
                    continue

                # Skip if depth limit reached
                if current_depth >= self.max_depth:
                    continue

                # Check robots.txt
                if not self._is_allowed_by_robots(normalized_url):
                    logger.debug(f"URL blocked by robots.txt: {normalized_url}")
                    self.stats['pages_skipped'] += 1
                    continue

                links.append((normalized_url, current_depth + 1))

        except Exception as e:
            logger.error(f"Error extracting links from {base_url}: {e}")

        return links

    def _crawl_page(self, url: str, depth: int) -> Optional[CrawlResult]:
        """
        Crawl a single page and extract data

        Args:
            url: URL to crawl
            depth: Current depth

        Returns:
            CrawlResult or None
        """
        result = CrawlResult(url)

        try:
            # Fetch page
            start_time = time.time()
            response = self.http_client.get(url, use_cache=False)
            result.response_time = time.time() - start_time

            if not response:
                result.errors.append("Failed to fetch URL")
                self.stats['errors'] += 1
                return result

            result.status_code = response.status_code
            result.content_size = len(response.content)

            # Only parse HTML content
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                logger.debug(f"Skipping non-HTML content: {url}")
                return result

            # Parse HTML
            parser = HTMLParser(response.text, url)

            # Extract basic SEO elements
            result.title = parser.get_title()
            result.meta_description = parser.get_meta_description()
            result.meta_keywords = parser.get_meta_keywords()
            result.meta_robots = parser.get_meta_robots()
            result.canonical_url = parser.get_canonical_url()

            # Extract headers
            result.h1_tags = parser.get_h1_tags()
            result.headers = parser.get_headers()

            # Extract images
            result.images = parser.get_images()

            # Extract links
            result.internal_links = parser.get_internal_links()
            result.external_links = parser.get_external_links()
            self.stats['total_links_found'] += len(result.internal_links) + len(result.external_links)

            # Extract structured data
            result.structured_data = parser.get_structured_data()

            # Extract social media tags
            result.open_graph = parser.get_open_graph_tags()
            result.twitter_card = parser.get_twitter_card_tags()

            # Extract hreflang
            result.hreflang = parser.get_hreflang_tags()

            # Word count
            result.word_count = parser.get_word_count()

            logger.info(f"Crawled: {url} (Status: {result.status_code}, Time: {result.response_time:.2f}s)")

        except Exception as e:
            logger.error(f"Error crawling {url}: {e}", exc_info=True)
            result.errors.append(str(e))
            self.stats['errors'] += 1

        return result

    @log_execution_time(logger)
    def crawl(self, start_url: str, max_pages: Optional[int] = None) -> List[CrawlResult]:
        """
        Start crawling from a URL

        Args:
            start_url: Starting URL
            max_pages: Optional override for max pages

        Returns:
            List of CrawlResult objects
        """
        if max_pages:
            self.max_pages = max_pages

        # Reset state
        self.visited_urls.clear()
        self.crawl_results.clear()
        self.url_queue.clear()
        self.stats['start_time'] = datetime.now()
        self.stats['pages_crawled'] = 0
        self.stats['pages_skipped'] = 0
        self.stats['errors'] = 0
        self.stats['total_links_found'] = 0

        # Normalize and add start URL
        start_url = self._normalize_url(start_url)
        self.url_queue.append((start_url, 0))

        logger.info(f"Starting crawl of {start_url}")

        # Breadth-first crawl
        while self.url_queue and len(self.crawl_results) < self.max_pages:
            url, depth = self.url_queue.popleft()

            # Skip if already visited
            if url in self.visited_urls:
                continue

            # Mark as visited
            self.visited_urls.add(url)

            # Check robots.txt
            if not self._is_allowed_by_robots(url):
                logger.info(f"Skipping (robots.txt): {url}")
                self.stats['pages_skipped'] += 1
                continue

            # Crawl page
            result = self._crawl_page(url, depth)
            if result:
                self.crawl_results.append(result)
                self.stats['pages_crawled'] += 1

                # Extract and queue new links
                if result.status_code == 200 and depth < self.max_depth:
                    try:
                        response = self.http_client.get(url, use_cache=True)
                        if response:
                            new_links = self._extract_links(response.text, url, depth)
                            for link_url, link_depth in new_links:
                                if link_url not in self.visited_urls:
                                    self.url_queue.append((link_url, link_depth))
                    except Exception as e:
                        logger.error(f"Error extracting links from {url}: {e}")

            # Respect crawl delay
            if self.crawl_delay > 0:
                time.sleep(self.crawl_delay)

        self.stats['end_time'] = datetime.now()

        # Log summary
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        logger.info(f"Crawl completed: {self.stats['pages_crawled']} pages in {duration:.2f}s")
        logger.info(f"  - Pages skipped: {self.stats['pages_skipped']}")
        logger.info(f"  - Errors: {self.stats['errors']}")
        logger.info(f"  - Links found: {self.stats['total_links_found']}")

        return self.crawl_results

    def get_results(self) -> List[Dict[str, Any]]:
        """
        Get crawl results as list of dictionaries

        Returns:
            List of result dictionaries
        """
        return [result.to_dict() for result in self.crawl_results]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get crawl statistics

        Returns:
            Statistics dictionary
        """
        stats = self.stats.copy()

        if stats['start_time'] and stats['end_time']:
            duration = (stats['end_time'] - stats['start_time']).total_seconds()
            stats['duration_seconds'] = round(duration, 2)
            stats['pages_per_second'] = round(
                stats['pages_crawled'] / duration if duration > 0 else 0,
                2
            )

        # Add HTTP client stats
        stats['http_stats'] = self.http_client.get_stats()

        return stats

    def get_url_list(self) -> List[str]:
        """Get list of all crawled URLs"""
        return [result.url for result in self.crawl_results]

    def find_page_by_url(self, url: str) -> Optional[CrawlResult]:
        """
        Find crawl result by URL

        Args:
            url: URL to find

        Returns:
            CrawlResult or None
        """
        normalized = self._normalize_url(url)
        for result in self.crawl_results:
            if self._normalize_url(result.url) == normalized:
                return result
        return None

    def get_sitemap_urls(self, base_url: str) -> List[str]:
        """
        Get URLs from sitemap.xml

        Args:
            base_url: Base URL of website

        Returns:
            List of URLs from sitemap
        """
        from utils.parsers import XMLParser

        try:
            sitemap_content = self.http_client.get_sitemap(base_url)
            if sitemap_content:
                xml_parser = XMLParser(sitemap_content)
                sitemap_urls = xml_parser.parse_sitemap()
                logger.info(f"Found {len(sitemap_urls)} URLs in sitemap")
                return [url_data['loc'] for url_data in sitemap_urls if url_data.get('loc')]
        except Exception as e:
            logger.error(f"Error parsing sitemap: {e}")

        return []

    def close(self):
        """Cleanup resources"""
        self.http_client.close()
        logger.info("Crawler closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

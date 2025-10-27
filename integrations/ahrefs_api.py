"""
Ahrefs API integration for SEO Auditor
Provides backlink analysis, domain metrics, and keyword data
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

import requests
from requests.exceptions import RequestException

from utils.cache import CacheManager
from utils.logger import log_execution_time

logger = logging.getLogger(__name__)


class AhrefsAPIError(Exception):
    """Custom exception for Ahrefs API errors"""
    pass


class AhrefsAPI:
    """
    Ahrefs API client for backlink and domain analysis
    """

    # API endpoints
    BASE_URL = "https://apiv2.ahrefs.com"

    # Available modes
    MODES = {
        'exact': 'exact',
        'domain': 'domain',
        'subdomains': 'subdomains',
        'prefix': 'prefix'
    }

    def __init__(self, config: Dict = None, cache_manager: Optional[CacheManager] = None):
        """
        Initialize Ahrefs API client

        Args:
            config: Configuration dictionary
            cache_manager: Optional cache manager for API responses
        """
        self.config = config or {}
        self.cache_manager = cache_manager

        # Get API configuration
        ahrefs_config = self.config.get('integrations', {}).get('ahrefs', {})

        # API credentials
        self.api_key = os.getenv('AHREFS_API_KEY') or ahrefs_config.get('api_key_env', '')
        self.enabled = ahrefs_config.get('enabled', False) and bool(self.api_key)

        if not self.api_key and self.enabled:
            logger.warning("Ahrefs API key not found. Set AHREFS_API_KEY environment variable.")
            self.enabled = False

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests

        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cached_requests': 0
        }

        if self.enabled:
            logger.info("Ahrefs API initialized and enabled")
        else:
            logger.info("Ahrefs API disabled or not configured")

    def _rate_limit(self):
        """Apply rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _make_request(
            self,
            endpoint: str,
            params: Dict[str, Any],
            cache_ttl: int = 86400
    ) -> Optional[Dict]:
        """
        Make API request with caching and error handling

        Args:
            endpoint: API endpoint (e.g., 'backlinks', 'domain-rating')
            params: Request parameters
            cache_ttl: Cache time-to-live in seconds

        Returns:
            API response data or None
        """
        if not self.enabled:
            logger.warning("Ahrefs API is not enabled")
            return None

        # Add API token to params
        params['token'] = self.api_key
        params['output'] = 'json'

        # Check cache
        cache_key = f"ahrefs_{endpoint}_{hash(frozenset(params.items()))}"
        if self.cache_manager:
            cached_data = self.cache_manager.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for Ahrefs {endpoint}")
                self.stats['cached_requests'] += 1
                return cached_data

        # Rate limiting
        self._rate_limit()

        # Make request
        try:
            self.stats['total_requests'] += 1

            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            # Check for API errors
            if 'error' in data:
                logger.error(f"Ahrefs API error: {data['error']}")
                self.stats['failed_requests'] += 1
                raise AhrefsAPIError(data['error'])

            self.stats['successful_requests'] += 1

            # Cache successful response
            if self.cache_manager:
                self.cache_manager.set(cache_key, data, cache_ttl)

            logger.debug(f"Ahrefs {endpoint} request successful")
            return data

        except RequestException as e:
            logger.error(f"Ahrefs API request failed: {e}")
            self.stats['failed_requests'] += 1
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Ahrefs API: {e}")
            self.stats['failed_requests'] += 1
            return None

    @log_execution_time(logger)
    def get_domain_rating(
            self,
            target: str,
            mode: str = 'domain'
    ) -> Optional[Dict[str, Any]]:
        """
        Get domain rating for a target

        Args:
            target: Target domain/URL
            mode: Mode (exact, domain, subdomains, prefix)

        Returns:
            Dictionary with domain rating data
        """
        params = {
            'from': 'domain_rating',
            'target': target,
            'mode': mode
        }

        data = self._make_request('domain_rating', params)

        if data and 'domain_rating' in data:
            return {
                'domain': target,
                'domain_rating': data['domain_rating'],
                'ahrefs_rank': data.get('ahrefs_rank'),
                'referring_domains': data.get('refdomains'),
                'backlinks': data.get('backlinks'),
                'timestamp': datetime.now().isoformat()
            }

        return None

    @log_execution_time(logger)
    def get_backlinks(
            self,
            target: str,
            mode: str = 'domain',
            limit: int = 100,
            order_by: str = 'domain_rating:desc'
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get backlinks for a target

        Args:
            target: Target domain/URL
            mode: Mode (exact, domain, subdomains, prefix)
            limit: Maximum number of results
            order_by: Sort order

        Returns:
            List of backlink dictionaries
        """
        params = {
            'from': 'backlinks',
            'target': target,
            'mode': mode,
            'limit': limit,
            'order_by': order_by
        }

        data = self._make_request('backlinks', params)

        if data and 'backlinks' in data:
            backlinks = []
            for link in data['backlinks']:
                backlinks.append({
                    'url_from': link.get('url_from'),
                    'url_to': link.get('url_to'),
                    'anchor': link.get('anchor'),
                    'domain_rating': link.get('domain_rating'),
                    'url_rating': link.get('url_rating'),
                    'is_dofollow': link.get('is_dofollow', True),
                    'is_content': link.get('is_content'),
                    'first_seen': link.get('first_seen'),
                    'last_visited': link.get('last_visited')
                })

            return backlinks

        return None

    @log_execution_time(logger)
    def get_referring_domains(
            self,
            target: str,
            mode: str = 'domain',
            limit: int = 100
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get referring domains for a target

        Args:
            target: Target domain/URL
            mode: Mode (exact, domain, subdomains, prefix)
            limit: Maximum number of results

        Returns:
            List of referring domain dictionaries
        """
        params = {
            'from': 'refdomains',
            'target': target,
            'mode': mode,
            'limit': limit,
            'order_by': 'domain_rating:desc'
        }

        data = self._make_request('refdomains', params)

        if data and 'refdomains' in data:
            domains = []
            for domain in data['refdomains']:
                domains.append({
                    'domain': domain.get('domain'),
                    'domain_rating': domain.get('domain_rating'),
                    'backlinks': domain.get('backlinks'),
                    'refpages': domain.get('refpages'),
                    'first_seen': domain.get('first_seen'),
                    'last_visited': domain.get('last_visited')
                })

            return domains

        return None

    @log_execution_time(logger)
    def get_organic_keywords(
            self,
            target: str,
            mode: str = 'domain',
            limit: int = 100,
            country: str = 'us'
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get organic keywords for a target

        Args:
            target: Target domain/URL
            mode: Mode (exact, domain, subdomains, prefix)
            limit: Maximum number of results
            country: Country code

        Returns:
            List of keyword dictionaries
        """
        params = {
            'from': 'positions_metrics',
            'target': target,
            'mode': mode,
            'limit': limit,
            'country': country,
            'order_by': 'traffic:desc'
        }

        data = self._make_request('positions_metrics', params)

        if data and 'keywords' in data:
            keywords = []
            for kw in data['keywords']:
                keywords.append({
                    'keyword': kw.get('keyword'),
                    'position': kw.get('position'),
                    'traffic': kw.get('traffic'),
                    'volume': kw.get('volume'),
                    'keyword_difficulty': kw.get('keyword_difficulty'),
                    'url': kw.get('url'),
                    'first_seen': kw.get('first_seen')
                })

            return keywords

        return None

    @log_execution_time(logger)
    def get_metrics_extended(
            self,
            target: str,
            mode: str = 'domain'
    ) -> Optional[Dict[str, Any]]:
        """
        Get extended metrics for a target

        Args:
            target: Target domain/URL
            mode: Mode (exact, domain, subdomains, prefix)

        Returns:
            Dictionary with extended metrics
        """
        params = {
            'from': 'metrics_extended',
            'target': target,
            'mode': mode
        }

        data = self._make_request('metrics_extended', params)

        if data:
            return {
                'domain': target,
                'domain_rating': data.get('domain_rating'),
                'ahrefs_rank': data.get('ahrefs_rank'),
                'url_rating': data.get('url_rating'),
                'referring_domains': data.get('refdomains'),
                'backlinks': data.get('backlinks'),
                'linked_domains': data.get('linked_domains'),
                'organic_traffic': data.get('traffic'),
                'organic_keywords': data.get('keywords'),
                'organic_value': data.get('value'),
                'organic_pages': data.get('pages'),
                'timestamp': datetime.now().isoformat()
            }

        return None

    @log_execution_time(logger)
    def get_broken_backlinks(
            self,
            target: str,
            mode: str = 'domain',
            limit: int = 100
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get broken backlinks (404s) for a target

        Args:
            target: Target domain/URL
            mode: Mode (exact, domain, subdomains, prefix)
            limit: Maximum number of results

        Returns:
            List of broken backlink dictionaries
        """
        params = {
            'from': 'broken_backlinks',
            'target': target,
            'mode': mode,
            'limit': limit
        }

        data = self._make_request('broken_backlinks', params)

        if data and 'backlinks' in data:
            broken_links = []
            for link in data['backlinks']:
                broken_links.append({
                    'url_from': link.get('url_from'),
                    'url_to': link.get('url_to'),
                    'anchor': link.get('anchor'),
                    'domain_rating': link.get('domain_rating'),
                    'http_code': link.get('http_code'),
                    'first_seen': link.get('first_seen')
                })

            return broken_links

        return None

    def analyze_domain(
            self,
            target: str,
            include_backlinks: bool = True,
            include_keywords: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive domain analysis

        Args:
            target: Target domain
            include_backlinks: Whether to fetch backlink data
            include_keywords: Whether to fetch keyword data

        Returns:
            Dictionary with complete analysis
        """
        if not self.enabled:
            return {'error': 'Ahrefs API not enabled'}

        analysis = {
            'domain': target,
            'timestamp': datetime.now().isoformat(),
            'metrics': None,
            'backlinks_sample': None,
            'referring_domains_sample': None,
            'organic_keywords_sample': None,
            'broken_backlinks': None
        }

        # Get extended metrics
        metrics = self.get_metrics_extended(target)
        if metrics:
            analysis['metrics'] = metrics

        # Get backlinks data
        if include_backlinks:
            backlinks = self.get_backlinks(target, limit=50)
            if backlinks:
                analysis['backlinks_sample'] = backlinks

            referring_domains = self.get_referring_domains(target, limit=50)
            if referring_domains:
                analysis['referring_domains_sample'] = referring_domains

            broken_links = self.get_broken_backlinks(target, limit=50)
            if broken_links:
                analysis['broken_backlinks'] = broken_links

        # Get keyword data
        if include_keywords:
            keywords = self.get_organic_keywords(target, limit=50)
            if keywords:
                analysis['organic_keywords_sample'] = keywords

        return analysis

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get API usage statistics

        Returns:
            Statistics dictionary
        """
        total = self.stats['total_requests']
        success_rate = (
            round(self.stats['successful_requests'] / total * 100, 2)
            if total > 0 else 0
        )

        return {
            'enabled': self.enabled,
            'total_requests': self.stats['total_requests'],
            'successful_requests': self.stats['successful_requests'],
            'failed_requests': self.stats['failed_requests'],
            'cached_requests': self.stats['cached_requests'],
            'success_rate': success_rate
        }

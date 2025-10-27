"""
DataForSEO API integration for SEO Auditor
Provides SERP data, keyword research, and on-page analysis
"""

import logging
import os
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

import requests
from requests.exceptions import RequestException

from utils.cache import CacheManager
from utils.logger import log_execution_time

logger = logging.getLogger(__name__)


class DataForSEOAPIError(Exception):
    """Custom exception for DataForSEO API errors"""
    pass


class DataForSEOAPI:
    """
    DataForSEO API client for SERP, keywords, and on-page analysis
    """

    # API configuration
    BASE_URL = "https://api.dataforseo.com/v3"

    def __init__(self, config: Dict = None, cache_manager: Optional[CacheManager] = None):
        """
        Initialize DataForSEO API client

        Args:
            config: Configuration dictionary
            cache_manager: Optional cache manager for API responses
        """
        self.config = config or {}
        self.cache_manager = cache_manager

        # Get API configuration
        dataforseo_config = self.config.get('integrations', {}).get('dataforseo', {})

        # API credentials
        self.username = os.getenv('DATAFORSEO_USERNAME') or dataforseo_config.get('username_env', '')
        self.password = os.getenv('DATAFORSEO_PASSWORD') or dataforseo_config.get('password_env', '')
        self.enabled = dataforseo_config.get('enabled', False) and bool(self.username) and bool(self.password)

        if not (self.username and self.password) and self.enabled:
            logger.warning("DataForSEO credentials not found. Set DATAFORSEO_USERNAME and DATAFORSEO_PASSWORD.")
            self.enabled = False

        # Create Basic Auth header
        if self.enabled:
            credentials = f"{self.username}:{self.password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            self.auth_header = f"Basic {encoded}"
        else:
            self.auth_header = None

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 0.5 seconds between requests

        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cached_requests': 0
        }

        if self.enabled:
            logger.info("DataForSEO API initialized and enabled")
        else:
            logger.info("DataForSEO API disabled or not configured")

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
            method: str = 'POST',
            data: Optional[List[Dict]] = None,
            cache_ttl: int = 86400
    ) -> Optional[Dict]:
        """
        Make API request with caching and error handling

        Args:
            endpoint: API endpoint path
            method: HTTP method (POST or GET)
            data: Request data for POST requests
            cache_ttl: Cache time-to-live in seconds

        Returns:
            API response data or None
        """
        if not self.enabled:
            logger.warning("DataForSEO API is not enabled")
            return None

        url = f"{self.BASE_URL}/{endpoint}"

        # Check cache
        cache_key = f"dataforseo_{endpoint}_{hash(str(data))}"
        if self.cache_manager and method == 'POST':
            cached_data = self.cache_manager.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for DataForSEO {endpoint}")
                self.stats['cached_requests'] += 1
                return cached_data

        # Rate limiting
        self._rate_limit()

        # Prepare headers
        headers = {
            'Authorization': self.auth_header,
            'Content-Type': 'application/json'
        }

        # Make request
        try:
            self.stats['total_requests'] += 1

            if method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=60)
            else:
                response = requests.get(url, headers=headers, timeout=60)

            response.raise_for_status()
            result = response.json()

            # Check for API errors
            if result.get('status_code') != 20000:
                error_msg = result.get('status_message', 'Unknown error')
                logger.error(f"DataForSEO API error: {error_msg}")
                self.stats['failed_requests'] += 1
                raise DataForSEOAPIError(error_msg)

            self.stats['successful_requests'] += 1

            # Cache successful response
            if self.cache_manager and method == 'POST':
                self.cache_manager.set(cache_key, result, cache_ttl)

            logger.debug(f"DataForSEO {endpoint} request successful")
            return result

        except RequestException as e:
            logger.error(f"DataForSEO API request failed: {e}")
            self.stats['failed_requests'] += 1
            return None
        except Exception as e:
            logger.error(f"Unexpected error in DataForSEO API: {e}")
            self.stats['failed_requests'] += 1
            return None

    @log_execution_time(logger)
    def get_serp_live(
            self,
            keyword: str,
            location_name: str = "United States",
            language_name: str = "English",
            device: str = "desktop",
            depth: int = 100
    ) -> Optional[Dict[str, Any]]:
        """
        Get live SERP results for a keyword

        Args:
            keyword: Search keyword
            location_name: Location for search
            language_name: Language for search
            device: Device type (desktop, mobile)
            depth: Number of results (max 700)

        Returns:
            Dictionary with SERP data
        """
        data = [{
            "keyword": keyword,
            "location_name": location_name,
            "language_name": language_name,
            "device": device,
            "depth": depth
        }]

        result = self._make_request('serp/google/organic/live/advanced', data=data)

        if result and 'tasks' in result:
            task = result['tasks'][0]
            if task['status_code'] == 20000 and task.get('result'):
                serp_data = task['result'][0]

                return {
                    'keyword': keyword,
                    'location': location_name,
                    'search_engine': 'google',
                    'total_count': serp_data.get('total_count'),
                    'organic_results': self._parse_organic_results(serp_data.get('items', [])),
                    'timestamp': datetime.now().isoformat()
                }

        return None

    def _parse_organic_results(self, items: List[Dict]) -> List[Dict]:
        """Parse organic SERP results"""
        results = []

        for item in items:
            if item.get('type') == 'organic':
                results.append({
                    'position': item.get('rank_absolute'),
                    'url': item.get('url'),
                    'domain': item.get('domain'),
                    'title': item.get('title'),
                    'description': item.get('description'),
                    'relative_url': item.get('relative_url')
                })

        return results

    @log_execution_time(logger)
    def get_keyword_data(
            self,
            keywords: List[str],
            location_code: int = 2840,  # United States
            language_code: str = "en"
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get keyword metrics (volume, CPC, competition)

        Args:
            keywords: List of keywords to check
            location_code: Location code
            language_code: Language code

        Returns:
            List of keyword data dictionaries
        """
        data = [{
            "keywords": keywords,
            "location_code": location_code,
            "language_code": language_code
        }]

        result = self._make_request(
            'keywords_data/google_ads/search_volume/live',
            data=data
        )

        if result and 'tasks' in result:
            task = result['tasks'][0]
            if task['status_code'] == 20000 and task.get('result'):
                keyword_results = []

                for kw_data in task['result']:
                    keyword_results.append({
                        'keyword': kw_data.get('keyword'),
                        'search_volume': kw_data.get('search_volume'),
                        'competition': kw_data.get('competition'),
                        'competition_level': kw_data.get('competition_level'),
                        'cpc': kw_data.get('cpc'),
                        'low_top_of_page_bid': kw_data.get('low_top_of_page_bid'),
                        'high_top_of_page_bid': kw_data.get('high_top_of_page_bid')
                    })

                return keyword_results

        return None

    @log_execution_time(logger)
    def create_onpage_task(
            self,
            target: str,
            max_crawl_pages: int = 100,
            enable_javascript: bool = False
    ) -> Optional[str]:
        """
        Create on-page analysis task

        Args:
            target: Target website URL
            max_crawl_pages: Maximum pages to crawl
            enable_javascript: Enable JS rendering

        Returns:
            Task ID or None
        """
        data = [{
            "target": target,
            "max_crawl_pages": max_crawl_pages,
            "enable_javascript": enable_javascript,
            "store_raw_html": False,
            "load_resources": True,
            "enable_browser_rendering": enable_javascript
        }]

        result = self._make_request('on_page/task_post', data=data)

        if result and 'tasks' in result:
            task = result['tasks'][0]
            if task['status_code'] == 20100:
                task_id = task['id']
                logger.info(f"OnPage task created: {task_id}")
                return task_id

        return None

    @log_execution_time(logger)
    def get_onpage_summary(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get on-page analysis summary

        Args:
            task_id: Task ID from create_onpage_task

        Returns:
            Summary data dictionary
        """
        result = self._make_request(f'on_page/summary/{task_id}', method='GET')

        if result and 'tasks' in result:
            task = result['tasks'][0]
            if task['status_code'] == 20000 and task.get('result'):
                summary = task['result'][0]

                return {
                    'task_id': task_id,
                    'crawl_progress': summary.get('crawl_progress'),
                    'crawl_status': summary.get('crawl_status'),
                    'pages_in_sitemap': summary.get('pages_in_sitemap'),
                    'pages_crawled': summary.get('pages_crawled'),
                    'pages_with_duplicate_title': summary.get('pages_with_duplicate_title'),
                    'pages_with_duplicate_description': summary.get('pages_with_duplicate_description'),
                    'pages_with_duplicate_content': summary.get('pages_with_duplicate_content'),
                    'broken_pages': summary.get('broken_pages'),
                    'broken_resources': summary.get('broken_resources'),
                    'checks': summary.get('checks', {}),
                    'timestamp': datetime.now().isoformat()
                }

        return None

    @log_execution_time(logger)
    def get_onpage_pages(
            self,
            task_id: str,
            limit: int = 100,
            filters: Optional[List] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get crawled pages with on-page metrics

        Args:
            task_id: Task ID from create_onpage_task
            limit: Maximum number of pages to return
            filters: Optional filters array

        Returns:
            List of page data dictionaries
        """
        data = [{
            "id": task_id,
            "limit": limit,
            "filters": filters or []
        }]

        result = self._make_request('on_page/pages', data=data)

        if result and 'tasks' in result:
            task = result['tasks'][0]
            if task['status_code'] == 20000 and task.get('result'):
                pages = []

                for page in task['result']:
                    pages.append({
                        'url': page.get('url'),
                        'meta': page.get('meta', {}),
                        'page_timing': page.get('page_timing', {}),
                        'onpage_score': page.get('onpage_score'),
                        'total_dom_size': page.get('total_dom_size'),
                        'custom_js_response': page.get('custom_js_response'),
                        'resource_errors': page.get('resource_errors', {}),
                        'broken_resources': page.get('broken_resources'),
                        'broken_links': page.get('broken_links'),
                        'duplicate_title': page.get('duplicate_title'),
                        'duplicate_description': page.get('duplicate_description'),
                        'duplicate_content': page.get('duplicate_content'),
                        'checks': page.get('checks', {}),
                        'content_parsing': page.get('content_parsing', {})
                    })

                return pages

        return None

    @log_execution_time(logger)
    def get_ranked_keywords(
            self,
            target: str,
            location_code: int = 2840,
            language_code: str = "en",
            limit: int = 100
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get keywords that a domain ranks for

        Args:
            target: Target domain
            location_code: Location code
            language_code: Language code
            limit: Maximum number of keywords

        Returns:
            List of ranking keywords
        """
        data = [{
            "target": target,
            "location_code": location_code,
            "language_code": language_code,
            "limit": limit
        }]

        result = self._make_request(
            'dataforseo_labs/google/ranked_keywords/live',
            data=data
        )

        if result and 'tasks' in result:
            task = result['tasks'][0]
            if task['status_code'] == 20000 and task.get('result'):
                keywords = []

                for item in task['result'][0].get('items', []):
                    keywords.append({
                        'keyword': item.get('keyword'),
                        'position': item.get('ranked_serp_element', {}).get('serp_item', {}).get('rank_absolute'),
                        'search_volume': item.get('keyword_data', {}).get('keyword_info', {}).get('search_volume'),
                        'competition': item.get('keyword_data', {}).get('keyword_info', {}).get('competition'),
                        'cpc': item.get('keyword_data', {}).get('keyword_info', {}).get('cpc')
                    })

                return keywords

        return None

    def comprehensive_analysis(
            self,
            target: str,
            keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive SEO analysis

        Args:
            target: Target website URL
            keywords: Optional list of keywords to check

        Returns:
            Dictionary with complete analysis
        """
        if not self.enabled:
            return {'error': 'DataForSEO API not enabled'}

        analysis = {
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'onpage_task_id': None,
            'onpage_summary': None,
            'ranked_keywords': None,
            'keyword_metrics': None
        }

        # Create on-page task
        task_id = self.create_onpage_task(target, max_crawl_pages=100)
        if task_id:
            analysis['onpage_task_id'] = task_id

            # Wait for task completion (in production, use task_ready endpoint)
            time.sleep(5)

            # Get summary
            summary = self.get_onpage_summary(task_id)
            if summary:
                analysis['onpage_summary'] = summary

        # Get ranked keywords
        ranked_kws = self.get_ranked_keywords(target, limit=50)
        if ranked_kws:
            analysis['ranked_keywords'] = ranked_kws

        # Get keyword metrics if provided
        if keywords:
            kw_metrics = self.get_keyword_data(keywords)
            if kw_metrics:
                analysis['keyword_metrics'] = kw_metrics

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

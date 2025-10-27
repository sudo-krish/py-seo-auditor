"""
Google APIs integration for SEO Auditor
Provides Google Search Console and PageSpeed Insights data
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time

import requests
from requests.exceptions import RequestException
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from utils.cache import CacheManager
from utils.logger import log_execution_time

logger = logging.getLogger(__name__)


class GoogleAPIsError(Exception):
    """Custom exception for Google APIs errors"""
    pass


class GoogleSearchConsoleAPI:
    """
    Google Search Console API client
    """

    SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

    def __init__(self, config: Dict = None, cache_manager: Optional[CacheManager] = None):
        """
        Initialize Google Search Console API client

        Args:
            config: Configuration dictionary
            cache_manager: Optional cache manager
        """
        self.config = config or {}
        self.cache_manager = cache_manager

        # Get API configuration
        google_config = self.config.get('integrations', {}).get('google', {}).get('search_console', {})

        # Service account credentials
        self.credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE') or google_config.get('credentials_file', '')
        self.enabled = google_config.get('enabled', False) and bool(self.credentials_file)

        # Initialize service
        self.service = None
        if self.enabled:
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_file,
                    scopes=self.SCOPES
                )
                self.service = build('searchconsole', 'v1', credentials=credentials)
                logger.info("Google Search Console API initialized")
            except Exception as e:
                logger.error(f"Failed to initialize GSC API: {e}")
                self.enabled = False

        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cached_requests': 0
        }

    @log_execution_time(logger)
    def get_sites(self) -> Optional[List[str]]:
        """
        Get list of verified sites

        Returns:
            List of site URLs
        """
        if not self.enabled:
            return None

        try:
            self.stats['total_requests'] += 1

            site_list = self.service.sites().list().execute()
            sites = [site['siteUrl'] for site in site_list.get('siteEntry', [])]

            self.stats['successful_requests'] += 1
            logger.info(f"Found {len(sites)} verified sites")

            return sites

        except HttpError as e:
            logger.error(f"GSC API error: {e}")
            self.stats['failed_requests'] += 1
            return None

    @log_execution_time(logger)
    def get_search_analytics(
            self,
            site_url: str,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            dimensions: Optional[List[str]] = None,
            row_limit: int = 1000
    ) -> Optional[Dict[str, Any]]:
        """
        Get search analytics data

        Args:
            site_url: Site URL (use sc-domain: format for domain property)
            start_date: Start date (YYYY-MM-DD), defaults to 90 days ago
            end_date: End date (YYYY-MM-DD), defaults to 3 days ago
            dimensions: List of dimensions (query, page, country, device, searchAppearance)
            row_limit: Maximum rows to return

        Returns:
            Dictionary with analytics data
        """
        if not self.enabled:
            return None

        # Set default dates
        if not end_date:
            end_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

        dimensions = dimensions or ['query', 'page']

        # Check cache
        cache_key = f"gsc_{site_url}_{start_date}_{end_date}_{'-'.join(dimensions)}"
        if self.cache_manager:
            cached_data = self.cache_manager.get(cache_key)
            if cached_data:
                logger.debug("Cache hit for GSC analytics")
                self.stats['cached_requests'] += 1
                return cached_data

        try:
            self.stats['total_requests'] += 1

            request_body = {
                'startDate': start_date,
                'endDate': end_date,
                'dimensions': dimensions,
                'rowLimit': row_limit
            }

            response = self.service.searchanalytics().query(
                siteUrl=site_url,
                body=request_body
            ).execute()

            result = {
                'site_url': site_url,
                'start_date': start_date,
                'end_date': end_date,
                'dimensions': dimensions,
                'rows': response.get('rows', []),
                'row_count': len(response.get('rows', [])),
                'timestamp': datetime.now().isoformat()
            }

            self.stats['successful_requests'] += 1

            # Cache result
            if self.cache_manager:
                self.cache_manager.set(cache_key, result, 43200)  # 12 hours

            logger.info(f"Retrieved {result['row_count']} rows from GSC")
            return result

        except HttpError as e:
            logger.error(f"GSC search analytics error: {e}")
            self.stats['failed_requests'] += 1
            return None

    @log_execution_time(logger)
    def get_sitemaps(self, site_url: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get submitted sitemaps

        Args:
            site_url: Site URL

        Returns:
            List of sitemap data
        """
        if not self.enabled:
            return None

        try:
            self.stats['total_requests'] += 1

            sitemaps = self.service.sitemaps().list(siteUrl=site_url).execute()

            sitemap_list = []
            for sitemap in sitemaps.get('sitemap', []):
                sitemap_list.append({
                    'path': sitemap.get('path'),
                    'last_submitted': sitemap.get('lastSubmitted'),
                    'is_pending': sitemap.get('isPending'),
                    'is_sitemaps_index': sitemap.get('isSitemapsIndex'),
                    'contents': sitemap.get('contents', [])
                })

            self.stats['successful_requests'] += 1
            return sitemap_list

        except HttpError as e:
            logger.error(f"GSC sitemaps error: {e}")
            self.stats['failed_requests'] += 1
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get API usage statistics"""
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


class PageSpeedInsightsAPI:
    """
    Google PageSpeed Insights API client
    """

    API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

    def __init__(self, config: Dict = None, cache_manager: Optional[CacheManager] = None):
        """
        Initialize PageSpeed Insights API client

        Args:
            config: Configuration dictionary
            cache_manager: Optional cache manager
        """
        self.config = config or {}
        self.cache_manager = cache_manager

        # Get API configuration
        psi_config = self.config.get('integrations', {}).get('google', {}).get('pagespeed_insights', {})

        # API key
        self.api_key = os.getenv('GOOGLE_API_KEY') or ''
        self.enabled = psi_config.get('enabled', False)
        self.strategy = psi_config.get('strategy', 'mobile')
        self.categories = psi_config.get('categories', ['performance', 'accessibility', 'best-practices', 'seo'])

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 2.0  # 2 seconds between requests

        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cached_requests': 0
        }

        if self.enabled:
            logger.info("PageSpeed Insights API initialized")
        else:
            logger.info("PageSpeed Insights API disabled")

    def _rate_limit(self):
        """Apply rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    @log_execution_time(logger)
    def analyze_url(
            self,
            url: str,
            strategy: Optional[str] = None,
            categories: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze URL with PageSpeed Insights

        Args:
            url: URL to analyze
            strategy: Strategy (mobile or desktop)
            categories: List of categories to analyze

        Returns:
            Dictionary with PSI results
        """
        if not self.enabled:
            return None

        strategy = strategy or self.strategy
        categories = categories or self.categories

        # Check cache
        cache_key = f"psi_{url}_{strategy}"
        if self.cache_manager:
            cached_data = self.cache_manager.get(cache_key)
            if cached_data:
                logger.debug("Cache hit for PageSpeed Insights")
                self.stats['cached_requests'] += 1
                return cached_data

        # Rate limiting
        self._rate_limit()

        # Build request
        params = {
            'url': url,
            'strategy': strategy
        }

        for category in categories:
            params[f'category'] = category

        if self.api_key:
            params['key'] = self.api_key

        try:
            self.stats['total_requests'] += 1

            response = requests.get(self.API_URL, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            # Extract key metrics
            lighthouse_result = data.get('lighthouseResult', {})
            categories_data = lighthouse_result.get('categories', {})
            audits = lighthouse_result.get('audits', {})

            result = {
                'url': url,
                'strategy': strategy,
                'fetch_time': lighthouse_result.get('fetchTime'),
                'scores': {
                    'performance': categories_data.get('performance', {}).get('score', 0) * 100,
                    'accessibility': categories_data.get('accessibility', {}).get('score', 0) * 100,
                    'best_practices': categories_data.get('best-practices', {}).get('score', 0) * 100,
                    'seo': categories_data.get('seo', {}).get('score', 0) * 100
                },
                'core_web_vitals': self._extract_core_web_vitals(audits),
                'opportunities': self._extract_opportunities(audits),
                'diagnostics': self._extract_diagnostics(audits),
                'timestamp': datetime.now().isoformat()
            }

            self.stats['successful_requests'] += 1

            # Cache result
            if self.cache_manager:
                self.cache_manager.set(cache_key, result, 86400)  # 24 hours

            logger.info(f"PSI analysis complete for {url} ({strategy})")
            return result

        except RequestException as e:
            logger.error(f"PageSpeed Insights API error: {e}")
            self.stats['failed_requests'] += 1
            return None

    def _extract_core_web_vitals(self, audits: Dict) -> Dict[str, Any]:
        """Extract Core Web Vitals from audits"""
        return {
            'lcp': {
                'value': audits.get('largest-contentful-paint', {}).get('numericValue'),
                'displayValue': audits.get('largest-contentful-paint', {}).get('displayValue'),
                'score': audits.get('largest-contentful-paint', {}).get('score')
            },
            'inp': {
                'value': audits.get('interaction-to-next-paint', {}).get('numericValue'),
                'displayValue': audits.get('interaction-to-next-paint', {}).get('displayValue'),
                'score': audits.get('interaction-to-next-paint', {}).get('score')
            },
            'cls': {
                'value': audits.get('cumulative-layout-shift', {}).get('numericValue'),
                'displayValue': audits.get('cumulative-layout-shift', {}).get('displayValue'),
                'score': audits.get('cumulative-layout-shift', {}).get('score')
            },
            'fcp': {
                'value': audits.get('first-contentful-paint', {}).get('numericValue'),
                'displayValue': audits.get('first-contentful-paint', {}).get('displayValue'),
                'score': audits.get('first-contentful-paint', {}).get('score')
            },
            'ttfb': {
                'value': audits.get('server-response-time', {}).get('numericValue'),
                'displayValue': audits.get('server-response-time', {}).get('displayValue'),
                'score': audits.get('server-response-time', {}).get('score')
            }
        }

    def _extract_opportunities(self, audits: Dict) -> List[Dict]:
        """Extract performance opportunities"""
        opportunities = []

        opportunity_audits = [
            'unused-css-rules', 'unused-javascript', 'modern-image-formats',
            'offscreen-images', 'render-blocking-resources', 'unminified-css',
            'unminified-javascript', 'efficiently-encode-images'
        ]

        for audit_id in opportunity_audits:
            audit = audits.get(audit_id, {})
            if audit.get('score', 1) < 1:
                opportunities.append({
                    'id': audit_id,
                    'title': audit.get('title'),
                    'description': audit.get('description'),
                    'score': audit.get('score'),
                    'displayValue': audit.get('displayValue')
                })

        return opportunities

    def _extract_diagnostics(self, audits: Dict) -> List[Dict]:
        """Extract diagnostic information"""
        diagnostics = []

        diagnostic_audits = [
            'total-byte-weight', 'dom-size', 'critical-request-chains',
            'mainthread-work-breakdown', 'bootup-time'
        ]

        for audit_id in diagnostic_audits:
            audit = audits.get(audit_id, {})
            if audit:
                diagnostics.append({
                    'id': audit_id,
                    'title': audit.get('title'),
                    'displayValue': audit.get('displayValue'),
                    'score': audit.get('score')
                })

        return diagnostics

    def get_statistics(self) -> Dict[str, Any]:
        """Get API usage statistics"""
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


class GoogleAPIs:
    """
    Unified Google APIs client
    """

    def __init__(self, config: Dict = None, cache_manager: Optional[CacheManager] = None):
        """
        Initialize all Google APIs

        Args:
            config: Configuration dictionary
            cache_manager: Optional cache manager
        """
        self.search_console = GoogleSearchConsoleAPI(config, cache_manager)
        self.pagespeed = PageSpeedInsightsAPI(config, cache_manager)

    def get_combined_statistics(self) -> Dict[str, Any]:
        """Get statistics from all Google APIs"""
        return {
            'search_console': self.search_console.get_statistics(),
            'pagespeed_insights': self.pagespeed.get_statistics()
        }

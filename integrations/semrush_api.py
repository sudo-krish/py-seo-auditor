"""
SEMrush API integration for SEO Auditor
Provides domain analytics, keyword research, and competitor analysis
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import csv
from io import StringIO

import requests
from requests.exceptions import RequestException

from utils.cache import CacheManager
from utils.logger import log_execution_time

logger = logging.getLogger(__name__)


class SEMrushAPIError(Exception):
    """Custom exception for SEMrush API errors"""
    pass


class SEMrushAPI:
    """
    SEMrush API client for domain and keyword analysis
    """

    # API configuration
    BASE_URL = "https://api.semrush.com"

    # Database codes
    DATABASES = {
        'us': 'us',
        'uk': 'uk',
        'ca': 'ca',
        'au': 'au',
        'global': 'us'
    }

    def __init__(self, config: Dict = None, cache_manager: Optional[CacheManager] = None):
        """
        Initialize SEMrush API client

        Args:
            config: Configuration dictionary
            cache_manager: Optional cache manager for API responses
        """
        self.config = config or {}
        self.cache_manager = cache_manager

        # Get API configuration
        semrush_config = self.config.get('integrations', {}).get('semrush', {})

        # API credentials
        self.api_key = os.getenv('SEMRUSH_API_KEY') or semrush_config.get('api_key_env', '')
        self.enabled = semrush_config.get('enabled', False) and bool(self.api_key)
        self.database = semrush_config.get('database', 'us')

        if not self.api_key and self.enabled:
            logger.warning("SEMrush API key not found. Set SEMRUSH_API_KEY environment variable.")
            self.enabled = False

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests

        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cached_requests': 0,
            'api_units_used': 0
        }

        if self.enabled:
            logger.info("SEMrush API initialized and enabled")
        else:
            logger.info("SEMrush API disabled or not configured")

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
    ) -> Optional[str]:
        """
        Make API request with caching and error handling

        Args:
            endpoint: API endpoint path
            params: Request parameters
            cache_ttl: Cache time-to-live in seconds

        Returns:
            CSV response data as string or None
        """
        if not self.enabled:
            logger.warning("SEMrush API is not enabled")
            return None

        # Add API key
        params['key'] = self.api_key
        params['export_columns'] = params.get('export_columns', '')

        # Build URL
        url = f"{self.BASE_URL}/{endpoint}"

        # Check cache
        cache_key = f"semrush_{endpoint}_{hash(frozenset(params.items()))}"
        if self.cache_manager:
            cached_data = self.cache_manager.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for SEMrush {endpoint}")
                self.stats['cached_requests'] += 1
                return cached_data

        # Rate limiting
        self._rate_limit()

        # Make request
        try:
            self.stats['total_requests'] += 1

            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()

            # Check for API errors
            csv_data = response.text
            if 'ERROR' in csv_data[:100]:
                logger.error(f"SEMrush API error: {csv_data[:200]}")
                self.stats['failed_requests'] += 1
                raise SEMrushAPIError(csv_data)

            self.stats['successful_requests'] += 1
            self.stats['api_units_used'] += 1  # Approximate

            # Cache successful response
            if self.cache_manager:
                self.cache_manager.set(cache_key, csv_data, cache_ttl)

            logger.debug(f"SEMrush {endpoint} request successful")
            return csv_data

        except RequestException as e:
            logger.error(f"SEMrush API request failed: {e}")
            self.stats['failed_requests'] += 1
            return None
        except Exception as e:
            logger.error(f"Unexpected error in SEMrush API: {e}")
            self.stats['failed_requests'] += 1
            return None

    def _parse_csv_response(self, csv_data: str) -> List[Dict[str, Any]]:
        """Parse CSV response into list of dictionaries"""
        if not csv_data:
            return []

        try:
            reader = csv.DictReader(StringIO(csv_data), delimiter=';')
            return list(reader)
        except Exception as e:
            logger.error(f"Error parsing CSV response: {e}")
            return []

    @log_execution_time(logger)
    def get_domain_overview(
            self,
            domain: str,
            database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get domain overview with key metrics

        Args:
            domain: Target domain
            database: Database code (us, uk, ca, etc.)

        Returns:
            Dictionary with domain metrics
        """
        database = database or self.database

        params = {
            'type': 'domain_ranks',
            'domain': domain,
            'database': database,
            'export_columns': 'Dn,Rk,Or,Ot,Oc,Ad,At,Ac,Sh'
        }

        csv_data = self._make_request('analytics/v1/', params)

        if csv_data:
            rows = self._parse_csv_response(csv_data)
            if rows:
                row = rows[0]
                return {
                    'domain': domain,
                    'rank': int(row.get('Rk', 0)),
                    'organic_keywords': int(row.get('Or', 0)),
                    'organic_traffic': int(row.get('Ot', 0)),
                    'organic_cost': float(row.get('Oc', 0)),
                    'adwords_keywords': int(row.get('Ad', 0)),
                    'adwords_traffic': int(row.get('At', 0)),
                    'adwords_cost': float(row.get('Ac', 0)),
                    'timestamp': datetime.now().isoformat()
                }

        return None

    @log_execution_time(logger)
    def get_organic_keywords(
            self,
            domain: str,
            database: Optional[str] = None,
            limit: int = 100,
            position_from: int = 1,
            position_to: int = 100
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get organic keywords ranking for domain

        Args:
            domain: Target domain
            database: Database code
            limit: Maximum number of keywords
            position_from: Filter by position from
            position_to: Filter by position to

        Returns:
            List of keyword dictionaries
        """
        database = database or self.database

        params = {
            'type': 'domain_organic',
            'domain': domain,
            'database': database,
            'display_limit': limit,
            'export_columns': 'Ph,Po,Pp,Pd,Nq,Cp,Ur,Tr,Tc,Co,Nr,Td',
            'display_filter': f'+|Po|Lt|{position_to}|+|Po|Gt|{position_from}'
        }

        csv_data = self._make_request('analytics/v1/', params)

        if csv_data:
            rows = self._parse_csv_response(csv_data)
            keywords = []

            for row in rows:
                try:
                    keywords.append({
                        'keyword': row.get('Ph', ''),
                        'position': int(row.get('Po', 0)),
                        'previous_position': int(row.get('Pp', 0)),
                        'search_volume': int(row.get('Nq', 0)),
                        'cpc': float(row.get('Cp', 0)),
                        'url': row.get('Ur', ''),
                        'traffic_percent': float(row.get('Tr', 0)),
                        'traffic_cost': float(row.get('Tc', 0)),
                        'competition': float(row.get('Co', 0)),
                        'results': int(row.get('Nr', 0)),
                        'trend': row.get('Td', '')
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing keyword row: {e}")

            return keywords

        return None

    @log_execution_time(logger)
    def get_backlinks_overview(
            self,
            target: str,
            target_type: str = 'root_domain'
    ) -> Optional[Dict[str, Any]]:
        """
        Get backlinks overview for target

        Args:
            target: Target domain or URL
            target_type: Type (root_domain, domain, url)

        Returns:
            Dictionary with backlinks metrics
        """
        params = {
            'type': 'backlinks_overview',
            'target': target,
            'target_type': target_type,
            'export_columns': 'ascore,total,domains_num,urls_num,ips_num,ipclassc_num,follows_num,nofollows_num,sponsored_num,ugc_num,texts_num,forms_num,frames_num,images_num'
        }

        csv_data = self._make_request('analytics/v1/', params)

        if csv_data:
            rows = self._parse_csv_response(csv_data)
            if rows:
                row = rows[0]
                return {
                    'target': target,
                    'authority_score': int(row.get('ascore', 0)),
                    'backlinks_total': int(row.get('total', 0)),
                    'referring_domains': int(row.get('domains_num', 0)),
                    'referring_ips': int(row.get('ips_num', 0)),
                    'dofollow_links': int(row.get('follows_num', 0)),
                    'nofollow_links': int(row.get('nofollows_num', 0)),
                    'text_links': int(row.get('texts_num', 0)),
                    'image_links': int(row.get('images_num', 0)),
                    'timestamp': datetime.now().isoformat()
                }

        return None

    @log_execution_time(logger)
    def get_competitors(
            self,
            domain: str,
            database: Optional[str] = None,
            limit: int = 10
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get organic competitors for domain

        Args:
            domain: Target domain
            database: Database code
            limit: Maximum competitors to return

        Returns:
            List of competitor dictionaries
        """
        database = database or self.database

        params = {
            'type': 'domain_organic_organic',
            'domain': domain,
            'database': database,
            'display_limit': limit,
            'export_columns': 'Dn,Cr,Np,Or,Ot,Oc,Ad'
        }

        csv_data = self._make_request('analytics/v1/', params)

        if csv_data:
            rows = self._parse_csv_response(csv_data)
            competitors = []

            for row in rows:
                try:
                    competitors.append({
                        'domain': row.get('Dn', ''),
                        'competition_level': float(row.get('Cr', 0)),
                        'common_keywords': int(row.get('Np', 0)),
                        'organic_keywords': int(row.get('Or', 0)),
                        'organic_traffic': int(row.get('Ot', 0)),
                        'organic_cost': float(row.get('Oc', 0)),
                        'adwords_keywords': int(row.get('Ad', 0))
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing competitor row: {e}")

            return competitors

        return None

    @log_execution_time(logger)
    def get_keyword_difficulty(
            self,
            keywords: List[str],
            database: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get keyword difficulty metrics

        Args:
            keywords: List of keywords to check
            database: Database code

        Returns:
            List of keyword difficulty data
        """
        database = database or self.database

        # SEMrush API expects semicolon-separated keywords
        keyword_list = ';'.join(keywords[:100])  # Max 100 keywords

        params = {
            'type': 'phrase_these',
            'phrase': keyword_list,
            'database': database,
            'export_columns': 'Ph,Nq,Cp,Co,Nr,Td,Kd'
        }

        csv_data = self._make_request('analytics/v1/', params)

        if csv_data:
            rows = self._parse_csv_response(csv_data)
            results = []

            for row in rows:
                try:
                    results.append({
                        'keyword': row.get('Ph', ''),
                        'search_volume': int(row.get('Nq', 0)),
                        'cpc': float(row.get('Cp', 0)),
                        'competition': float(row.get('Co', 0)),
                        'results': int(row.get('Nr', 0)),
                        'trend': row.get('Td', ''),
                        'keyword_difficulty': int(row.get('Kd', 0))
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing keyword difficulty row: {e}")

            return results

        return None

    @log_execution_time(logger)
    def check_api_units(self) -> Optional[int]:
        """
        Check remaining API units

        Returns:
            Number of remaining API units
        """
        try:
            url = f"{self.BASE_URL}/users/countapiunits.html"
            params = {'key': self.api_key}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            units = int(response.text.strip())
            logger.info(f"SEMrush API units remaining: {units}")
            return units

        except Exception as e:
            logger.error(f"Error checking API units: {e}")
            return None

    def comprehensive_analysis(
            self,
            domain: str,
            include_competitors: bool = True,
            include_backlinks: bool = True
    ) -> Dict[str, Any]:
        """
        Perform comprehensive domain analysis

        Args:
            domain: Target domain
            include_competitors: Whether to fetch competitor data
            include_backlinks: Whether to fetch backlink data

        Returns:
            Dictionary with complete analysis
        """
        if not self.enabled:
            return {'error': 'SEMrush API not enabled'}

        analysis = {
            'domain': domain,
            'timestamp': datetime.now().isoformat(),
            'overview': None,
            'top_keywords': None,
            'competitors': None,
            'backlinks': None
        }

        # Get domain overview
        overview = self.get_domain_overview(domain)
        if overview:
            analysis['overview'] = overview

        # Get top organic keywords
        keywords = self.get_organic_keywords(domain, limit=50)
        if keywords:
            analysis['top_keywords'] = keywords

        # Get competitors
        if include_competitors:
            competitors = self.get_competitors(domain, limit=10)
            if competitors:
                analysis['competitors'] = competitors

        # Get backlinks overview
        if include_backlinks:
            backlinks = self.get_backlinks_overview(domain)
            if backlinks:
                analysis['backlinks'] = backlinks

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
            'api_units_used': self.stats['api_units_used'],
            'success_rate': success_rate
        }

"""
Screaming Frog SEO Spider integration for SEO Auditor
Supports CLI automation and CSV import parsing
"""

import logging
import os
import subprocess
import csv
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import platform

from utils.logger import log_execution_time
from core.crawler import CrawlResult

logger = logging.getLogger(__name__)


class ScreamingFrogError(Exception):
    """Custom exception for Screaming Frog errors"""
    pass


class ScreamingFrogCLI:
    """
    Screaming Frog CLI automation wrapper
    """

    # Default CLI paths by OS
    CLI_PATHS = {
        'Windows': r'C:\Program Files (x86)\Screaming Frog SEO Spider\ScreamingFrogSEOSpiderCli.exe',
        'Darwin': '/Applications/Screaming Frog SEO Spider.app/Contents/MacOS/ScreamingFrogSEOSpiderLauncher',
        'Linux': '/opt/screamingfrogseospider/ScreamingFrogSEOSpiderCli'
    }

    def __init__(self, config: Dict = None):
        """
        Initialize Screaming Frog CLI

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # Get configuration
        sf_config = self.config.get('integrations', {}).get('screaming_frog', {})
        self.enabled = sf_config.get('enabled', False)
        self.cli_path = sf_config.get('cli_path') or self._get_default_cli_path()
        self.license_key = os.getenv('SCREAMING_FROG_LICENSE')
        self.output_dir = Path(sf_config.get('output_dir', 'data/screaming_frog'))

        # CLI options
        self.headless = sf_config.get('headless', True)
        self.max_crawl_depth = sf_config.get('max_crawl_depth', 3)
        self.max_urls = sf_config.get('max_urls', 1000)

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Verify CLI exists
        if self.enabled and not Path(self.cli_path).exists():
            logger.warning(f"Screaming Frog CLI not found at {self.cli_path}")
            self.enabled = False

        # Statistics
        self.stats = {
            'total_crawls': 0,
            'successful_crawls': 0,
            'failed_crawls': 0
        }

        if self.enabled:
            logger.info(f"Screaming Frog CLI initialized at {self.cli_path}")
        else:
            logger.info("Screaming Frog integration disabled")

    def _get_default_cli_path(self) -> str:
        """Get default CLI path for current OS"""
        system = platform.system()
        return self.CLI_PATHS.get(system, '')

    @log_execution_time(logger)
    def crawl(
            self,
            url: str,
            output_name: Optional[str] = None,
            save_crawl: bool = True
    ) -> Optional[str]:
        """
        Execute Screaming Frog crawl via CLI

        Args:
            url: URL to crawl
            output_name: Output file name (without extension)
            save_crawl: Whether to save crawl (requires license)

        Returns:
            Path to saved crawl file or None
        """
        if not self.enabled:
            logger.warning("Screaming Frog CLI is not enabled")
            return None

        self.stats['total_crawls'] += 1

        # Generate output name
        if not output_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            domain = url.replace('https://', '').replace('http://', '').split('/')[0]
            output_name = f"{domain}_{timestamp}"

        output_path = self.output_dir / f"{output_name}.seospider"

        # Build command
        cmd = [self.cli_path, '--crawl', url]

        if self.headless:
            cmd.append('--headless')

        if save_crawl:
            cmd.extend(['--save-crawl', '--output-folder', str(self.output_dir)])

            # Note: --save-crawl requires a license
            if not self.license_key:
                logger.warning("License key required for --save-crawl functionality")

        # Add crawl configuration
        cmd.extend([
            '--max-crawl-depth', str(self.max_crawl_depth),
            '--max-urls', str(self.max_urls)
        ])

        try:
            logger.info(f"Starting Screaming Frog crawl of {url}")

            # Execute command
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for completion
            stdout, stderr = process.communicate(timeout=3600)  # 1 hour timeout

            if process.returncode == 0:
                self.stats['successful_crawls'] += 1
                logger.info(f"Crawl completed successfully: {output_name}")

                if save_crawl and output_path.exists():
                    return str(output_path)
                return output_name
            else:
                self.stats['failed_crawls'] += 1
                logger.error(f"Crawl failed with return code {process.returncode}")
                logger.error(f"Error: {stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("Crawl timed out after 1 hour")
            self.stats['failed_crawls'] += 1
            process.kill()
            return None
        except Exception as e:
            logger.error(f"Error executing Screaming Frog CLI: {e}")
            self.stats['failed_crawls'] += 1
            return None

    @log_execution_time(logger)
    def export_csv(
            self,
            crawl_file: str,
            export_type: str = 'internal_all'
    ) -> Optional[str]:
        """
        Export crawl data to CSV

        Args:
            crawl_file: Path to .seospider crawl file
            export_type: Type of export (internal_all, external_all, response_codes, etc.)

        Returns:
            Path to exported CSV file
        """
        if not self.enabled:
            return None

        output_csv = Path(crawl_file).with_suffix('.csv')

        cmd = [
            self.cli_path,
            '--open', crawl_file,
            '--export-tabs', export_type,
            '--export-format', 'csv',
            '--output-folder', str(self.output_dir)
        ]

        try:
            subprocess.run(cmd, check=True, timeout=600)
            logger.info(f"Exported CSV: {output_csv}")
            return str(output_csv)
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get CLI usage statistics"""
        return {
            'enabled': self.enabled,
            'total_crawls': self.stats['total_crawls'],
            'successful_crawls': self.stats['successful_crawls'],
            'failed_crawls': self.stats['failed_crawls']
        }


class ScreamingFrogParser:
    """
    Parser for Screaming Frog CSV exports
    """

    # Column name mappings (SF export -> our format)
    COLUMN_MAPPINGS = {
        'Address': 'url',
        'Status Code': 'status_code',
        'Title 1': 'title',
        'Meta Description 1': 'meta_description',
        'Meta Keywords 1': 'meta_keywords',
        'H1-1': 'h1',
        'H1-2': 'h1_2',
        'Word Count': 'word_count',
        'Canonical Link Element 1': 'canonical_url',
        'Meta Robots 1': 'meta_robots',
        'Indexability': 'indexability',
        'Indexability Status': 'indexability_status'
    }

    def __init__(self):
        """Initialize parser"""
        logger.info("Screaming Frog parser initialized")

    @log_execution_time(logger)
    def parse_internal_all_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        Parse Screaming Frog 'Internal - All' CSV export

        Args:
            csv_path: Path to CSV file

        Returns:
            List of parsed page data dictionaries
        """
        pages = []

        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    page_data = self._parse_row(row)
                    if page_data:
                        pages.append(page_data)

            logger.info(f"Parsed {len(pages)} pages from {csv_path}")
            return pages

        except Exception as e:
            logger.error(f"Error parsing CSV {csv_path}: {e}")
            return []

    def _parse_row(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Parse a single CSV row"""
        try:
            # Map columns
            page_data = {}

            for sf_col, our_col in self.COLUMN_MAPPINGS.items():
                if sf_col in row:
                    page_data[our_col] = row[sf_col]

            # Parse status code to int
            if 'status_code' in page_data:
                try:
                    page_data['status_code'] = int(page_data['status_code'])
                except (ValueError, TypeError):
                    page_data['status_code'] = None

            # Parse word count to int
            if 'word_count' in page_data:
                try:
                    page_data['word_count'] = int(page_data['word_count'])
                except (ValueError, TypeError):
                    page_data['word_count'] = 0

            # Collect H1 tags
            h1_tags = []
            if page_data.get('h1'):
                h1_tags.append(page_data['h1'])
            if page_data.get('h1_2'):
                h1_tags.append(page_data['h1_2'])
            page_data['h1_tags'] = h1_tags

            # Add timestamp
            page_data['crawl_timestamp'] = datetime.now().isoformat()

            return page_data

        except Exception as e:
            logger.error(f"Error parsing row: {e}")
            return None

    def convert_to_crawl_results(
            self,
            pages: List[Dict[str, Any]]
    ) -> List[CrawlResult]:
        """
        Convert Screaming Frog data to CrawlResult objects

        Args:
            pages: List of parsed page data

        Returns:
            List of CrawlResult objects
        """
        crawl_results = []

        for page in pages:
            try:
                result = CrawlResult(page.get('url', ''))

                # Map basic fields
                result.status_code = page.get('status_code')
                result.title = page.get('title')
                result.meta_description = page.get('meta_description')
                result.meta_keywords = page.get('meta_keywords')
                result.meta_robots = page.get('meta_robots')
                result.canonical_url = page.get('canonical_url')
                result.h1_tags = page.get('h1_tags', [])
                result.word_count = page.get('word_count', 0)

                # Set timestamp
                if page.get('crawl_timestamp'):
                    result.crawl_timestamp = datetime.fromisoformat(page['crawl_timestamp'])

                crawl_results.append(result)

            except Exception as e:
                logger.error(f"Error converting page to CrawlResult: {e}")

        logger.info(f"Converted {len(crawl_results)} pages to CrawlResult objects")
        return crawl_results

    def parse_links_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        Parse Screaming Frog 'All Links' export

        Args:
            csv_path: Path to CSV file

        Returns:
            List of link data
        """
        links = []

        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    link_data = {
                        'source': row.get('Source'),
                        'destination': row.get('Destination'),
                        'anchor_text': row.get('Anchor'),
                        'link_type': row.get('Type'),
                        'rel': row.get('Rel'),
                        'status_code': row.get('Status Code')
                    }
                    links.append(link_data)

            logger.info(f"Parsed {len(links)} links from {csv_path}")
            return links

        except Exception as e:
            logger.error(f"Error parsing links CSV: {e}")
            return []


class ScreamingFrogIntegration:
    """
    Unified Screaming Frog integration
    """

    def __init__(self, config: Dict = None):
        """
        Initialize Screaming Frog integration

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.cli = ScreamingFrogCLI(config)
        self.parser = ScreamingFrogParser()

    @log_execution_time(logger)
    def crawl_and_parse(
            self,
            url: str,
            auto_export: bool = True
    ) -> Optional[List[CrawlResult]]:
        """
        Crawl URL with CLI and parse results

        Args:
            url: URL to crawl
            auto_export: Automatically export and parse CSV

        Returns:
            List of CrawlResult objects
        """
        # Execute crawl
        crawl_file = self.cli.crawl(url, save_crawl=True)

        if not crawl_file:
            logger.error("Crawl failed or not saved")
            return None

        if not auto_export:
            return None

        # Export CSV
        csv_file = self.cli.export_csv(crawl_file, 'internal_all')

        if not csv_file:
            logger.error("CSV export failed")
            return None

        # Parse CSV
        pages = self.parser.parse_internal_all_csv(csv_file)

        # Convert to CrawlResults
        crawl_results = self.parser.convert_to_crawl_results(pages)

        return crawl_results

    def import_csv(self, csv_path: str) -> Optional[List[CrawlResult]]:
        """
        Import existing Screaming Frog CSV export

        Args:
            csv_path: Path to CSV file

        Returns:
            List of CrawlResult objects
        """
        pages = self.parser.parse_internal_all_csv(csv_path)
        return self.parser.convert_to_crawl_results(pages)

    def get_statistics(self) -> Dict[str, Any]:
        """Get combined statistics"""
        return {
            'cli': self.cli.get_statistics()
        }

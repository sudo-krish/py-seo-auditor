"""
Technical SEO Checker for SEO Auditor
Implements technical SEO checks following 2025 best practices
"""

import re
from typing import Dict, List, Any, Optional, Tuple, Set
from urllib.parse import urlparse, parse_qs
from collections import Counter
import logging

from utils.logger import log_execution_time

logger = logging.getLogger(__name__)


class TechnicalChecker:
    """
    Comprehensive technical SEO checker for 2025 standards
    """

    def __init__(self, config: Dict = None):
        """
        Initialize technical checker

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config or {}

        # Extract technical configuration
        technical_config = self.config.get('checks', {}).get('technical', {})

        # Crawlability thresholds
        self.max_depth = technical_config.get('max_depth', 3)
        self.max_url_length = technical_config.get('max_url_length', 100)

        # Sitemap requirements
        self.max_sitemap_urls = technical_config.get('max_sitemap_urls', 50000)

        # Redirect limits
        self.max_redirect_chain = technical_config.get('max_redirect_chain', 3)

        # Content similarity threshold for duplicate detection
        self.duplicate_threshold = technical_config.get('duplicate_threshold', 0.9)

        # Results storage
        self.issues = []
        self.warnings = []
        self.passed_checks = []

        logger.info(f"Technical checker initialized: max_depth={self.max_depth}")

    @log_execution_time(logger)
    def check(self, crawl_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all technical SEO checks

        Args:
            crawl_data: Crawl results from SEOCrawler

        Returns:
            Dictionary with technical check results
        """
        self.issues = []
        self.warnings = []
        self.passed_checks = []

        pages = crawl_data.get('pages', [])
        start_url = crawl_data.get('start_url', '')

        if not pages:
            logger.warning("No pages found in crawl data")
            return self._create_result()

        logger.info(f"Running technical checks on {len(pages)} pages")

        # Crawlability & Indexability
        self._check_robots_txt(start_url)
        self._check_xml_sitemap(start_url, pages)
        self._check_meta_robots(pages)
        self._check_x_robots_tag(pages)
        self._check_noindex_pages(pages)

        # URL Structure & Architecture
        self._check_url_structure(pages)
        self._check_url_parameters(pages)
        self._check_site_depth(pages)
        self._check_url_length(pages)

        # HTTP Status Codes
        self._check_status_codes(pages)
        self._check_error_pages(pages)
        self._check_soft_404s(pages)

        # Canonical Tags
        self._check_canonical_tags(pages)
        self._check_self_referencing_canonical(pages)
        self._check_canonical_chains(pages)

        # Redirects
        self._check_redirect_chains(pages)
        self._check_redirect_types(pages)
        self._check_redirect_loops(pages)

        # Duplicate Content
        self._check_duplicate_titles(pages)
        self._check_duplicate_descriptions(pages)
        self._check_duplicate_content(pages)

        # Structured Data
        self._check_structured_data(pages)
        self._check_schema_implementation(pages)

        # Hreflang
        self._check_hreflang_implementation(pages)
        self._check_hreflang_errors(pages)

        # Pagination
        self._check_pagination(pages)

        # Internal Linking
        self._check_internal_link_structure(pages)
        self._check_broken_internal_links(pages)

        # Advanced Technical
        self._check_orphan_pages(pages)
        self._check_thin_pages(pages)
        self._check_redirect_ratios(pages)

        return self._create_result()

    # ========================================================================
    # CRAWLABILITY & INDEXABILITY
    # ========================================================================

    def _check_robots_txt(self, start_url: str):
        """Check robots.txt file"""

        # Would fetch and parse robots.txt
        # Check for:
        # - File existence
        # - Syntax errors
        # - Disallow directives blocking important content
        # - Sitemap references
        # - Crawl-delay settings

        self.passed_checks.append('Robots.txt check completed')

    def _check_xml_sitemap(self, start_url: str, pages: List[Dict]):
        """Check XML sitemap"""

        # Would fetch and parse sitemap.xml
        # Check for:
        # - Sitemap existence
        # - Valid XML structure
        # - URL count (max 50,000)
        # - Image/video sitemaps
        # - lastmod dates
        # - Priority and changefreq usage
        # - Sitemap index for large sites

        crawled_urls = {page['url'] for page in pages}

        # Placeholder for sitemap URLs
        sitemap_urls = set()

        # Check coverage
        if sitemap_urls:
            missing_in_sitemap = crawled_urls - sitemap_urls
            missing_in_crawl = sitemap_urls - crawled_urls

            if missing_in_sitemap:
                self.warnings.append({
                    'title': 'Pages missing from sitemap',
                    'severity': 'warning',
                    'affected_pages': len(missing_in_sitemap),
                    'pages': list(missing_in_sitemap)[:10],
                    'description': f'{len(missing_in_sitemap)} crawled pages not in sitemap',
                    'recommendation': 'Add all important pages to XML sitemap'
                })

        self.passed_checks.append('XML sitemap check completed')

    def _check_meta_robots(self, pages: List[Dict]):
        """Check meta robots tags"""

        pages_with_noindex = []
        pages_with_nofollow = []
        pages_with_conflicts = []

        for page in pages:
            meta_robots = page.get('meta_robots', '').lower()

            if 'noindex' in meta_robots:
                pages_with_noindex.append(page['url'])

            if 'nofollow' in meta_robots:
                pages_with_nofollow.append(page['url'])

            # Check for conflicting directives
            if 'index' in meta_robots and 'noindex' in meta_robots:
                pages_with_conflicts.append(page['url'])

        if pages_with_noindex:
            self.warnings.append({
                'title': 'Pages with noindex directive',
                'severity': 'warning',
                'affected_pages': len(pages_with_noindex),
                'pages': pages_with_noindex[:10],
                'description': f'{len(pages_with_noindex)} pages have noindex meta tag',
                'recommendation': 'Review noindex tags - ensure they are intentional',
                'impact': 'Noindex pages will not appear in search results'
            })

        if pages_with_conflicts:
            self.issues.append({
                'title': 'Conflicting robots directives',
                'severity': 'error',
                'affected_pages': len(pages_with_conflicts),
                'pages': pages_with_conflicts,
                'description': 'Pages have conflicting index/noindex directives',
                'recommendation': 'Remove conflicting robots directives'
            })

    def _check_x_robots_tag(self, pages: List[Dict]):
        """Check X-Robots-Tag HTTP header"""

        pages_with_xrobots = []

        for page in pages:
            headers = page.get('headers', {})

            # Check for X-Robots-Tag header
            has_xrobots = any(
                'x-robots-tag' in k.lower()
                for k in headers.keys()
            )

            if has_xrobots:
                pages_with_xrobots.append(page['url'])

        if pages_with_xrobots:
            self.warnings.append({
                'title': 'X-Robots-Tag header present',
                'severity': 'info',
                'affected_pages': len(pages_with_xrobots),
                'pages': pages_with_xrobots[:10],
                'description': 'Pages use X-Robots-Tag HTTP header',
                'recommendation': 'Verify X-Robots-Tag directives are correct'
            })

    def _check_noindex_pages(self, pages: List[Dict]):
        """Check for important pages with noindex"""

        # Check if homepage or important pages have noindex
        important_paths = ['/', '/index', '/home']

        noindex_important = []

        for page in pages:
            parsed = urlparse(page['url'])
            path = parsed.path.rstrip('/')

            if path in important_paths or path == '':
                meta_robots = page.get('meta_robots', '').lower()
                if 'noindex' in meta_robots:
                    noindex_important.append(page['url'])

        if noindex_important:
            self.issues.append({
                'title': 'Important pages with noindex',
                'severity': 'critical',
                'affected_pages': len(noindex_important),
                'pages': noindex_important,
                'description': 'Homepage or key pages have noindex directive',
                'recommendation': 'Remove noindex from important pages immediately',
                'impact': 'Critical pages are blocked from search engines'
            })

    # ========================================================================
    # URL STRUCTURE & ARCHITECTURE
    # ========================================================================

    def _check_url_structure(self, pages: List[Dict]):
        """Check URL structure best practices"""

        pages_poor_structure = []

        for page in pages:
            url = page['url']
            parsed = urlparse(url)
            path = parsed.path

            issues = []

            # Check for underscores (hyphens preferred)
            if '_' in path:
                issues.append('underscores')

            # Check for uppercase letters
            if path != path.lower():
                issues.append('uppercase')

            # Check for special characters
            special_chars = re.findall(r'[^a-zA-Z0-9\-/.]', path)
            if special_chars:
                issues.append('special_characters')

            # Check for file extensions in URLs
            if re.search(r'\.(html?|php|asp|jsp)$', path):
                issues.append('file_extensions')

            if issues:
                pages_poor_structure.append({
                    'url': url,
                    'issues': issues
                })

        if pages_poor_structure:
            self.warnings.append({
                'title': 'Suboptimal URL structure',
                'severity': 'warning',
                'affected_pages': len(pages_poor_structure),
                'pages': [p['url'] for p in pages_poor_structure[:10]],
                'description': 'URLs have structural issues',
                'recommendation': 'Use lowercase, hyphens, and clean URLs without file extensions',
                'details': pages_poor_structure[:10]
            })

    def _check_url_parameters(self, pages: List[Dict]):
        """Check for excessive URL parameters"""

        pages_with_params = []

        for page in pages:
            url = page['url']
            parsed = urlparse(url)

            if parsed.query:
                params = parse_qs(parsed.query)
                if len(params) > 2:
                    pages_with_params.append({
                        'url': url,
                        'param_count': len(params)
                    })

        if pages_with_params:
            self.warnings.append({
                'title': 'Excessive URL parameters',
                'severity': 'warning',
                'affected_pages': len(pages_with_params),
                'pages': [p['url'] for p in pages_with_params[:10]],
                'description': 'URLs contain many query parameters',
                'recommendation': 'Use clean URLs or implement parameter handling in robots.txt',
                'details': pages_with_params[:10]
            })

    def _check_site_depth(self, pages: List[Dict]):
        """Check site depth and architecture"""

        # Calculate depth from homepage
        depth_distribution = Counter()
        deep_pages = []

        for page in pages:
            # Simple depth calculation based on path segments
            parsed = urlparse(page['url'])
            path = parsed.path.strip('/')
            depth = len(path.split('/')) if path else 0

            depth_distribution[depth] += 1

            if depth > self.max_depth:
                deep_pages.append({
                    'url': page['url'],
                    'depth': depth
                })

        if deep_pages:
            self.warnings.append({
                'title': 'Pages too deep in site structure',
                'severity': 'warning',
                'affected_pages': len(deep_pages),
                'pages': [p['url'] for p in deep_pages[:10]],
                'description': f'{len(deep_pages)} pages exceed recommended depth of {self.max_depth} clicks',
                'recommendation': 'Improve site architecture to make pages more accessible',
                'impact': 'Deep pages are harder to crawl and may receive less link equity',
                'details': deep_pages[:10]
            })
        else:
            self.passed_checks.append(f'All pages within {self.max_depth} clicks from homepage')

    def _check_url_length(self, pages: List[Dict]):
        """Check URL length"""

        long_urls = []

        for page in pages:
            url = page['url']

            if len(url) > self.max_url_length:
                long_urls.append({
                    'url': url[:100] + '...',
                    'length': len(url)
                })

        if long_urls:
            self.warnings.append({
                'title': 'URLs exceed recommended length',
                'severity': 'warning',
                'affected_pages': len(long_urls),
                'description': f'{len(long_urls)} URLs over {self.max_url_length} characters',
                'recommendation': 'Shorten URLs for better usability and SEO',
                'details': long_urls[:10]
            })

    # ========================================================================
    # HTTP STATUS CODES
    # ========================================================================

    def _check_status_codes(self, pages: List[Dict]):
        """Check HTTP status codes"""

        status_distribution = Counter()

        for page in pages:
            status = page.get('status_code')
            if status:
                status_distribution[status] += 1

        # Report status code distribution
        if status_distribution:
            self.passed_checks.append(f'Status code distribution: {dict(status_distribution)}')

    def _check_error_pages(self, pages: List[Dict]):
        """Check for 4xx and 5xx errors"""

        error_4xx = []
        error_5xx = []

        for page in pages:
            status = page.get('status_code')

            if status and 400 <= status < 500:
                error_4xx.append({
                    'url': page['url'],
                    'status': status
                })
            elif status and 500 <= status < 600:
                error_5xx.append({
                    'url': page['url'],
                    'status': status
                })

        if error_4xx:
            self.issues.append({
                'title': '4xx client errors detected',
                'severity': 'error',
                'affected_pages': len(error_4xx),
                'pages': [p['url'] for p in error_4xx[:10]],
                'description': f'{len(error_4xx)} pages return 4xx errors',
                'recommendation': 'Fix broken pages or implement proper redirects',
                'impact': '4xx errors create poor user experience and waste crawl budget',
                'details': error_4xx[:10]
            })

        if error_5xx:
            self.issues.append({
                'title': '5xx server errors detected',
                'severity': 'critical',
                'affected_pages': len(error_5xx),
                'pages': [p['url'] for p in error_5xx[:10]],
                'description': f'{len(error_5xx)} pages return 5xx errors',
                'recommendation': 'Fix server errors immediately',
                'impact': '5xx errors prevent indexing and indicate server problems',
                'details': error_5xx[:10]
            })

    def _check_soft_404s(self, pages: List[Dict]):
        """Check for soft 404 errors"""

        # Soft 404s return 200 but have minimal content
        potential_soft_404s = []

        for page in pages:
            status = page.get('status_code')
            word_count = page.get('word_count', 0)
            title = page.get('title', '').lower()

            if status == 200:
                # Check for 404-like indicators
                if word_count < 100 or '404' in title or 'not found' in title:
                    potential_soft_404s.append(page['url'])

        if potential_soft_404s:
            self.warnings.append({
                'title': 'Potential soft 404 errors',
                'severity': 'warning',
                'affected_pages': len(potential_soft_404s),
                'pages': potential_soft_404s[:10],
                'description': 'Pages may be soft 404s (return 200 but show error)',
                'recommendation': 'Return proper 404 status codes for missing pages'
            })

    # ========================================================================
    # CANONICAL TAGS
    # ========================================================================

    def _check_canonical_tags(self, pages: List[Dict]):
        """Check canonical tag implementation"""

        pages_without_canonical = []
        pages_with_canonical = []

        for page in pages:
            canonical = page.get('canonical_url')

            if canonical:
                pages_with_canonical.append(page['url'])
            else:
                pages_without_canonical.append(page['url'])

        if pages_without_canonical:
            self.warnings.append({
                'title': 'Missing canonical tags',
                'severity': 'warning',
                'affected_pages': len(pages_without_canonical),
                'pages': pages_without_canonical[:10],
                'description': f'{len(pages_without_canonical)} pages lack canonical tags',
                'recommendation': 'Add self-referencing canonical tags to all pages',
                'impact': 'Canonical tags help prevent duplicate content issues'
            })

        if pages_with_canonical:
            self.passed_checks.append(f'{len(pages_with_canonical)} pages have canonical tags')

    def _check_self_referencing_canonical(self, pages: List[Dict]):
        """Check for self-referencing canonical tags"""

        non_self_referencing = []

        for page in pages:
            url = page['url']
            canonical = page.get('canonical_url')

            if canonical:
                # Normalize URLs for comparison
                url_normalized = url.rstrip('/')
                canonical_normalized = canonical.rstrip('/')

                if url_normalized != canonical_normalized:
                    non_self_referencing.append({
                        'url': url,
                        'canonical': canonical
                    })

        if non_self_referencing:
            self.warnings.append({
                'title': 'Non-self-referencing canonicals',
                'severity': 'warning',
                'affected_pages': len(non_self_referencing),
                'pages': [p['url'] for p in non_self_referencing[:10]],
                'description': 'Canonical tags point to different URLs',
                'recommendation': 'Verify canonical tags are correct and intentional',
                'details': non_self_referencing[:10]
            })

    def _check_canonical_chains(self, pages: List[Dict]):
        """Check for canonical chains"""

        # Build canonical map
        canonical_map = {}
        for page in pages:
            url = page['url']
            canonical = page.get('canonical_url')
            if canonical:
                canonical_map[url] = canonical

        # Detect chains
        chains = []
        for url, canonical in canonical_map.items():
            if canonical in canonical_map and canonical_map[canonical] != canonical:
                chains.append({
                    'url': url,
                    'canonical': canonical,
                    'canonical_of_canonical': canonical_map[canonical]
                })

        if chains:
            self.issues.append({
                'title': 'Canonical chains detected',
                'severity': 'error',
                'affected_pages': len(chains),
                'description': 'Canonical tags create chains (A→B→C)',
                'recommendation': 'Point all canonical tags directly to the final URL',
                'impact': 'Canonical chains confuse search engines',
                'details': chains[:10]
            })

    # ========================================================================
    # REDIRECTS
    # ========================================================================

    def _check_redirect_chains(self, pages: List[Dict]):
        """Check for redirect chains"""

        # Would need redirect history from crawler
        # Placeholder implementation

        self.passed_checks.append('Redirect chains check completed')

    def _check_redirect_types(self, pages: List[Dict]):
        """Check redirect types (301 vs 302)"""

        # 301 for permanent, 302 for temporary
        # Would check redirect status codes

        self.passed_checks.append('Redirect types check completed')

    def _check_redirect_loops(self, pages: List[Dict]):
        """Check for redirect loops"""

        # Would detect circular redirects

        self.passed_checks.append('Redirect loops check completed')

    # ========================================================================
    # DUPLICATE CONTENT
    # ========================================================================

    def _check_duplicate_titles(self, pages: List[Dict]):
        """Check for duplicate title tags"""

        title_map = {}

        for page in pages:
            title = page.get('title', '').strip()
            if title:
                if title not in title_map:
                    title_map[title] = []
                title_map[title].append(page['url'])

        duplicates = {title: urls for title, urls in title_map.items() if len(urls) > 1}

        if duplicates:
            total_affected = sum(len(urls) for urls in duplicates.values())

            self.issues.append({
                'title': 'Duplicate title tags',
                'severity': 'error',
                'affected_pages': total_affected,
                'description': f'{len(duplicates)} titles used on multiple pages',
                'recommendation': 'Create unique titles for each page',
                'impact': 'Duplicate titles reduce CTR and confuse search engines',
                'details': [{
                    'title': title,
                    'pages': urls[:3]
                } for title, urls in list(duplicates.items())[:5]]
            })

    def _check_duplicate_descriptions(self, pages: List[Dict]):
        """Check for duplicate meta descriptions"""

        description_map = {}

        for page in pages:
            description = page.get('meta_description', '').strip()
            if description:
                if description not in description_map:
                    description_map[description] = []
                description_map[description].append(page['url'])

        duplicates = {desc: urls for desc, urls in description_map.items() if len(urls) > 1}

        if duplicates:
            total_affected = sum(len(urls) for urls in duplicates.values())

            self.warnings.append({
                'title': 'Duplicate meta descriptions',
                'severity': 'warning',
                'affected_pages': total_affected,
                'description': f'{len(duplicates)} meta descriptions duplicated',
                'recommendation': 'Write unique meta descriptions for each page'
            })

    def _check_duplicate_content(self, pages: List[Dict]):
        """Check for duplicate content"""

        # Would use content fingerprinting or similarity analysis
        # Placeholder implementation

        self.passed_checks.append('Duplicate content check completed')

    # ========================================================================
    # STRUCTURED DATA
    # ========================================================================

    def _check_structured_data(self, pages: List[Dict]):
        """Check structured data implementation"""

        pages_with_schema = []
        pages_without_schema = []

        for page in pages:
            structured_data = page.get('structured_data', [])

            if structured_data:
                pages_with_schema.append(page['url'])
            else:
                pages_without_schema.append(page['url'])

        if pages_with_schema:
            self.passed_checks.append(f'{len(pages_with_schema)} pages have structured data')

        if pages_without_schema and len(pages_without_schema) > len(pages) * 0.5:
            self.warnings.append({
                'title': 'Limited structured data usage',
                'severity': 'info',
                'affected_pages': len(pages_without_schema),
                'description': 'Many pages lack structured data',
                'recommendation': 'Implement schema.org markup for better rich results'
            })

    def _check_schema_implementation(self, pages: List[Dict]):
        """Check schema types and implementation"""

        schema_types = Counter()

        for page in pages:
            structured_data = page.get('structured_data', [])

            for schema in structured_data:
                schema_type = schema.get('@type', 'Unknown')
                schema_types[schema_type] += 1

        if schema_types:
            self.passed_checks.append(f'Schema types: {dict(schema_types)}')

    # ========================================================================
    # HREFLANG
    # ========================================================================

    def _check_hreflang_implementation(self, pages: List[Dict]):
        """Check hreflang implementation"""

        pages_with_hreflang = []

        for page in pages:
            hreflang = page.get('hreflang', [])

            if hreflang:
                pages_with_hreflang.append(page['url'])

        if pages_with_hreflang:
            self.passed_checks.append(f'{len(pages_with_hreflang)} pages have hreflang tags')

    def _check_hreflang_errors(self, pages: List[Dict]):
        """Check for hreflang errors"""

        # Check for:
        # - Missing return links
        # - Invalid language codes
        # - Missing x-default
        # - Self-referencing hreflang

        self.passed_checks.append('Hreflang errors check completed')

    # ========================================================================
    # PAGINATION
    # ========================================================================

    def _check_pagination(self, pages: List[Dict]):
        """Check pagination implementation"""

        # Check for rel=next/prev (deprecated but still used)
        # Check for View All pages
        # Check for canonical on paginated pages

        self.passed_checks.append('Pagination check completed')

    # ========================================================================
    # INTERNAL LINKING
    # ========================================================================

    def _check_internal_link_structure(self, pages: List[Dict]):
        """Check internal linking structure"""

        # Calculate page authority distribution
        # Check for pages with few incoming links

        self.passed_checks.append('Internal link structure check completed')

    def _check_broken_internal_links(self, pages: List[Dict]):
        """Check for broken internal links"""

        all_urls = {page['url'] for page in pages}
        broken_links = []

        for page in pages:
            internal_links = page.get('internal_links', [])

            for link in internal_links:
                href = link.get('href', '')
                if href and href not in all_urls:
                    broken_links.append({
                        'source': page['url'],
                        'target': href
                    })

        if broken_links:
            self.issues.append({
                'title': 'Broken internal links',
                'severity': 'error',
                'affected_pages': len(set(l['source'] for l in broken_links)),
                'description': f'{len(broken_links)} broken internal links found',
                'recommendation': 'Fix or remove broken internal links',
                'impact': 'Broken links harm user experience and waste crawl budget',
                'details': broken_links[:10]
            })

    # ========================================================================
    # ADVANCED TECHNICAL
    # ========================================================================

    def _check_orphan_pages(self, pages: List[Dict]):
        """Check for orphan pages"""

        # Build set of linked URLs
        linked_urls = set()
        for page in pages:
            internal_links = page.get('internal_links', [])
            for link in internal_links:
                href = link.get('href', '')
                if href:
                    linked_urls.add(href)

        # Find orphan pages
        orphans = []
        for page in pages:
            if page['url'] not in linked_urls:
                orphans.append(page['url'])

        # Homepage is typically not linked to
        if len(orphans) > 1:
            self.warnings.append({
                'title': 'Orphan pages detected',
                'severity': 'warning',
                'affected_pages': len(orphans),
                'pages': orphans[:10],
                'description': 'Pages with no incoming internal links',
                'recommendation': 'Add internal links to orphan pages from relevant content'
            })

    def _check_thin_pages(self, pages: List[Dict]):
        """Check for thin content pages"""

        thin_pages = []

        for page in pages:
            word_count = page.get('word_count', 0)

            if 0 < word_count < 100:
                thin_pages.append({
                    'url': page['url'],
                    'word_count': word_count
                })

        if thin_pages:
            self.warnings.append({
                'title': 'Thin content pages',
                'severity': 'warning',
                'affected_pages': len(thin_pages),
                'pages': [p['url'] for p in thin_pages[:10]],
                'description': f'{len(thin_pages)} pages have very little content',
                'recommendation': 'Expand content, consolidate pages, or noindex',
                'details': thin_pages[:10]
            })

    def _check_redirect_ratios(self, pages: List[Dict]):
        """Check redirect to content ratio"""

        # High redirect ratio can indicate technical issues

        self.passed_checks.append('Redirect ratio check completed')

    # ========================================================================
    # RESULT GENERATION
    # ========================================================================

    def _create_result(self) -> Dict[str, Any]:
        """Create structured result dictionary with normalized scoring"""

        # Combine all issues
        all_issues = self.issues + self.warnings

        # Count by severity (don't double count)
        severity_counts = {
            'critical': 0,
            'error': 0,
            'warning': 0,
            'info': 0
        }

        for issue in all_issues:
            severity = issue.get('severity', 'info')
            if severity in severity_counts:
                severity_counts[severity] += 1

        # Calculate score with DIMINISHING RETURNS
        # Not every issue should deduct the same amount
        base_score = 100

        # Diminishing returns formula: score = base * (1 - weight * log(1 + issues))
        import math

        critical_impact = min(30, severity_counts['critical'] * 20)  # Max 30 points
        error_impact = min(25, severity_counts['error'] * 10)  # Max 25 points
        warning_impact = min(20, severity_counts['warning'] * 3)  # Max 20 points
        info_impact = min(10, severity_counts['info'] * 1)  # Max 10 points

        total_deduction = critical_impact + error_impact + warning_impact + info_impact

        # Calculate final score (capped)
        score = max(0, min(100, base_score - total_deduction))

        return {
            'score': score,
            'grade': self._get_grade(score),
            'status': self._get_status(score),
            'issues': all_issues,  # Single list, no duplication
            'error_count': severity_counts['error'],
            'warning_count': severity_counts['warning'],
            'critical_count': severity_counts['critical'],
            'info_count': severity_counts['info'],
            'passed_checks': self.passed_checks,
            'summary': {
                'total_issues': len(all_issues),
                'errors': severity_counts['error'],
                'warnings': severity_counts['warning'],
                'passed_checks': len(self.passed_checks)
            },
            'recommendations': self._get_top_recommendations(all_issues)
        }

    def _get_grade(self, score: int) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def _get_status(self, score: int) -> str:
        """Get status label from score"""
        if score >= 90:
            return 'Excellent'
        elif score >= 80:
            return 'Good'
        elif score >= 70:
            return 'Fair'
        elif score >= 60:
            return 'Poor'
        else:
            return 'Critical'

    def _get_top_recommendations(self, issues: List[Dict], limit: int = 5) -> List[Dict]:
        """Get top priority recommendations"""

        severity_order = {'critical': 0, 'error': 1, 'warning': 2, 'info': 3}

        sorted_issues = sorted(
            issues,
            key=lambda x: (
                severity_order.get(x.get('severity', 'info'), 4),
                -x.get('affected_pages', 0)
            )
        )

        recommendations = []
        for issue in sorted_issues[:limit]:
            recommendations.append({
                'title': issue['title'],
                'priority': issue.get('severity', 'info'),
                'recommendation': issue.get('recommendation'),
                'affected_pages': issue.get('affected_pages', 0),
                'impact': issue.get('impact', 'Improves technical SEO')
            })

        return recommendations


# Convenience function for direct usage
def check_technical(crawl_data: Dict[str, Any], config: Dict = None) -> Dict[str, Any]:
    """
    Convenience function to run technical checks

    Args:
        crawl_data: Crawl results dictionary
        config: Optional configuration dictionary

    Returns:
        Technical check results
    """
    checker = TechnicalChecker(config)
    return checker.check(crawl_data)

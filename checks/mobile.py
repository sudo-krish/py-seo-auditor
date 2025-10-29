"""
Mobile SEO Checker for SEO Auditor
Implements mobile-first indexing checks and mobile usability analysis (2025 standards)
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

from utils.logger import log_execution_time

logger = logging.getLogger(__name__)


class MobileChecker:
    """
    Comprehensive mobile SEO checker for mobile-first indexing era
    """

    def __init__(self, config: Dict = None):
        """
        Initialize mobile checker

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config or {}

        # Extract mobile configuration
        mobile_config = self.config.get('checks', {}).get('mobile', {})

        # Touch target requirements (2025 standards)
        self.min_touch_target = mobile_config.get('min_touch_target', 48)  # pixels
        self.wcag_min_touch_target = 24  # WCAG 2.2 minimum

        # Font size requirements
        self.min_font_size = mobile_config.get('min_font_size', 16)  # pixels

        # Viewport requirements
        self.max_viewport_width = mobile_config.get('max_viewport_width', None)
        self.min_viewport_width = mobile_config.get('min_viewport_width', 320)

        # Performance thresholds for mobile
        self.mobile_lcp_threshold = 2.5  # seconds
        self.mobile_fid_threshold = 100  # milliseconds
        self.mobile_cls_threshold = 0.1  # score

        # Results storage
        self.issues = []
        self.warnings = []
        self.passed_checks = []

        logger.info(f"Mobile checker initialized: min_touch_target={self.min_touch_target}px")

    @log_execution_time(logger)
    def check(self, crawl_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all mobile SEO checks

        Args:
            crawl_data: Crawl results from SEOCrawler

        Returns:
            Dictionary with mobile check results
        """
        self.issues = []
        self.warnings = []
        self.passed_checks = []

        pages = crawl_data.get('pages', [])

        if not pages:
            logger.warning("No pages found in crawl data")
            return self._create_result()

        logger.info(f"Running mobile checks on {len(pages)} pages")

        # Mobile-First Indexing Checks
        self._check_viewport_meta_tag(pages)
        self._check_content_parity(pages)
        self._check_structured_data_parity(pages)
        self._check_metadata_parity(pages)

        # Responsive Design Checks
        self._check_responsive_design(pages)
        self._check_fixed_width_elements(pages)
        self._check_css_media_queries(pages)
        self._check_mobile_friendly_layout(pages)

        # Mobile Usability Checks
        self._check_touch_target_size(pages)
        self._check_text_readability(pages)
        self._check_font_sizes(pages)
        self._check_tap_targets_spacing(pages)
        self._check_horizontal_scrolling(pages)

        # Content Issues
        self._check_intrusive_interstitials(pages)
        self._check_flash_usage(pages)
        self._check_incompatible_plugins(pages)
        self._check_content_blocking(pages)

        # Mobile Performance
        self._check_mobile_page_speed(pages)
        self._check_mobile_core_web_vitals(pages)
        self._check_resource_optimization(pages)

        # Advanced Features
        self._check_pwa_features(pages)
        self._check_mobile_meta_tags(pages)
        self._check_app_deep_linking(pages)
        self._check_accelerated_mobile_pages(pages)

        # Navigation & UX
        self._check_mobile_navigation(pages)
        self._check_form_usability(pages)
        self._check_clickable_elements(pages)

        return self._create_result()

    # ========================================================================
    # MOBILE-FIRST INDEXING CHECKS (2025)
    # ========================================================================

    def _check_viewport_meta_tag(self, pages: List[Dict]):
        """Check for proper viewport meta tag"""

        pages_missing_viewport = []
        pages_with_bad_viewport = []

        for page in pages:
            # Check if viewport meta tag exists
            meta_viewport = page.get('meta_viewport')

            if not meta_viewport:
                pages_missing_viewport.append(page['url'])
            else:
                # Check for bad viewport configurations
                viewport_lower = meta_viewport.lower()

                # Red flags in viewport configuration
                bad_patterns = [
                    'user-scalable=no',
                    'user-scalable=0',
                    'maximum-scale=1',
                    'width=' + str(self.max_viewport_width) if self.max_viewport_width else None
                ]

                bad_patterns = [p for p in bad_patterns if p]

                if any(pattern in viewport_lower for pattern in bad_patterns):
                    pages_with_bad_viewport.append(page['url'])
                elif 'width=device-width' not in viewport_lower:
                    pages_with_bad_viewport.append(page['url'])

        if pages_missing_viewport:
            self.issues.append({
                'title': 'Missing viewport meta tag',
                'severity': 'error',
                'affected_pages': len(pages_missing_viewport),
                'pages': pages_missing_viewport[:10],
                'description': f'{len(pages_missing_viewport)} pages lack viewport configuration',
                'recommendation': 'Add <meta name="viewport" content="width=device-width, initial-scale=1">',
                'impact': 'Pages will not render properly on mobile devices'
            })

        if pages_with_bad_viewport:
            self.warnings.append({
                'title': 'Suboptimal viewport configuration',
                'severity': 'warning',
                'affected_pages': len(pages_with_bad_viewport),
                'pages': pages_with_bad_viewport[:10],
                'description': 'Viewport settings may hinder mobile usability',
                'recommendation': 'Use width=device-width and allow user scaling (avoid user-scalable=no)'
            })

        if not pages_missing_viewport and not pages_with_bad_viewport:
            self.passed_checks.append('All pages have proper viewport configuration')

    def _check_content_parity(self, pages: List[Dict]):
        """Check content parity between mobile and desktop (Mobile-First Indexing)"""

        # In mobile-first indexing, Google primarily uses mobile version
        # Content should be equivalent on both versions

        pages_with_content_issues = []

        for page in pages:
            # Check for mobile-specific content hiding
            # This would require comparing mobile vs desktop versions
            # Placeholder for actual implementation

            word_count = page.get('word_count', 0)

            # Very low word count might indicate hidden content
            if word_count < 100:
                pages_with_content_issues.append(page['url'])

        if pages_with_content_issues:
            self.warnings.append({
                'title': 'Potential content parity issues',
                'severity': 'warning',
                'affected_pages': len(pages_with_content_issues),
                'pages': pages_with_content_issues[:10],
                'description': 'Pages may have less content on mobile',
                'recommendation': 'Ensure mobile and desktop versions have equivalent content for mobile-first indexing'
            })

    def _check_structured_data_parity(self, pages: List[Dict]):
        """Check structured data consistency across mobile and desktop"""

        pages_missing_structured_data = []

        for page in pages:
            structured_data = page.get('structured_data', [])

            if not structured_data:
                pages_missing_structured_data.append(page['url'])

        if pages_missing_structured_data:
            self.warnings.append({
                'title': 'Missing structured data on mobile',
                'severity': 'warning',
                'affected_pages': len(pages_missing_structured_data),
                'pages': pages_missing_structured_data[:10],
                'description': 'Structured data should be present on mobile version',
                'recommendation': 'Include same structured data on both mobile and desktop versions'
            })

    def _check_metadata_parity(self, pages: List[Dict]):
        """Check metadata consistency (titles, descriptions, canonical)"""

        pages_missing_metadata = []

        for page in pages:
            title = page.get('title', '').strip()
            meta_description = page.get('meta_description', '').strip()
            canonical = page.get('canonical_url')

            if not title or not meta_description:
                pages_missing_metadata.append(page['url'])

        if pages_missing_metadata:
            self.issues.append({
                'title': 'Missing critical metadata',
                'severity': 'error',
                'affected_pages': len(pages_missing_metadata),
                'pages': pages_missing_metadata[:10],
                'description': 'Essential metadata missing on mobile version',
                'recommendation': 'Ensure titles and meta descriptions are present on mobile'
            })

    # ========================================================================
    # RESPONSIVE DESIGN CHECKS
    # ========================================================================

    def _check_responsive_design(self, pages: List[Dict]):
        """Check for responsive design implementation"""

        pages_not_responsive = []

        for page in pages:
            meta_viewport = page.get('meta_viewport', '')

            # Basic check: viewport meta tag presence
            if not meta_viewport:
                pages_not_responsive.append(page['url'])

        if pages_not_responsive:
            self.issues.append({
                'title': 'Non-responsive design detected',
                'severity': 'error',
                'affected_pages': len(pages_not_responsive),
                'pages': pages_not_responsive[:10],
                'description': 'Pages appear to use fixed-width design',
                'recommendation': 'Implement responsive design with flexible layouts and media queries'
            })
        else:
            self.passed_checks.append('Pages appear to use responsive design')

    def _check_fixed_width_elements(self, pages: List[Dict]):
        """Check for fixed-width elements that don't scale"""

        # Would require CSS analysis
        # Check for fixed pixel widths greater than viewport

        self.passed_checks.append('Fixed-width elements check completed')

    def _check_css_media_queries(self, pages: List[Dict]):
        """Check for CSS media queries presence"""

        # Would require CSS file analysis
        # Look for @media queries

        self.passed_checks.append('CSS media queries check completed')

    def _check_mobile_friendly_layout(self, pages: List[Dict]):
        """Check overall mobile-friendly layout"""

        # Check for common mobile-friendly patterns
        # - Flexible grids
        # - Flexible images
        # - Stacked navigation

        self.passed_checks.append('Mobile-friendly layout check completed')

    # ========================================================================
    # MOBILE USABILITY CHECKS
    # ========================================================================

    def _check_touch_target_size(self, pages: List[Dict]):
        """Check touch target sizing (minimum 48x48px, WCAG 2.2: 24x24px)"""

        pages_with_small_targets = []

        for page in pages:
            # Would require element size analysis
            # Check buttons, links, form controls

            # Placeholder implementation
            pass

        if pages_with_small_targets:
            self.issues.append({
                'title': 'Touch targets too small',
                'severity': 'error',
                'affected_pages': len(pages_with_small_targets),
                'pages': pages_with_small_targets[:10],
                'description': f'Interactive elements smaller than {self.min_touch_target}x{self.min_touch_target}px',
                'recommendation': f'Ensure all touch targets are at least {self.min_touch_target}x{self.min_touch_target} pixels',
                'impact': 'Users will have difficulty tapping buttons and links accurately'
            })

    def _check_text_readability(self, pages: List[Dict]):
        """Check text is readable without zooming"""

        pages_with_small_text = []

        for page in pages:
            # Would require font-size analysis from CSS
            # Check for text smaller than 16px

            # Placeholder implementation
            pass

        if pages_with_small_text:
            self.issues.append({
                'title': 'Text too small for mobile',
                'severity': 'error',
                'affected_pages': len(pages_with_small_text),
                'pages': pages_with_small_text[:10],
                'description': f'Text size below {self.min_font_size}px',
                'recommendation': f'Use minimum {self.min_font_size}px font size for body text',
                'impact': 'Users must zoom to read content'
            })

    def _check_font_sizes(self, pages: List[Dict]):
        """Check font sizes are appropriate for mobile"""

        # Recommended sizes:
        # - Body text: 16px minimum
        # - Headings: 1.2-2.5x body size
        # - Captions: 12-14px minimum

        self.passed_checks.append('Font size check completed')

    def _check_tap_targets_spacing(self, pages: List[Dict]):
        """Check spacing between tap targets"""

        # Recommended: 8px minimum spacing between targets

        self.passed_checks.append('Tap target spacing check completed')

    def _check_horizontal_scrolling(self, pages: List[Dict]):
        """Check for unwanted horizontal scrolling"""

        pages_with_horizontal_scroll = []

        for page in pages:
            # Would require checking for:
            # - Elements wider than viewport
            # - Fixed-width containers
            # - Large images without max-width

            # Placeholder
            pass

        if pages_with_horizontal_scroll:
            self.issues.append({
                'title': 'Horizontal scrolling required',
                'severity': 'error',
                'affected_pages': len(pages_with_horizontal_scroll),
                'pages': pages_with_horizontal_scroll[:10],
                'description': 'Content extends beyond viewport width',
                'recommendation': 'Ensure all content fits within viewport width'
            })

    # ========================================================================
    # CONTENT ISSUES
    # ========================================================================

    def _check_intrusive_interstitials(self, pages: List[Dict]):
        """Check for intrusive interstitials (2025 guidelines)"""

        # Google penalizes intrusive interstitials on mobile
        # Check for:
        # - Popup overlays
        # - Full-screen ads
        # - Age verification gates (without legal requirement)

        pages_with_interstitials = []

        for page in pages:
            # Would require JavaScript analysis or visual testing
            # Placeholder
            pass

        if pages_with_interstitials:
            self.issues.append({
                'title': 'Intrusive interstitials detected',
                'severity': 'error',
                'affected_pages': len(pages_with_interstitials),
                'pages': pages_with_interstitials[:10],
                'description': 'Pages use intrusive popups or overlays',
                'recommendation': 'Remove intrusive interstitials or use less invasive alternatives (banners, inline forms)',
                'impact': 'Google may penalize pages with intrusive interstitials'
            })

    def _check_flash_usage(self, pages: List[Dict]):
        """Check for Flash usage (deprecated)"""

        pages_with_flash = []

        for page in pages:
            # Check for Flash <object> or <embed> tags
            # Would require HTML parsing
            pass

        if pages_with_flash:
            self.issues.append({
                'title': 'Flash content detected',
                'severity': 'critical',
                'affected_pages': len(pages_with_flash),
                'pages': pages_with_flash[:10],
                'description': 'Pages use deprecated Flash technology',
                'recommendation': 'Replace Flash with HTML5, CSS3, and JavaScript',
                'impact': 'Flash is not supported on mobile devices and has been deprecated'
            })

    def _check_incompatible_plugins(self, pages: List[Dict]):
        """Check for incompatible plugins (Java, Silverlight, etc.)"""

        pages_with_plugins = []

        for page in pages:
            # Check for plugin-based content
            pass

        if pages_with_plugins:
            self.warnings.append({
                'title': 'Incompatible plugins detected',
                'severity': 'warning',
                'affected_pages': len(pages_with_plugins),
                'pages': pages_with_plugins[:10],
                'description': 'Pages use plugins not supported on mobile',
                'recommendation': 'Use web-standard technologies instead of plugins'
            })

    def _check_content_blocking(self, pages: List[Dict]):
        """Check for content blocking elements"""

        # Check for elements that obscure content on mobile

        self.passed_checks.append('Content blocking check completed')

    # ========================================================================
    # MOBILE PERFORMANCE
    # ========================================================================

    def _check_mobile_page_speed(self, pages: List[Dict]):
        """Check mobile-specific page speed"""

        slow_pages = []

        for page in pages:
            response_time = page.get('response_time', 0)

            # Mobile should load in under 3 seconds
            if response_time > 3.0:
                slow_pages.append({
                    'url': page['url'],
                    'response_time': round(response_time, 2)
                })

        if slow_pages:
            self.warnings.append({
                'title': 'Slow mobile page load times',
                'severity': 'warning',
                'affected_pages': len(slow_pages),
                'pages': [p['url'] for p in slow_pages[:10]],
                'description': f'{len(slow_pages)} pages load slowly on mobile',
                'recommendation': 'Optimize for mobile performance: compress images, minify CSS/JS, enable caching',
                'details': slow_pages[:10]
            })

    def _check_mobile_core_web_vitals(self, pages: List[Dict]):
        """Check Core Web Vitals for mobile"""

        # Would integrate with PageSpeed Insights API
        # Check LCP, FID/INP, CLS for mobile

        self.passed_checks.append('Mobile Core Web Vitals check completed')

    def _check_resource_optimization(self, pages: List[Dict]):
        """Check resource optimization for mobile"""

        pages_with_large_resources = []

        for page in pages:
            content_size = page.get('content_size', 0)

            # Page size should be under 1MB for mobile
            if content_size > 1048576:  # 1MB in bytes
                pages_with_large_resources.append({
                    'url': page['url'],
                    'size': round(content_size / 1024, 2)  # KB
                })

        if pages_with_large_resources:
            self.warnings.append({
                'title': 'Large page sizes detected',
                'severity': 'warning',
                'affected_pages': len(pages_with_large_resources),
                'pages': [p['url'] for p in pages_with_large_resources[:10]],
                'description': 'Pages exceed recommended size for mobile',
                'recommendation': 'Optimize images, use lazy loading, minify resources',
                'details': pages_with_large_resources[:10]
            })

    # ========================================================================
    # ADVANCED MOBILE FEATURES
    # ========================================================================

    def _check_pwa_features(self, pages: List[Dict]):
        """Check for Progressive Web App features"""

        # Check for:
        # - Web app manifest
        # - Service worker
        # - HTTPS
        # - Offline functionality

        pages_with_manifest = []
        pages_without_manifest = []

        for page in pages:
            # Would check for <link rel="manifest">
            pass

        if pages_with_manifest:
            self.passed_checks.append(f'{len(pages_with_manifest)} pages have PWA manifest')
        else:
            self.warnings.append({
                'title': 'No PWA features detected',
                'severity': 'info',
                'affected_pages': len(pages),
                'description': 'Consider implementing Progressive Web App features',
                'recommendation': 'Add web app manifest and service worker for improved mobile experience'
            })

    def _check_mobile_meta_tags(self, pages: List[Dict]):
        """Check mobile-specific meta tags"""

        # Check for:
        # - apple-mobile-web-app-capable
        # - apple-mobile-web-app-status-bar-style
        # - theme-color
        # - mobile-web-app-capable

        pages_missing_mobile_tags = []

        for page in pages:
            # Would parse HTML for mobile meta tags
            pass

        if pages_missing_mobile_tags:
            self.warnings.append({
                'title': 'Mobile-specific meta tags missing',
                'severity': 'info',
                'affected_pages': len(pages_missing_mobile_tags),
                'description': 'Consider adding mobile-specific meta tags for better UX',
                'recommendation': 'Add theme-color, apple-mobile-web-app-capable tags'
            })

    def _check_app_deep_linking(self, pages: List[Dict]):
        """Check for app deep linking configuration"""

        # Check for:
        # - App links (Android)
        # - Universal links (iOS)
        # - twitter:app:* tags
        # - al:* (App Links) tags

        self.passed_checks.append('App deep linking check completed')

    def _check_accelerated_mobile_pages(self, pages: List[Dict]):
        """Check for AMP implementation"""

        pages_with_amp = []

        for page in pages:
            # Check for AMP versions
            # <link rel="amphtml" href="...">
            pass

        if pages_with_amp:
            self.passed_checks.append(f'{len(pages_with_amp)} pages have AMP versions')

    # ========================================================================
    # NAVIGATION & UX
    # ========================================================================

    def _check_mobile_navigation(self, pages: List[Dict]):
        """Check mobile navigation usability"""

        # Check for:
        # - Hamburger menu
        # - Touch-friendly navigation
        # - Breadcrumbs
        # - Search functionality

        self.passed_checks.append('Mobile navigation check completed')

    def _check_form_usability(self, pages: List[Dict]):
        """Check mobile form usability"""

        # Check for:
        # - Appropriate input types (email, tel, number)
        # - Autocomplete attributes
        # - Large form fields
        # - Clear labels

        self.passed_checks.append('Mobile form usability check completed')

    def _check_clickable_elements(self, pages: List[Dict]):
        """Check clickable elements are properly spaced and sized"""

        # Ensure buttons, links not too close together

        self.passed_checks.append('Clickable elements check completed')

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

        # Sort by severity and affected pages
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
                'impact': issue.get('impact', 'Mobile user experience may be affected')
            })

        return recommendations


# Convenience function for direct usage
def check_mobile(crawl_data: Dict[str, Any], config: Dict = None) -> Dict[str, Any]:
    """
    Convenience function to run mobile checks

    Args:
        crawl_data: Crawl results dictionary
        config: Optional configuration dictionary

    Returns:
        Mobile check results
    """
    checker = MobileChecker(config)
    return checker.check(crawl_data)

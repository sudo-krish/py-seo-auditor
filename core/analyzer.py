"""
Analysis engine for SEO Auditor
Orchestrates all SEO checks and aggregates results
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from core.crawler import CrawlResult
from checks import technical, onpage, performance, mobile, security, accessibility
from utils.logger import log_execution_time, AuditLogger

logger = logging.getLogger(__name__)


class AnalysisResult:
    """
    Data class for storing complete analysis results
    """

    def __init__(self, url: str):
        self.url = url
        self.timestamp = datetime.now()
        self.overall_score = 0

        # Category results
        self.technical = {}
        self.onpage = {}
        self.performance = {}
        self.mobile = {}
        self.security = {}
        self.accessibility = {}

        # Aggregated metrics
        self.issues = {
            'critical': [],
            'error': [],
            'warning': [],
            'info': []
        }

        self.category_scores = {}
        self.total_issues = 0
        self.pages_analyzed = 0
        self.recommendations = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'url': self.url,
            'timestamp': self.timestamp.isoformat(),
            'overall_score': self.overall_score,
            'category_scores': self.category_scores,
            'technical': self.technical,
            'onpage': self.onpage,
            'performance': self.performance,
            'mobile': self.mobile,
            'security': self.security,
            'accessibility': self.accessibility,
            'issues': self.issues,
            'total_issues': self.total_issues,
            'pages_analyzed': self.pages_analyzed,
            'recommendations': self.recommendations
        }


class SEOAnalyzer:
    """
    Main analysis engine that orchestrates all SEO checks
    """

    def __init__(self, config: Dict = None):
        """
        Initialize SEO analyzer

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config or {}
        self.checks_config = self.config.get('checks', {})
        self.thresholds = self.config.get('thresholds', {})

        # Initialize check modules
        self.technical_checker = technical.TechnicalSEOChecker(config)
        self.onpage_checker = onpage.OnPageChecker(config)
        self.performance_checker = performance.PerformanceChecker(config)
        self.mobile_checker = mobile.MobileChecker(config)
        self.security_checker = security.SecurityChecker(config)
        self.accessibility_checker = accessibility.AccessibilityChecker(config)

        # Audit logger
        self.audit_logger = AuditLogger(config)

        # Thread safety
        self.lock = threading.Lock()

        logger.info("Analyzer initialized with all check modules")

    @log_execution_time(logger)
    def analyze(
            self,
            crawl_results: List[CrawlResult],
            selected_checks: Optional[Dict[str, bool]] = None,
            parallel: bool = False
    ) -> AnalysisResult:
        """
        Perform complete SEO analysis

        Args:
            crawl_results: List of crawl results from crawler
            selected_checks: Optional dict of which checks to run
            parallel: Whether to run checks in parallel

        Returns:
            AnalysisResult with all findings
        """
        if not crawl_results:
            logger.warning("No crawl results provided for analysis")
            return AnalysisResult("")

        # Get base URL from first result
        base_url = crawl_results[0].url
        result = AnalysisResult(base_url)
        result.pages_analyzed = len(crawl_results)

        # Start audit session
        session_id = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.audit_logger.start_session(base_url, session_id)

        logger.info(f"Starting analysis of {len(crawl_results)} pages")

        # Determine which checks to run
        checks_to_run = self._get_checks_to_run(selected_checks)

        try:
            if parallel:
                result = self._run_checks_parallel(crawl_results, checks_to_run, result)
            else:
                result = self._run_checks_sequential(crawl_results, checks_to_run, result)

            # Calculate overall score
            result.overall_score = self._calculate_overall_score(result)

            # Generate recommendations
            result.recommendations = self._generate_recommendations(result)

            # Count total issues
            result.total_issues = sum(len(issues) for issues in result.issues.values())

            logger.info(f"Analysis complete. Overall score: {result.overall_score}/100")
            logger.info(f"Issues found - Critical: {len(result.issues['critical'])}, "
                        f"Errors: {len(result.issues['error'])}, "
                        f"Warnings: {len(result.issues['warning'])}")

        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            self.audit_logger.log_error("analysis_error", str(e))
        finally:
            # End audit session
            self.audit_logger.end_session({
                'overall_score': result.overall_score,
                'total_issues': result.total_issues,
                'pages_analyzed': result.pages_analyzed
            })

        return result

    def _get_checks_to_run(self, selected_checks: Optional[Dict[str, bool]]) -> Dict[str, bool]:
        """
        Determine which checks should be run

        Args:
            selected_checks: User-selected checks

        Returns:
            Dictionary of check names to boolean
        """
        # Default: all checks enabled
        default_checks = {
            'technical': True,
            'onpage': True,
            'performance': True,
            'mobile': True,
            'security': True,
            'accessibility': True
        }

        # Override with config
        for check, enabled in self.checks_config.items():
            if isinstance(enabled, dict):
                default_checks[check] = enabled.get('enabled', True)
            elif isinstance(enabled, bool):
                default_checks[check] = enabled

        # Override with selected_checks
        if selected_checks:
            default_checks.update(selected_checks)

        return default_checks

    def _run_checks_sequential(
            self,
            crawl_results: List[CrawlResult],
            checks_to_run: Dict[str, bool],
            result: AnalysisResult
    ) -> AnalysisResult:
        """Run all checks sequentially"""

        if checks_to_run.get('technical', False):
            logger.info("Running technical SEO checks...")
            result.technical = self.technical_checker.check(crawl_results)
            result.category_scores['technical'] = result.technical.get('score', 0)
            self._merge_issues(result, result.technical.get('issues', {}))

        if checks_to_run.get('onpage', False):
            logger.info("Running on-page SEO checks...")
            result.onpage = self.onpage_checker.check(crawl_results)
            result.category_scores['onpage'] = result.onpage.get('score', 0)
            self._merge_issues(result, result.onpage.get('issues', {}))

        if checks_to_run.get('performance', False):
            logger.info("Running performance checks...")
            result.performance = self.performance_checker.check(crawl_results)
            result.category_scores['performance'] = result.performance.get('score', 0)
            self._merge_issues(result, result.performance.get('issues', {}))

        if checks_to_run.get('mobile', False):
            logger.info("Running mobile checks...")
            result.mobile = self.mobile_checker.check(crawl_results)
            result.category_scores['mobile'] = result.mobile.get('score', 0)
            self._merge_issues(result, result.mobile.get('issues', {}))

        if checks_to_run.get('security', False):
            logger.info("Running security checks...")
            result.security = self.security_checker.check(crawl_results)
            result.category_scores['security'] = result.security.get('score', 0)
            self._merge_issues(result, result.security.get('issues', {}))

        if checks_to_run.get('accessibility', False):
            logger.info("Running accessibility checks...")
            result.accessibility = self.accessibility_checker.check(crawl_results)
            result.category_scores['accessibility'] = result.accessibility.get('score', 0)
            self._merge_issues(result, result.accessibility.get('issues', {}))

        return result

    def _run_checks_parallel(
            self,
            crawl_results: List[CrawlResult],
            checks_to_run: Dict[str, bool],
            result: AnalysisResult
    ) -> AnalysisResult:
        """Run all checks in parallel for faster execution"""

        check_tasks = []

        # Build list of checks to execute
        if checks_to_run.get('technical', False):
            check_tasks.append(('technical', self.technical_checker.check, crawl_results))

        if checks_to_run.get('onpage', False):
            check_tasks.append(('onpage', self.onpage_checker.check, crawl_results))

        if checks_to_run.get('performance', False):
            check_tasks.append(('performance', self.performance_checker.check, crawl_results))

        if checks_to_run.get('mobile', False):
            check_tasks.append(('mobile', self.mobile_checker.check, crawl_results))

        if checks_to_run.get('security', False):
            check_tasks.append(('security', self.security_checker.check, crawl_results))

        if checks_to_run.get('accessibility', False):
            check_tasks.append(('accessibility', self.accessibility_checker.check, crawl_results))

        # Execute in parallel
        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_check = {
                executor.submit(check_func, data): check_name
                for check_name, check_func, data in check_tasks
            }

            for future in as_completed(future_to_check):
                check_name = future_to_check[future]
                try:
                    check_result = future.result()

                    # Store result
                    setattr(result, check_name, check_result)
                    result.category_scores[check_name] = check_result.get('score', 0)
                    self._merge_issues(result, check_result.get('issues', {}))

                    logger.info(f"Completed {check_name} checks")

                except Exception as e:
                    logger.error(f"Error in {check_name} check: {e}", exc_info=True)

        return result

    def _merge_issues(self, result: AnalysisResult, issues: Dict[str, List]):
        """Merge issues from a check into result"""
        for severity in ['critical', 'error', 'warning', 'info']:
            if severity in issues:
                result.issues[severity].extend(issues[severity])

    def _calculate_overall_score(self, result: AnalysisResult) -> int:
        """
        Calculate overall score based on category scores and weights

        Args:
            result: AnalysisResult with category scores

        Returns:
            Overall score (0-100)
        """
        scoring_config = self.config.get('scoring', {})
        weights = scoring_config.get('weights', {
            'technical': 25,
            'onpage': 25,
            'performance': 20,
            'mobile': 15,
            'security': 10,
            'accessibility': 5
        })

        total_score = 0
        total_weight = 0

        for category, weight in weights.items():
            if category in result.category_scores:
                total_score += result.category_scores[category] * weight
                total_weight += weight

        if total_weight == 0:
            return 0

        overall = round(total_score / total_weight)
        return max(0, min(100, overall))  # Clamp between 0-100

    def _generate_recommendations(self, result: AnalysisResult) -> List[Dict[str, Any]]:
        """
        Generate prioritized recommendations based on issues

        Args:
            result: AnalysisResult with issues

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        # Critical issues first
        for issue in result.issues.get('critical', []):
            recommendations.append({
                'priority': 'critical',
                'category': issue.get('category', 'unknown'),
                'title': issue.get('title', ''),
                'description': issue.get('description', ''),
                'impact': 'high',
                'effort': issue.get('effort', 'medium'),
                'affected_pages': issue.get('affected_pages', [])
            })

        # High-impact errors
        for issue in result.issues.get('error', []):
            recommendations.append({
                'priority': 'high',
                'category': issue.get('category', 'unknown'),
                'title': issue.get('title', ''),
                'description': issue.get('description', ''),
                'impact': 'medium',
                'effort': issue.get('effort', 'medium'),
                'affected_pages': issue.get('affected_pages', [])
            })

        # Warnings (top 10 most impactful)
        warning_issues = result.issues.get('warning', [])
        for issue in warning_issues[:10]:
            recommendations.append({
                'priority': 'medium',
                'category': issue.get('category', 'unknown'),
                'title': issue.get('title', ''),
                'description': issue.get('description', ''),
                'impact': 'low',
                'effort': issue.get('effort', 'low'),
                'affected_pages': issue.get('affected_pages', [])
            })

        return recommendations

    def analyze_single_page(self, crawl_result: CrawlResult) -> Dict[str, Any]:
        """
        Analyze a single page (useful for real-time checking)

        Args:
            crawl_result: Single CrawlResult

        Returns:
            Dictionary with page analysis
        """
        results = self.analyze([crawl_result])
        return results.to_dict()

    def get_issue_summary(self, result: AnalysisResult) -> Dict[str, int]:
        """
        Get summary count of issues by severity

        Args:
            result: AnalysisResult

        Returns:
            Dictionary with counts
        """
        return {
            'critical': len(result.issues['critical']),
            'error': len(result.issues['error']),
            'warning': len(result.issues['warning']),
            'info': len(result.issues['info']),
            'total': result.total_issues
        }

    def get_category_summary(self, result: AnalysisResult) -> Dict[str, Dict]:
        """
        Get summary of each category's performance

        Args:
            result: AnalysisResult

        Returns:
            Dictionary with category summaries
        """
        return {
            'technical': {
                'score': result.category_scores.get('technical', 0),
                'status': self._get_score_status(result.category_scores.get('technical', 0))
            },
            'onpage': {
                'score': result.category_scores.get('onpage', 0),
                'status': self._get_score_status(result.category_scores.get('onpage', 0))
            },
            'performance': {
                'score': result.category_scores.get('performance', 0),
                'status': self._get_score_status(result.category_scores.get('performance', 0))
            },
            'mobile': {
                'score': result.category_scores.get('mobile', 0),
                'status': self._get_score_status(result.category_scores.get('mobile', 0))
            },
            'security': {
                'score': result.category_scores.get('security', 0),
                'status': self._get_score_status(result.category_scores.get('security', 0))
            },
            'accessibility': {
                'score': result.category_scores.get('accessibility', 0),
                'status': self._get_score_status(result.category_scores.get('accessibility', 0))
            }
        }

    def _get_score_status(self, score: int) -> str:
        """
        Get status label for a score

        Args:
            score: Score value

        Returns:
            Status string
        """
        thresholds = self.config.get('scoring', {}).get('grade_thresholds', {
            'excellent': 90,
            'good': 75,
            'fair': 60,
            'poor': 40
        })

        if score >= thresholds['excellent']:
            return 'excellent'
        elif score >= thresholds['good']:
            return 'good'
        elif score >= thresholds['fair']:
            return 'fair'
        elif score >= thresholds['poor']:
            return 'poor'
        else:
            return 'failing'

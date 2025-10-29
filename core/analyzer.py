"""
Analysis Engine for SEO Auditor
Orchestrates all SEO checks and aggregates results (2025)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from checks.technical import TechnicalChecker
from checks.onpage import OnPageChecker
from checks.performance import PerformanceChecker
from checks.mobile import MobileChecker
from checks.security import SecurityChecker
from checks.accessibility import AccessibilityChecker
from core.scorer import SEOScorer
from utils.logger import log_execution_time

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
        self.issues = []
        self.issues_by_severity = {
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
            'issues_by_severity': self.issues_by_severity,
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

        # Initialize check modules
        self.technical_checker = TechnicalChecker(config)
        self.onpage_checker = OnPageChecker(config)
        self.performance_checker = PerformanceChecker(config)
        self.mobile_checker = MobileChecker(config)
        self.security_checker = SecurityChecker(config)
        self.accessibility_checker = AccessibilityChecker(config)

        # Initialize scorer
        self.scorer = SEOScorer(config)

        # Thread safety
        self.lock = threading.Lock()

        logger.info("SEO Analyzer initialized with all check modules")

    @log_execution_time(logger)
    def analyze(
        self,
        crawl_data: Dict[str, Any],
        selected_checks: Optional[Dict[str, bool]] = None,
        parallel: bool = False
    ) -> Dict[str, Any]:
        """
        Perform complete SEO analysis

        Args:
            crawl_data: Dictionary with crawl results (includes 'pages', 'start_url', etc.)
            selected_checks: Optional dict of which checks to run
            parallel: Whether to run checks in parallel

        Returns:
            Dictionary with complete analysis results
        """
        if not crawl_data or not crawl_data.get('pages'):
            logger.warning("No crawl data provided for analysis")
            return self._create_empty_result()

        # Get base URL
        base_url = crawl_data.get('start_url', '')
        pages = crawl_data.get('pages', [])

        result = AnalysisResult(base_url)
        result.pages_analyzed = len(pages)

        logger.info(f"Starting analysis of {len(pages)} pages for {base_url}")

        # Determine which checks to run
        checks_to_run = self._get_checks_to_run(selected_checks)

        try:
            if parallel and len(checks_to_run) > 1:
                self._run_checks_parallel(crawl_data, checks_to_run, result)
            else:
                self._run_checks_sequential(crawl_data, checks_to_run, result)

            # Calculate overall score using scorer
            result.overall_score = self.scorer.calculate_weighted_score(result.category_scores)

            # Generate recommendations
            result.recommendations = self._generate_recommendations(result)

            # Count total issues
            result.total_issues = len(result.issues)

            logger.info(f"Analysis complete. Overall score: {result.overall_score}/100")
            logger.info(f"Issues found - Critical: {len(result.issues_by_severity['critical'])}, "
                       f"Errors: {len(result.issues_by_severity['error'])}, "
                       f"Warnings: {len(result.issues_by_severity['warning'])}")

            # Convert to dict and add scoring metadata
            result_dict = result.to_dict()
            result_dict = self.scorer.score_analysis(result_dict)

            return result_dict

        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            return self._create_error_result(base_url, str(e))

    def _get_checks_to_run(self, selected_checks: Optional[Dict[str, bool]]) -> Dict[str, bool]:
        """Determine which checks should be run"""
        default_checks = {
            'technical': True,
            'onpage': True,
            'performance': True,
            'mobile': True,
            'security': True,
            'accessibility': True
        }

        if selected_checks:
            for check_name, enabled in selected_checks.items():
                if check_name in default_checks:
                    default_checks[check_name] = enabled

        enabled_checks = {k: v for k, v in default_checks.items() if v}
        logger.info(f"Checks to run: {list(enabled_checks.keys())}")

        return enabled_checks

    def _run_checks_sequential(
        self,
        crawl_data: Dict[str, Any],
        checks_to_run: Dict[str, bool],
        result: AnalysisResult
    ):
        """Run all checks sequentially"""

        if checks_to_run.get('technical', False):
            logger.info("Running technical SEO checks...")
            try:
                tech_result = self.technical_checker.check(crawl_data)
                result.technical = tech_result
                result.category_scores['technical'] = tech_result.get('score', 0)
                self._merge_issues(result, tech_result.get('issues', []), 'technical')
            except Exception as e:
                logger.error(f"Technical check failed: {e}", exc_info=True)
                result.technical = {'score': 0, 'error': str(e)}

        if checks_to_run.get('onpage', False):
            logger.info("Running on-page SEO checks...")
            try:
                onpage_result = self.onpage_checker.check(crawl_data)
                result.onpage = onpage_result
                result.category_scores['onpage'] = onpage_result.get('score', 0)
                self._merge_issues(result, onpage_result.get('issues', []), 'onpage')
            except Exception as e:
                logger.error(f"On-page check failed: {e}", exc_info=True)
                result.onpage = {'score': 0, 'error': str(e)}

        if checks_to_run.get('performance', False):
            logger.info("Running performance checks...")
            try:
                perf_result = self.performance_checker.check(crawl_data)
                result.performance = perf_result
                result.category_scores['performance'] = perf_result.get('score', 0)
                self._merge_issues(result, perf_result.get('issues', []), 'performance')
            except Exception as e:
                logger.error(f"Performance check failed: {e}", exc_info=True)
                result.performance = {'score': 0, 'error': str(e)}

        if checks_to_run.get('mobile', False):
            logger.info("Running mobile checks...")
            try:
                mobile_result = self.mobile_checker.check(crawl_data)
                result.mobile = mobile_result
                result.category_scores['mobile'] = mobile_result.get('score', 0)
                self._merge_issues(result, mobile_result.get('issues', []), 'mobile')
            except Exception as e:
                logger.error(f"Mobile check failed: {e}", exc_info=True)
                result.mobile = {'score': 0, 'error': str(e)}

        if checks_to_run.get('security', False):
            logger.info("Running security checks...")
            try:
                security_result = self.security_checker.check(crawl_data)
                result.security = security_result
                result.category_scores['security'] = security_result.get('score', 0)
                self._merge_issues(result, security_result.get('issues', []), 'security')
            except Exception as e:
                logger.error(f"Security check failed: {e}", exc_info=True)
                result.security = {'score': 0, 'error': str(e)}

        if checks_to_run.get('accessibility', False):
            logger.info("Running accessibility checks...")
            try:
                access_result = self.accessibility_checker.check(crawl_data)
                result.accessibility = access_result
                result.category_scores['accessibility'] = access_result.get('score', 0)
                self._merge_issues(result, access_result.get('issues', []), 'accessibility')
            except Exception as e:
                logger.error(f"Accessibility check failed: {e}", exc_info=True)
                result.accessibility = {'score': 0, 'error': str(e)}

    def _run_checks_parallel(
        self,
        crawl_data: Dict[str, Any],
        checks_to_run: Dict[str, bool],
        result: AnalysisResult
    ):
        """Run all checks in parallel for faster execution"""

        check_tasks = []

        if checks_to_run.get('technical', False):
            check_tasks.append(('technical', self.technical_checker.check))

        if checks_to_run.get('onpage', False):
            check_tasks.append(('onpage', self.onpage_checker.check))

        if checks_to_run.get('performance', False):
            check_tasks.append(('performance', self.performance_checker.check))

        if checks_to_run.get('mobile', False):
            check_tasks.append(('mobile', self.mobile_checker.check))

        if checks_to_run.get('security', False):
            check_tasks.append(('security', self.security_checker.check))

        if checks_to_run.get('accessibility', False):
            check_tasks.append(('accessibility', self.accessibility_checker.check))

        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_check = {
                executor.submit(check_func, crawl_data): check_name
                for check_name, check_func in check_tasks
            }

            for future in as_completed(future_to_check):
                check_name = future_to_check[future]
                try:
                    check_result = future.result()
                    setattr(result, check_name, check_result)
                    result.category_scores[check_name] = check_result.get('score', 0)
                    self._merge_issues(result, check_result.get('issues', []), check_name)
                    logger.info(f"Completed {check_name} checks: {check_result.get('score', 0)}/100")
                except Exception as e:
                    logger.error(f"Error in {check_name} check: {e}", exc_info=True)
                    setattr(result, check_name, {'score': 0, 'error': str(e)})

    def _merge_issues(self, result: AnalysisResult, issues: List[Dict], category: str):
        """Merge issues from a check into result"""
        with self.lock:
            for issue in issues:
                issue['category'] = category
                result.issues.append(issue)
                severity = issue.get('severity', 'info')
                if severity in result.issues_by_severity:
                    result.issues_by_severity[severity].append(issue)

    def _generate_recommendations(self, result: AnalysisResult) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations based on issues"""
        recommendations = []
        severity_priority = {'critical': 0, 'error': 1, 'warning': 2, 'info': 3}

        sorted_issues = sorted(
            result.issues,
            key=lambda x: (
                severity_priority.get(x.get('severity', 'info'), 4),
                -x.get('affected_pages', 0)
            )
        )

        for issue in sorted_issues[:20]:
            recommendations.append({
                'title': issue.get('title', 'Unknown issue'),
                'category': issue.get('category', 'general'),
                'severity': issue.get('severity', 'info'),
                'priority': self._map_severity_to_priority(issue.get('severity', 'info')),
                'description': issue.get('description', ''),
                'recommendation': issue.get('recommendation', ''),
                'affected_pages': issue.get('affected_pages', 0),
                'impact': issue.get('impact', 'Unknown impact'),
                'effort': self._estimate_effort(issue)
            })

        return recommendations

    def _map_severity_to_priority(self, severity: str) -> str:
        """Map severity to priority label"""
        mapping = {'critical': 'critical', 'error': 'high', 'warning': 'medium', 'info': 'low'}
        return mapping.get(severity, 'low')

    def _estimate_effort(self, issue: Dict) -> str:
        """Estimate effort required to fix issue"""
        affected = issue.get('affected_pages', 0)
        if affected == 0:
            return 'low'
        elif affected < 5:
            return 'low'
        elif affected < 20:
            return 'medium'
        else:
            return 'high'

    def _create_empty_result(self) -> Dict[str, Any]:
        """Create empty result for when no data is provided"""
        result = AnalysisResult("")
        return result.to_dict()

    def _create_error_result(self, url: str, error_message: str) -> Dict[str, Any]:
        """Create error result when analysis fails"""
        result = AnalysisResult(url)
        result.issues.append({
            'title': 'Analysis Error',
            'severity': 'critical',
            'category': 'system',
            'description': f'Analysis failed: {error_message}',
            'recommendation': 'Check logs for details and try again'
        })
        return result.to_dict()


# Export
__all__ = ['SEOAnalyzer', 'AnalysisResult']

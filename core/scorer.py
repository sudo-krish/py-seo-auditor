"""
Scoring algorithm for SEO Auditor
Calculates scores based on issues, severity, and weighted categories
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Impact(Enum):
    """Issue impact levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Issue:
    """
    Data class representing an SEO issue
    """
    title: str
    description: str
    severity: Severity
    category: str
    affected_pages: List[str]
    impact: Impact = Impact.MEDIUM
    effort: str = "medium"  # low, medium, high
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'title': self.title,
            'description': self.description,
            'severity': self.severity.value,
            'category': self.category,
            'affected_pages': self.affected_pages,
            'impact': self.impact.value,
            'effort': self.effort,
            'recommendation': self.recommendation
        }


class SEOScorer:
    """
    Main scoring engine for calculating SEO audit scores
    """

    def __init__(self, config: Dict = None):
        """
        Initialize scorer

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config or {}

        # Get scoring configuration
        scoring_config = self.config.get('scoring', {})

        # Category weights (must sum to 100)
        self.category_weights = scoring_config.get('weights', {
            'technical': 25,
            'onpage': 25,
            'performance': 20,
            'mobile': 15,
            'security': 10,
            'accessibility': 5
        })

        # Issue severity point deductions
        self.severity_points = scoring_config.get('issue_severity', {
            'critical': -10,
            'error': -5,
            'warning': -2,
            'info': 0
        })

        # Grade thresholds
        self.grade_thresholds = scoring_config.get('grade_thresholds', {
            'excellent': 90,
            'good': 75,
            'fair': 60,
            'poor': 40
        })

        # Maximum score
        self.max_score = 100

        logger.info("Scorer initialized with weighted scoring model")

    def calculate_category_score(
            self,
            issues: List[Issue],
            total_checks: int = 10,
            base_score: int = 100
    ) -> int:
        """
        Calculate score for a single category based on issues

        Args:
            issues: List of Issue objects found
            total_checks: Total number of checks performed
            base_score: Starting score (default 100)

        Returns:
            Category score (0-100)
        """
        if total_checks == 0:
            return base_score

        score = base_score

        # Deduct points based on issue severity
        for issue in issues:
            severity_key = issue.severity.value
            deduction = self.severity_points.get(severity_key, 0)
            score += deduction

            logger.debug(f"Issue '{issue.title}' ({severity_key}): {deduction} points")

        # Normalize score
        score = max(0, min(100, score))

        return score

    def calculate_weighted_score(self, category_scores: Dict[str, int]) -> int:
        """
        Calculate overall weighted score from category scores

        Args:
            category_scores: Dictionary mapping category names to scores

        Returns:
            Overall weighted score (0-100)
        """
        total_score = 0
        total_weight = 0

        for category, score in category_scores.items():
            weight = self.category_weights.get(category, 0)

            if weight > 0:
                weighted_value = score * weight
                total_score += weighted_value
                total_weight += weight

                logger.debug(f"Category '{category}': score={score}, weight={weight}, "
                             f"weighted={weighted_value}")

        if total_weight == 0:
            return 0

        # Calculate weighted average
        overall_score = round(total_score / total_weight)

        # Ensure score is within bounds
        overall_score = max(0, min(100, overall_score))

        logger.info(f"Overall weighted score: {overall_score}/100 "
                    f"(from {len(category_scores)} categories)")

        return overall_score

    def get_grade(self, score: int) -> str:
        """
        Get letter grade for a score

        Args:
            score: Numeric score (0-100)

        Returns:
            Grade string (A+, A, B, C, F)
        """
        if score >= self.grade_thresholds['excellent']:
            return 'A+'
        elif score >= self.grade_thresholds['good']:
            return 'A'
        elif score >= self.grade_thresholds['fair']:
            return 'B'
        elif score >= self.grade_thresholds['poor']:
            return 'C'
        else:
            return 'F'

    def get_status(self, score: int) -> str:
        """
        Get status label for a score

        Args:
            score: Numeric score (0-100)

        Returns:
            Status string (excellent, good, fair, poor, failing)
        """
        if score >= self.grade_thresholds['excellent']:
            return 'excellent'
        elif score >= self.grade_thresholds['good']:
            return 'good'
        elif score >= self.grade_thresholds['fair']:
            return 'fair'
        elif score >= self.grade_thresholds['poor']:
            return 'poor'
        else:
            return 'failing'

    def assess_issue_priority(
            self,
            severity: Severity,
            impact: Impact,
            affected_pages_count: int
    ) -> Tuple[str, int]:
        """
        Assess issue priority based on severity, impact, and scope

        Args:
            severity: Issue severity level
            impact: Business impact level
            affected_pages_count: Number of affected pages

        Returns:
            Tuple of (priority_label, priority_score)
        """
        # Base priority scores
        severity_scores = {
            Severity.CRITICAL: 10,
            Severity.ERROR: 7,
            Severity.WARNING: 4,
            Severity.INFO: 1
        }

        impact_scores = {
            Impact.HIGH: 3,
            Impact.MEDIUM: 2,
            Impact.LOW: 1
        }

        # Calculate priority score
        base_score = severity_scores.get(severity, 1)
        impact_multiplier = impact_scores.get(impact, 1)

        # Factor in scope (more pages = higher priority)
        scope_multiplier = 1.0
        if affected_pages_count > 50:
            scope_multiplier = 2.0
        elif affected_pages_count > 10:
            scope_multiplier = 1.5
        elif affected_pages_count > 1:
            scope_multiplier = 1.2

        priority_score = int(base_score * impact_multiplier * scope_multiplier)

        # Determine priority label
        if priority_score >= 20:
            priority_label = "critical"
        elif priority_score >= 10:
            priority_label = "high"
        elif priority_score >= 5:
            priority_label = "medium"
        else:
            priority_label = "low"

        return priority_label, priority_score

    def score_check_result(
            self,
            check_name: str,
            passed: bool,
            expected_value: Any = None,
            actual_value: Any = None,
            severity: Severity = Severity.WARNING
    ) -> Dict[str, Any]:
        """
        Score an individual check result

        Args:
            check_name: Name of the check
            passed: Whether check passed
            expected_value: Expected value
            actual_value: Actual value found
            severity: Severity if check failed

        Returns:
            Dictionary with check result and score impact
        """
        result = {
            'check': check_name,
            'passed': passed,
            'expected': expected_value,
            'actual': actual_value,
            'severity': severity.value,
            'score_impact': 0
        }

        if not passed:
            result['score_impact'] = self.severity_points.get(severity.value, 0)

        return result

    def calculate_improvement_potential(
            self,
            current_score: int,
            issues_by_severity: Dict[str, List[Issue]]
    ) -> Dict[str, Any]:
        """
        Calculate potential score improvement if issues are fixed

        Args:
            current_score: Current overall score
            issues_by_severity: Dictionary of issues grouped by severity

        Returns:
            Dictionary with improvement analysis
        """
        # Calculate points to gain from fixing each severity level
        potential_gains = {}

        for severity_level in ['critical', 'error', 'warning']:
            issues = issues_by_severity.get(severity_level, [])
            if issues:
                points_per_issue = abs(self.severity_points.get(severity_level, 0))
                total_gain = points_per_issue * len(issues)
                potential_gains[severity_level] = {
                    'issue_count': len(issues),
                    'points_per_issue': points_per_issue,
                    'total_potential_gain': total_gain
                }

        # Calculate maximum potential score
        total_possible_gain = sum(
            gain['total_potential_gain']
            for gain in potential_gains.values()
        )
        max_potential_score = min(100, current_score + total_possible_gain)

        return {
            'current_score': current_score,
            'max_potential_score': max_potential_score,
            'total_possible_gain': total_possible_gain,
            'potential_gains_by_severity': potential_gains,
            'improvement_percentage': round(
                (max_potential_score - current_score) / current_score * 100
                if current_score > 0 else 0,
                1
            )
        }

    def compare_scores(
            self,
            previous_score: int,
            current_score: int
    ) -> Dict[str, Any]:
        """
        Compare two scores and calculate changes

        Args:
            previous_score: Previous audit score
            current_score: Current audit score

        Returns:
            Dictionary with comparison data
        """
        difference = current_score - previous_score
        percentage_change = (
            round((difference / previous_score * 100), 1)
            if previous_score > 0 else 0
        )

        if difference > 0:
            trend = "improving"
            trend_icon = "↑"
        elif difference < 0:
            trend = "declining"
            trend_icon = "↓"
        else:
            trend = "stable"
            trend_icon = "→"

        return {
            'previous_score': previous_score,
            'current_score': current_score,
            'difference': difference,
            'percentage_change': percentage_change,
            'trend': trend,
            'trend_icon': trend_icon,
            'previous_grade': self.get_grade(previous_score),
            'current_grade': self.get_grade(current_score)
        }

    def generate_score_breakdown(
            self,
            category_scores: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Generate detailed score breakdown with weights

        Args:
            category_scores: Dictionary of category scores

        Returns:
            Dictionary with score breakdown
        """
        breakdown = {}
        total_weighted = 0
        total_weight = 0

        for category, score in category_scores.items():
            weight = self.category_weights.get(category, 0)
            weighted_score = (score * weight) / 100

            breakdown[category] = {
                'score': score,
                'weight': weight,
                'weighted_score': round(weighted_score, 2),
                'grade': self.get_grade(score),
                'status': self.get_status(score)
            }

            total_weighted += weighted_score
            total_weight += weight

        overall_score = round(total_weighted) if total_weight > 0 else 0

        return {
            'categories': breakdown,
            'overall_score': overall_score,
            'overall_grade': self.get_grade(overall_score),
            'overall_status': self.get_status(overall_score),
            'total_weight': total_weight
        }

    def create_score_report(
            self,
            category_scores: Dict[str, int],
            issues_by_category: Dict[str, List[Issue]],
            total_pages: int = 1
    ) -> Dict[str, Any]:
        """
        Create comprehensive score report

        Args:
            category_scores: Dictionary of category scores
            issues_by_category: Dictionary of issues by category
            total_pages: Total pages analyzed

        Returns:
            Complete score report dictionary
        """
        # Calculate overall score
        overall_score = self.calculate_weighted_score(category_scores)

        # Generate breakdown
        breakdown = self.generate_score_breakdown(category_scores)

        # Count issues by severity
        all_issues = []
        for issues in issues_by_category.values():
            all_issues.extend(issues)

        issues_by_severity = {
            'critical': [i for i in all_issues if i.severity == Severity.CRITICAL],
            'error': [i for i in all_issues if i.severity == Severity.ERROR],
            'warning': [i for i in all_issues if i.severity == Severity.WARNING],
            'info': [i for i in all_issues if i.severity == Severity.INFO]
        }

        # Calculate improvement potential
        improvement = self.calculate_improvement_potential(
            overall_score,
            issues_by_severity
        )

        return {
            'overall_score': overall_score,
            'overall_grade': self.get_grade(overall_score),
            'overall_status': self.get_status(overall_score),
            'breakdown': breakdown,
            'total_pages_analyzed': total_pages,
            'issue_counts': {
                'critical': len(issues_by_severity['critical']),
                'error': len(issues_by_severity['error']),
                'warning': len(issues_by_severity['warning']),
                'info': len(issues_by_severity['info']),
                'total': len(all_issues)
            },
            'improvement_potential': improvement
        }


def create_issue(
        title: str,
        description: str,
        severity: str,
        category: str,
        affected_pages: List[str],
        impact: str = "medium",
        effort: str = "medium",
        recommendation: str = ""
) -> Issue:
    """
    Helper function to create Issue object

    Args:
        title: Issue title
        description: Issue description
        severity: Severity level (critical, error, warning, info)
        category: Category name
        affected_pages: List of affected page URLs
        impact: Impact level (high, medium, low)
        effort: Effort to fix (high, medium, low)
        recommendation: Recommendation text

    Returns:
        Issue object
    """
    severity_map = {
        'critical': Severity.CRITICAL,
        'error': Severity.ERROR,
        'warning': Severity.WARNING,
        'info': Severity.INFO
    }

    impact_map = {
        'high': Impact.HIGH,
        'medium': Impact.MEDIUM,
        'low': Impact.LOW
    }

    return Issue(
        title=title,
        description=description,
        severity=severity_map.get(severity.lower(), Severity.WARNING),
        category=category,
        affected_pages=affected_pages,
        impact=impact_map.get(impact.lower(), Impact.MEDIUM),
        effort=effort,
        recommendation=recommendation
    )

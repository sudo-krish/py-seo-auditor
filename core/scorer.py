"""
Scoring Engine for SEO Auditor
Calculates overall scores, grades, and provides score analysis (2025)
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class SEOScorer:
    """
    Scoring engine that calculates overall scores and provides analysis
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

        # Grade thresholds
        self.grade_thresholds = scoring_config.get('grade_thresholds', {
            'excellent': 90,
            'good': 75,
            'fair': 60,
            'poor': 40
        })

        logger.info("SEO Scorer initialized with weighted scoring model")

    def score_analysis(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add scoring metadata to analysis results

        Args:
            analysis_results: Dictionary with analysis results from analyzer

        Returns:
            Enhanced results with grade, status, and score breakdown
        """
        # Get overall score (already calculated by analyzer)
        overall_score = analysis_results.get('overall_score', 0)

        # Add grade and status
        analysis_results['overall_grade'] = self.get_grade(overall_score)
        analysis_results['overall_status'] = self.get_status(overall_score)

        # Add category grades and status
        category_scores = analysis_results.get('category_scores', {})
        analysis_results['category_breakdown'] = self._create_category_breakdown(category_scores)

        # Add score interpretation
        analysis_results['score_interpretation'] = self._get_score_interpretation(overall_score)

        # Add improvement potential
        issues_by_severity = analysis_results.get('issues_by_severity', {})
        analysis_results['improvement_potential'] = self._calculate_improvement_potential(
            overall_score,
            issues_by_severity
        )

        return analysis_results

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
            Grade string (A, B, C, D, F)
        """
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

    def _create_category_breakdown(self, category_scores: Dict[str, int]) -> Dict[str, Dict]:
        """
        Create detailed breakdown of category scores

        Args:
            category_scores: Dictionary of category scores

        Returns:
            Dictionary with category details
        """
        breakdown = {}

        for category, score in category_scores.items():
            weight = self.category_weights.get(category, 0)
            weighted_contribution = round((score * weight) / 100, 1)

            breakdown[category] = {
                'score': score,
                'grade': self.get_grade(score),
                'status': self.get_status(score),
                'weight': weight,
                'weighted_contribution': weighted_contribution
            }

        return breakdown

    def _get_score_interpretation(self, score: int) -> Dict[str, str]:
        """
        Get interpretation and guidance for score

        Args:
            score: Overall score

        Returns:
            Dictionary with interpretation
        """
        if score >= 90:
            return {
                'level': 'Excellent',
                'message': 'Outstanding SEO performance! Site follows best practices.',
                'action': 'Continue monitoring and maintain current standards.'
            }
        elif score >= 75:
            return {
                'level': 'Good',
                'message': 'Strong SEO foundation with minor issues to address.',
                'action': 'Focus on resolving remaining warnings and errors.'
            }
        elif score >= 60:
            return {
                'level': 'Fair',
                'message': 'Adequate SEO but significant improvements needed.',
                'action': 'Prioritize fixing errors and high-impact warnings.'
            }
        elif score >= 40:
            return {
                'level': 'Poor',
                'message': 'Major SEO issues affecting search visibility.',
                'action': 'Address critical and error-level issues immediately.'
            }
        else:
            return {
                'level': 'Critical',
                'message': 'Severe SEO problems requiring immediate attention.',
                'action': 'Implement urgent fixes for critical issues before other optimizations.'
            }

    def _calculate_improvement_potential(
        self,
        current_score: int,
        issues_by_severity: Dict[str, List[Dict]]
    ) -> Dict[str, Any]:
        """
        Calculate potential score improvement if issues are fixed

        Args:
            current_score: Current overall score
            issues_by_severity: Dictionary of issues grouped by severity

        Returns:
            Dictionary with improvement analysis
        """
        # Estimated point gains (simplified model)
        severity_potential = {
            'critical': 15,
            'error': 10,
            'warning': 5,
            'info': 2
        }

        potential_gains = {}
        total_gain = 0

        for severity, issues in issues_by_severity.items():
            if issues and severity in severity_potential:
                # Diminishing returns - can't gain full points for every issue
                issue_count = len(issues)
                base_gain = severity_potential[severity]

                # Cap gain per severity level
                max_gain = base_gain * min(issue_count, 3)

                potential_gains[severity] = {
                    'issue_count': issue_count,
                    'estimated_gain': max_gain
                }

                total_gain += max_gain

        max_potential_score = min(100, current_score + total_gain)

        return {
            'current_score': current_score,
            'max_potential_score': max_potential_score,
            'total_possible_gain': total_gain,
            'gains_by_severity': potential_gains,
            'improvement_percentage': round(
                (max_potential_score - current_score) / max(current_score, 1) * 100,
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
            trend_color = "green"
        elif difference < 0:
            trend = "declining"
            trend_icon = "↓"
            trend_color = "red"
        else:
            trend = "stable"
            trend_icon = "→"
            trend_color = "gray"

        return {
            'previous_score': previous_score,
            'current_score': current_score,
            'difference': difference,
            'percentage_change': percentage_change,
            'trend': trend,
            'trend_icon': trend_icon,
            'trend_color': trend_color,
            'previous_grade': self.get_grade(previous_score),
            'current_grade': self.get_grade(current_score),
            'previous_status': self.get_status(previous_score),
            'current_status': self.get_status(current_score)
        }


# Export
__all__ = ['SEOScorer']

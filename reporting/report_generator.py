"""
Report generator for SEO Auditor
Creates comprehensive SEO audit reports with multiple sections
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, Template

    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    logging.warning("Jinja2 not installed. Template-based reports unavailable.")

from core.scorer import Severity, Impact
from reporting.export import Exporter
from utils.logger import log_execution_time

logger = logging.getLogger(__name__)


class ReportGeneratorError(Exception):
    """Custom exception for report generation errors"""
    pass


class ReportGenerator:
    """
    Main report generator for SEO audits
    """

    # Report types
    REPORT_TYPES = {
        'quick': 'Quick Overview',
        'standard': 'Standard Audit',
        'comprehensive': 'Comprehensive Analysis',
        'executive': 'Executive Summary'
    }

    def __init__(self, config: Dict = None):
        """
        Initialize report generator

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # Get configuration
        report_config = self.config.get('reporting', {})
        self.include_charts = report_config.get('include_charts', True)
        self.branding = report_config.get('branding', {})

        # Initialize exporter
        self.exporter = Exporter(config)

        # Initialize Jinja2 if available
        if JINJA2_AVAILABLE:
            template_dir = Path(__file__).parent / 'templates'
            template_dir.mkdir(exist_ok=True)
            self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
        else:
            self.jinja_env = None

        logger.info("Report generator initialized")

    @log_execution_time(logger)
    def generate_report(
            self,
            analysis_result: Dict[str, Any],
            report_type: str = 'standard',
            export_formats: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate complete SEO audit report

        Args:
            analysis_result: Analysis results from analyzer
            report_type: Type of report (quick, standard, comprehensive, executive)
            export_formats: List of formats to export (json, html, pdf, csv)

        Returns:
            Dictionary with report data and export paths
        """
        if report_type not in self.REPORT_TYPES:
            logger.warning(f"Unknown report type: {report_type}. Using 'standard'.")
            report_type = 'standard'

        logger.info(f"Generating {report_type} report for {analysis_result.get('url', 'unknown')}")

        # Build report structure
        report_data = {
            'metadata': self._generate_metadata(analysis_result, report_type),
            'executive_summary': self._generate_executive_summary(analysis_result),
            'overall_score': self._generate_overall_score_section(analysis_result),
            'category_scores': self._generate_category_scores_section(analysis_result),
            'findings': self._generate_findings_section(analysis_result, report_type),
            'recommendations': self._generate_recommendations_section(analysis_result),
            'action_items': self._generate_action_items(analysis_result),
            'technical_details': self._generate_technical_details(
                analysis_result) if report_type == 'comprehensive' else None
        }

        # Export in requested formats
        export_formats = export_formats or ['html', 'json']
        exported_files = {}

        base_filename = self._generate_filename(analysis_result)

        for format_type in export_formats:
            try:
                if format_type == 'json':
                    exported_files['json'] = self.exporter.export_json(report_data, base_filename)
                elif format_type == 'html':
                    html_content = self._render_html_report(report_data)
                    exported_files['html'] = self.exporter.export_html(report_data, base_filename, html_content)
                elif format_type == 'pdf':
                    html_content = self._render_html_report(report_data)
                    exported_files['pdf'] = self.exporter.export_pdf_from_html(html_content, base_filename)
                elif format_type == 'csv':
                    csv_data = self._prepare_csv_data(report_data)
                    if csv_data:
                        exported_files['csv'] = self.exporter.export_csv(csv_data, base_filename)
            except Exception as e:
                logger.error(f"Failed to export {format_type}: {e}")

        return {
            'report_data': report_data,
            'exported_files': exported_files,
            'report_type': report_type
        }

    def _generate_metadata(self, analysis_result: Dict[str, Any], report_type: str) -> Dict[str, Any]:
        """Generate report metadata"""
        return {
            'title': f'SEO Audit Report - {self.REPORT_TYPES[report_type]}',
            'url': analysis_result.get('url', 'N/A'),
            'generated_at': datetime.now().isoformat(),
            'generated_by': self.branding.get('name', 'SEO Auditor'),
            'report_type': report_type,
            'pages_analyzed': analysis_result.get('pages_analyzed', 0),
            'version': '1.0'
        }

    def _generate_executive_summary(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary section"""
        overall_score = analysis_result.get('overall_score', 0)
        issues = analysis_result.get('issues', {})

        # Determine overall health
        if overall_score >= 90:
            health = 'Excellent'
            health_description = 'Your website is well-optimized and following SEO best practices.'
        elif overall_score >= 75:
            health = 'Good'
            health_description = 'Your website is performing well with minor areas for improvement.'
        elif overall_score >= 60:
            health = 'Fair'
            health_description = 'Your website needs attention in several key areas.'
        else:
            health = 'Poor'
            health_description = 'Your website requires significant SEO improvements.'

        # Count issues
        critical_count = len(issues.get('critical', []))
        error_count = len(issues.get('error', []))
        warning_count = len(issues.get('warning', []))

        # Key findings
        key_findings = []
        if critical_count > 0:
            key_findings.append(f'{critical_count} critical issues require immediate attention')
        if error_count > 0:
            key_findings.append(f'{error_count} errors should be fixed soon')
        if warning_count > 0:
            key_findings.append(f'{warning_count} warnings for optimization')

        # Best performing categories
        category_scores = analysis_result.get('category_scores', {})
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        strengths = [cat for cat, score in sorted_categories[:3] if score >= 80]
        weaknesses = [cat for cat, score in sorted_categories[-3:] if score < 70]

        return {
            'overall_health': health,
            'health_description': health_description,
            'overall_score': overall_score,
            'total_issues': critical_count + error_count + warning_count,
            'critical_issues': critical_count,
            'key_findings': key_findings,
            'strengths': strengths,
            'weaknesses': weaknesses
        }

    def _generate_overall_score_section(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall score section"""
        overall_score = analysis_result.get('overall_score', 0)

        return {
            'score': overall_score,
            'grade': self._get_grade(overall_score),
            'status': self._get_status(overall_score),
            'score_color': self._get_score_color(overall_score),
            'description': self._get_score_description(overall_score)
        }

    def _generate_category_scores_section(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate category scores section"""
        category_scores = analysis_result.get('category_scores', {})
        categories = []

        category_info = {
            'technical': {'name': 'Technical SEO', 'icon': '🔧'},
            'onpage': {'name': 'On-Page SEO', 'icon': '📄'},
            'performance': {'name': 'Performance', 'icon': '⚡'},
            'mobile': {'name': 'Mobile', 'icon': '📱'},
            'security': {'name': 'Security', 'icon': '🔒'},
            'accessibility': {'name': 'Accessibility', 'icon': '♿'}
        }

        for category, score in category_scores.items():
            info = category_info.get(category, {'name': category.title(), 'icon': '📊'})
            categories.append({
                'id': category,
                'name': info['name'],
                'icon': info['icon'],
                'score': score,
                'grade': self._get_grade(score),
                'status': self._get_status(score),
                'color': self._get_score_color(score)
            })

        # Sort by score (lowest first to prioritize fixes)
        return sorted(categories, key=lambda x: x['score'])

    def _generate_findings_section(
            self,
            analysis_result: Dict[str, Any],
            report_type: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate findings section organized by category"""
        findings = {
            'technical': analysis_result.get('technical', {}),
            'onpage': analysis_result.get('onpage', {}),
            'performance': analysis_result.get('performance', {}),
            'mobile': analysis_result.get('mobile', {}),
            'security': analysis_result.get('security', {}),
            'accessibility': analysis_result.get('accessibility', {})
        }

        # Filter findings based on report type
        if report_type == 'quick':
            # Only include critical and error issues
            findings = self._filter_findings_by_severity(findings, ['critical', 'error'])
        elif report_type == 'executive':
            # Only include critical issues
            findings = self._filter_findings_by_severity(findings, ['critical'])

        return findings

    def _generate_recommendations_section(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations"""
        recommendations = []
        issues = analysis_result.get('issues', {})

        # Generate recommendations from critical issues
        for issue in issues.get('critical', [])[:10]:  # Top 10 critical
            recommendations.append({
                'priority': 'high',
                'title': issue.get('title', ''),
                'description': issue.get('description', ''),
                'category': issue.get('category', ''),
                'effort': issue.get('effort', 'medium'),
                'impact': issue.get('impact', 'high'),
                'affected_pages': len(issue.get('affected_pages', []))
            })

        # Add error-level recommendations
        for issue in issues.get('error', [])[:10]:
            recommendations.append({
                'priority': 'medium',
                'title': issue.get('title', ''),
                'description': issue.get('description', ''),
                'category': issue.get('category', ''),
                'effort': issue.get('effort', 'medium'),
                'impact': issue.get('impact', 'medium'),
                'affected_pages': len(issue.get('affected_pages', []))
            })

        # Sort by priority and impact
        priority_order = {'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))

        return recommendations[:20]  # Top 20 recommendations

    def _generate_action_items(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate prioritized action items"""
        action_items = []
        issues = analysis_result.get('issues', {})

        # Quick wins (low effort, high impact)
        quick_wins = [
            issue for issue in issues.get('error', []) + issues.get('warning', [])
            if issue.get('effort') == 'low' and issue.get('impact') in ['high', 'medium']
        ]

        if quick_wins:
            action_items.append({
                'category': 'Quick Wins',
                'description': 'Low effort fixes that will improve your SEO score',
                'items': [{'title': i.get('title'), 'effort': i.get('effort')} for i in quick_wins[:5]]
            })

        # Critical fixes
        if issues.get('critical'):
            action_items.append({
                'category': 'Critical Fixes',
                'description': 'Issues that require immediate attention',
                'items': [{'title': i.get('title'), 'effort': i.get('effort')} for i in issues['critical'][:5]]
            })

        return action_items

    def _generate_technical_details(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate technical details section for comprehensive reports"""
        return {
            'crawl_statistics': {
                'pages_crawled': analysis_result.get('pages_analyzed', 0),
                'timestamp': analysis_result.get('timestamp', datetime.now().isoformat())
            },
            'raw_data': {
                'technical': analysis_result.get('technical', {}),
                'onpage': analysis_result.get('onpage', {}),
                'performance': analysis_result.get('performance', {}),
                'mobile': analysis_result.get('mobile', {}),
                'security': analysis_result.get('security', {}),
                'accessibility': analysis_result.get('accessibility', {})
            }
        }

    def _filter_findings_by_severity(
            self,
            findings: Dict[str, Any],
            severities: List[str]
    ) -> Dict[str, Any]:
        """Filter findings to only include specified severities"""
        filtered = {}

        for category, data in findings.items():
            if isinstance(data, dict) and 'issues' in data:
                filtered_issues = [
                    issue for issue in data.get('issues', [])
                    if issue.get('severity') in severities
                ]
                filtered[category] = {**data, 'issues': filtered_issues}
            else:
                filtered[category] = data

        return filtered

    def _render_html_report(self, report_data: Dict[str, Any]) -> str:
        """Render HTML report from data"""
        # Try to use Jinja2 template if available
        if self.jinja_env:
            try:
                template = self.jinja_env.get_template('audit_report.html')
                return template.render(**report_data)
            except Exception as e:
                logger.warning(f"Failed to load Jinja2 template: {e}. Using default HTML.")

        # Fallback to default HTML generation
        return self._generate_default_html(report_data)

    def _generate_default_html(self, report_data: Dict[str, Any]) -> str:
        """Generate default HTML report without Jinja2"""
        metadata = report_data['metadata']
        summary = report_data['executive_summary']
        overall = report_data['overall_score']
        categories = report_data['category_scores']
        recommendations = report_data['recommendations']

        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{metadata['title']}</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background: #f5f7fa; }}
                .container {{ max-width: 1200px; margin: 0 auto; padding: 40px 20px; }}
                header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 60px 20px; text-align: center; border-radius: 12px; margin-bottom: 40px; }}
                h1 {{ font-size: 48px; margin-bottom: 10px; }}
                .meta {{ font-size: 18px; opacity: 0.9; }}
                .section {{ background: white; padding: 30px; margin-bottom: 30px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                h2 {{ color: #2d3748; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 3px solid #667eea; }}
                .score-display {{ text-align: center; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 12px; margin: 20px 0; }}
                .score-number {{ font-size: 96px; font-weight: bold; }}
                .score-label {{ font-size: 24px; opacity: 0.9; }}
                .categories {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
                .category-card {{ padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; background: #f7fafc; }}
                .category-score {{ font-size: 36px; font-weight: bold; color: #667eea; }}
                .recommendation {{ padding: 20px; margin: 15px 0; border-left: 4px solid #f59e0b; background: #fffbeb; border-radius: 4px; }}
                .priority-high {{ border-left-color: #ef4444; background: #fef2f2; }}
                .priority-medium {{ border-left-color: #f59e0b; background: #fffbeb; }}
                .footer {{ text-align: center; padding: 40px 20px; color: #718096; }}
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>SEO Audit Report</h1>
                    <div class="meta">
                        <p>{metadata['url']}</p>
                        <p>Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
                    </div>
                </header>

                <div class="section">
                    <h2>Executive Summary</h2>
                    <div class="score-display">
                        <div class="score-number">{overall['score']}</div>
                        <div class="score-label">{overall['status'].title()}</div>
                    </div>
                    <p><strong>Overall Health:</strong> {summary['overall_health']}</p>
                    <p>{summary['health_description']}</p>
                    <p><strong>Total Issues:</strong> {summary['total_issues']} ({summary['critical_issues']} critical)</p>
                </div>

                <div class="section">
                    <h2>Category Scores</h2>
                    <div class="categories">
        """

        for category in categories:
            html += f"""
                        <div class="category-card">
                            <div>{category['icon']} <strong>{category['name']}</strong></div>
                            <div class="category-score">{category['score']}/100</div>
                            <div>{category['status'].title()}</div>
                        </div>
            """

        html += """
                    </div>
                </div>

                <div class="section">
                    <h2>Top Recommendations</h2>
        """

        for rec in recommendations[:10]:
            priority_class = f"priority-{rec['priority']}"
            html += f"""
                    <div class="recommendation {priority_class}">
                        <strong>{rec['title']}</strong>
                        <p>{rec['description']}</p>
                        <small>Category: {rec['category'].title()} | Effort: {rec['effort'].title()} | {rec['affected_pages']} pages affected</small>
                    </div>
            """

        html += """
                </div>

                <div class="footer">
                    <p>Generated by SEO Auditor</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _prepare_csv_data(self, report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare data for CSV export"""
        csv_data = []

        # Export recommendations as CSV
        for rec in report_data['recommendations']:
            csv_data.append({
                'Priority': rec['priority'].title(),
                'Title': rec['title'],
                'Category': rec['category'].title(),
                'Effort': rec['effort'].title(),
                'Impact': rec['impact'].title(),
                'Affected Pages': rec['affected_pages']
            })

        return csv_data

    def _generate_filename(self, analysis_result: Dict[str, Any]) -> str:
        """Generate filename from URL"""
        url = analysis_result.get('url', 'seo_audit')
        # Clean URL for filename
        clean_url = url.replace('https://', '').replace('http://', '').replace('/', '_').replace(':', '')
        return f"seo_audit_{clean_url}"

    def _get_grade(self, score: int) -> str:
        """Get letter grade from score"""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        else:
            return 'F'

    def _get_status(self, score: int) -> str:
        """Get status label from score"""
        if score >= 90:
            return 'excellent'
        elif score >= 75:
            return 'good'
        elif score >= 60:
            return 'fair'
        elif score >= 40:
            return 'poor'
        else:
            return 'critical'

    def _get_score_color(self, score: int) -> str:
        """Get color for score"""
        if score >= 80:
            return '#10b981'  # green
        elif score >= 60:
            return '#f59e0b'  # yellow
        else:
            return '#ef4444'  # red

    def _get_score_description(self, score: int) -> str:
        """Get description for score"""
        if score >= 90:
            return 'Your website is exceptionally well-optimized for search engines.'
        elif score >= 75:
            return 'Your website is performing well with minor improvements needed.'
        elif score >= 60:
            return 'Your website meets basic SEO standards but needs improvement.'
        elif score >= 40:
            return 'Your website has significant SEO issues that need attention.'
        else:
            return 'Your website requires urgent SEO improvements.'

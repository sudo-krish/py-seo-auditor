"""
Export module for SEO Auditor
Handles exporting reports to multiple formats (PDF, CSV, JSON, HTML)
"""

import logging
import json
import csv
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from io import BytesIO, StringIO

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.platypus import Image as RLImage

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("ReportLab not installed. PDF export will be limited.")

try:
    from weasyprint import HTML

    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logging.warning("WeasyPrint not installed. HTML to PDF conversion unavailable.")

from utils.logger import log_execution_time

logger = logging.getLogger(__name__)


class ExportError(Exception):
    """Custom exception for export errors"""
    pass


class Exporter:
    """
    Main exporter class for SEO audit reports
    """

    def __init__(self, config: Dict = None):
        """
        Initialize exporter

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # Get export configuration
        export_config = self.config.get('reporting', {}).get('export', {})
        self.output_dir = Path(export_config.get('output_dir', 'data/reports'))

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Export settings
        self.pdf_pagesize = export_config.get('pdf_pagesize', 'letter')
        self.include_charts = export_config.get('include_charts', True)

        logger.info("Exporter initialized")

    def _generate_filename(self, base_name: str, extension: str) -> Path:
        """
        Generate unique filename with timestamp

        Args:
            base_name: Base name for file
            extension: File extension (without dot)

        Returns:
            Path object with full filename
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{base_name}_{timestamp}.{extension}"
        return self.output_dir / filename

    @log_execution_time(logger)
    def export_json(
            self,
            data: Dict[str, Any],
            filename: Optional[str] = None
    ) -> str:
        """
        Export data to JSON format

        Args:
            data: Dictionary to export
            filename: Optional filename (without extension)

        Returns:
            Path to exported file
        """
        if not filename:
            filename = self._generate_filename('seo_audit', 'json')
        else:
            filename = self.output_dir / f"{filename}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"Exported JSON to {filename}")
            return str(filename)

        except Exception as e:
            logger.error(f"Error exporting JSON: {e}")
            raise ExportError(f"JSON export failed: {e}")

    @log_execution_time(logger)
    def export_csv(
            self,
            data: List[Dict[str, Any]],
            filename: Optional[str] = None,
            fieldnames: Optional[List[str]] = None
    ) -> str:
        """
        Export data to CSV format

        Args:
            data: List of dictionaries to export
            filename: Optional filename (without extension)
            fieldnames: Optional list of field names to include

        Returns:
            Path to exported file
        """
        if not data:
            raise ExportError("No data to export to CSV")

        if not filename:
            filename = self._generate_filename('seo_audit', 'csv')
        else:
            filename = self.output_dir / f"{filename}.csv"

        # Determine fieldnames if not provided
        if not fieldnames:
            fieldnames = list(data[0].keys())

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for row in data:
                    # Only write fields that are in fieldnames
                    filtered_row = {k: v for k, v in row.items() if k in fieldnames}
                    writer.writerow(filtered_row)

            logger.info(f"Exported CSV to {filename}")
            return str(filename)

        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            raise ExportError(f"CSV export failed: {e}")

    @log_execution_time(logger)
    def export_html(
            self,
            data: Dict[str, Any],
            filename: Optional[str] = None,
            template: Optional[str] = None
    ) -> str:
        """
        Export data to HTML format

        Args:
            data: Dictionary to export
            filename: Optional filename (without extension)
            template: Optional HTML template string

        Returns:
            Path to exported file
        """
        if not filename:
            filename = self._generate_filename('seo_audit', 'html')
        else:
            filename = self.output_dir / f"{filename}.html"

        # Generate HTML content
        if template:
            html_content = template
        else:
            html_content = self._generate_default_html(data)

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"Exported HTML to {filename}")
            return str(filename)

        except Exception as e:
            logger.error(f"Error exporting HTML: {e}")
            raise ExportError(f"HTML export failed: {e}")

    def _generate_default_html(self, data: Dict[str, Any]) -> str:
        """Generate default HTML report"""
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SEO Audit Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    color: #333;
                }}
                h1 {{
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #34495e;
                    margin-top: 30px;
                }}
                .metric {{
                    display: inline-block;
                    padding: 15px 25px;
                    margin: 10px;
                    border-radius: 8px;
                    background: #ecf0f1;
                }}
                .score {{
                    font-size: 48px;
                    font-weight: bold;
                    color: #2ecc71;
                }}
                .issue {{
                    padding: 10px;
                    margin: 5px 0;
                    border-left: 4px solid #e74c3c;
                    background: #fadbd8;
                }}
                .warning {{
                    border-left-color: #f39c12;
                    background: #fef5e7;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #3498db;
                    color: white;
                }}
                .footer {{
                    margin-top: 50px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    text-align: center;
                    color: #7f8c8d;
                }}
            </style>
        </head>
        <body>
            <h1>SEO Audit Report</h1>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>URL:</strong> {data.get('url', 'N/A')}</p>

            <h2>Overall Score</h2>
            <div class="metric">
                <div class="score">{data.get('overall_score', 0)}/100</div>
                <div>Overall SEO Score</div>
            </div>

            <h2>Category Scores</h2>
            <table>
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Score</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Add category scores
        category_scores = data.get('category_scores', {})
        for category, score in category_scores.items():
            status = 'Good' if score >= 80 else 'Fair' if score >= 60 else 'Poor'
            html += f"""
                    <tr>
                        <td>{category.title()}</td>
                        <td>{score}</td>
                        <td>{status}</td>
                    </tr>
            """

        html += """
                </tbody>
            </table>

            <h2>Issues Summary</h2>
        """

        # Add issues
        issues = data.get('issues', {})
        for severity in ['critical', 'error', 'warning']:
            issue_list = issues.get(severity, [])
            if issue_list:
                html += f"<h3>{severity.title()} Issues ({len(issue_list)})</h3>"
                for issue in issue_list[:10]:  # Limit to top 10
                    html += f'<div class="issue {severity}">{issue.get("title", "Issue")}</div>'

        html += """
            <div class="footer">
                <p>Generated by SEO Auditor</p>
            </div>
        </body>
        </html>
        """

        return html

    @log_execution_time(logger)
    def export_pdf_from_html(
            self,
            html_content: str,
            filename: Optional[str] = None
    ) -> str:
        """
        Export HTML content to PDF using WeasyPrint

        Args:
            html_content: HTML string to convert
            filename: Optional filename (without extension)

        Returns:
            Path to exported file
        """
        if not WEASYPRINT_AVAILABLE:
            raise ExportError("WeasyPrint not installed. Cannot export HTML to PDF.")

        if not filename:
            filename = self._generate_filename('seo_audit', 'pdf')
        else:
            filename = self.output_dir / f"{filename}.pdf"

        try:
            HTML(string=html_content).write_pdf(filename)
            logger.info(f"Exported PDF (from HTML) to {filename}")
            return str(filename)

        except Exception as e:
            logger.error(f"Error exporting PDF from HTML: {e}")
            raise ExportError(f"PDF export failed: {e}")

    @log_execution_time(logger)
    def export_pdf_reportlab(
            self,
            data: Dict[str, Any],
            filename: Optional[str] = None
    ) -> str:
        """
        Export data to PDF using ReportLab

        Args:
            data: Dictionary to export
            filename: Optional filename (without extension)

        Returns:
            Path to exported file
        """
        if not REPORTLAB_AVAILABLE:
            raise ExportError("ReportLab not installed. Cannot export PDF.")

        if not filename:
            filename = self._generate_filename('seo_audit', 'pdf')
        else:
            filename = self.output_dir / f"{filename}.pdf"

        try:
            # Create PDF document
            pagesize = A4 if self.pdf_pagesize == 'a4' else letter
            doc = SimpleDocTemplate(str(filename), pagesize=pagesize)
            story = []

            # Get styles
            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            heading_style = styles['Heading2']
            normal_style = styles['Normal']

            # Title
            story.append(Paragraph("SEO Audit Report", title_style))
            story.append(Spacer(1, 0.2 * inch))

            # Meta information
            story.append(Paragraph(f"<b>URL:</b> {data.get('url', 'N/A')}", normal_style))
            story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
            story.append(Spacer(1, 0.3 * inch))

            # Overall Score
            story.append(Paragraph("Overall Score", heading_style))
            score_text = f"<font size=36><b>{data.get('overall_score', 0)}/100</b></font>"
            story.append(Paragraph(score_text, normal_style))
            story.append(Spacer(1, 0.3 * inch))

            # Category Scores Table
            story.append(Paragraph("Category Scores", heading_style))
            story.append(Spacer(1, 0.1 * inch))

            category_scores = data.get('category_scores', {})
            if category_scores:
                table_data = [['Category', 'Score', 'Status']]

                for category, score in category_scores.items():
                    status = 'Good' if score >= 80 else 'Fair' if score >= 60 else 'Poor'
                    table_data.append([category.title(), str(score), status])

                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)

            story.append(Spacer(1, 0.3 * inch))

            # Issues Summary
            story.append(Paragraph("Issues Summary", heading_style))
            story.append(Spacer(1, 0.1 * inch))

            issues = data.get('issues', {})
            for severity in ['critical', 'error', 'warning']:
                issue_list = issues.get(severity, [])
                if issue_list:
                    story.append(Paragraph(f"<b>{severity.title()} Issues: {len(issue_list)}</b>", normal_style))
                    for issue in issue_list[:5]:  # Limit to top 5 per severity
                        story.append(Paragraph(f"• {issue.get('title', 'Issue')}", normal_style))
                    story.append(Spacer(1, 0.2 * inch))

            # Build PDF
            doc.build(story)

            logger.info(f"Exported PDF (ReportLab) to {filename}")
            return str(filename)

        except Exception as e:
            logger.error(f"Error exporting PDF with ReportLab: {e}")
            raise ExportError(f"PDF export failed: {e}")

    def export_all_formats(
            self,
            data: Dict[str, Any],
            base_filename: str
    ) -> Dict[str, str]:
        """
        Export report in all available formats

        Args:
            data: Dictionary to export
            base_filename: Base filename (without extension)

        Returns:
            Dictionary with format -> filepath mappings
        """
        exported_files = {}

        # JSON
        try:
            exported_files['json'] = self.export_json(data, base_filename)
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")

        # HTML
        try:
            html_file = self.export_html(data, base_filename)
            exported_files['html'] = html_file

            # PDF from HTML (if WeasyPrint available)
            if WEASYPRINT_AVAILABLE:
                try:
                    with open(html_file, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    exported_files['pdf'] = self.export_pdf_from_html(html_content, base_filename)
                except Exception as e:
                    logger.error(f"Failed to export PDF from HTML: {e}")
        except Exception as e:
            logger.error(f"Failed to export HTML: {e}")

        # PDF with ReportLab (fallback if WeasyPrint not available)
        if 'pdf' not in exported_files and REPORTLAB_AVAILABLE:
            try:
                exported_files['pdf'] = self.export_pdf_reportlab(data, base_filename)
            except Exception as e:
                logger.error(f"Failed to export PDF with ReportLab: {e}")

        logger.info(f"Exported {len(exported_files)} formats: {list(exported_files.keys())}")
        return exported_files

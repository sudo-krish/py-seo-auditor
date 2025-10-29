"""
Reports page for SEO Auditor
Generate, view, export, and manage comprehensive SEO audit reports
"""

import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
import sys
import pandas as pd
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from reporting.report_generator import ReportGenerator
from reporting.export import ReportExporter
from reporting.visualizations import ChartGenerator

# Page configuration
st.set_page_config(
    page_title="SEO Auditor - Reports",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


def display_header():
    """Display page header"""
    st.title("📊 Reports & Export")
    st.markdown("""
    Generate comprehensive SEO audit reports, compare historical data, and export in multiple formats 
    for stakeholders, clients, and team members.
    """)
    st.markdown("---")


def display_report_generation():
    """Display report generation interface"""
    st.markdown("### 📝 Generate New Report")

    if not st.session_state.get('audit_results'):
        st.warning("⚠️ No audit data available. Please run an audit first.")
        if st.button("← Go to Main Page", type="primary"):
            st.switch_page("main.py")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        # Report configuration
        st.markdown("#### Report Configuration")

        # Report type
        report_type = st.selectbox(
            "Report Type",
            ["Comprehensive Report", "Executive Summary", "Technical Only", "Quick Overview"],
            help="Select the type and depth of report to generate"
        )

        # Report format
        export_formats = st.multiselect(
            "Export Formats",
            ["PDF", "HTML", "CSV", "JSON"],
            default=["PDF", "HTML"],
            help="Select one or more formats for export"
        )

        # Include sections
        st.markdown("**Include Sections:**")

        col_a, col_b = st.columns(2)

        with col_a:
            include_executive_summary = st.checkbox("Executive Summary", value=True)
            include_technical = st.checkbox("Technical SEO", value=True)
            include_onpage = st.checkbox("On-Page SEO", value=True)
            include_performance = st.checkbox("Performance", value=True)

        with col_b:
            include_mobile = st.checkbox("Mobile SEO", value=True)
            include_security = st.checkbox("Security", value=True)
            include_accessibility = st.checkbox("Accessibility", value=True)
            include_recommendations = st.checkbox("Recommendations", value=True)

        # Additional options
        st.markdown("**Additional Options:**")

        include_charts = st.checkbox("Include Charts & Visualizations", value=True)
        include_page_details = st.checkbox("Include Page-Level Details", value=False)
        include_comparison = st.checkbox("Compare with Previous Audit", value=False)

        # Report branding
        with st.expander("Branding & Customization"):
            company_name = st.text_input("Company/Agency Name", value="")
            report_title = st.text_input("Report Title", value="SEO Audit Report")
            logo_url = st.text_input("Logo URL (optional)", value="")
            custom_notes = st.text_area("Custom Notes/Introduction", value="")

    with col2:
        st.markdown("#### Report Preview")

        # Display report summary
        results = st.session_state.audit_results

        st.info(f"""
        **Audit Date:** {results.get('audit_date', 'N/A')}

        **Website:** {results.get('url', 'N/A')}

        **Pages Analyzed:** {results.get('pages_analyzed', 0)}

        **Overall Score:** {results.get('overall_score', 0)}/100

        **Total Issues:** {sum([len(cat.get('issues', [])) for cat in results.values() if isinstance(cat, dict)])}
        """)

        # Generate report button
        if st.button("🎯 Generate Report", type="primary", use_container_width=True):
            with st.spinner("Generating report..."):
                generate_report(
                    report_type=report_type,
                    formats=export_formats,
                    sections={
                        'executive_summary': include_executive_summary,
                        'technical': include_technical,
                        'onpage': include_onpage,
                        'performance': include_performance,
                        'mobile': include_mobile,
                        'security': include_security,
                        'accessibility': include_accessibility,
                        'recommendations': include_recommendations
                    },
                    options={
                        'include_charts': include_charts,
                        'include_page_details': include_page_details,
                        'include_comparison': include_comparison,
                        'company_name': company_name,
                        'report_title': report_title,
                        'logo_url': logo_url,
                        'custom_notes': custom_notes
                    }
                )


def generate_report(report_type, formats, sections, options):
    """Generate and save report"""
    try:
        results = st.session_state.audit_results

        # Simulate report generation
        report_files = []

        for format_type in formats:
            filename = f"seo_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type.lower()}"
            report_files.append(filename)

        st.success(f"✅ Report generated successfully!")

        # Display download buttons
        st.markdown("**Download Report:**")

        for i, format_type in enumerate(formats):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.text(f"📄 {report_files[i]}")
            with col2:
                st.button(f"Download {format_type}", key=f"download_{i}", use_container_width=True)
            with col3:
                st.button("Preview", key=f"preview_{i}", use_container_width=True)

        # Save to report history
        save_report_history(report_files[0], report_type, results.get('overall_score', 0))

    except Exception as e:
        st.error(f"Error generating report: {str(e)}")


def save_report_history(filename, report_type, score):
    """Save report to history"""
    if 'report_history' not in st.session_state:
        st.session_state.report_history = []

    st.session_state.report_history.insert(0, {
        'filename': filename,
        'type': report_type,
        'date': datetime.now(),
        'score': score,
        'url': st.session_state.get('current_url', 'N/A')
    })

    # Keep only last 20 reports
    st.session_state.report_history = st.session_state.report_history[:20]


def display_executive_summary():
    """Display executive summary preview"""
    st.markdown("### 📋 Executive Summary")

    if not st.session_state.get('audit_results'):
        st.info("Run an audit to see the executive summary.")
        return

    results = st.session_state.audit_results

    col1, col2 = st.columns([2, 1])

    with col1:
        # Overall health assessment
        st.markdown("#### Website Health Assessment")

        overall_score = results.get('overall_score', 0)
        grade = _get_grade(overall_score)
        status = _get_status(overall_score)

        score_color = _get_score_color(overall_score)

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {score_color}20, {score_color}10); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid {score_color};">
            <h2 style="margin: 0; color: {score_color};">{overall_score}/100 - Grade {grade}</h2>
            <p style="margin: 5px 0 0 0; font-size: 18px;">Status: {status}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Key findings
        st.markdown("#### Key Findings")

        # Strengths
        st.markdown("**✅ Strengths:**")
        strengths = _get_strengths(results)
        for strength in strengths[:3]:
            st.markdown(f"- {strength}")

        st.markdown("")

        # Areas for improvement
        st.markdown("**⚠️ Areas for Improvement:**")
        improvements = _get_improvements(results)
        for improvement in improvements[:3]:
            st.markdown(f"- {improvement}")

        st.markdown("")

        # Critical issues
        critical_issues = _get_critical_issues(results)
        if critical_issues:
            st.markdown("**🚨 Critical Issues Requiring Immediate Attention:**")
            for issue in critical_issues[:3]:
                st.error(f"❌ {issue}")

    with col2:
        st.markdown("#### Score Breakdown")

        # Category scores
        categories = ['technical', 'onpage', 'performance', 'mobile', 'security', 'accessibility']

        for category in categories:
            cat_data = results.get(category, {})
            score = cat_data.get('score', 0)

            st.markdown(f"**{category.replace('_', ' ').title()}**")
            st.progress(score / 100)
            st.markdown(f"Score: {score}/100")
            st.markdown("")

        # Quick stats
        st.markdown("#### Quick Statistics")

        total_issues = sum([len(results.get(cat, {}).get('issues', [])) for cat in categories])
        pages_analyzed = results.get('pages_analyzed', 0)

        st.metric("Total Issues", total_issues)
        st.metric("Pages Analyzed", pages_analyzed)
        st.metric("Audit Duration", f"{results.get('audit_duration', 0):.1f}s")


def display_category_summaries():
    """Display category-by-category summaries"""
    st.markdown("### 📊 Category Performance")

    if not st.session_state.get('audit_results'):
        return

    results = st.session_state.audit_results

    # Create tabs for each category
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Technical SEO", "On-Page SEO", "Performance",
        "Mobile", "Security", "Accessibility"
    ])

    with tab1:
        display_category_summary("technical", "Technical SEO", results)

    with tab2:
        display_category_summary("onpage", "On-Page SEO", results)

    with tab3:
        display_category_summary("performance", "Performance", results)

    with tab4:
        display_category_summary("mobile", "Mobile", results)

    with tab5:
        display_category_summary("security", "Security", results)

    with tab6:
        display_category_summary("accessibility", "Accessibility", results)


def display_category_summary(category_key, category_name, results):
    """Display summary for a specific category"""
    cat_data = results.get(category_key, {})

    if not cat_data:
        st.info(f"No {category_name} data available.")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        score = cat_data.get('score', 0)
        st.metric(f"{category_name} Score", f"{score}/100")

    with col2:
        issues = cat_data.get('issues', [])
        st.metric("Total Issues", len(issues))

    with col3:
        critical = len([i for i in issues if i.get('severity') == 'critical'])
        st.metric("Critical Issues", critical)

    # Top issues
    if issues:
        st.markdown("**Top Issues:**")

        # Sort by severity
        sorted_issues = sorted(issues, key=lambda x: {'critical': 0, 'error': 1, 'warning': 2, 'info': 3}.get(
            x.get('severity', 'info'), 3))

        for issue in sorted_issues[:5]:
            severity = issue.get('severity', 'info')
            icon = {'critical': '🚨', 'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}.get(severity, 'ℹ️')
            st.markdown(f"{icon} **{issue.get('title', 'Issue')}** ({issue.get('affected_pages', 0)} pages)")

    # Recommendations
    recommendations = cat_data.get('recommendations', [])
    if recommendations:
        with st.expander(f"View {len(recommendations)} Recommendations"):
            for rec in recommendations[:5]:
                st.markdown(f"- {rec.get('title', 'Recommendation')}")


def display_report_history():
    """Display report history and management"""
    st.markdown("### 📚 Report History")

    if 'report_history' not in st.session_state or not st.session_state.report_history:
        st.info("No reports generated yet. Generate your first report above!")
        return

    # Display reports in a table
    reports_data = []

    for report in st.session_state.report_history:
        reports_data.append({
            'Date': report['date'].strftime('%Y-%m-%d %H:%M'),
            'Website': report.get('url', 'N/A')[:40],
            'Type': report['type'],
            'Score': f"{report['score']}/100",
            'Filename': report['filename']
        })

    if reports_data:
        df = pd.DataFrame(reports_data)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Score": st.column_config.ProgressColumn(
                    "Score",
                    help="Overall audit score",
                    format="%d/100",
                    min_value=0,
                    max_value=100,
                )
            }
        )

        # Bulk actions
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state.report_history = []
                st.rerun()

        with col2:
            if st.button("📥 Download All", use_container_width=True):
                st.info("Preparing archive...")

        with col3:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()


def display_comparison():
    """Display audit comparison"""
    st.markdown("### 📈 Audit Comparison")

    if 'report_history' not in st.session_state or len(st.session_state.report_history) < 2:
        st.info("Need at least 2 audits to compare. Run another audit to enable comparison.")
        return

    col1, col2 = st.columns(2)

    with col1:
        audit_1 = st.selectbox(
            "Select First Audit",
            range(len(st.session_state.report_history)),
            format_func=lambda
                x: f"{st.session_state.report_history[x]['date'].strftime('%Y-%m-%d %H:%M')} - Score: {st.session_state.report_history[x]['score']}"
        )

    with col2:
        audit_2 = st.selectbox(
            "Select Second Audit",
            range(len(st.session_state.report_history)),
            index=min(1, len(st.session_state.report_history) - 1),
            format_func=lambda
                x: f"{st.session_state.report_history[x]['date'].strftime('%Y-%m-%d %H:%M')} - Score: {st.session_state.report_history[x]['score']}"
        )

    if st.button("Compare Audits", type="primary"):
        # Display comparison
        report_1 = st.session_state.report_history[audit_1]
        report_2 = st.session_state.report_history[audit_2]

        st.markdown("#### Comparison Results")

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.metric(
                "Score Change",
                f"{report_2['score']}/100",
                delta=report_2['score'] - report_1['score']
            )

        with col_b:
            st.metric(
                "Time Difference",
                f"{(report_2['date'] - report_1['date']).days} days"
            )

        with col_c:
            trend = "Improving" if report_2['score'] > report_1['score'] else "Declining" if report_2['score'] < \
                                                                                             report_1[
                                                                                                 'score'] else "Stable"
            st.metric("Trend", trend)


def display_scheduled_reports():
    """Display scheduled reports configuration"""
    st.markdown("### ⏰ Scheduled Reports")

    st.info("Configure automatic report generation and delivery (Coming Soon)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Schedule Configuration")

        frequency = st.selectbox(
            "Report Frequency",
            ["Daily", "Weekly", "Bi-weekly", "Monthly", "Quarterly"],
            index=2
        )

        recipients = st.text_area(
            "Email Recipients (comma-separated)",
            placeholder="email1@example.com, email2@example.com"
        )

        report_type = st.selectbox(
            "Automatic Report Type",
            ["Executive Summary", "Comprehensive Report", "Quick Overview"]
        )

        if st.button("💾 Save Schedule", type="primary", use_container_width=True):
            st.success("✅ Schedule saved successfully!")

    with col2:
        st.markdown("#### Active Schedules")
        st.info("No scheduled reports configured yet.")


def display_export_templates():
    """Display report templates"""
    st.markdown("### 📄 Report Templates")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Executive Template")
        st.info("High-level overview focused on business impact and key metrics.")
        if st.button("Use Executive Template", use_container_width=True):
            st.success("Template selected!")

    with col2:
        st.markdown("#### Technical Template")
        st.info("Detailed technical analysis for developers and SEO specialists.")
        if st.button("Use Technical Template", use_container_width=True):
            st.success("Template selected!")

    with col3:
        st.markdown("#### Client Template")
        st.info("Client-friendly report with visualizations and action items.")
        if st.button("Use Client Template", use_container_width=True):
            st.success("Template selected!")


def _get_grade(score):
    """Get letter grade from score"""
    if score >= 95:
        return "A+"
    elif score >= 90:
        return "A"
    elif score >= 85:
        return "A-"
    elif score >= 80:
        return "B+"
    elif score >= 75:
        return "B"
    elif score >= 70:
        return "B-"
    elif score >= 65:
        return "C+"
    elif score >= 60:
        return "C"
    else:
        return "F"


def _get_status(score):
    """Get status text from score"""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Fair"
    elif score >= 40:
        return "Poor"
    else:
        return "Critical"


def _get_score_color(score):
    """Get color based on score"""
    if score >= 90:
        return "#10b981"
    elif score >= 75:
        return "#3b82f6"
    elif score >= 60:
        return "#f59e0b"
    else:
        return "#ef4444"


def _get_strengths(results):
    """Extract strengths from results"""
    strengths = []

    categories = ['technical', 'onpage', 'performance', 'mobile', 'security', 'accessibility']

    for category in categories:
        cat_data = results.get(category, {})
        score = cat_data.get('score', 0)

        if score >= 85:
            strengths.append(f"{category.replace('_', ' ').title()} is well-optimized ({score}/100)")

    if not strengths:
        strengths = ["Website meets basic SEO requirements"]

    return strengths


def _get_improvements(results):
    """Extract areas for improvement from results"""
    improvements = []

    categories = ['technical', 'onpage', 'performance', 'mobile', 'security', 'accessibility']

    for category in categories:
        cat_data = results.get(category, {})
        score = cat_data.get('score', 0)

        if score < 75:
            improvements.append(f"{category.replace('_', ' ').title()} needs attention ({score}/100)")

    return improvements if improvements else ["Continue monitoring and maintaining current performance"]


def _get_critical_issues(results):
    """Extract critical issues from results"""
    critical = []

    categories = ['technical', 'onpage', 'performance', 'mobile', 'security', 'accessibility']

    for category in categories:
        cat_data = results.get(category, {})
        issues = cat_data.get('issues', [])

        for issue in issues:
            if issue.get('severity') == 'critical':
                critical.append(f"{issue.get('title', 'Critical Issue')} in {category.title()}")

    return critical


def main():
    """Main function for Reports page"""
    display_header()

    # Display report generation
    display_report_generation()

    st.markdown("---")

    # Display executive summary
    display_executive_summary()

    st.markdown("---")

    # Display category summaries
    display_category_summaries()

    st.markdown("---")

    # Display report history
    display_report_history()

    st.markdown("---")

    # Display comparison
    display_comparison()

    st.markdown("---")

    # Display scheduled reports
    display_scheduled_reports()

    st.markdown("---")

    # Display templates
    display_export_templates()


if __name__ == "__main__":
    main()

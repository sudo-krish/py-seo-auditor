"""
Dashboard page for SEO Auditor
Main overview page showing audit results and key metrics
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from reporting.visualizations import ChartGenerator
from core.analyzer import AnalysisResult
from core.scorer import SEOScorer

# Page configuration
st.set_page_config(
    page_title="SEO Auditor - Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize chart generator
if 'chart_generator' not in st.session_state:
    config = st.session_state.get('config', {})
    st.session_state.chart_generator = ChartGenerator(config)

chart_gen = st.session_state.chart_generator


def display_header():
    """Display page header"""
    st.title("🏠 SEO Audit Dashboard")
    st.markdown("---")


def display_overview_metrics():
    """Display overview metrics in cards"""
    if not st.session_state.get('audit_results'):
        st.info("👋 Welcome! Start by running an SEO audit from the main page.")
        return

    results = st.session_state.audit_results

    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        overall_score = results.get('overall_score', 0)
        score_color = _get_score_color(overall_score)
        st.metric(
            label="Overall Score",
            value=f"{overall_score}/100",
            delta=_get_score_delta(overall_score),
            help="Your overall SEO health score"
        )

    with col2:
        issues = results.get('issues', {})
        critical_count = len(issues.get('critical', []))
        st.metric(
            label="Critical Issues",
            value=critical_count,
            delta=f"-{critical_count}" if critical_count > 0 else "None",
            delta_color="inverse",
            help="Issues requiring immediate attention"
        )

    with col3:
        pages_analyzed = results.get('pages_analyzed', 0)
        st.metric(
            label="Pages Analyzed",
            value=pages_analyzed,
            help="Total pages crawled and analyzed"
        )

    with col4:
        timestamp = results.get('timestamp')
        if timestamp:
            time_str = datetime.fromisoformat(timestamp).strftime('%H:%M')
            st.metric(
                label="Last Audit",
                value=time_str,
                help="Time of last audit"
            )


def display_score_visualization():
    """Display overall score gauge and category breakdown"""
    if not st.session_state.get('audit_results'):
        return

    results = st.session_state.audit_results
    overall_score = results.get('overall_score', 0)
    category_scores = results.get('category_scores', {})

    st.markdown("### 📊 Score Overview")

    col1, col2 = st.columns([1, 2])

    with col1:
        try:
            # Create gauge chart
            fig = chart_gen.create_score_gauge(overall_score, "Overall SEO Score")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating gauge chart: {e}")
            # Fallback display
            st.markdown(f"""
            <div style="text-align: center; padding: 40px;">
                <h1 style="font-size: 72px; color: {_get_score_color(overall_score)};">
                    {overall_score}
                </h1>
                <p style="font-size: 24px;">Overall Score</p>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        if category_scores:
            try:
                # Create category bar chart
                fig = chart_gen.create_category_scores_chart(category_scores)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating category chart: {e}")
                # Fallback display
                for category, score in category_scores.items():
                    st.progress(score / 100, text=f"{category.title()}: {score}/100")


def display_issues_summary():
    """Display issues summary with distribution chart"""
    if not st.session_state.get('audit_results'):
        return

    results = st.session_state.audit_results
    issues = results.get('issues', {})

    if not any(issues.values()):
        st.success("🎉 No issues found! Your site is in great shape.")
        return

    st.markdown("### ⚠️ Issues Summary")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Display top issues
        for severity in ['critical', 'error', 'warning']:
            issue_list = issues.get(severity, [])
            if issue_list:
                with st.expander(f"{severity.title()} Issues ({len(issue_list)})", expanded=(severity == 'critical')):
                    for i, issue in enumerate(issue_list[:5], 1):
                        st.markdown(f"""
                        **{i}. {issue.get('title', 'Unknown Issue')}**  
                        {issue.get('description', '')}  
                        *Category: {issue.get('category', 'N/A').title()}* | 
                        *Affected: {len(issue.get('affected_pages', []))} pages*
                        """)

                    if len(issue_list) > 5:
                        st.info(f"+ {len(issue_list) - 5} more issues")

    with col2:
        try:
            # Create issues distribution pie chart
            fig = chart_gen.create_issues_distribution_chart(issues)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning("Could not generate issues chart")
            # Fallback display
            for severity, issue_list in issues.items():
                if issue_list:
                    st.markdown(f"**{severity.title()}:** {len(issue_list)}")


def display_category_overview():
    """Display category-wise performance overview"""
    if not st.session_state.get('audit_results'):
        return

    results = st.session_state.audit_results
    category_scores = results.get('category_scores', {})

    if not category_scores:
        return

    st.markdown("### 📈 Category Performance")

    # Create tabs for each category
    categories = list(category_scores.keys())
    tabs = st.tabs([cat.title() for cat in categories])

    category_icons = {
        'technical': '🔧',
        'onpage': '📄',
        'performance': '⚡',
        'mobile': '📱',
        'security': '🔒',
        'accessibility': '♿'
    }

    for tab, category in zip(tabs, categories):
        with tab:
            score = category_scores[category]
            icon = category_icons.get(category, '📊')

            col1, col2 = st.columns([1, 3])

            with col1:
                st.markdown(f"""
                <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            border-radius: 10px; color: white;">
                    <div style="font-size: 48px;">{icon}</div>
                    <div style="font-size: 36px; font-weight: bold;">{score}</div>
                    <div style="font-size: 16px;">Score</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                # Get category-specific findings
                category_data = results.get(category, {})
                category_issues = category_data.get('issues', [])

                if category_issues:
                    st.markdown(f"**Top Issues in {category.title()}:**")
                    for i, issue in enumerate(category_issues[:3], 1):
                        st.markdown(f"{i}. {issue.get('title', 'Issue')}")
                else:
                    st.success(f"No issues found in {category.title()}!")

                # Show recommendations if available
                recommendations = category_data.get('recommendations', [])
                if recommendations:
                    with st.expander("💡 Recommendations"):
                        for rec in recommendations[:3]:
                            st.markdown(f"• {rec}")


def display_quick_actions():
    """Display quick action buttons"""
    st.markdown("### ⚡ Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔄 New Audit", use_container_width=True, type="primary"):
            st.switch_page("main.py")

    with col2:
        if st.button("📊 View Reports", use_container_width=True):
            st.switch_page("streamlit_app/pages/8_📊_Reports.py")

    with col3:
        if st.button("💾 Export Results", use_container_width=True):
            if st.session_state.get('audit_results'):
                st.info("Export functionality available in Reports page")
            else:
                st.warning("No results to export")

    with col4:
        if st.button("🗑️ Clear Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache cleared!")
            st.rerun()


def display_recent_audits():
    """Display recent audit history"""
    st.markdown("### 📜 Recent Audits")

    # Get recent audits from session state
    recent_audits = st.session_state.get('recent_audits', [])

    if not recent_audits:
        st.info("No recent audits. Start your first audit from the main page!")
        return

    # Display in a table
    for i, audit in enumerate(recent_audits[:5], 1):
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            st.markdown(f"**{audit.get('url', 'Unknown')}**")

        with col2:
            score = audit.get('overall_score', 0)
            st.markdown(f"Score: **{score}/100**")

        with col3:
            timestamp = audit.get('timestamp', '')
            if timestamp:
                dt = datetime.fromisoformat(timestamp)
                st.markdown(f"*{dt.strftime('%Y-%m-%d %H:%M')}*")

        with col4:
            if st.button("View", key=f"view_{i}", use_container_width=True):
                st.session_state.audit_results = audit
                st.rerun()


def _get_score_color(score: float) -> str:
    """Get color based on score"""
    if score >= 80:
        return "#10b981"  # green
    elif score >= 60:
        return "#f59e0b"  # yellow
    else:
        return "#ef4444"  # red


def _get_score_delta(score: float) -> str:
    """Get delta text based on score"""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Fair"
    else:
        return "Needs Work"


def main():
    """Main dashboard function"""
    # Display header
    display_header()

    # Check if user is authenticated (if authentication is enabled)
    if st.session_state.get('authentication_enabled', False):
        if not st.session_state.get('authenticated', False):
            st.warning("Please login to access the dashboard")
            return

    # Display overview metrics
    display_overview_metrics()

    st.markdown("---")

    # Display score visualization
    display_score_visualization()

    st.markdown("---")

    # Display issues summary
    display_issues_summary()

    st.markdown("---")

    # Display category overview
    display_category_overview()

    st.markdown("---")

    # Display quick actions
    display_quick_actions()

    st.markdown("---")

    # Display recent audits
    display_recent_audits()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px;">
        <p>SEO Auditor v1.0 | Built with Streamlit</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

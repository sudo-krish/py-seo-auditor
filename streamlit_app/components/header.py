"""
Header component for SEO Auditor
Provides consistent header with branding, navigation, and audit context
"""

import streamlit as st
from datetime import datetime
from typing import Optional, Dict, Any


def display_app_header(
        show_logo: bool = True,
        show_audit_info: bool = True,
        show_quick_stats: bool = False,
        custom_title: Optional[str] = None
):
    """
    Display application header with branding and context

    Args:
        show_logo: Whether to display the logo/branding
        show_audit_info: Whether to display current audit information
        show_quick_stats: Whether to display quick stats from current audit
        custom_title: Optional custom title to display
    """

    # Main header container
    header_container = st.container()

    with header_container:
        if show_logo:
            display_branding()

        if show_audit_info and st.session_state.get('audit_results'):
            display_audit_context()

        if show_quick_stats and st.session_state.get('audit_results'):
            display_quick_stats()


def display_branding():
    """Display application branding and logo"""

    col1, col2 = st.columns([1, 5])

    with col1:
        # Logo placeholder - can be replaced with actual logo image
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            width: 60px;
            height: 60px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            color: white;
            font-weight: bold;
        ">
            🔍
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="padding-top: 5px;">
            <h2 style="margin: 0; color: #1f2937; font-weight: 700;">
                SEO Auditor Pro
            </h2>
            <p style="margin: 0; color: #6b7280; font-size: 14px;">
                Comprehensive SEO Analysis Tool - 2025 Edition
            </p>
        </div>
        """, unsafe_allow_html=True)


def display_audit_context():
    """Display current audit context and information"""

    results = st.session_state.audit_results
    current_url = st.session_state.get('current_url', 'N/A')

    # Create an info box with current audit details
    st.markdown("""
    <style>
    .audit-context {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        border-left: 4px solid #3b82f6;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }
    .audit-context-title {
        font-size: 14px;
        font-weight: 600;
        color: #374151;
        margin-bottom: 8px;
    }
    .audit-context-detail {
        font-size: 13px;
        color: #6b7280;
        margin: 4px 0;
    }
    .audit-score {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 13px;
    }
    .score-excellent {
        background: #10b981;
        color: white;
    }
    .score-good {
        background: #3b82f6;
        color: white;
    }
    .score-fair {
        background: #f59e0b;
        color: white;
    }
    .score-poor {
        background: #ef4444;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    overall_score = results.get('overall_score', 0)
    score_class = _get_score_class(overall_score)

    audit_date = results.get('audit_date', datetime.now().strftime('%Y-%m-%d %H:%M'))
    pages_analyzed = results.get('pages_analyzed', 0)

    st.markdown(f"""
    <div class="audit-context">
        <div class="audit-context-title">📊 Current Audit</div>
        <div class="audit-context-detail">
            <strong>URL:</strong> {current_url[:60]}{'...' if len(current_url) > 60 else ''}
        </div>
        <div class="audit-context-detail">
            <strong>Date:</strong> {audit_date} | 
            <strong>Pages:</strong> {pages_analyzed} | 
            <strong>Score:</strong> <span class="audit-score {score_class}">{overall_score}/100</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def display_quick_stats():
    """Display quick statistics from current audit"""

    results = st.session_state.audit_results

    # Calculate aggregate statistics
    categories = ['technical', 'onpage', 'performance', 'mobile', 'security', 'accessibility']

    total_issues = 0
    critical_issues = 0
    category_scores = []

    for category in categories:
        cat_data = results.get(category, {})
        issues = cat_data.get('issues', [])
        total_issues += len(issues)
        critical_issues += len([i for i in issues if i.get('severity') == 'critical'])

        score = cat_data.get('score', 0)
        if score > 0:
            category_scores.append(score)

    avg_category_score = sum(category_scores) / len(category_scores) if category_scores else 0

    # Display stats in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Overall Score",
            value=f"{results.get('overall_score', 0)}/100",
            delta=_get_score_delta(results.get('overall_score', 0))
        )

    with col2:
        st.metric(
            label="Total Issues",
            value=total_issues,
            delta=f"-{total_issues}" if total_issues > 0 else "None",
            delta_color="inverse"
        )

    with col3:
        st.metric(
            label="Critical Issues",
            value=critical_issues,
            delta=f"-{critical_issues}" if critical_issues > 0 else "None",
            delta_color="inverse"
        )

    with col4:
        st.metric(
            label="Avg Category Score",
            value=f"{avg_category_score:.0f}/100"
        )


def display_navigation_breadcrumb(current_page: str, pages: list = None):
    """
    Display breadcrumb navigation

    Args:
        current_page: Name of the current page
        pages: Optional list of parent pages for breadcrumb
    """

    if pages is None:
        pages = []

    breadcrumb_html = '<div style="margin: 10px 0; font-size: 14px; color: #6b7280;">'
    breadcrumb_html += '<a href="/" style="color: #3b82f6; text-decoration: none;">🏠 Home</a>'

    for page in pages:
        breadcrumb_html += f' <span style="margin: 0 8px;">›</span> <a href="#{page}" style="color: #3b82f6; text-decoration: none;">{page}</a>'

    breadcrumb_html += f' <span style="margin: 0 8px;">›</span> <span style="color: #1f2937; font-weight: 600;">{current_page}</span>'
    breadcrumb_html += '</div>'

    st.markdown(breadcrumb_html, unsafe_allow_html=True)


def display_page_header(
        title: str,
        description: str = "",
        icon: str = "📊",
        show_divider: bool = True
):
    """
    Display page-specific header with title and description

    Args:
        title: Page title
        description: Page description
        icon: Icon emoji for the page
        show_divider: Whether to show divider after header
    """

    st.markdown(f"""
    <div style="margin-bottom: 20px;">
        <h1 style="margin: 0; color: #1f2937; font-weight: 700;">
            {icon} {title}
        </h1>
        {f'<p style="margin: 10px 0 0 0; color: #6b7280; font-size: 16px;">{description}</p>' if description else ''}
    </div>
    """, unsafe_allow_html=True)

    if show_divider:
        st.markdown("---")


def display_action_buttons():
    """Display common action buttons in header"""

    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

    with col1:
        pass  # Empty space

    with col2:
        if st.button("🔄 New Audit", use_container_width=True, help="Start a new audit"):
            st.switch_page("main.py")

    with col3:
        if st.button("📥 Export", use_container_width=True, help="Export current audit"):
            if st.session_state.get('audit_results'):
                st.switch_page("pages/8_📊_Reports.py")
            else:
                st.warning("No audit data to export")

    with col4:
        if st.button("🗑️ Clear Cache", use_container_width=True, help="Clear cached data"):
            if 'audit_results' in st.session_state:
                st.cache_data.clear()
                st.success("✅ Cache cleared!")
                st.rerun()


def display_api_status():
    """Display API integration status indicators"""

    st.markdown("### 🔌 API Integrations")

    api_keys_configured = st.session_state.get('api_keys_configured', {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Available Services:**")

        services = {
            'Google APIs': api_keys_configured.get('google', False),
            'Ahrefs': api_keys_configured.get('ahrefs', False),
            'SEMrush': api_keys_configured.get('semrush', False),
            'DataForSEO': api_keys_configured.get('dataforseo', False)
        }

        for service, configured in services.items():
            status = "✅" if configured else "⚪"
            status_text = "Connected" if configured else "Not configured"
            st.markdown(f"{status} {service}: *{status_text}*")

    with col2:
        st.markdown("**Quick Actions:**")
        if st.button("⚙️ Configure APIs", use_container_width=True):
            st.info("API configuration panel coming soon!")


def display_notification_banner(
        message: str,
        notification_type: str = "info",
        dismissible: bool = True
):
    """
    Display a notification banner at the top of the page

    Args:
        message: Notification message
        notification_type: Type of notification (info, success, warning, error)
        dismissible: Whether the notification can be dismissed
    """

    colors = {
        'info': ('#3b82f6', '#dbeafe', '#1e40af'),
        'success': ('#10b981', '#d1fae5', '#065f46'),
        'warning': ('#f59e0b', '#fef3c7', '#92400e'),
        'error': ('#ef4444', '#fee2e2', '#991b1b')
    }

    bg_color, border_color, text_color = colors.get(notification_type, colors['info'])

    icons = {
        'info': 'ℹ️',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌'
    }

    icon = icons.get(notification_type, 'ℹ️')

    notification_html = f"""
    <div style="
        background-color: {border_color};
        border-left: 4px solid {bg_color};
        padding: 15px;
        margin: 10px 0;
        border-radius: 4px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    ">
        <div>
            <span style="font-size: 20px; margin-right: 10px;">{icon}</span>
            <span style="color: {text_color}; font-weight: 500;">{message}</span>
        </div>
        {f'<span style="cursor: pointer; font-size: 20px; color: {text_color};">×</span>' if dismissible else ''}
    </div>
    """

    st.markdown(notification_html, unsafe_allow_html=True)


def _get_score_class(score: int) -> str:
    """Get CSS class based on score"""
    if score >= 90:
        return "score-excellent"
    elif score >= 75:
        return "score-good"
    elif score >= 60:
        return "score-fair"
    else:
        return "score-poor"


def _get_score_delta(score: int) -> str:
    """Get delta text based on score"""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Fair"
    else:
        return "Needs Work"


# Helper function to inject custom CSS for consistent styling
def inject_custom_css():
    """Inject custom CSS for header components"""

    st.markdown("""
    <style>
    /* Header Styling */
    .main-header {
        padding: 20px 0;
        border-bottom: 2px solid #e5e7eb;
        margin-bottom: 20px;
    }

    /* Metric Cards */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
        border: 1px solid #e5e7eb;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    /* Button Styling */
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Info Box Styling */
    .stAlert {
        border-radius: 8px;
        border-left-width: 4px;
    }

    /* Divider */
    hr {
        margin: 30px 0;
        border: none;
        border-top: 2px solid #e5e7eb;
    }
    </style>
    """, unsafe_allow_html=True)

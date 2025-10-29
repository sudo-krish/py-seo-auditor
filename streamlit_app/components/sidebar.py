"""
Sidebar component for SEO Auditor
Provides navigation, audit context, API status, and quick actions
"""

import streamlit as st
from datetime import datetime
from typing import Optional, Dict, List, Any


def display_sidebar(current_page: Optional[str] = None):
    """
    Display comprehensive sidebar with navigation and context

    Args:
        current_page: Name of the current page for highlighting
    """

    with st.sidebar:
        # Display branding/logo
        display_sidebar_branding()

        st.markdown("---")

        # Display navigation menu
        display_navigation_menu(current_page)

        st.markdown("---")

        # Display audit status
        if st.session_state.get('audit_results'):
            display_audit_status()
            st.markdown("---")

        # Display quick actions
        display_quick_actions()

        st.markdown("---")

        # Display API status
        display_api_integrations()

        st.markdown("---")

        # Display recent audits
        display_recent_audits()

        # Display footer
        display_sidebar_footer()


def display_sidebar_branding():
    """Display sidebar branding with logo and title"""

    st.markdown("""
    <div style="text-align: center; padding: 10px 0;">
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            width: 50px;
            height: 50px;
            border-radius: 10px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            margin-bottom: 10px;
        ">
            🔍
        </div>
        <h3 style="margin: 0; font-size: 18px; font-weight: 700;">SEO Auditor Pro</h3>
        <p style="margin: 5px 0 0 0; font-size: 11px; color: #6b7280;">2025 Edition</p>
    </div>
    """, unsafe_allow_html=True)


def display_navigation_menu(current_page: Optional[str] = None):
    """
    Display navigation menu with page links

    Args:
        current_page: Current page name for highlighting
    """

    st.markdown("### 🧭 Navigation")

    # Define navigation items
    nav_items = [
        {"icon": "🏠", "label": "Dashboard", "page": "main.py"},
        {"icon": "🔍", "label": "Technical SEO", "page": "pages/2_🔍_Technical_SEO.py"},
        {"icon": "📄", "label": "On-Page", "page": "pages/3_📄_On_Page.py"},
        {"icon": "⚡", "label": "Performance", "page": "pages/4_⚡_Performance.py"},
        {"icon": "📱", "label": "Mobile", "page": "pages/5_📱_Mobile.py"},
        {"icon": "🔒", "label": "Security", "page": "pages/6_🔒_Security.py"},
        {"icon": "♿", "label": "Accessibility", "page": "pages/7_♿_Accessibility.py"},
        {"icon": "📊", "label": "Reports", "page": "pages/8_📊_Reports.py"},
    ]

    # Display navigation buttons
    for item in nav_items:
        # Check if this is the current page
        is_current = current_page and item['label'].lower() in current_page.lower()

        button_type = "primary" if is_current else "secondary"

        if st.button(
                f"{item['icon']} {item['label']}",
                use_container_width=True,
                key=f"nav_{item['label']}",
                type=button_type
        ):
            st.switch_page(item['page'])


def display_audit_status():
    """Display current audit status and key metrics"""

    results = st.session_state.audit_results
    current_url = st.session_state.get('current_url', 'N/A')

    st.markdown("### 📊 Current Audit")

    # Display URL
    st.markdown(f"**Website:**")
    st.caption(current_url[:30] + ('...' if len(current_url) > 30 else ''))

    # Display overall score
    overall_score = results.get('overall_score', 0)

    # Create score visualization
    score_color = _get_score_color(overall_score)

    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 15px;
        background: linear-gradient(135deg, {score_color}20, {score_color}10);
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid {score_color};
    ">
        <div style="font-size: 32px; font-weight: 700; color: {score_color};">
            {overall_score}
        </div>
        <div style="font-size: 12px; color: #6b7280; margin-top: 5px;">
            Overall Score
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Display category scores
    st.markdown("**Category Scores:**")

    categories = [
        ('technical', 'Technical'),
        ('onpage', 'On-Page'),
        ('performance', 'Performance'),
        ('mobile', 'Mobile'),
        ('security', 'Security'),
        ('accessibility', 'Accessibility')
    ]

    for cat_key, cat_label in categories:
        cat_data = results.get(cat_key, {})
        score = cat_data.get('score', 0)

        # Create mini progress bar
        st.markdown(f"""
        <div style="margin: 8px 0;">
            <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 3px;">
                <span>{cat_label}</span>
                <span style="font-weight: 600;">{score}/100</span>
            </div>
            <div style="
                background: #e5e7eb;
                height: 6px;
                border-radius: 3px;
                overflow: hidden;
            ">
                <div style="
                    background: {_get_score_color(score)};
                    height: 100%;
                    width: {score}%;
                    transition: width 0.3s ease;
                "></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Display audit date
    audit_date = results.get('audit_date', datetime.now().strftime('%Y-%m-%d %H:%M'))
    st.caption(f"📅 {audit_date}")


def display_quick_actions():
    """Display quick action buttons"""

    st.markdown("### ⚡ Quick Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 New Audit", use_container_width=True, help="Start a new SEO audit"):
            st.switch_page("main.py")

    with col2:
        if st.button("📥 Export", use_container_width=True, help="Export audit report"):
            if st.session_state.get('audit_results'):
                st.switch_page("pages/8_📊_Reports.py")
            else:
                st.warning("No audit to export")

    # Additional actions
    if st.button("🗑️ Clear Cache", use_container_width=True, help="Clear cached data"):
        st.cache_data.clear()
        if 'audit_results' in st.session_state:
            del st.session_state.audit_results
        st.success("✅ Cache cleared!")
        st.rerun()

    if st.button("⚙️ Settings", use_container_width=True, help="Configure settings"):
        st.session_state['show_settings'] = True


def display_api_integrations():
    """Display API integration status"""

    st.markdown("### 🔌 API Status")

    api_keys_configured = st.session_state.get('api_keys_configured', {})

    # Define API services
    services = {
        'google': {'name': 'Google APIs', 'icon': '🔵'},
        'ahrefs': {'name': 'Ahrefs', 'icon': '🟠'},
        'semrush': {'name': 'SEMrush', 'icon': '🟡'},
        'dataforseo': {'name': 'DataForSEO', 'icon': '🟢'}
    }

    for key, service in services.items():
        is_configured = api_keys_configured.get(key, False)
        status_icon = "✅" if is_configured else "⚪"

        st.markdown(f"{status_icon} {service['icon']} {service['name']}")

    # Configure APIs button
    with st.expander("⚙️ Configure APIs"):
        st.markdown("""
        Configure API keys to enable advanced features:

        - **Google APIs**: Search Console + PageSpeed Insights
        - **Ahrefs**: Backlink analysis
        - **SEMrush**: Competitor analysis
        - **DataForSEO**: SERP data
        """)

        if st.button("Open API Settings", use_container_width=True):
            st.info("API configuration coming soon!")


def display_recent_audits():
    """Display recent audit history"""

    st.markdown("### 📚 Recent Audits")

    if 'audit_history' not in st.session_state or not st.session_state.audit_history:
        st.caption("No recent audits")
        return

    # Display last 5 audits
    for i, audit in enumerate(st.session_state.audit_history[:5]):
        audit_date = audit.get('date', datetime.now())
        audit_url = audit.get('url', 'Unknown')
        audit_score = audit.get('score', 0)

        # Format date
        if isinstance(audit_date, datetime):
            date_str = audit_date.strftime('%m/%d %H:%M')
        else:
            date_str = str(audit_date)

        # Create clickable audit entry
        score_color = _get_score_color(audit_score)

        with st.expander(f"🔍 {audit_url[:20]}... ({audit_score})"):
            st.markdown(f"""
            **URL:** {audit_url}  
            **Score:** <span style="color: {score_color}; font-weight: 600;">{audit_score}/100</span>  
            **Date:** {date_str}
            """, unsafe_allow_html=True)

            if st.button("Load Audit", key=f"load_audit_{i}", use_container_width=True):
                # Load audit data (placeholder)
                st.info("Loading audit data...")


def display_sidebar_footer():
    """Display sidebar footer with app info"""

    st.markdown("---")

    st.markdown("""
    <div style="text-align: center; font-size: 11px; color: #9ca3af; padding: 10px 0;">
        <p style="margin: 5px 0;">
            <strong>SEO Auditor Pro</strong><br>
            Version 1.0.0 (2025)
        </p>
        <p style="margin: 5px 0;">
            Powered by Streamlit
        </p>
        <p style="margin: 10px 0 0 0;">
            <a href="#" style="color: #3b82f6; text-decoration: none;">Documentation</a> • 
            <a href="#" style="color: #3b82f6; text-decoration: none;">Support</a>
        </p>
    </div>
    """, unsafe_allow_html=True)


def display_progress_indicator(progress: int, label: str = "Processing"):
    """
    Display progress indicator in sidebar

    Args:
        progress: Progress percentage (0-100)
        label: Label for the progress
    """

    with st.sidebar:
        st.markdown(f"### {label}")
        st.progress(progress / 100)
        st.caption(f"{progress}% complete")


def display_settings_panel():
    """Display settings panel in sidebar"""

    if not st.session_state.get('show_settings', False):
        return

    with st.sidebar:
        st.markdown("### ⚙️ Settings")

        # Audit settings
        with st.expander("🔍 Audit Settings", expanded=True):
            max_pages = st.number_input(
                "Max Pages to Crawl",
                min_value=1,
                max_value=1000,
                value=50,
                help="Maximum number of pages to analyze"
            )

            crawl_depth = st.number_input(
                "Crawl Depth",
                min_value=1,
                max_value=10,
                value=3,
                help="Maximum depth for crawling"
            )

            follow_external = st.checkbox(
                "Follow External Links",
                value=False,
                help="Include external links in analysis"
            )

        # Report settings
        with st.expander("📊 Report Settings"):
            include_screenshots = st.checkbox(
                "Include Screenshots",
                value=False
            )

            report_format = st.selectbox(
                "Default Export Format",
                ["PDF", "HTML", "CSV", "JSON"]
            )

        # Display settings
        with st.expander("🎨 Display Settings"):
            theme = st.selectbox(
                "Theme",
                ["Auto", "Light", "Dark"]
            )

            show_advanced = st.checkbox(
                "Show Advanced Options",
                value=False
            )

        # Save settings button
        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Save", use_container_width=True):
                st.success("Settings saved!")
                st.session_state['show_settings'] = False
                st.rerun()

        with col2:
            if st.button("✖️ Cancel", use_container_width=True):
                st.session_state['show_settings'] = False
                st.rerun()


def display_notification_badge(count: int, label: str = "Issues"):
    """
    Display notification badge in sidebar

    Args:
        count: Number to display in badge
        label: Label for the notification
    """

    if count == 0:
        return

    with st.sidebar:
        st.markdown(f"""
        <div style="
            background: #ef4444;
            color: white;
            padding: 5px 10px;
            border-radius: 12px;
            text-align: center;
            font-size: 12px;
            font-weight: 600;
            margin: 10px 0;
        ">
            {count} {label}
        </div>
        """, unsafe_allow_html=True)


def _get_score_color(score: int) -> str:
    """Get color based on score"""
    if score >= 90:
        return "#10b981"  # Green
    elif score >= 75:
        return "#3b82f6"  # Blue
    elif score >= 60:
        return "#f59e0b"  # Orange
    else:
        return "#ef4444"  # Red


def inject_sidebar_css():
    """Inject custom CSS for sidebar styling"""

    st.markdown("""
    <style>
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f9fafb 0%, #ffffff 100%);
    }

    /* Sidebar buttons */
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.2s;
        border: 1px solid #e5e7eb;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    /* Primary buttons in sidebar */
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
    }

    /* Expander styling */
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        font-size: 13px;
        font-weight: 600;
    }

    /* Progress bars */
    [data-testid="stSidebar"] .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }

    /* Dividers */
    [data-testid="stSidebar"] hr {
        margin: 15px 0;
        border: none;
        border-top: 1px solid #e5e7eb;
    }

    /* Captions */
    [data-testid="stSidebar"] .caption {
        font-size: 11px;
        color: #6b7280;
    }
    </style>
    """, unsafe_allow_html=True)

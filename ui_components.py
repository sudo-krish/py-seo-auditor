"""
UI Components and Display Functions
All display and rendering logic for the main page
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any
import uuid

from streamlit_app.components.widgets import score_card, category_score_card
from audit_engine import start_audit, load_sample_audit


def display_hero_section():
    """Display hero section with branding"""

    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 40px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 30px;
        color: white;
    ">
        <h1 style="margin: 0; font-size: 42px; font-weight: 700;">
            🔍 SEO Auditor Pro
        </h1>
        <p style="margin: 15px 0 0 0; font-size: 18px; opacity: 0.9;">
            Comprehensive SEO Analysis Tool - 2025 Edition
        </p>
        <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.8;">
            Analyze, optimize, and dominate search rankings with enterprise-grade insights
        </p>
    </div>
    """, unsafe_allow_html=True)


def display_audit_form():
    """Display the main audit form"""

    st.markdown("### 🎯 Start New SEO Audit")

    col1, col2 = st.columns([2, 1])

    with col1:
        # URL input
        url = st.text_input(
            "Website URL",
            value=st.session_state.current_url,
            placeholder="https://example.com",
            help="Enter the website URL to audit"
        )

        # Audit scope
        st.markdown("**Audit Scope:**")

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            max_pages = st.number_input(
                "Max Pages",
                min_value=1,
                max_value=1000,
                value=st.session_state.config.get('crawler', {}).get('max_pages', 50),
                help="Maximum number of pages to crawl"
            )

        with col_b:
            max_depth = st.number_input(
                "Max Depth",
                min_value=1,
                max_value=10,
                value=st.session_state.config.get('crawler', {}).get('max_depth', 3),
                help="Maximum crawl depth"
            )

        with col_c:
            crawl_delay = st.number_input(
                "Delay (seconds)",
                min_value=0.0,
                max_value=10.0,
                value=float(st.session_state.config.get('crawler', {}).get('delay', 1.0)),
                step=0.5,
                help="Delay between requests"
            )

    with col2:
        st.markdown("**Select Checks:**")

        checks = {}
        checks['technical'] = st.checkbox("🔍 Technical SEO", value=True)
        checks['onpage'] = st.checkbox("📄 On-Page SEO", value=True)
        checks['performance'] = st.checkbox("⚡ Performance", value=True)
        checks['mobile'] = st.checkbox("📱 Mobile SEO", value=True)
        checks['security'] = st.checkbox("🔒 Security", value=True)
        checks['accessibility'] = st.checkbox("♿ Accessibility", value=True)

        st.session_state.selected_checks = checks

    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        col_x, col_y = st.columns(2)

        with col_x:
            follow_external = st.checkbox("Follow External Links", value=False)
            respect_robots = st.checkbox("Respect robots.txt", value=True)
            use_api_integrations = st.checkbox("Use API Integrations", value=True)

        with col_y:
            include_subdomains = st.checkbox("Include Subdomains", value=False)
            check_images = st.checkbox("Analyze Images", value=True)
            check_scripts = st.checkbox("Analyze Scripts", value=True)

    # Start audit button
    st.markdown("---")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col2:
        if st.button("🚀 Start Audit", type="primary", use_container_width=True, disabled=st.session_state.audit_in_progress):
            if url:
                start_audit(url, max_pages, max_depth, crawl_delay)
            else:
                st.error("Please enter a valid URL")

    with col3:
        if st.button("📥 Load Sample", use_container_width=True):
            load_sample_audit()


def display_audit_results():
    """Display current audit results overview"""

    if not st.session_state.audit_results:
        return

    st.markdown("### 📊 Current Audit Results")

    results = st.session_state.audit_results

    # Overall score
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        score_card(
            label="Overall Score",
            score=results.get('overall_score', 0),
            help_text="Weighted average of all category scores"
        )

    with col2:
        st.metric(
            "Pages Analyzed",
            results.get('pages_analyzed', 0)
        )

    with col3:
        total_issues = sum([
            len(results.get(cat, {}).get('issues', []))
            for cat in ['technical', 'onpage', 'performance', 'mobile', 'security', 'accessibility']
        ])
        st.metric(
            "Total Issues",
            total_issues,
            delta=f"-{total_issues}" if total_issues > 0 else "None",
            delta_color="inverse"
        )

    with col4:
        duration = results.get('audit_duration', 0)
        st.metric(
            "Duration",
            f"{duration:.1f}s" if duration else "N/A"
        )

    st.caption(f"Audit Date: {results.get('audit_date', 'N/A')}")

    st.markdown("---")

    # Category scores
    st.markdown("### 📈 Category Performance")

    col1, col2, col3 = st.columns(3)

    categories = [
        ('technical', 'Technical SEO', '🔍'),
        ('onpage', 'On-Page SEO', '📄'),
        ('performance', 'Performance', '⚡'),
        ('mobile', 'Mobile SEO', '📱'),
        ('security', 'Security', '🔒'),
        ('accessibility', 'Accessibility', '♿')
    ]

    for i, (key, name, icon) in enumerate(categories):
        cat_data = results.get(key, {})
        score = cat_data.get('score', 0)
        issues = len(cat_data.get('issues', []))

        with [col1, col2, col3][i % 3]:
            category_score_card(name, score, issues, icon)


def display_quick_actions():
    """Display quick action cards"""

    st.markdown("### ⚡ Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📊 View Reports", use_container_width=True):
            st.switch_page("pages/8_📊_Reports.py")

    with col2:
        if st.button("🔍 Technical SEO", use_container_width=True):
            st.switch_page("pages/2_🔍_Technical_SEO.py")

    with col3:
        if st.button("⚡ Performance", use_container_width=True):
            st.switch_page("pages/4_⚡_Performance.py")

    with col4:
        if st.button("📥 Export Data", use_container_width=True):
            st.switch_page("pages/8_📊_Reports.py")


def display_recent_audits():
    """Display recent audit history"""

    if not st.session_state.audit_history:
        return

    st.markdown("### 📚 Recent Audits")

    history_data = []
    for audit in st.session_state.audit_history[:10]:
        history_data.append({
            'Date': audit['date'].strftime('%Y-%m-%d %H:%M'),
            'Website': audit['url'][:40] + ('...' if len(audit['url']) > 40 else ''),
            'Score': f"{audit['score']}/100"
        })

    if history_data:
        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True, hide_index=True)


def display_features_overview():
    """Display features overview for new users"""

    st.markdown("### ✨ What We Analyze")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **🔍 Technical SEO**
        - Crawlability & Indexability
        - Robots.txt & Sitemaps
        - URL Structure
        - Canonical Tags
        - Structured Data
        
        **📄 On-Page SEO**
        - Title & Meta Tags
        - Header Hierarchy
        - Content Quality
        - Keyword Optimization
        - Internal Linking
        
        **⚡ Performance**
        - Core Web Vitals (2025)
        - Page Speed Analysis
        - Resource Optimization
        - Caching Strategies
        """)

    with col2:
        st.markdown("""
        **📱 Mobile SEO**
        - Mobile-First Indexing
        - Responsive Design
        - Touch Target Sizing
        - Mobile Usability
        
        **🔒 Security**
        - HTTPS Implementation
        - Security Headers
        - SSL Certificate
        - Cookie Security
        
        **♿ Accessibility**
        - WCAG 2.2 Compliance
        - ARIA Implementation
        - Color Contrast
        - Keyboard Navigation
        """)

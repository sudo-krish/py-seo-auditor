"""
SEO Auditor Pro - Main Entry Point
A comprehensive SEO audit tool with Streamlit interface
"""

import streamlit as st
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import app modules
from app_config import initialize_app, load_config, inject_custom_styles
from ui_components import (
    display_hero_section,
    display_audit_form,
    display_audit_results,
    display_quick_actions,
    display_recent_audits,
    display_features_overview
)
from streamlit_app.components.sidebar import display_sidebar, inject_sidebar_css
from streamlit_app.components.header import inject_custom_css

# Configure page
st.set_page_config(
    page_title="SEO Auditor Pro",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/seo-auditor',
        'Report a bug': 'https://github.com/yourusername/seo-auditor/issues',
        'About': 'SEO Auditor Pro v1.0.0 - Comprehensive SEO Analysis Tool'
    }
)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""

    # Initialize application
    initialize_app()

    # Inject custom styles
    inject_custom_styles()
    inject_sidebar_css()
    inject_custom_css()

    # Display sidebar
    display_sidebar(current_page="Dashboard")

    # Main content
    display_hero_section()

    # Show audit form
    display_audit_form()

    st.markdown("---")

    # Show results if available
    if st.session_state.audit_results:
        display_audit_results()

        st.markdown("---")

        display_quick_actions()
    else:
        # Show features overview for new users
        display_features_overview()

    st.markdown("---")

    # Show recent audits
    display_recent_audits()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #9ca3af; font-size: 13px; padding: 20px;">
        <p>
            <strong>SEO Auditor Pro</strong> v1.0.0 | 
            Built with ❤️ using Streamlit | 
            © 2025 All Rights Reserved
        </p>
        <p>
            <a href="#" style="color: #3b82f6; text-decoration: none;">Documentation</a> • 
            <a href="#" style="color: #3b82f6; text-decoration: none;">GitHub</a> • 
            <a href="#" style="color: #3b82f6; text-decoration: none;">Support</a>
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

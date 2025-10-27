"""
SEO Auditor - Main Entry Point
A comprehensive SEO audit tool built with Streamlit
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import yaml
from dotenv import load_dotenv
import os

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import core modules
from utils.logger import setup_logger
from utils.cache import CacheManager
from core.crawler import SEOCrawler
from core.analyzer import SEOAnalyzer
from core.scorer import SEOScorer

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="SEO Auditor Pro",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/py-seo-auditor',
        'Report a bug': "https://github.com/yourusername/py-seo-auditor/issues",
        'About': "# SEO Auditor Pro\nComprehensive SEO analysis tool for technical and on-page optimization."
    }
)


# Load configuration
@st.cache_resource
def load_config():
    """Load configuration from config.yaml"""
    try:
        config_path = project_root / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            logger.warning("config.yaml not found, using defaults")
            return {
                'app': {
                    'name': 'SEO Auditor Pro',
                    'version': '1.0.0',
                    'max_pages_crawl': 100,
                    'timeout': 30
                },
                'checks': {
                    'technical': True,
                    'onpage': True,
                    'performance': True,
                    'mobile': True,
                    'security': True,
                    'accessibility': True
                }
            }
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}


# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'audit_results': None,
        'current_url': '',
        'crawl_data': None,
        'analysis_complete': False,
        'last_audit_time': None,
        'audit_history': [],
        'api_keys_configured': {
            'google': bool(os.getenv('GOOGLE_API_KEY')),
            'ahrefs': bool(os.getenv('AHREFS_API_KEY')),
            'semrush': bool(os.getenv('SEMRUSH_API_KEY')),
            'dataforseo': bool(os.getenv('DATAFORSEO_API_KEY'))
        },
        'selected_checks': {
            'technical': True,
            'onpage': True,
            'performance': True,
            'mobile': True,
            'security': True,
            'accessibility': True
        },
        'export_format': 'pdf',
        'overall_score': 0,
        'cache_enabled': True
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


# Custom CSS
def apply_custom_css():
    """Apply custom styling to the app"""
    st.markdown("""
        <style>
        /* Main container styling */
        .main {
            padding: 0rem 1rem;
        }

        /* Metric cards */
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 10px;
            color: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }

        .metric-card:hover {
            transform: translateY(-5px);
        }

        /* Score badges */
        .score-excellent { color: #10b981; font-weight: bold; font-size: 2rem; }
        .score-good { color: #3b82f6; font-weight: bold; font-size: 2rem; }
        .score-fair { color: #f59e0b; font-weight: bold; font-size: 2rem; }
        .score-poor { color: #ef4444; font-weight: bold; font-size: 2rem; }

        /* Section headers */
        .section-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }

        /* Sidebar styling */
        .css-1d391kg {
            background-color: #f8f9fa;
        }

        /* Button styling */
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            height: 3rem;
            font-weight: 600;
        }

        /* Alert boxes */
        .alert-box {
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }

        .alert-info { background-color: #dbeafe; border-left: 4px solid #3b82f6; }
        .alert-warning { background-color: #fef3c7; border-left: 4px solid #f59e0b; }
        .alert-success { background-color: #d1fae5; border-left: 4px solid #10b981; }
        .alert-error { background-color: #fee2e2; border-left: 4px solid #ef4444; }
        </style>
    """, unsafe_allow_html=True)


# Dashboard/Home page
def home_page():
    """Main dashboard page"""
    st.title("🔍 SEO Auditor Pro")
    st.markdown("### Comprehensive website SEO analysis and optimization")

    # Quick stats row
    if st.session_state.audit_results:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            score = st.session_state.overall_score
            score_class = (
                "score-excellent" if score >= 90 else
                "score-good" if score >= 75 else
                "score-fair" if score >= 50 else
                "score-poor"
            )
            st.markdown(f'<div class="{score_class}">{score}/100</div>', unsafe_allow_html=True)
            st.caption("Overall Score")

        with col2:
            st.metric("Pages Crawled", st.session_state.audit_results.get('pages_crawled', 0))

        with col3:
            st.metric("Issues Found", st.session_state.audit_results.get('total_issues', 0))

        with col4:
            st.metric("Critical Issues", st.session_state.audit_results.get('critical_issues', 0))

    # URL input section
    st.markdown("---")
    st.subheader("🚀 Start New Audit")

    col1, col2 = st.columns([3, 1])

    with col1:
        url = st.text_input(
            "Enter Website URL",
            placeholder="https://example.com",
            help="Enter the full URL including https://",
            key="url_input"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        start_audit = st.button("🔎 Start Audit", type="primary", use_container_width=True)

    # Audit options
    with st.expander("⚙️ Audit Options", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.checkbox("Technical SEO", value=True, key="check_technical")
            st.checkbox("On-Page SEO", value=True, key="check_onpage")

        with col2:
            st.checkbox("Performance", value=True, key="check_performance")
            st.checkbox("Mobile-Friendly", value=True, key="check_mobile")

        with col3:
            st.checkbox("Security", value=True, key="check_security")
            st.checkbox("Accessibility", value=True, key="check_accessibility")

        max_pages = st.slider("Max Pages to Crawl", 10, 500, 100, 10)

    # Start audit logic
    if start_audit:
        if not url:
            st.error("⚠️ Please enter a valid URL")
        elif not url.startswith(('http://', 'https://')):
            st.error("⚠️ URL must start with http:// or https://")
        else:
            st.session_state.current_url = url
            # Switch to dashboard page to show results
            st.success(f"✅ Starting audit for: {url}")
            st.info("👉 Navigate to the respective sections to view detailed results")

            # Placeholder for actual audit logic
            with st.spinner("🔄 Initializing audit..."):
                # This would trigger the actual crawler and analyzer
                st.session_state.audit_results = {
                    'url': url,
                    'timestamp': datetime.now(),
                    'pages_crawled': 0,
                    'total_issues': 0,
                    'critical_issues': 0
                }

    # Recent audits
    if st.session_state.audit_history:
        st.markdown("---")
        st.subheader("📋 Recent Audits")

        for idx, audit in enumerate(st.session_state.audit_history[-5:]):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"🌐 {audit.get('url', 'N/A')}")
                with col2:
                    st.caption(audit.get('timestamp', 'N/A'))
                with col3:
                    if st.button("View", key=f"view_{idx}"):
                        st.session_state.audit_results = audit

    # Feature highlights
    st.markdown("---")
    st.subheader("✨ Features")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **🔧 Technical SEO**
        - Crawlability & Indexing
        - Robots.txt & Sitemap
        - Canonical Tags
        - Structured Data
        """)

    with col2:
        st.markdown("""
        **📄 On-Page Analysis**
        - Meta Tags Optimization
        - Content Quality
        - Internal Linking
        - Keyword Usage
        """)

    with col3:
        st.markdown("""
        **⚡ Performance**
        - Core Web Vitals
        - Page Speed
        - Mobile Optimization
        - Security Checks
        """)

    # API Status
    st.markdown("---")
    st.subheader("🔌 API Integration Status")

    api_status = st.session_state.api_keys_configured

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status = "✅ Connected" if api_status['google'] else "❌ Not Connected"
        st.markdown(f"**Google APIs**  \n{status}")

    with col2:
        status = "✅ Connected" if api_status['ahrefs'] else "❌ Not Connected"
        st.markdown(f"**Ahrefs**  \n{status}")

    with col3:
        status = "✅ Connected" if api_status['semrush'] else "❌ Not Connected"
        st.markdown(f"**SEMrush**  \n{status}")

    with col4:
        status = "✅ Connected" if api_status['dataforseo'] else "❌ Not Connected"
        st.markdown(f"**DataForSEO**  \n{status}")


# Define pages
def main():
    """Main application entry point"""
    # Initialize
    init_session_state()
    apply_custom_css()
    config = load_config()

    # Define pages with st.Page
    pages = {
        "Home": [
            st.Page(home_page, title="Dashboard", icon="🏠", default=True),
        ],
        "SEO Analysis": [
            st.Page("streamlit_app/pages/2_🔍_Technical_SEO.py", title="Technical SEO", icon="🔍"),
            st.Page("streamlit_app/pages/3_📄_On_Page.py", title="On-Page SEO", icon="📄"),
            st.Page("streamlit_app/pages/4_⚡_Performance.py", title="Performance", icon="⚡"),
            st.Page("streamlit_app/pages/5_📱_Mobile.py", title="Mobile", icon="📱"),
            st.Page("streamlit_app/pages/6_🔒_Security.py", title="Security", icon="🔒"),
            st.Page("streamlit_app/pages/7_♿_Accessibility.py", title="Accessibility", icon="♿"),
        ],
        "Reports": [
            st.Page("streamlit_app/pages/8_📊_Reports.py", title="Reports", icon="📊"),
        ],
    }

    # Create navigation
    pg = st.navigation(pages)

    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50/667eea/ffffff?text=SEO+Auditor", use_container_width=True)
        st.markdown("---")

        # Current audit info
        if st.session_state.current_url:
            st.markdown("### 🎯 Current Audit")
            st.info(f"**URL:** {st.session_state.current_url}")

            if st.session_state.last_audit_time:
                st.caption(f"Last run: {st.session_state.last_audit_time}")

        st.markdown("---")

        # Quick actions
        st.markdown("### ⚡ Quick Actions")

        if st.button("🔄 New Audit", use_container_width=True):
            st.session_state.audit_results = None
            st.session_state.current_url = ''
            st.rerun()

        if st.button("💾 Export Report", use_container_width=True, disabled=not st.session_state.audit_results):
            st.info("Export functionality - Navigate to Reports page")

        if st.button("🗑️ Clear Cache", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("Cache cleared!")

        st.markdown("---")

        # App info
        st.caption(f"**Version:** {config.get('app', {}).get('version', '1.0.0')}")
        st.caption("© 2025 SEO Auditor Pro")

    # Run the selected page
    pg.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")
        st.info("Please check the logs for more details.")

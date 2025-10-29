"""
Application Configuration and Initialization
Handles config loading, session state, and API key checks
"""

import streamlit as st
from pathlib import Path
import yaml
import os
from typing import Dict, Any, List
from utils.logger import get_logger, AuditLogger, PerformanceLogger
from utils.cache import CacheManager

# Initialize loggers
logger = get_logger(__name__)
audit_logger = AuditLogger()
performance_logger = PerformanceLogger()

# Initialize cache manager
cache_manager = CacheManager()


@st.cache_resource
def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent / "config.yaml"

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info("Configuration loaded successfully")
        return config
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        # Return default configuration
        return {
            'crawler': {
                'max_pages': 50,
                'max_depth': 3,
                'delay': 1.0,
                'timeout': 30,
                'user_agent': 'SEO-Auditor-Bot/1.0'
            },
            'scoring': {
                'weights': {
                    'technical': 20,
                    'onpage': 20,
                    'performance': 20,
                    'mobile': 15,
                    'security': 15,
                    'accessibility': 10
                }
            }
        }


def check_api_keys() -> Dict[str, bool]:
    """Check which API keys are configured"""
    return {
        'google': bool(os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE') or os.getenv('GOOGLE_PAGESPEED_API_KEY')),
        'ahrefs': bool(os.getenv('AHREFS_API_TOKEN')),
        'semrush': bool(os.getenv('SEMRUSH_API_KEY')),
        'dataforseo': bool(os.getenv('DATAFORSEO_LOGIN') and os.getenv('DATAFORSEO_PASSWORD'))
    }


def load_audit_history() -> List[Dict[str, Any]]:
    """Load audit history from cache or database"""
    try:
        # Try to load from cache
        cached_history = cache_manager.get('audit_history')
        if cached_history:
            return cached_history
        return []
    except Exception as e:
        logger.error(f"Error loading audit history: {str(e)}")
        return []


def save_audit_history():
    """Save audit history to cache"""
    try:
        cache_manager.set('audit_history', st.session_state.audit_history, ttl=86400 * 30)  # 30 days
    except Exception as e:
        logger.error(f"Error saving audit history: {str(e)}")


def initialize_session_state():
    """Initialize Streamlit session state variables"""

    # Core audit data
    if 'audit_results' not in st.session_state:
        st.session_state.audit_results = None

    if 'current_url' not in st.session_state:
        st.session_state.current_url = ""

    if 'crawl_data' not in st.session_state:
        st.session_state.crawl_data = None

    # Configuration
    if 'config' not in st.session_state:
        st.session_state.config = load_config()

    # Selected audit checks
    if 'selected_checks' not in st.session_state:
        st.session_state.selected_checks = {
            'technical': True,
            'onpage': True,
            'performance': True,
            'mobile': True,
            'security': True,
            'accessibility': True
        }

    # API integration status
    if 'api_keys_configured' not in st.session_state:
        st.session_state.api_keys_configured = check_api_keys()

    # Audit history
    if 'audit_history' not in st.session_state:
        st.session_state.audit_history = load_audit_history()

    # Report history
    if 'report_history' not in st.session_state:
        st.session_state.report_history = []

    # UI state
    if 'show_settings' not in st.session_state:
        st.session_state.show_settings = False

    if 'audit_in_progress' not in st.session_state:
        st.session_state.audit_in_progress = False

    # Current session ID for audit logging
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None


def initialize_app():
    """Initialize the entire application"""
    initialize_session_state()


def inject_custom_styles():
    """Inject custom CSS styles"""

    st.markdown("""
    <style>
    /* Global Styles */
    .main {
        background: linear-gradient(180deg, #ffffff 0%, #f9fafb 100%);
    }

    /* Metric Cards */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
        border: 1px solid #e5e7eb;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }

    /* Text Inputs */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e5e7eb;
        padding: 12px;
    }

    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    /* Number Inputs */
    .stNumberInput > div > div > input {
        border-radius: 8px;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background: #f9fafb;
        border-radius: 8px;
        font-weight: 600;
    }

    /* Progress Bars */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }

    /* Dividers */
    hr {
        margin: 30px 0;
        border: none;
        border-top: 2px solid #e5e7eb;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
    }

    /* DataFrames */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)


# Export commonly used objects
__all__ = [
    'initialize_app',
    'load_config',
    'check_api_keys',
    'save_audit_history',
    'inject_custom_styles',
    'logger',
    'audit_logger',
    'performance_logger',
    'cache_manager'
]

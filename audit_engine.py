"""
Audit Engine - Core Audit Logic
Handles audit execution, sample data, and history management
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any
import uuid
import time

from core.crawler import SEOCrawler
from core.analyzer import SEOAnalyzer
from app_config import (
    logger,
    audit_logger,
    performance_logger,
    save_audit_history,
    cache_manager
)


def start_audit(url: str, max_pages: int, max_depth: int, crawl_delay: float):
    """Start the SEO audit process"""

    start_time = time.time()

    try:
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            st.error("URL must start with http:// or https://")
            return

        st.session_state.current_url = url
        st.session_state.audit_in_progress = True

        # Generate session ID
        session_id = str(uuid.uuid4())
        st.session_state.current_session_id = session_id

        # Log audit start
        audit_logger.start_session(url, session_id)
        logger.info(f"Starting audit for {url}")

        # Show progress
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Step 1: Crawl website
        status_text.text("🔍 Crawling website...")
        progress_bar.progress(10)

        with st.spinner("Crawling website..."):
            try:
                crawler = SEOCrawler(
                    config=st.session_state.config,
                    cache_manager=cache_manager
                )

                crawler.max_pages = max_pages
                crawler.max_depth = max_depth
                crawler.crawl_delay = crawl_delay

                crawl_results_list = crawler.crawl(start_url=url)

                crawl_results = {
                    'pages': [result.to_dict() for result in crawl_results_list],
                    'statistics': crawler.get_statistics(),
                    'url_list': crawler.get_url_list(),
                    'start_url': url,
                    'total_pages': len(crawl_results_list)
                }

                st.session_state.crawl_data = crawl_results

                performance_logger.log_metric(
                    'crawl_pages',
                    len(crawl_results['pages']),
                    unit='pages',
                    context={'session_id': session_id, 'url': url}
                )

                crawler.close()

            except Exception as e:
                audit_logger.log_error('crawl_error', str(e), {'url': url})
                raise

        progress_bar.progress(40)

        # Step 2: Run analysis (includes scoring)
        status_text.text("🔬 Analyzing SEO factors and calculating scores...")

        with st.spinner("Running comprehensive SEO analysis..."):
            try:
                analyzer = SEOAnalyzer(st.session_state.config)

                # Analyzer handles both analysis and scoring
                analysis_results = analyzer.analyze(
                    crawl_results,
                    selected_checks=st.session_state.selected_checks,
                    parallel=True
                )

            except Exception as e:
                audit_logger.log_error('analysis_error', str(e), {'url': url})
                raise

        progress_bar.progress(95)

        # Step 3: Finalize results
        status_text.text("📊 Finalizing audit report...")

        # Add audit metadata
        analysis_results['audit_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        analysis_results['session_id'] = session_id

        # Calculate execution time
        execution_time = time.time() - start_time
        analysis_results['audit_duration'] = execution_time

        progress_bar.progress(100)

        # Save results
        st.session_state.audit_results = analysis_results

        # Add to history
        save_to_history(analysis_results)

        # Log completion
        audit_logger.end_session({
            'overall_score': analysis_results.get('overall_score', 0),
            'pages_analyzed': analysis_results.get('pages_analyzed', 0),
            'duration': execution_time
        })

        performance_logger.log_metric(
            'audit_duration',
            execution_time,
            unit='seconds',
            context={'session_id': session_id, 'url': url}
        )

        status_text.text("✅ Audit complete!")
        st.success(
            f"✅ Audit completed successfully in {execution_time:.2f}s! "
            f"Overall score: {analysis_results.get('overall_score', 0)}/100"
        )

        logger.info(f"Audit completed for {url}: Score {analysis_results.get('overall_score', 0)}/100")

        # Clear progress indicators
        time.sleep(2)
        progress_bar.empty()
        status_text.empty()

        st.session_state.audit_in_progress = False
        st.rerun()

    except Exception as e:
        logger.error(f"Error during audit: {str(e)}", exc_info=True)
        audit_logger.log_error('audit_failed', str(e), {'url': url})
        st.error(f"❌ Error during audit: {str(e)}")
        st.session_state.audit_in_progress = False


def load_sample_audit():
    """Load sample audit data for demonstration"""

    # Sample data matches analyzer output format
    sample_data = {
        'overall_score': 78,
        'overall_grade': 'B',
        'overall_status': 'good',
        'audit_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'url': 'https://example.com',
        'pages_analyzed': 25,
        'audit_duration': 45.3,
        'session_id': str(uuid.uuid4()),
        'timestamp': datetime.now().isoformat(),
        'category_scores': {
            'technical': 85,
            'onpage': 75,
            'performance': 70,
            'mobile': 82,
            'security': 90,
            'accessibility': 68
        },
        'technical': {
            'score': 85,
            'grade': 'B',
            'status': 'good',
            'issues': [
                {
                    'title': 'Missing meta descriptions',
                    'severity': 'warning',
                    'category': 'technical',
                    'affected_pages': 5,
                    'description': '5 pages are missing meta descriptions',
                    'recommendation': 'Add unique meta descriptions to all pages (150-160 characters)'
                }
            ]
        },
        'onpage': {'score': 75, 'issues': []},
        'performance': {'score': 70, 'issues': []},
        'mobile': {'score': 82, 'issues': []},
        'security': {'score': 90, 'issues': []},
        'accessibility': {'score': 68, 'issues': []},
        'issues': [],
        'issues_by_severity': {
            'critical': [],
            'error': [],
            'warning': [],
            'info': []
        },
        'total_issues': 0,
        'recommendations': []
    }

    st.session_state.audit_results = sample_data
    st.session_state.current_url = 'https://example.com'

    st.session_state.crawl_data = {
        'pages': [],
        'statistics': {'pages_crawled': 25, 'duration_seconds': 45.3},
        'url_list': [f'https://example.com/page-{i}' for i in range(25)],
        'start_url': 'https://example.com',
        'total_pages': 25
    }

    logger.info("Sample audit data loaded")
    st.success("✅ Sample audit loaded!")
    st.rerun()


def save_to_history(results: Dict[str, Any]):
    """Save audit results to history"""

    history_entry = {
        'url': results.get('url'),
        'date': datetime.now(),
        'score': results.get('overall_score', 0),
        'session_id': results.get('session_id'),
        'pages_analyzed': results.get('pages_analyzed', 0),
        'duration': results.get('audit_duration', 0)
    }

    st.session_state.audit_history.insert(0, history_entry)
    st.session_state.audit_history = st.session_state.audit_history[:20]

    save_audit_history()


__all__ = ['start_audit', 'load_sample_audit', 'save_to_history']

"""
Mobile page for SEO Auditor
Displays mobile-friendliness, responsive design, and mobile usability analysis
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import sys
import pandas as pd

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from reporting.visualizations import ChartGenerator

# Page configuration
st.set_page_config(
    page_title="SEO Auditor - Mobile SEO",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)


def display_header():
    """Display page header"""
    st.title("📱 Mobile SEO & Usability")
    st.markdown("""
    Mobile-first indexing means Google predominantly uses the mobile version of your content for indexing and ranking. 
    This page analyzes your site's mobile-friendliness, responsive design, and mobile user experience.
    """)
    st.markdown("---")


def display_overview_metrics():
    """Display mobile SEO overview metrics"""
    if not st.session_state.get('audit_results'):
        st.info("⚠️ No audit data available. Please run an audit first.")
        return

    results = st.session_state.audit_results
    mobile_data = results.get('mobile', {})

    if not mobile_data:
        st.warning("Mobile SEO data not available in audit results.")
        return

    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)

    score = mobile_data.get('score', 0)

    with col1:
        st.metric(
            label="Mobile SEO Score",
            value=f"{score}/100",
            delta=_get_score_status(score),
            help="Overall mobile optimization score"
        )

    with col2:
        mobile_friendly = mobile_data.get('mobile_friendly_pages', 0)
        total_pages = results.get('pages_analyzed', 0)
        friendly_rate = (mobile_friendly / total_pages * 100) if total_pages > 0 else 0
        st.metric(
            label="Mobile-Friendly Rate",
            value=f"{friendly_rate:.0f}%",
            help="Percentage of mobile-optimized pages"
        )

    with col3:
        viewport_issues = mobile_data.get('viewport_issues', 0)
        st.metric(
            label="Viewport Issues",
            value=viewport_issues,
            delta=f"-{viewport_issues}" if viewport_issues > 0 else "None",
            delta_color="inverse",
            help="Pages with viewport configuration issues"
        )

    with col4:
        usability_issues = mobile_data.get('usability_issues', 0)
        st.metric(
            label="Usability Issues",
            value=usability_issues,
            delta=f"-{usability_issues}" if usability_issues > 0 else "None",
            delta_color="inverse",
            help="Mobile usability problems detected"
        )


def display_mobile_first_indexing():
    """Display mobile-first indexing compliance"""
    st.markdown("### 🔍 Mobile-First Indexing Compliance")

    if not st.session_state.get('audit_results'):
        return

    mobile_data = st.session_state.audit_results.get('mobile', {})
    indexing_data = mobile_data.get('mobile_first_indexing', {})

    st.info("""
    **Mobile-First Indexing (2025):** Google uses the mobile version of your site for indexing and ranking. 
    Your mobile and desktop content must be equivalent for optimal SEO performance.
    """)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Content Parity Check")

        # Check if mobile and desktop content match
        content_parity = indexing_data.get('content_parity', {})

        matching_content = content_parity.get('matching', 0)
        missing_content = content_parity.get('missing_on_mobile', 0)
        extra_content = content_parity.get('extra_on_mobile', 0)

        if missing_content == 0:
            st.success(f"✅ All content present on mobile ({matching_content} pages)")
        else:
            st.error(f"❌ {missing_content} pages missing content on mobile")

        # Structured data parity
        st.markdown("#### Structured Data Consistency")

        schema_parity = indexing_data.get('schema_parity', {})
        consistent_schema = schema_parity.get('consistent', 0)
        inconsistent_schema = schema_parity.get('inconsistent', 0)

        if inconsistent_schema == 0:
            st.success(f"✅ Structured data consistent ({consistent_schema} pages)")
        else:
            st.warning(f"⚠️ {inconsistent_schema} pages have inconsistent structured data")

        # Metadata parity
        st.markdown("#### Metadata Consistency")

        meta_parity = indexing_data.get('metadata_parity', {})

        parity_checks = {
            "Title tags": meta_parity.get('title_mismatch', 0),
            "Meta descriptions": meta_parity.get('description_mismatch', 0),
            "Canonical tags": meta_parity.get('canonical_mismatch', 0),
            "Robots directives": meta_parity.get('robots_mismatch', 0)
        }

        for check, count in parity_checks.items():
            if count == 0:
                st.success(f"✅ {check}: Consistent")
            else:
                st.warning(f"⚠️ {check}: {count} mismatches")

    with col2:
        st.markdown("#### Mobile-First Best Practices")
        st.markdown("""
        **Essential Requirements (2025):**

        ✓ Same content on mobile and desktop
        ✓ Consistent structured data
        ✓ Identical metadata (titles, descriptions)
        ✓ Same internal linking structure
        ✓ Equivalent images and media
        ✓ Responsive or adaptive design
        ✓ No blocked resources (CSS, JS)
        ✓ Proper viewport configuration

        **Critical:** Desktop-only content won't be indexed!
        """)


def display_responsive_design():
    """Display responsive design analysis"""
    st.markdown("### 📐 Responsive Design Analysis")

    if not st.session_state.get('audit_results'):
        return

    mobile_data = st.session_state.audit_results.get('mobile', {})
    responsive_data = mobile_data.get('responsive_design', {})

    tab1, tab2 = st.tabs(["Viewport Configuration", "Responsive Design"])

    with tab1:
        display_viewport_analysis(responsive_data.get('viewport', {}))

    with tab2:
        display_design_responsiveness(responsive_data.get('design', {}))


def display_viewport_analysis(viewport_data):
    """Display viewport meta tag analysis"""
    st.markdown("#### 📱 Viewport Meta Tag")

    col1, col2 = st.columns([1, 1])

    with col1:
        viewport_present = viewport_data.get('present', 0)
        viewport_missing = viewport_data.get('missing', 0)
        viewport_incorrect = viewport_data.get('incorrect', 0)

        total = viewport_present + viewport_missing + viewport_incorrect

        st.metric("Pages with Viewport", viewport_present)

        if viewport_missing > 0:
            st.error(f"❌ {viewport_missing} pages missing viewport tag")
        if viewport_incorrect > 0:
            st.warning(f"⚠️ {viewport_incorrect} pages with incorrect viewport")
        if viewport_missing == 0 and viewport_incorrect == 0:
            st.success("✅ All pages have correct viewport configuration")

        # Common viewport issues
        st.markdown("**Common Issues Found:**")
        issues = viewport_data.get('issues', [])
        if issues:
            for issue in issues[:5]:
                st.markdown(f"- {issue.get('page', '')[:50]}: {issue.get('issue', '')}")

    with col2:
        st.markdown("**Correct Viewport Tag (2025):**")
        st.code("""<meta name="viewport" 
      content="width=device-width, 
               initial-scale=1">""", language="html")

        st.markdown("**Why It Matters:**")
        st.markdown("""
        - Controls page scaling on mobile devices
        - Essential for mobile-first indexing
        - Enables responsive design
        - Improves mobile user experience
        - Required for Google's mobile-friendly test
        """)


def display_design_responsiveness(design_data):
    """Display responsive design checks"""
    st.markdown("#### 🎨 Responsive Design Implementation")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Design Method:**")
        design_method = design_data.get('method', 'unknown')

        if design_method == 'responsive':
            st.success("✅ Responsive design (recommended)")
        elif design_method == 'adaptive':
            st.info("ℹ️ Adaptive design (acceptable)")
        elif design_method == 'separate':
            st.warning("⚠️ Separate mobile site (m.domain.com)")
        else:
            st.error("❌ No mobile optimization detected")

        # CSS Media queries
        st.markdown("**CSS Media Queries:**")
        media_queries = design_data.get('media_queries', 0)

        if media_queries > 0:
            st.success(f"✅ {media_queries} media queries detected")
        else:
            st.warning("⚠️ No CSS media queries found")

    with col2:
        st.markdown("**Responsive Issues:**")

        issues = design_data.get('issues', {})

        issue_types = {
            "Fixed-width elements": issues.get('fixed_width', 0),
            "Horizontal scrolling": issues.get('horizontal_scroll', 0),
            "Small fonts (<12px)": issues.get('small_fonts', 0),
            "Blocked resources": issues.get('blocked_resources', 0)
        }

        has_issues = False
        for issue_type, count in issue_types.items():
            if count > 0:
                st.warning(f"⚠️ {issue_type}: {count} pages")
                has_issues = True

        if not has_issues:
            st.success("✅ No responsive design issues found")


def display_mobile_usability():
    """Display mobile usability analysis"""
    st.markdown("### 👆 Mobile Usability")

    if not st.session_state.get('audit_results'):
        return

    mobile_data = st.session_state.audit_results.get('mobile', {})
    usability_data = mobile_data.get('usability', {})

    tab1, tab2, tab3 = st.tabs(["Touch Elements", "Text Readability", "Interactive Elements"])

    with tab1:
        display_touch_elements(usability_data.get('touch_elements', {}))

    with tab2:
        display_text_readability(usability_data.get('text_readability', {}))

    with tab3:
        display_interactive_elements(usability_data.get('interactive_elements', {}))


def display_touch_elements(touch_data):
    """Display touch element analysis"""
    st.markdown("#### 👆 Touch Target Sizing")

    st.info("**2025 Standard:** Touch targets should be at least **48x48 pixels** with adequate spacing.")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Touch target issues
        small_targets = touch_data.get('small_targets', 0)
        close_targets = touch_data.get('too_close', 0)
        overlapping = touch_data.get('overlapping', 0)

        if small_targets > 0:
            st.error(f"❌ {small_targets} touch targets too small (<48px)")
        else:
            st.success("✅ All touch targets adequately sized")

        if close_targets > 0:
            st.warning(f"⚠️ {close_targets} touch targets too close together")

        if overlapping > 0:
            st.error(f"❌ {overlapping} overlapping touch targets")

        # Problem pages
        problem_pages = touch_data.get('problem_pages', [])
        if problem_pages:
            with st.expander(f"View {len(problem_pages)} Pages with Touch Issues"):
                for page in problem_pages[:10]:
                    st.markdown(f"""
                    **{page.get('url', '')[:60]}**  
                    Issue: {page.get('issue', '')}  
                    Element: {page.get('element', '')}
                    """)
                    st.markdown("---")

    with col2:
        st.markdown("**Touch Target Guidelines:**")
        st.markdown("""
        **Minimum Size:** 48x48px
        **Recommended:** 56x56px or larger
        **Spacing:** 8px minimum between targets

        **Best Practices:**
        - Increase button padding
        - Add spacing between links
        - Make clickable areas larger than visible elements
        - Use finger-friendly navigation
        - Avoid clustered tap targets
        """)


def display_text_readability(text_data):
    """Display text readability analysis"""
    st.markdown("#### 📖 Text Readability")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("**Font Size Issues:**")

        small_text = text_data.get('small_text', 0)
        illegible_text = text_data.get('illegible', 0)
        low_contrast = text_data.get('low_contrast', 0)

        if small_text > 0:
            st.warning(f"⚠️ {small_text} pages with text <16px")
        else:
            st.success("✅ All text adequately sized")

        if illegible_text > 0:
            st.error(f"❌ {illegible_text} pages with illegible text")

        if low_contrast > 0:
            st.warning(f"⚠️ {low_contrast} pages with low contrast text")

        # Line length issues
        st.markdown("**Line Length:**")
        long_lines = text_data.get('long_lines', 0)

        if long_lines > 0:
            st.info(f"ℹ️ {long_lines} pages have lines >75 characters")

    with col2:
        st.markdown("**Text Best Practices:**")
        st.markdown("""
        **Font Size:**
        - Body text: ≥16px
        - Never below 12px

        **Contrast Ratio:**
        - Normal text: ≥4.5:1
        - Large text: ≥3:1

        **Line Length:**
        - Optimal: 50-75 characters
        - Single column layout

        **Typography:**
        - Readable font families
        - Adequate line spacing (1.5)
        - Clear hierarchy
        """)


def display_interactive_elements(interactive_data):
    """Display interactive elements analysis"""
    st.markdown("#### ⚡ Interactive Elements")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Form Usability:**")

        form_issues = interactive_data.get('forms', {})

        small_inputs = form_issues.get('small_inputs', 0)
        no_labels = form_issues.get('missing_labels', 0)
        wrong_input_types = form_issues.get('wrong_input_types', 0)

        if small_inputs > 0:
            st.warning(f"⚠️ {small_inputs} form inputs too small")
        if no_labels > 0:
            st.error(f"❌ {no_labels} form inputs without labels")
        if wrong_input_types > 0:
            st.info(f"ℹ️ {wrong_input_types} inputs with incorrect type attribute")

    with col2:
        st.markdown("**Navigation & Menus:**")

        nav_issues = interactive_data.get('navigation', {})

        small_nav = nav_issues.get('small_nav_items', 0)
        complex_menus = nav_issues.get('complex_menus', 0)
        hamburger_issues = nav_issues.get('hamburger_issues', 0)

        if small_nav > 0:
            st.warning(f"⚠️ {small_nav} navigation items too small")
        if complex_menus > 0:
            st.info(f"ℹ️ {complex_menus} overly complex menus")


def display_content_issues():
    """Display mobile content issues"""
    st.markdown("### 📝 Mobile Content Issues")

    if not st.session_state.get('audit_results'):
        return

    mobile_data = st.session_state.audit_results.get('mobile', {})
    content_data = mobile_data.get('content_issues', {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Intrusive Interstitials")

        interstitials = content_data.get('interstitials', {})

        intrusive_popups = interstitials.get('intrusive', 0)
        blocking_content = interstitials.get('blocking', 0)

        if intrusive_popups > 0:
            st.error(f"❌ {intrusive_popups} pages with intrusive popups")
            st.markdown("**Google Penalty Risk:** Intrusive interstitials can harm rankings!")
        else:
            st.success("✅ No intrusive interstitials detected")

        if blocking_content > 0:
            st.warning(f"⚠️ {blocking_content} pages with content-blocking elements")

        st.markdown("**Acceptable Interstitials:**")
        st.markdown("""
        - Legal requirements (age verification, cookies)
        - Login dialogs for gated content
        - Easy-to-dismiss banners using reasonable space
        """)

    with col2:
        st.markdown("#### Flash & Plugins")

        plugins = content_data.get('plugins', {})

        flash_content = plugins.get('flash', 0)
        unsupported_plugins = plugins.get('unsupported', 0)

        if flash_content > 0:
            st.error(f"❌ {flash_content} pages using Flash (deprecated)")
        if unsupported_plugins > 0:
            st.warning(f"⚠️ {unsupported_plugins} pages with unsupported plugins")

        if flash_content == 0 and unsupported_plugins == 0:
            st.success("✅ No deprecated plugins detected")

        st.markdown("**Modern Alternatives:**")
        st.markdown("""
        - Use HTML5 for video/audio
        - CSS3 for animations
        - JavaScript for interactivity
        - SVG for graphics
        """)


def display_mobile_speed():
    """Display mobile speed analysis"""
    st.markdown("### ⚡ Mobile Speed Performance")

    if not st.session_state.get('audit_results'):
        return

    mobile_data = st.session_state.audit_results.get('mobile', {})
    speed_data = mobile_data.get('mobile_speed', {})

    col1, col2, col3 = st.columns(3)

    with col1:
        mobile_load_time = speed_data.get('avg_load_time', 0)
        st.metric("Avg. Mobile Load Time", f"{mobile_load_time:.2f}s")

        if mobile_load_time <= 2:
            st.success("✅ Fast (<2s)")
        elif mobile_load_time <= 3:
            st.warning("⚠️ Moderate (2-3s)")
        else:
            st.error("❌ Slow (>3s)")

    with col2:
        mobile_score = speed_data.get('mobile_performance_score', 0)
        st.metric("Mobile Performance Score", f"{mobile_score}/100")

        if mobile_score >= 90:
            st.success("✅ Excellent")
        elif mobile_score >= 50:
            st.warning("⚠️ Needs Improvement")
        else:
            st.error("❌ Poor")

    with col3:
        slow_3g = speed_data.get('slow_3g_load_time', 0)
        st.metric("Slow 3G Load Time", f"{slow_3g:.2f}s")

        if slow_3g <= 5:
            st.success("✅ Acceptable")
        else:
            st.warning("⚠️ Too slow on 3G")

    st.markdown("**Mobile Speed Optimization Tips:**")
    st.markdown("""
    - Optimize images for mobile (smaller sizes)
    - Minimize JavaScript execution
    - Use adaptive serving for images
    - Implement lazy loading
    - Reduce server response time
    - Enable compression
    - Leverage browser caching
    - Consider AMP for content pages
    """)


def display_mobile_specific_features():
    """Display mobile-specific features analysis"""
    st.markdown("### 🎯 Mobile-Specific Features")

    if not st.session_state.get('audit_results'):
        return

    mobile_data = st.session_state.audit_results.get('mobile', {})
    features_data = mobile_data.get('mobile_features', {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Progressive Web App (PWA)")

        pwa_data = features_data.get('pwa', {})

        has_manifest = pwa_data.get('has_manifest', False)
        has_service_worker = pwa_data.get('has_service_worker', False)
        installable = pwa_data.get('installable', False)

        if installable:
            st.success("✅ Site is a Progressive Web App")
        elif has_manifest and has_service_worker:
            st.info("ℹ️ PWA features partially implemented")
        else:
            st.info("ℹ️ Not a PWA (optional but recommended)")

        st.markdown("**PWA Benefits:**")
        st.markdown("""
        - Offline functionality
        - App-like experience
        - Push notifications
        - Home screen installation
        - Improved performance
        """)

    with col2:
        st.markdown("#### Mobile-Specific Tags")

        tags_data = features_data.get('mobile_tags', {})

        has_app_links = tags_data.get('has_app_links', False)
        has_tel_links = tags_data.get('has_tel_links', False)
        has_geo_meta = tags_data.get('has_geo_meta', False)

        st.markdown("**Mobile Enhancement Tags:**")
        st.markdown(f"""
        - Telephone links (tel:): {'✅' if has_tel_links else '❌'}
        - App deep links: {'✅' if has_app_links else '❌'}
        - Geo meta tags: {'✅' if has_geo_meta else '❌'}
        """)


def display_recommendations():
    """Display prioritized mobile recommendations"""
    st.markdown("### 💡 Mobile SEO Recommendations")

    if not st.session_state.get('audit_results'):
        return

    mobile_data = st.session_state.audit_results.get('mobile', {})
    recommendations = mobile_data.get('recommendations', [])

    if not recommendations:
        st.success("🎉 Your mobile SEO is excellent!")
        return

    # Group by priority
    high_priority = [r for r in recommendations if r.get('priority') == 'high']
    medium_priority = [r for r in recommendations if r.get('priority') == 'medium']

    if high_priority:
        st.markdown("#### 🔴 High Priority (Critical for Mobile-First)")
        for rec in high_priority[:5]:
            with st.expander(f"✓ {rec.get('title', 'Recommendation')}"):
                st.markdown(rec.get('description', ''))
                st.markdown(f"**Affected Pages:** {rec.get('affected_pages', 0)}")
                st.markdown(f"**Impact:** {rec.get('impact', 'High').title()}")
                st.markdown(f"**Effort:** {rec.get('effort', 'Medium').title()}")

    if medium_priority:
        st.markdown("#### 🟡 Medium Priority")
        for rec in medium_priority[:5]:
            st.markdown(f"- {rec.get('title', 'Recommendation')} ({rec.get('affected_pages', 0)} pages)")


def _get_score_status(score: float) -> str:
    """Get status text based on score"""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Fair"
    else:
        return "Needs Work"


def main():
    """Main function for Mobile SEO page"""
    display_header()

    # Check if audit data exists
    if not st.session_state.get('audit_results'):
        st.info("👋 No audit data available. Please run an audit from the main page.")
        if st.button("← Go to Main Page", type="primary"):
            st.switch_page("main.py")
        return

    # Display overview metrics
    display_overview_metrics()

    st.markdown("---")

    # Display mobile-first indexing
    display_mobile_first_indexing()

    st.markdown("---")

    # Display responsive design
    display_responsive_design()

    st.markdown("---")

    # Display mobile usability
    display_mobile_usability()

    st.markdown("---")

    # Display content issues
    display_content_issues()

    st.markdown("---")

    # Display mobile speed
    display_mobile_speed()

    st.markdown("---")

    # Display mobile-specific features
    display_mobile_specific_features()

    st.markdown("---")

    # Display recommendations
    display_recommendations()


if __name__ == "__main__":
    main()

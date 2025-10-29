"""
Performance page for SEO Auditor
Displays Core Web Vitals, page speed, and performance optimization analysis
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
    page_title="SEO Auditor - Performance",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)


def display_header():
    """Display page header"""
    st.title("⚡ Performance & Core Web Vitals")
    st.markdown("""
    Website performance directly impacts user experience, SEO rankings, and conversions. 
    This page analyzes your site's loading speed, Core Web Vitals, and identifies optimization opportunities.
    """)
    st.markdown("---")


def display_overview_metrics():
    """Display performance overview metrics"""
    if not st.session_state.get('audit_results'):
        st.info("⚠️ No audit data available. Please run an audit first.")
        return

    results = st.session_state.audit_results
    performance_data = results.get('performance', {})

    if not performance_data:
        st.warning("Performance data not available in audit results.")
        return

    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)

    score = performance_data.get('score', 0)

    with col1:
        st.metric(
            label="Performance Score",
            value=f"{score}/100",
            delta=_get_score_status(score),
            help="Overall performance health score"
        )

    with col2:
        cwv_passed = performance_data.get('cwv_passed', 0)
        total_pages = results.get('pages_analyzed', 0)
        cwv_pass_rate = (cwv_passed / total_pages * 100) if total_pages > 0 else 0
        st.metric(
            label="Core Web Vitals Pass Rate",
            value=f"{cwv_pass_rate:.0f}%",
            help="Percentage of pages passing all CWV thresholds"
        )

    with col3:
        avg_load_time = performance_data.get('avg_load_time', 0)
        st.metric(
            label="Avg. Load Time",
            value=f"{avg_load_time:.2f}s",
            delta="Good" if avg_load_time < 3 else "Slow",
            delta_color="normal" if avg_load_time < 3 else "inverse"
        )

    with col4:
        slow_pages = performance_data.get('slow_pages', 0)
        st.metric(
            label="Slow Pages (>3s)",
            value=slow_pages,
            delta=f"-{slow_pages}" if slow_pages > 0 else "None",
            delta_color="inverse"
        )


def display_core_web_vitals():
    """Display Core Web Vitals analysis"""
    st.markdown("### 🎯 Core Web Vitals (2025)")

    if not st.session_state.get('audit_results'):
        return

    performance_data = st.session_state.audit_results.get('performance', {})
    cwv_data = performance_data.get('core_web_vitals', {})

    st.info("""
    **Core Web Vitals** are Google's key metrics for measuring user experience. 
    In 2025, these include LCP (loading), INP (interactivity), and CLS (visual stability).
    """)

    tab1, tab2, tab3 = st.tabs(["📊 LCP", "⚡ INP", "🎨 CLS"])

    with tab1:
        display_lcp_analysis(cwv_data.get('lcp', {}))

    with tab2:
        display_inp_analysis(cwv_data.get('inp', {}))

    with tab3:
        display_cls_analysis(cwv_data.get('cls', {}))


def display_lcp_analysis(lcp_data):
    """Display Largest Contentful Paint analysis"""
    st.markdown("#### 📊 Largest Contentful Paint (LCP)")

    st.markdown("""
    **LCP** measures loading performance. It represents how long it takes for the largest 
    content element to become visible.
    """)

    col1, col2 = st.columns([1, 2])

    with col1:
        avg_lcp = lcp_data.get('average', 0)
        st.metric("Average LCP", f"{avg_lcp:.2f}s")

        # LCP Status
        if avg_lcp <= 2.5:
            st.success("✅ Good (≤2.5s)")
        elif avg_lcp <= 4.0:
            st.warning("⚠️ Needs Improvement (2.5s-4s)")
        else:
            st.error("❌ Poor (>4s)")

        # Mobile vs Desktop
        mobile_lcp = lcp_data.get('mobile', 0)
        desktop_lcp = lcp_data.get('desktop', 0)

        st.markdown("**By Device:**")
        st.markdown(f"- Mobile: {mobile_lcp:.2f}s")
        st.markdown(f"- Desktop: {desktop_lcp:.2f}s")

    with col2:
        st.markdown("**2025 Thresholds:**")
        st.markdown("- ✅ Good: ≤2.5 seconds")
        st.markdown("- ⚠️ Needs Improvement: 2.5s - 4s")
        st.markdown("- ❌ Poor: >4 seconds")

        st.markdown("**Common LCP Elements:**")
        lcp_elements = lcp_data.get('elements', [])
        if lcp_elements:
            for elem in lcp_elements[:5]:
                st.markdown(f"- {elem.get('type', '')}: {elem.get('url', '')[:60]}")

        st.markdown("**How to Improve:**")
        st.markdown("""
        - Optimize images (compress, use WebP)
        - Use CDN for faster delivery
        - Minimize render-blocking resources
        - Implement lazy loading
        - Optimize server response time
        """)


def display_inp_analysis(inp_data):
    """Display Interaction to Next Paint analysis"""
    st.markdown("#### ⚡ Interaction to Next Paint (INP)")

    st.markdown("""
    **INP** measures interactivity and responsiveness. It replaced FID in 2024 and tracks 
    the worst interaction delay during a page visit.
    """)

    col1, col2 = st.columns([1, 2])

    with col1:
        avg_inp = inp_data.get('average', 0)
        st.metric("Average INP", f"{avg_inp:.0f}ms")

        # INP Status
        if avg_inp <= 200:
            st.success("✅ Good (≤200ms)")
        elif avg_inp <= 500:
            st.warning("⚠️ Needs Improvement (200ms-500ms)")
        else:
            st.error("❌ Poor (>500ms)")

        # Mobile vs Desktop
        mobile_inp = inp_data.get('mobile', 0)
        desktop_inp = inp_data.get('desktop', 0)

        st.markdown("**By Device:**")
        st.markdown(f"- Mobile: {mobile_inp:.0f}ms")
        st.markdown(f"- Desktop: {desktop_inp:.0f}ms")

    with col2:
        st.markdown("**2025 Thresholds (NEW):**")
        st.markdown("- ✅ Good: ≤200 milliseconds")
        st.markdown("- ⚠️ Needs Improvement: 200ms - 500ms")
        st.markdown("- ❌ Poor: >500 milliseconds")

        st.info("🆕 INP replaced First Input Delay (FID) in 2024 as the official Core Web Vital metric")

        st.markdown("**How to Improve:**")
        st.markdown("""
        - Minimize JavaScript execution time
        - Break up long tasks
        - Optimize event handlers
        - Use web workers for heavy computations
        - Defer non-critical JavaScript
        - Reduce third-party script impact
        """)


def display_cls_analysis(cls_data):
    """Display Cumulative Layout Shift analysis"""
    st.markdown("#### 🎨 Cumulative Layout Shift (CLS)")

    st.markdown("""
    **CLS** measures visual stability. It quantifies unexpected layout shifts that occur 
    during page loading.
    """)

    col1, col2 = st.columns([1, 2])

    with col1:
        avg_cls = cls_data.get('average', 0)
        st.metric("Average CLS", f"{avg_cls:.3f}")

        # CLS Status
        if avg_cls <= 0.1:
            st.success("✅ Good (≤0.1)")
        elif avg_cls <= 0.25:
            st.warning("⚠️ Needs Improvement (0.1-0.25)")
        else:
            st.error("❌ Poor (>0.25)")

        # Mobile vs Desktop
        mobile_cls = cls_data.get('mobile', 0)
        desktop_cls = cls_data.get('desktop', 0)

        st.markdown("**By Device:**")
        st.markdown(f"- Mobile: {mobile_cls:.3f}")
        st.markdown(f"- Desktop: {desktop_cls:.3f}")

    with col2:
        st.markdown("**2025 Thresholds:**")
        st.markdown("- ✅ Good: ≤0.1")
        st.markdown("- ⚠️ Needs Improvement: 0.1 - 0.25")
        st.markdown("- ❌ Poor: >0.25")

        st.markdown("**Common CLS Causes:**")
        cls_issues = cls_data.get('issues', [])
        if cls_issues:
            for issue in cls_issues[:5]:
                st.markdown(f"- {issue}")

        st.markdown("**How to Improve:**")
        st.markdown("""
        - Set explicit dimensions for images/videos
        - Reserve space for ads and embeds
        - Avoid inserting content above existing content
        - Use transform animations instead of layout properties
        - Preload fonts to avoid FOIT/FOUT
        """)


def display_additional_metrics():
    """Display additional performance metrics"""
    st.markdown("### 📈 Additional Performance Metrics")

    if not st.session_state.get('audit_results'):
        return

    performance_data = st.session_state.audit_results.get('performance', {})
    metrics_data = performance_data.get('additional_metrics', {})

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### First Contentful Paint (FCP)")
        fcp = metrics_data.get('fcp', 0)
        st.metric("FCP", f"{fcp:.2f}s")

        if fcp <= 1.8:
            st.success("✅ Good (≤1.8s)")
        elif fcp <= 3.0:
            st.warning("⚠️ Needs Improvement")
        else:
            st.error("❌ Poor (>3s)")

    with col2:
        st.markdown("#### Time to First Byte (TTFB)")
        ttfb = metrics_data.get('ttfb', 0)
        st.metric("TTFB", f"{ttfb:.0f}ms")

        if ttfb <= 800:
            st.success("✅ Good (≤800ms)")
        elif ttfb <= 1800:
            st.warning("⚠️ Needs Improvement")
        else:
            st.error("❌ Poor (>1800ms)")

    with col3:
        st.markdown("#### Total Blocking Time (TBT)")
        tbt = metrics_data.get('tbt', 0)
        st.metric("TBT", f"{tbt:.0f}ms")

        if tbt <= 200:
            st.success("✅ Good (≤200ms)")
        elif tbt <= 600:
            st.warning("⚠️ Needs Improvement")
        else:
            st.error("❌ Poor (>600ms)")


def display_page_speed_analysis():
    """Display page speed analysis"""
    st.markdown("### 🏎️ Page Speed Analysis")

    if not st.session_state.get('audit_results'):
        return

    performance_data = st.session_state.audit_results.get('performance', {})
    speed_data = performance_data.get('page_speed', {})

    tab1, tab2 = st.tabs(["Slowest Pages", "Speed Distribution"])

    with tab1:
        st.markdown("#### Slowest Loading Pages")

        slowest_pages = speed_data.get('slowest_pages', [])

        if slowest_pages:
            speed_df = pd.DataFrame([
                {
                    'Page': page.get('url', '')[:60] + '...',
                    'Load Time': f"{page.get('load_time', 0):.2f}s",
                    'Size': f"{page.get('page_size', 0) / 1024:.1f}KB",
                    'Requests': page.get('requests', 0),
                    'Status': _get_speed_status(page.get('load_time', 0))
                }
                for page in slowest_pages[:20]
            ])

            st.dataframe(
                speed_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Status": st.column_config.TextColumn(
                        "Status",
                        help="Loading speed status"
                    )
                }
            )
        else:
            st.info("No page speed data available")

    with tab2:
        st.markdown("#### Load Time Distribution")

        distribution = speed_data.get('distribution', {})

        if distribution:
            col1, col2, col3 = st.columns(3)

            with col1:
                fast_pages = distribution.get('fast', 0)  # <2s
                st.metric("Fast (<2s)", fast_pages)

            with col2:
                moderate_pages = distribution.get('moderate', 0)  # 2-4s
                st.metric("Moderate (2-4s)", moderate_pages)

            with col3:
                slow_pages = distribution.get('slow', 0)  # >4s
                st.metric("Slow (>4s)", slow_pages)


def display_resource_optimization():
    """Display resource optimization analysis"""
    st.markdown("### 📦 Resource Optimization")

    if not st.session_state.get('audit_results'):
        return

    performance_data = st.session_state.audit_results.get('performance', {})
    resources_data = performance_data.get('resources', {})

    tab1, tab2, tab3, tab4 = st.tabs(["Images", "JavaScript", "CSS", "Fonts"])

    with tab1:
        display_image_optimization(resources_data.get('images', {}))

    with tab2:
        display_javascript_optimization(resources_data.get('javascript', {}))

    with tab3:
        display_css_optimization(resources_data.get('css', {}))

    with tab4:
        display_font_optimization(resources_data.get('fonts', {}))


def display_image_optimization(image_data):
    """Display image optimization analysis"""
    st.markdown("#### 🖼️ Image Optimization")

    col1, col2 = st.columns(2)

    with col1:
        total_images = image_data.get('total', 0)
        total_size = image_data.get('total_size', 0) / 1024 / 1024  # Convert to MB

        st.metric("Total Images", f"{total_images}")
        st.metric("Total Image Size", f"{total_size:.2f}MB")

        # Issues
        unoptimized = image_data.get('unoptimized', 0)
        wrong_format = image_data.get('wrong_format', 0)
        missing_dimensions = image_data.get('missing_dimensions', 0)

        if unoptimized > 0:
            st.warning(f"⚠️ {unoptimized} images can be compressed")
        if wrong_format > 0:
            st.info(f"ℹ️ {wrong_format} images should use WebP format")
        if missing_dimensions > 0:
            st.warning(f"⚠️ {missing_dimensions} images missing width/height")

    with col2:
        st.markdown("**Image Optimization Tips:**")
        st.markdown("""
        - Use WebP or AVIF format (better compression)
        - Compress images (aim for <100KB per image)
        - Use responsive images with srcset
        - Implement lazy loading for below-fold images
        - Set explicit width and height attributes
        - Use CSS sprites for icons
        - Consider image CDN for delivery
        - Optimize SVGs (remove unnecessary data)
        """)


def display_javascript_optimization(js_data):
    """Display JavaScript optimization analysis"""
    st.markdown("#### ⚙️ JavaScript Optimization")

    col1, col2 = st.columns(2)

    with col1:
        total_js = js_data.get('total_files', 0)
        total_size = js_data.get('total_size', 0) / 1024  # Convert to KB

        st.metric("Total JS Files", f"{total_js}")
        st.metric("Total JS Size", f"{total_size:.1f}KB")

        # Issues
        render_blocking = js_data.get('render_blocking', 0)
        unused_js = js_data.get('unused', 0)
        unminified = js_data.get('unminified', 0)

        if render_blocking > 0:
            st.error(f"❌ {render_blocking} render-blocking scripts")
        if unused_js > 0:
            st.warning(f"⚠️ {unused_js}KB of unused JavaScript")
        if unminified > 0:
            st.warning(f"⚠️ {unminified} unminified JS files")

    with col2:
        st.markdown("**JavaScript Optimization Tips:**")
        st.markdown("""
        - Minify and compress JavaScript files
        - Remove unused code (tree shaking)
        - Defer non-critical JavaScript
        - Use async/defer attributes
        - Code splitting for large bundles
        - Reduce third-party script impact
        - Use Web Workers for heavy tasks
        - Implement Service Workers for caching
        """)


def display_css_optimization(css_data):
    """Display CSS optimization analysis"""
    st.markdown("#### 🎨 CSS Optimization")

    col1, col2 = st.columns(2)

    with col1:
        total_css = css_data.get('total_files', 0)
        total_size = css_data.get('total_size', 0) / 1024  # Convert to KB

        st.metric("Total CSS Files", f"{total_css}")
        st.metric("Total CSS Size", f"{total_size:.1f}KB")

        # Issues
        render_blocking = css_data.get('render_blocking', 0)
        unused_css = css_data.get('unused', 0)
        unminified = css_data.get('unminified', 0)

        if render_blocking > 0:
            st.error(f"❌ {render_blocking} render-blocking stylesheets")
        if unused_css > 0:
            st.warning(f"⚠️ {unused_css}KB of unused CSS")
        if unminified > 0:
            st.warning(f"⚠️ {unminified} unminified CSS files")

    with col2:
        st.markdown("**CSS Optimization Tips:**")
        st.markdown("""
        - Minify and compress CSS files
        - Remove unused CSS rules
        - Use critical CSS inline
        - Load non-critical CSS asynchronously
        - Combine multiple CSS files
        - Use CSS sprites for icons
        - Avoid @import in CSS
        - Optimize CSS delivery
        """)


def display_font_optimization(font_data):
    """Display font optimization analysis"""
    st.markdown("#### 🔤 Font Optimization")

    col1, col2 = st.columns(2)

    with col1:
        total_fonts = font_data.get('total', 0)
        total_size = font_data.get('total_size', 0) / 1024  # Convert to KB

        st.metric("Total Fonts", f"{total_fonts}")
        st.metric("Total Font Size", f"{total_size:.1f}KB")

        # Issues
        no_display = font_data.get('no_font_display', 0)
        unoptimized = font_data.get('unoptimized_format', 0)

        if no_display > 0:
            st.warning(f"⚠️ {no_display} fonts missing font-display property")
        if unoptimized > 0:
            st.info(f"ℹ️ {unoptimized} fonts should use WOFF2 format")

    with col2:
        st.markdown("**Font Optimization Tips:**")
        st.markdown("""
        - Use WOFF2 format (best compression)
        - Subset fonts (include only needed characters)
        - Use font-display: swap
        - Preload critical fonts
        - Limit number of font families
        - Use system fonts when possible
        - Self-host fonts (avoid external requests)
        - Minimize font variations
        """)


def display_caching_analysis():
    """Display caching strategy analysis"""
    st.markdown("### 💾 Caching & Compression")

    if not st.session_state.get('audit_results'):
        return

    performance_data = st.session_state.audit_results.get('performance', {})
    caching_data = performance_data.get('caching', {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Browser Caching")

        cache_stats = caching_data.get('browser_cache', {})

        cached_resources = cache_stats.get('cached', 0)
        uncached_resources = cache_stats.get('uncached', 0)
        total_resources = cached_resources + uncached_resources
        cache_rate = (cached_resources / total_resources * 100) if total_resources > 0 else 0

        st.metric("Cache Hit Rate", f"{cache_rate:.0f}%")
        st.metric("Uncached Resources", uncached_resources)

        if uncached_resources > 0:
            st.warning(f"⚠️ {uncached_resources} resources without caching headers")

    with col2:
        st.markdown("#### Compression")

        compression_data = caching_data.get('compression', {})

        compressed = compression_data.get('compressed', 0)
        uncompressed = compression_data.get('uncompressed', 0)

        st.metric("Compressed Resources", compressed)
        st.metric("Uncompressed Resources", uncompressed)

        if uncompressed > 0:
            st.error(f"❌ {uncompressed} resources not using compression")
            potential_savings = compression_data.get('potential_savings', 0) / 1024
            st.info(f"💡 Potential savings: {potential_savings:.1f}KB")


def display_recommendations():
    """Display prioritized performance recommendations"""
    st.markdown("### 💡 Performance Recommendations")

    if not st.session_state.get('audit_results'):
        return

    performance_data = st.session_state.audit_results.get('performance', {})
    recommendations = performance_data.get('recommendations', [])

    if not recommendations:
        st.success("🎉 Your website performance is excellent!")
        return

    # Group by priority
    high_priority = [r for r in recommendations if r.get('priority') == 'high']
    medium_priority = [r for r in recommendations if r.get('priority') == 'medium']

    if high_priority:
        st.markdown("#### 🔴 High Priority (Largest Impact)")
        for rec in high_priority[:5]:
            with st.expander(f"✓ {rec.get('title', 'Recommendation')}"):
                st.markdown(rec.get('description', ''))
                st.markdown(f"**Estimated Savings:** {rec.get('savings', 'N/A')}")
                st.markdown(f"**Effort:** {rec.get('effort', 'Medium').title()}")

    if medium_priority:
        st.markdown("#### 🟡 Medium Priority")
        for rec in medium_priority[:5]:
            st.markdown(f"- {rec.get('title', 'Recommendation')} (Savings: {rec.get('savings', 'N/A')})")


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


def _get_speed_status(load_time: float) -> str:
    """Get speed status based on load time"""
    if load_time <= 2:
        return "Fast"
    elif load_time <= 4:
        return "Moderate"
    else:
        return "Slow"


def main():
    """Main function for Performance page"""
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

    # Display Core Web Vitals
    display_core_web_vitals()

    st.markdown("---")

    # Display additional metrics
    display_additional_metrics()

    st.markdown("---")

    # Display page speed analysis
    display_page_speed_analysis()

    st.markdown("---")

    # Display resource optimization
    display_resource_optimization()

    st.markdown("---")

    # Display caching analysis
    display_caching_analysis()

    st.markdown("---")

    # Display recommendations
    display_recommendations()


if __name__ == "__main__":
    main()

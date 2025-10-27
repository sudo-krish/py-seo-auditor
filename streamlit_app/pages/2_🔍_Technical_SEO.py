"""
Technical SEO page for SEO Auditor
Displays crawlability, indexability, and technical infrastructure analysis
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
    page_title="SEO Auditor - Technical SEO",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)


def display_header():
    """Display page header"""
    st.title("🔍 Technical SEO Analysis")
    st.markdown("""
    Technical SEO ensures search engines can effectively crawl, index, and understand your website.
    This page analyzes your site's technical infrastructure and identifies optimization opportunities.
    """)
    st.markdown("---")


def display_overview_metrics():
    """Display technical SEO overview metrics"""
    if not st.session_state.get('audit_results'):
        st.info("⚠️ No audit data available. Please run an audit first.")
        return

    results = st.session_state.audit_results
    technical_data = results.get('technical', {})

    if not technical_data:
        st.warning("Technical SEO data not available in audit results.")
        return

    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)

    score = technical_data.get('score', 0)
    issues = technical_data.get('issues', [])

    with col1:
        st.metric(
            label="Technical SEO Score",
            value=f"{score}/100",
            delta=_get_score_status(score),
            help="Overall technical SEO health score"
        )

    with col2:
        critical_issues = [i for i in issues if i.get('severity') == 'critical']
        st.metric(
            label="Critical Issues",
            value=len(critical_issues),
            delta=f"-{len(critical_issues)}" if critical_issues else "None",
            delta_color="inverse"
        )

    with col3:
        crawlable_pages = technical_data.get('crawlable_pages', 0)
        total_pages = results.get('pages_analyzed', 0)
        crawlability_rate = (crawlable_pages / total_pages * 100) if total_pages > 0 else 0
        st.metric(
            label="Crawlability Rate",
            value=f"{crawlability_rate:.1f}%",
            help="Percentage of pages that are crawlable"
        )

    with col4:
        indexable_pages = technical_data.get('indexable_pages', 0)
        indexability_rate = (indexable_pages / total_pages * 100) if total_pages > 0 else 0
        st.metric(
            label="Indexability Rate",
            value=f"{indexability_rate:.1f}%",
            help="Percentage of pages that are indexable"
        )


def display_crawlability_section():
    """Display crawlability analysis"""
    st.markdown("### 🕷️ Crawlability Analysis")

    if not st.session_state.get('audit_results'):
        return

    technical_data = st.session_state.audit_results.get('technical', {})
    crawl_data = technical_data.get('crawlability', {})

    col1, col2 = st.columns([2, 1])

    with col1:
        # Robots.txt analysis
        st.markdown("#### Robots.txt Status")
        robots_data = crawl_data.get('robots_txt', {})

        if robots_data.get('exists'):
            st.success("✅ Robots.txt file found")

            with st.expander("View Robots.txt Details"):
                st.code(robots_data.get('content', 'No content available')[:1000], language="text")

                # Check for issues
                robots_issues = robots_data.get('issues', [])
                if robots_issues:
                    st.warning(f"Found {len(robots_issues)} potential issues:")
                    for issue in robots_issues:
                        st.markdown(f"- {issue}")

                # Blocked resources
                blocked_resources = robots_data.get('blocked_resources', [])
                if blocked_resources:
                    st.info(f"**Blocked resources:** {len(blocked_resources)}")
                    for resource in blocked_resources[:5]:
                        st.text(f"• {resource}")
        else:
            st.warning("⚠️ No robots.txt file found")
            st.markdown("""
            **Recommendation:** Create a robots.txt file to guide search engines on how to crawl your site.
            """)

        st.markdown("---")

        # XML Sitemap analysis
        st.markdown("#### XML Sitemap Status")
        sitemap_data = crawl_data.get('sitemap', {})

        if sitemap_data.get('exists'):
            st.success("✅ XML sitemap found")

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("URLs in Sitemap", sitemap_data.get('url_count', 0))
            with col_b:
                st.metric("Valid URLs", sitemap_data.get('valid_urls', 0))
            with col_c:
                st.metric("Invalid URLs", sitemap_data.get('invalid_urls', 0))

            with st.expander("Sitemap Issues"):
                sitemap_issues = sitemap_data.get('issues', [])
                if sitemap_issues:
                    for issue in sitemap_issues:
                        st.markdown(f"⚠️ {issue}")
                else:
                    st.success("No sitemap issues found")
        else:
            st.error("❌ No XML sitemap found")
            st.markdown("""
            **Recommendation:** Create and submit an XML sitemap to help search engines discover all your pages.
            """)

    with col2:
        # Crawl statistics
        st.markdown("#### Crawl Statistics")

        crawl_stats = crawl_data.get('statistics', {})

        stats_data = {
            "Total Pages": crawl_stats.get('total_pages', 0),
            "Crawled Successfully": crawl_stats.get('crawled_pages', 0),
            "Blocked by Robots": crawl_stats.get('blocked_pages', 0),
            "Crawl Errors": crawl_stats.get('error_pages', 0)
        }

        for label, value in stats_data.items():
            st.metric(label, value)


def display_indexability_section():
    """Display indexability analysis"""
    st.markdown("### 📇 Indexability Analysis")

    if not st.session_state.get('audit_results'):
        return

    technical_data = st.session_state.audit_results.get('technical', {})
    indexability_data = technical_data.get('indexability', {})

    # Meta robots analysis
    st.markdown("#### Meta Robots & Directives")

    col1, col2, col3 = st.columns(3)

    with col1:
        noindex_count = indexability_data.get('noindex_pages', 0)
        if noindex_count > 0:
            st.warning(f"⚠️ {noindex_count} pages with noindex")
        else:
            st.success("✅ No noindex issues")

    with col2:
        nofollow_count = indexability_data.get('nofollow_pages', 0)
        if nofollow_count > 0:
            st.info(f"ℹ️ {nofollow_count} pages with nofollow")
        else:
            st.success("✅ No nofollow directives")

    with col3:
        canonical_issues = indexability_data.get('canonical_issues', 0)
        if canonical_issues > 0:
            st.error(f"❌ {canonical_issues} canonical issues")
        else:
            st.success("✅ Canonical tags OK")

    # Pages with indexability issues
    problematic_pages = indexability_data.get('problematic_pages', [])
    if problematic_pages:
        st.markdown("#### Pages with Indexability Issues")

        df_data = []
        for page in problematic_pages[:20]:
            df_data.append({
                'URL': page.get('url', '')[:50] + '...',
                'Issue': page.get('issue', ''),
                'Severity': page.get('severity', '').title(),
                'Recommendation': page.get('recommendation', '')[:100]
            })

        if df_data:
            df = pd.DataFrame(df_data)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Severity": st.column_config.TextColumn(
                        "Severity",
                        help="Issue severity level"
                    )
                }
            )


def display_url_structure_section():
    """Display URL structure analysis"""
    st.markdown("### 🔗 URL Structure & Architecture")

    if not st.session_state.get('audit_results'):
        return

    technical_data = st.session_state.audit_results.get('technical', {})
    url_data = technical_data.get('url_structure', {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### URL Health Check")

        url_issues = url_data.get('issues', {})

        issue_types = {
            "Long URLs (>100 chars)": url_issues.get('long_urls', 0),
            "URLs with Parameters": url_issues.get('parameter_urls', 0),
            "Non-ASCII Characters": url_issues.get('non_ascii_urls', 0),
            "Uppercase Characters": url_issues.get('uppercase_urls', 0),
            "Underscores in URLs": url_issues.get('underscore_urls', 0)
        }

        for issue_type, count in issue_types.items():
            if count > 0:
                st.warning(f"⚠️ {issue_type}: {count}")
            else:
                st.success(f"✅ {issue_type}: None")

    with col2:
        st.markdown("#### Site Depth Analysis")

        depth_data = url_data.get('depth_analysis', {})

        if depth_data:
            depth_df = pd.DataFrame([
                {"Depth Level": f"Level {i}", "Page Count": count}
                for i, count in enumerate(depth_data.get('by_level', []), 1)
            ])

            st.bar_chart(depth_df.set_index("Depth Level"))

            avg_depth = depth_data.get('average_depth', 0)
            max_depth = depth_data.get('max_depth', 0)

            st.metric("Average Depth", f"{avg_depth:.1f} clicks")
            st.metric("Maximum Depth", f"{max_depth} clicks")

            if max_depth > 3:
                st.warning("⚠️ Some pages are too deep in site structure (>3 clicks from homepage)")


def display_http_status_section():
    """Display HTTP status code analysis"""
    st.markdown("### 📊 HTTP Status Codes")

    if not st.session_state.get('audit_results'):
        return

    technical_data = st.session_state.audit_results.get('technical', {})
    status_data = technical_data.get('http_status', {})

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Success (2xx)")
        success_count = status_data.get('2xx', 0)
        st.metric("Status 200 (OK)", success_count)

    with col2:
        st.markdown("#### Redirects (3xx)")
        redirect_301 = status_data.get('301', 0)
        redirect_302 = status_data.get('302', 0)
        st.metric("301 Redirects", redirect_301)
        st.metric("302 Redirects", redirect_302)

        if redirect_302 > 0:
            st.warning("⚠️ Consider using 301 for permanent redirects")

    with col3:
        st.markdown("#### Errors (4xx/5xx)")
        error_404 = status_data.get('404', 0)
        error_500 = status_data.get('500', 0)
        st.metric("404 Not Found", error_404)
        st.metric("500 Server Error", error_500)

        if error_404 > 0 or error_500 > 0:
            st.error("❌ Fix error pages immediately")

    # Error pages list
    error_pages = status_data.get('error_pages', [])
    if error_pages:
        with st.expander(f"View {len(error_pages)} Error Pages"):
            error_df = pd.DataFrame([
                {
                    'URL': page.get('url', '')[:60],
                    'Status Code': page.get('status_code', ''),
                    'Referring Page': page.get('referrer', 'Direct')[:40]
                }
                for page in error_pages[:50]
            ])
            st.dataframe(error_df, use_container_width=True, hide_index=True)


def display_canonical_redirect_section():
    """Display canonical tags and redirects analysis"""
    st.markdown("### 🔄 Canonical Tags & Redirects")

    if not st.session_state.get('audit_results'):
        return

    technical_data = st.session_state.audit_results.get('technical', {})
    canonical_data = technical_data.get('canonical', {})

    tab1, tab2 = st.tabs(["Canonical Tags", "Redirect Chains"])

    with tab1:
        st.markdown("#### Canonical Tag Analysis")

        col1, col2, col3 = st.columns(3)

        with col1:
            missing_canonical = canonical_data.get('missing_canonical', 0)
            if missing_canonical > 0:
                st.warning(f"⚠️ {missing_canonical} pages without canonical")
            else:
                st.success("✅ All pages have canonical tags")

        with col2:
            self_canonical = canonical_data.get('self_referencing', 0)
            st.info(f"ℹ️ {self_canonical} self-referencing canonicals")

        with col3:
            cross_domain = canonical_data.get('cross_domain', 0)
            if cross_domain > 0:
                st.warning(f"⚠️ {cross_domain} cross-domain canonicals")

        # Canonical issues list
        canonical_issues = canonical_data.get('issues', [])
        if canonical_issues:
            st.markdown("**Pages with Canonical Issues:**")
            for issue in canonical_issues[:10]:
                st.markdown(f"- {issue.get('url', '')}: *{issue.get('issue', '')}*")

    with tab2:
        st.markdown("#### Redirect Chain Analysis")

        redirect_data = technical_data.get('redirects', {})

        redirect_chains = redirect_data.get('chains', [])
        if redirect_chains:
            st.warning(f"⚠️ Found {len(redirect_chains)} redirect chains")

            for i, chain in enumerate(redirect_chains[:5], 1):
                with st.expander(f"Chain {i}: {len(chain.get('hops', []))} hops"):
                    for j, hop in enumerate(chain.get('hops', []), 1):
                        st.text(f"{j}. {hop.get('url', '')} → {hop.get('status', '')}")
        else:
            st.success("✅ No redirect chains detected")


def display_duplicate_content_section():
    """Display duplicate content analysis"""
    st.markdown("### 📋 Duplicate Content Analysis")

    if not st.session_state.get('audit_results'):
        return

    technical_data = st.session_state.audit_results.get('technical', {})
    duplicate_data = technical_data.get('duplicate_content', {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Duplicate Titles")
        duplicate_titles = duplicate_data.get('duplicate_titles', {})
        if duplicate_titles:
            st.warning(f"⚠️ {len(duplicate_titles)} duplicate title groups")

            with st.expander("View Duplicates"):
                for title, urls in list(duplicate_titles.items())[:5]:
                    st.markdown(f"**{title[:50]}...** ({len(urls)} pages)")
                    for url in urls[:3]:
                        st.text(f"  • {url[:60]}")
        else:
            st.success("✅ No duplicate titles found")

    with col2:
        st.markdown("#### Duplicate Meta Descriptions")
        duplicate_descriptions = duplicate_data.get('duplicate_descriptions', {})
        if duplicate_descriptions:
            st.warning(f"⚠️ {len(duplicate_descriptions)} duplicate description groups")

            with st.expander("View Duplicates"):
                for desc, urls in list(duplicate_descriptions.items())[:5]:
                    st.markdown(f"**{desc[:50]}...** ({len(urls)} pages)")
                    for url in urls[:3]:
                        st.text(f"  • {url[:60]}")
        else:
            st.success("✅ No duplicate meta descriptions")


def display_structured_data_section():
    """Display structured data analysis"""
    st.markdown("### 📝 Structured Data (Schema.org)")

    if not st.session_state.get('audit_results'):
        return

    technical_data = st.session_state.audit_results.get('technical', {})
    schema_data = technical_data.get('structured_data', {})

    pages_with_schema = schema_data.get('pages_with_schema', 0)
    total_pages = st.session_state.audit_results.get('pages_analyzed', 0)
    schema_coverage = (pages_with_schema / total_pages * 100) if total_pages > 0 else 0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Pages with Schema", pages_with_schema)
        st.metric("Coverage", f"{schema_coverage:.1f}%")

    with col2:
        schema_types = schema_data.get('schema_types', {})
        st.markdown("**Schema Types Found:**")
        for schema_type, count in list(schema_types.items())[:5]:
            st.text(f"• {schema_type}: {count}")

    with col3:
        schema_errors = schema_data.get('validation_errors', 0)
        if schema_errors > 0:
            st.error(f"❌ {schema_errors} validation errors")
        else:
            st.success("✅ No validation errors")


def display_recommendations():
    """Display prioritized recommendations"""
    st.markdown("### 💡 Recommendations")

    if not st.session_state.get('audit_results'):
        return

    technical_data = st.session_state.audit_results.get('technical', {})
    recommendations = technical_data.get('recommendations', [])

    if not recommendations:
        st.success("🎉 No major technical SEO issues found!")
        return

    # Group by priority
    high_priority = [r for r in recommendations if r.get('priority') == 'high']
    medium_priority = [r for r in recommendations if r.get('priority') == 'medium']
    low_priority = [r for r in recommendations if r.get('priority') == 'low']

    if high_priority:
        st.markdown("#### 🔴 High Priority")
        for rec in high_priority[:5]:
            with st.expander(f"✓ {rec.get('title', 'Recommendation')}"):
                st.markdown(rec.get('description', ''))
                st.markdown(f"**Impact:** {rec.get('impact', 'Medium').title()}")
                st.markdown(f"**Effort:** {rec.get('effort', 'Medium').title()}")

    if medium_priority:
        st.markdown("#### 🟡 Medium Priority")
        for rec in medium_priority[:5]:
            st.markdown(f"- {rec.get('title', 'Recommendation')}")

    if low_priority:
        with st.expander(f"🟢 Low Priority ({len(low_priority)} items)"):
            for rec in low_priority:
                st.markdown(f"- {rec.get('title', 'Recommendation')}")


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
    """Main function for Technical SEO page"""
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

    # Display crawlability section
    display_crawlability_section()

    st.markdown("---")

    # Display indexability section
    display_indexability_section()

    st.markdown("---")

    # Display URL structure section
    display_url_structure_section()

    st.markdown("---")

    # Display HTTP status section
    display_http_status_section()

    st.markdown("---")

    # Display canonical and redirects
    display_canonical_redirect_section()

    st.markdown("---")

    # Display duplicate content
    display_duplicate_content_section()

    st.markdown("---")

    # Display structured data
    display_structured_data_section()

    st.markdown("---")

    # Display recommendations
    display_recommendations()


if __name__ == "__main__":
    main()

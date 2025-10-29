"""
On-Page SEO page for SEO Auditor
Displays content optimization, meta tags, and on-page element analysis
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
    page_title="SEO Auditor - On-Page SEO",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)


def display_header():
    """Display page header"""
    st.title("📄 On-Page SEO Analysis")
    st.markdown("""
    On-page SEO focuses on optimizing individual pages to rank higher and earn more relevant traffic. 
    This includes content quality, meta tags, headers, keywords, and internal linking.
    """)
    st.markdown("---")


def display_overview_metrics():
    """Display on-page SEO overview metrics"""
    if not st.session_state.get('audit_results'):
        st.info("⚠️ No audit data available. Please run an audit first.")
        return

    results = st.session_state.audit_results
    onpage_data = results.get('onpage', {})

    if not onpage_data:
        st.warning("On-page SEO data not available in audit results.")
        return

    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)

    score = onpage_data.get('score', 0)
    issues = onpage_data.get('issues', [])

    with col1:
        st.metric(
            label="On-Page SEO Score",
            value=f"{score}/100",
            delta=_get_score_status(score),
            help="Overall on-page optimization score"
        )

    with col2:
        pages_optimized = onpage_data.get('optimized_pages', 0)
        total_pages = results.get('pages_analyzed', 0)
        optimization_rate = (pages_optimized / total_pages * 100) if total_pages > 0 else 0
        st.metric(
            label="Optimization Rate",
            value=f"{optimization_rate:.1f}%",
            help="Percentage of well-optimized pages"
        )

    with col3:
        content_issues = [i for i in issues if i.get('category') == 'content']
        st.metric(
            label="Content Issues",
            value=len(content_issues),
            help="Issues related to content quality"
        )

    with col4:
        thin_content_pages = onpage_data.get('thin_content_pages', 0)
        st.metric(
            label="Thin Content Pages",
            value=thin_content_pages,
            delta=f"-{thin_content_pages}" if thin_content_pages > 0 else "None",
            delta_color="inverse",
            help="Pages with insufficient content"
        )


def display_title_tags_section():
    """Display title tag analysis"""
    st.markdown("### 📝 Title Tags Analysis")

    if not st.session_state.get('audit_results'):
        return

    onpage_data = st.session_state.audit_results.get('onpage', {})
    title_data = onpage_data.get('title_tags', {})

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Title Tag Health Check")

        title_stats = title_data.get('statistics', {})

        # Display title tag issues
        issue_types = {
            "Missing Titles": title_stats.get('missing', 0),
            "Too Short (<30 chars)": title_stats.get('too_short', 0),
            "Too Long (>60 chars)": title_stats.get('too_long', 0),
            "Duplicate Titles": title_stats.get('duplicates', 0),
            "Missing Keywords": title_stats.get('no_keywords', 0)
        }

        for issue_type, count in issue_types.items():
            if count > 0:
                st.warning(f"⚠️ {issue_type}: {count} pages")
            else:
                st.success(f"✅ {issue_type}: None")

        # Pages with title issues
        problem_titles = title_data.get('problem_pages', [])
        if problem_titles:
            with st.expander(f"View {len(problem_titles)} Pages with Title Issues"):
                title_df = pd.DataFrame([
                    {
                        'Page': page.get('url', '')[:50] + '...',
                        'Current Title': page.get('title', 'Missing')[:50],
                        'Length': len(page.get('title', '')),
                        'Issue': page.get('issue', ''),
                        'Priority': page.get('priority', 'Medium').title()
                    }
                    for page in problem_titles[:20]
                ])
                st.dataframe(title_df, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("#### Best Practices")
        st.info("""
        **Optimal Title Length:** 50-60 characters

        **Best Practices (2025):**
        - Include primary keyword near the start
        - Make it unique and descriptive
        - Match user search intent
        - Add brand name at the end
        - Avoid keyword stuffing
        - Use power words for CTR
        """)

        avg_length = title_stats.get('average_length', 0)
        st.metric("Average Title Length", f"{avg_length} chars")

        if avg_length < 30:
            st.warning("Titles are too short")
        elif avg_length > 60:
            st.warning("Titles are too long")
        else:
            st.success("Average length is good")


def display_meta_descriptions_section():
    """Display meta description analysis"""
    st.markdown("### 📋 Meta Descriptions Analysis")

    if not st.session_state.get('audit_results'):
        return

    onpage_data = st.session_state.audit_results.get('onpage', {})
    meta_data = onpage_data.get('meta_descriptions', {})

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Meta Description Health Check")

        meta_stats = meta_data.get('statistics', {})

        issue_types = {
            "Missing Descriptions": meta_stats.get('missing', 0),
            "Too Short (<120 chars)": meta_stats.get('too_short', 0),
            "Too Long (>160 chars)": meta_stats.get('too_long', 0),
            "Duplicate Descriptions": meta_stats.get('duplicates', 0),
            "Not Compelling": meta_stats.get('not_compelling', 0)
        }

        for issue_type, count in issue_types.items():
            if count > 0:
                st.warning(f"⚠️ {issue_type}: {count} pages")
            else:
                st.success(f"✅ {issue_type}: None")

        # Pages with meta description issues
        problem_metas = meta_data.get('problem_pages', [])
        if problem_metas:
            with st.expander(f"View {len(problem_metas)} Pages with Meta Description Issues"):
                for page in problem_metas[:10]:
                    st.markdown(f"""
                    **{page.get('url', '')[:60]}**  
                    Current: *{page.get('description', 'Missing')[:100]}...*  
                    Issue: {page.get('issue', '')} | Length: {len(page.get('description', ''))} chars
                    """)
                    st.markdown("---")

    with col2:
        st.markdown("#### Best Practices")
        st.info("""
        **Optimal Length:** 150-160 characters

        **Best Practices (2025):**
        - Include target keyword naturally
        - Write compelling copy
        - Add call-to-action
        - Match page content
        - Be unique per page
        - Focus on benefits
        """)

        avg_length = meta_stats.get('average_length', 0)
        st.metric("Average Description Length", f"{avg_length} chars")


def display_header_tags_section():
    """Display header tags (H1-H6) analysis"""
    st.markdown("### 🔤 Header Tags Structure")

    if not st.session_state.get('audit_results'):
        return

    onpage_data = st.session_state.audit_results.get('onpage', {})
    header_data = onpage_data.get('header_tags', {})

    tab1, tab2 = st.tabs(["H1 Analysis", "Header Hierarchy"])

    with tab1:
        st.markdown("#### H1 Tag Analysis")

        col1, col2, col3 = st.columns(3)

        h1_stats = header_data.get('h1_statistics', {})

        with col1:
            missing_h1 = h1_stats.get('missing', 0)
            if missing_h1 > 0:
                st.error(f"❌ {missing_h1} pages without H1")
            else:
                st.success("✅ All pages have H1")

        with col2:
            multiple_h1 = h1_stats.get('multiple', 0)
            if multiple_h1 > 0:
                st.warning(f"⚠️ {multiple_h1} pages with multiple H1s")
            else:
                st.success("✅ Single H1 per page")

        with col3:
            duplicate_h1 = h1_stats.get('duplicates', 0)
            if duplicate_h1 > 0:
                st.warning(f"⚠️ {duplicate_h1} duplicate H1s")
            else:
                st.success("✅ Unique H1 tags")

        # H1 recommendations
        st.markdown("**H1 Best Practices:**")
        st.markdown("""
        - Use only one H1 per page
        - Include primary keyword
        - Make it descriptive and compelling
        - Keep it under 70 characters
        - Differentiate from title tag
        """)

    with tab2:
        st.markdown("#### Header Tag Hierarchy")

        hierarchy_data = header_data.get('hierarchy', {})

        # Display header usage statistics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Pages with H2", hierarchy_data.get('h2_count', 0))
            st.metric("Pages with H3", hierarchy_data.get('h3_count', 0))

        with col2:
            st.metric("Pages with H4", hierarchy_data.get('h4_count', 0))
            st.metric("Pages with H5", hierarchy_data.get('h5_count', 0))

        with col3:
            broken_hierarchy = hierarchy_data.get('broken_hierarchy', 0)
            if broken_hierarchy > 0:
                st.warning(f"⚠️ {broken_hierarchy} pages with broken hierarchy")
            else:
                st.success("✅ Proper header structure")

        # Pages with hierarchy issues
        hierarchy_issues = hierarchy_data.get('issues', [])
        if hierarchy_issues:
            with st.expander("View Hierarchy Issues"):
                for issue in hierarchy_issues[:10]:
                    st.markdown(f"- **{issue.get('url', '')[:60]}**: {issue.get('issue', '')}")


def display_content_analysis_section():
    """Display content quality and optimization analysis"""
    st.markdown("### 📖 Content Quality & Optimization")

    if not st.session_state.get('audit_results'):
        return

    onpage_data = st.session_state.audit_results.get('onpage', {})
    content_data = onpage_data.get('content', {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Content Length Analysis")

        length_stats = content_data.get('length_statistics', {})

        avg_word_count = length_stats.get('average_word_count', 0)
        st.metric("Average Word Count", f"{avg_word_count:,}")

        # Content length distribution
        thin_content = length_stats.get('thin_content', 0)  # <300 words
        short_content = length_stats.get('short_content', 0)  # 300-600 words
        medium_content = length_stats.get('medium_content', 0)  # 600-1200 words
        long_content = length_stats.get('long_content', 0)  # >1200 words

        st.markdown("**Content Length Distribution:**")
        st.markdown(f"- Thin (<300 words): {thin_content} pages")
        st.markdown(f"- Short (300-600 words): {short_content} pages")
        st.markdown(f"- Medium (600-1200 words): {medium_content} pages")
        st.markdown(f"- Long (>1200 words): {long_content} pages")

        if thin_content > 0:
            st.warning(f"⚠️ {thin_content} pages need more content")

    with col2:
        st.markdown("#### Content Quality Indicators")

        quality_data = content_data.get('quality', {})

        readability_score = quality_data.get('avg_readability', 0)
        st.metric("Avg. Readability Score", f"{readability_score}/100")

        if readability_score < 60:
            st.warning("Content may be difficult to read")
        elif readability_score >= 80:
            st.success("Content is highly readable")

        # Quality issues
        st.markdown("**Quality Issues:**")

        quality_issues = {
            "Low Readability": quality_data.get('low_readability', 0),
            "Keyword Stuffing": quality_data.get('keyword_stuffing', 0),
            "Duplicate Content": quality_data.get('duplicate_content', 0),
            "Broken Grammar": quality_data.get('grammar_issues', 0)
        }

        for issue, count in quality_issues.items():
            if count > 0:
                st.warning(f"⚠️ {issue}: {count} pages")


def display_keyword_optimization_section():
    """Display keyword optimization analysis"""
    st.markdown("### 🎯 Keyword Optimization")

    if not st.session_state.get('audit_results'):
        return

    onpage_data = st.session_state.audit_results.get('onpage', {})
    keyword_data = onpage_data.get('keywords', {})

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Keyword Usage Analysis")

        # Target keywords presence
        target_keywords = keyword_data.get('target_keywords', {})

        if target_keywords:
            st.markdown("**Pages Missing Target Keywords:**")

            missing_in_title = target_keywords.get('missing_in_title', 0)
            missing_in_h1 = target_keywords.get('missing_in_h1', 0)
            missing_in_content = target_keywords.get('missing_in_content', 0)
            missing_in_url = target_keywords.get('missing_in_url', 0)

            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Not in Title", missing_in_title)
                st.metric("Not in H1", missing_in_h1)
            with col_b:
                st.metric("Not in Content", missing_in_content)
                st.metric("Not in URL", missing_in_url)

        # Keyword density
        st.markdown("#### Keyword Density")

        density_issues = keyword_data.get('density_issues', [])
        if density_issues:
            for issue in density_issues[:10]:
                keyword = issue.get('keyword', '')
                density = issue.get('density', 0)
                url = issue.get('url', '')[:60]

                if density > 3:
                    st.warning(f"⚠️ **{keyword}** ({density:.1f}%) on {url} - Too high (keyword stuffing)")
                elif density < 0.5:
                    st.info(f"ℹ️ **{keyword}** ({density:.1f}%) on {url} - Too low")

    with col2:
        st.markdown("#### Keyword Best Practices")
        st.info("""
        **Optimal Keyword Density:** 1-2%

        **Keyword Placement:**
        - Title tag (near start)
        - H1 heading
        - First 100 words
        - H2/H3 subheadings
        - URL slug
        - Meta description
        - Image alt texts
        - Throughout content naturally

        **2025 Best Practices:**
        - Focus on semantic keywords
        - Use natural language
        - Include LSI keywords
        - Match search intent
        - Avoid keyword stuffing
        """)


def display_internal_linking_section():
    """Display internal linking analysis"""
    st.markdown("### 🔗 Internal Linking Structure")

    if not st.session_state.get('audit_results'):
        return

    onpage_data = st.session_state.audit_results.get('onpage', {})
    linking_data = onpage_data.get('internal_links', {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Internal Link Statistics")

        link_stats = linking_data.get('statistics', {})

        total_internal_links = link_stats.get('total', 0)
        avg_internal_links = link_stats.get('average_per_page', 0)

        st.metric("Total Internal Links", f"{total_internal_links:,}")
        st.metric("Average per Page", f"{avg_internal_links:.1f}")

        # Link issues
        orphaned_pages = link_stats.get('orphaned_pages', 0)
        pages_no_outbound = link_stats.get('no_outbound_links', 0)
        broken_internal_links = link_stats.get('broken_links', 0)

        if orphaned_pages > 0:
            st.error(f"❌ {orphaned_pages} orphaned pages (no inbound links)")

        if pages_no_outbound > 0:
            st.warning(f"⚠️ {pages_no_outbound} pages with no outbound links")

        if broken_internal_links > 0:
            st.error(f"❌ {broken_internal_links} broken internal links")

    with col2:
        st.markdown("#### Anchor Text Analysis")

        anchor_data = linking_data.get('anchor_text', {})

        generic_anchors = anchor_data.get('generic', 0)
        exact_match = anchor_data.get('exact_match', 0)
        branded = anchor_data.get('branded', 0)

        st.markdown("**Anchor Text Distribution:**")
        st.markdown(f"- Generic ('click here', 'read more'): {generic_anchors}")
        st.markdown(f"- Exact Match Keywords: {exact_match}")
        st.markdown(f"- Branded: {branded}")

        if generic_anchors > exact_match + branded:
            st.warning("⚠️ Too many generic anchor texts. Use descriptive anchors.")


def display_image_optimization_section():
    """Display image optimization analysis"""
    st.markdown("### 🖼️ Image Optimization")

    if not st.session_state.get('audit_results'):
        return

    onpage_data = st.session_state.audit_results.get('onpage', {})
    image_data = onpage_data.get('images', {})

    col1, col2, col3 = st.columns(3)

    with col1:
        total_images = image_data.get('total', 0)
        st.metric("Total Images", f"{total_images:,}")

        missing_alt = image_data.get('missing_alt', 0)
        if missing_alt > 0:
            st.error(f"❌ {missing_alt} images without alt text")
        else:
            st.success("✅ All images have alt text")

    with col2:
        large_images = image_data.get('large_size', 0)
        if large_images > 0:
            st.warning(f"⚠️ {large_images} images >200KB")
        else:
            st.success("✅ Image sizes optimized")

        wrong_format = image_data.get('wrong_format', 0)
        if wrong_format > 0:
            st.info(f"ℹ️ {wrong_format} images should use WebP")

    with col3:
        avg_size = image_data.get('average_size', 0)
        st.metric("Average Image Size", f"{avg_size}KB")

        if avg_size > 100:
            st.warning("Consider compressing images")

    # Image issues list
    image_issues = image_data.get('problem_images', [])
    if image_issues:
        with st.expander(f"View {len(image_issues)} Images with Issues"):
            image_df = pd.DataFrame([
                {
                    'Image': img.get('src', '')[:50],
                    'Page': img.get('page_url', '')[:40],
                    'Issue': img.get('issue', ''),
                    'Size': f"{img.get('size', 0)}KB"
                }
                for img in image_issues[:20]
            ])
            st.dataframe(image_df, use_container_width=True, hide_index=True)


def display_url_optimization_section():
    """Display URL optimization analysis"""
    st.markdown("### 🌐 URL Optimization")

    if not st.session_state.get('audit_results'):
        return

    onpage_data = st.session_state.audit_results.get('onpage', {})
    url_data = onpage_data.get('urls', {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### URL Structure Analysis")

        url_issues = url_data.get('issues', {})

        issue_types = {
            "URLs too long (>75 chars)": url_issues.get('too_long', 0),
            "Non-descriptive URLs": url_issues.get('non_descriptive', 0),
            "Missing keywords in URL": url_issues.get('no_keywords', 0),
            "Special characters in URL": url_issues.get('special_chars', 0),
            "Stop words in URL": url_issues.get('stop_words', 0)
        }

        for issue, count in issue_types.items():
            if count > 0:
                st.warning(f"⚠️ {issue}: {count} pages")
            else:
                st.success(f"✅ {issue}: None")

    with col2:
        st.markdown("#### URL Best Practices")
        st.info("""
        **2025 URL Guidelines:**
        - Keep URLs short (<75 chars)
        - Use hyphens, not underscores
        - Include target keyword
        - Use lowercase letters
        - Avoid special characters
        - Remove stop words
        - Make URLs readable
        - Use logical hierarchy

        **Example:**
        ✅ /seo/on-page-optimization
        ❌ /page?id=123&cat=seo
        """)


def display_recommendations():
    """Display prioritized on-page SEO recommendations"""
    st.markdown("### 💡 On-Page SEO Recommendations")

    if not st.session_state.get('audit_results'):
        return

    onpage_data = st.session_state.audit_results.get('onpage', {})
    recommendations = onpage_data.get('recommendations', [])

    if not recommendations:
        st.success("🎉 Your on-page SEO is well-optimized!")
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
                st.markdown(f"**Affected Pages:** {rec.get('affected_pages', 0)}")
                st.markdown(f"**Impact:** {rec.get('impact', 'Medium').title()}")
                st.markdown(f"**Effort:** {rec.get('effort', 'Medium').title()}")

                # Show example pages
                examples = rec.get('example_pages', [])
                if examples:
                    st.markdown("**Example Pages:**")
                    for example in examples[:3]:
                        st.text(f"• {example}")

    if medium_priority:
        st.markdown("#### 🟡 Medium Priority")
        for rec in medium_priority[:5]:
            st.markdown(f"- {rec.get('title', 'Recommendation')} ({rec.get('affected_pages', 0)} pages)")

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
    """Main function for On-Page SEO page"""
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

    # Display title tags section
    display_title_tags_section()

    st.markdown("---")

    # Display meta descriptions section
    display_meta_descriptions_section()

    st.markdown("---")

    # Display header tags section
    display_header_tags_section()

    st.markdown("---")

    # Display content analysis
    display_content_analysis_section()

    st.markdown("---")

    # Display keyword optimization
    display_keyword_optimization_section()

    st.markdown("---")

    # Display internal linking
    display_internal_linking_section()

    st.markdown("---")

    # Display image optimization
    display_image_optimization_section()

    st.markdown("---")

    # Display URL optimization
    display_url_optimization_section()

    st.markdown("---")

    # Display recommendations
    display_recommendations()


if __name__ == "__main__":
    main()

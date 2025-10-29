"""
Accessibility page for SEO Auditor
Displays WCAG 2.2 compliance, accessibility issues, and inclusive design analysis
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
    page_title="SEO Auditor - Accessibility",
    page_icon="♿",
    layout="wide",
    initial_sidebar_state="expanded"
)


def display_header():
    """Display page header"""
    st.title("♿ Web Accessibility Analysis")
    st.markdown("""
    Web accessibility ensures your site is usable by everyone, including people with disabilities. 
    WCAG 2.2 (now ISO/IEC 40500:2025) is the global standard for digital accessibility and positively impacts SEO.
    """)
    st.markdown("---")


def display_overview_metrics():
    """Display accessibility overview metrics"""
    if not st.session_state.get('audit_results'):
        st.info("⚠️ No audit data available. Please run an audit first.")
        return

    results = st.session_state.audit_results
    accessibility_data = results.get('accessibility', {})

    if not accessibility_data:
        st.warning("Accessibility data not available in audit results.")
        return

    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)

    score = accessibility_data.get('score', 0)

    with col1:
        st.metric(
            label="Accessibility Score",
            value=f"{score}/100",
            delta=_get_score_status(score),
            help="Overall WCAG 2.2 compliance score"
        )

    with col2:
        wcag_level = accessibility_data.get('wcag_level', 'None')
        st.metric(
            label="WCAG 2.2 Level",
            value=wcag_level,
            help="Highest conformance level achieved (A, AA, or AAA)"
        )

    with col3:
        total_issues = accessibility_data.get('total_issues', 0)
        st.metric(
            label="Accessibility Issues",
            value=total_issues,
            delta=f"-{total_issues}" if total_issues > 0 else "None",
            delta_color="inverse",
            help="Total accessibility violations detected"
        )

    with col4:
        compliant_pages = accessibility_data.get('compliant_pages', 0)
        total_pages = results.get('pages_analyzed', 0)
        compliance_rate = (compliant_pages / total_pages * 100) if total_pages > 0 else 0
        st.metric(
            label="Compliance Rate",
            value=f"{compliance_rate:.0f}%",
            help="Percentage of pages meeting WCAG AA"
        )


def display_wcag_principles():
    """Display WCAG 2.2 principles overview"""
    st.markdown("### 📋 WCAG 2.2 Principles (POUR)")

    if not st.session_state.get('audit_results'):
        return

    accessibility_data = st.session_state.audit_results.get('accessibility', {})
    principles_data = accessibility_data.get('wcag_principles', {})

    st.info("""
    **WCAG 2.2** (ISO/IEC 40500:2025) is built on four principles, known as **POUR**:
    Content must be **Perceivable, Operable, Understandable, and Robust**.
    """)

    tab1, tab2, tab3, tab4 = st.tabs(["📡 Perceivable", "⚙️ Operable", "🧠 Understandable", "🛠️ Robust"])

    with tab1:
        display_perceivable_principle(principles_data.get('perceivable', {}))

    with tab2:
        display_operable_principle(principles_data.get('operable', {}))

    with tab3:
        display_understandable_principle(principles_data.get('understandable', {}))

    with tab4:
        display_robust_principle(principles_data.get('robust', {}))


def display_perceivable_principle(perceivable_data):
    """Display Perceivable principle analysis"""
    st.markdown("#### 📡 Perceivable")
    st.markdown("Information and user interface components must be presentable to users in ways they can perceive.")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Text alternatives
        st.markdown("**1.1 Text Alternatives**")
        alt_text_issues = perceivable_data.get('missing_alt_text', 0)

        if alt_text_issues == 0:
            st.success("✅ All images have alt text")
        else:
            st.error(f"❌ {alt_text_issues} images missing alt text")

        # Time-based media
        st.markdown("**1.2 Time-based Media**")
        media_issues = perceivable_data.get('media_issues', {})

        missing_captions = media_issues.get('missing_captions', 0)
        missing_transcripts = media_issues.get('missing_transcripts', 0)

        if missing_captions > 0:
            st.warning(f"⚠️ {missing_captions} videos without captions")
        if missing_transcripts > 0:
            st.info(f"ℹ️ {missing_transcripts} audio files without transcripts")

        # Adaptable
        st.markdown("**1.3 Adaptable**")
        adaptable_issues = perceivable_data.get('adaptable_issues', {})

        improper_headings = adaptable_issues.get('improper_headings', 0)
        missing_labels = adaptable_issues.get('missing_form_labels', 0)

        if improper_headings > 0:
            st.warning(f"⚠️ {improper_headings} pages with improper heading structure")
        if missing_labels > 0:
            st.error(f"❌ {missing_labels} form fields without labels")

        # Distinguishable
        st.markdown("**1.4 Distinguishable**")
        contrast_issues = perceivable_data.get('contrast_issues', 0)

        if contrast_issues > 0:
            st.error(f"❌ {contrast_issues} color contrast violations")
        else:
            st.success("✅ Color contrast meets WCAG requirements")

    with col2:
        st.markdown("**Perceivable Guidelines:**")
        st.markdown("""
        **1.1 Text Alternatives**
        - Provide alt text for images
        - Use empty alt for decorative images

        **1.2 Time-based Media**
        - Captions for videos
        - Transcripts for audio
        - Audio descriptions

        **1.3 Adaptable**
        - Semantic HTML structure
        - Proper heading hierarchy
        - Form labels and instructions

        **1.4 Distinguishable**
        - 4.5:1 contrast (normal text)
        - 3:1 contrast (large text)
        - Don't rely on color alone
        - Text resizable to 200%
        """)


def display_operable_principle(operable_data):
    """Display Operable principle analysis"""
    st.markdown("#### ⚙️ Operable")
    st.markdown("User interface components and navigation must be operable by all users.")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Keyboard accessible
        st.markdown("**2.1 Keyboard Accessible**")
        keyboard_issues = operable_data.get('keyboard_issues', {})

        keyboard_traps = keyboard_issues.get('keyboard_traps', 0)
        non_keyboard_accessible = keyboard_issues.get('non_accessible', 0)

        if keyboard_traps > 0:
            st.error(f"❌ {keyboard_traps} keyboard traps detected")
        if non_keyboard_accessible > 0:
            st.warning(f"⚠️ {non_keyboard_accessible} elements not keyboard accessible")

        if keyboard_traps == 0 and non_keyboard_accessible == 0:
            st.success("✅ All interactive elements keyboard accessible")

        # Enough time
        st.markdown("**2.2 Enough Time**")
        timing_issues = operable_data.get('timing_issues', {})

        auto_refresh = timing_issues.get('auto_refresh', 0)
        time_limits = timing_issues.get('time_limits_no_control', 0)

        if auto_refresh > 0:
            st.warning(f"⚠️ {auto_refresh} pages with auto-refresh")
        if time_limits > 0:
            st.warning(f"⚠️ {time_limits} timed elements without user control")

        # Seizures and physical reactions
        st.markdown("**2.3 Seizures and Physical Reactions**")
        flashing_content = operable_data.get('flashing_content', 0)

        if flashing_content > 0:
            st.error(f"❌ {flashing_content} elements with rapid flashing")
        else:
            st.success("✅ No flashing content detected")

        # Navigable
        st.markdown("**2.4 Navigable**")
        navigation_issues = operable_data.get('navigation_issues', {})

        missing_skip_links = navigation_issues.get('missing_skip_links', 0)
        poor_focus_visibility = navigation_issues.get('poor_focus_visibility', 0)

        if missing_skip_links > 0:
            st.warning(f"⚠️ {missing_skip_links} pages without skip links")
        if poor_focus_visibility > 0:
            st.error(f"❌ {poor_focus_visibility} elements with poor focus indicators")

        # Input modalities (WCAG 2.2 NEW)
        st.markdown("**2.5 Input Modalities** 🆕")
        input_issues = operable_data.get('input_modalities', {})

        touch_targets = input_issues.get('small_touch_targets', 0)
        dragging_required = input_issues.get('dragging_required', 0)

        if touch_targets > 0:
            st.warning(f"⚠️ {touch_targets} touch targets too small (< 24x24px)")
        if dragging_required > 0:
            st.info(f"ℹ️ {dragging_required} interactions require dragging (provide alternative)")

    with col2:
        st.markdown("**Operable Guidelines:**")
        st.markdown("""
        **2.1 Keyboard Accessible**
        - All functionality via keyboard
        - No keyboard traps
        - Visible focus indicators

        **2.2 Enough Time**
        - User control over timing
        - Pause/stop/hide moving content
        - Extend time limits

        **2.3 Seizures**
        - No content flashing > 3/sec

        **2.4 Navigable**
        - Skip navigation links
        - Descriptive page titles
        - Logical focus order
        - Clear link purpose
        - Multiple navigation methods

        **2.5 Input Modalities** 🆕
        - 24x24px minimum touch targets
        - Alternative to dragging
        - Accessible labels
        """)


def display_understandable_principle(understandable_data):
    """Display Understandable principle analysis"""
    st.markdown("#### 🧠 Understandable")
    st.markdown("Information and operation of the user interface must be understandable.")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Readable
        st.markdown("**3.1 Readable**")
        language_issues = understandable_data.get('language_issues', {})

        missing_lang = language_issues.get('missing_lang_attribute', 0)
        complex_language = language_issues.get('complex_language', 0)

        if missing_lang > 0:
            st.error(f"❌ {missing_lang} pages without lang attribute")
        else:
            st.success("✅ All pages have language declared")

        if complex_language > 0:
            st.info(f"ℹ️ {complex_language} pages with complex reading level")

        # Predictable
        st.markdown("**3.2 Predictable**")
        predictable_issues = understandable_data.get('predictable_issues', {})

        on_focus_changes = predictable_issues.get('on_focus_changes', 0)
        inconsistent_navigation = predictable_issues.get('inconsistent_navigation', 0)
        inconsistent_help = predictable_issues.get('inconsistent_help', 0)  # WCAG 2.2

        if on_focus_changes > 0:
            st.warning(f"⚠️ {on_focus_changes} elements change context on focus")
        if inconsistent_navigation > 0:
            st.warning(f"⚠️ Navigation inconsistent across pages")
        if inconsistent_help > 0:
            st.info(f"ℹ️ Help not in consistent location (WCAG 2.2)")

        # Input assistance
        st.markdown("**3.3 Input Assistance**")
        input_assistance = understandable_data.get('input_assistance', {})

        missing_error_messages = input_assistance.get('missing_error_messages', 0)
        missing_labels = input_assistance.get('missing_labels', 0)
        redundant_entry = input_assistance.get('redundant_entry', 0)  # WCAG 2.2
        auth_issues = input_assistance.get('auth_cognitive_load', 0)  # WCAG 2.2

        if missing_error_messages > 0:
            st.error(f"❌ {missing_error_messages} forms without error messages")
        if missing_labels > 0:
            st.error(f"❌ {missing_labels} form fields without labels")
        if redundant_entry > 0:
            st.info(f"ℹ️ {redundant_entry} forms ask for same info twice (WCAG 2.2)")
        if auth_issues > 0:
            st.warning(f"⚠️ Authentication requires cognitive function tests (WCAG 2.2)")

    with col2:
        st.markdown("**Understandable Guidelines:**")
        st.markdown("""
        **3.1 Readable**
        - Identify page language
        - Identify language changes
        - Define unusual words
        - Use clear language

        **3.2 Predictable**
        - No context change on focus
        - Consistent navigation
        - Consistent identification
        - **Consistent help** 🆕

        **3.3 Input Assistance**
        - Error identification
        - Clear labels/instructions
        - Error suggestions
        - Error prevention
        - **No redundant entry** 🆕
        - **Accessible authentication** 🆕
        """)


def display_robust_principle(robust_data):
    """Display Robust principle analysis"""
    st.markdown("#### 🛠️ Robust")
    st.markdown("Content must be robust enough to be interpreted reliably by assistive technologies.")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Compatible
        st.markdown("**4.1 Compatible**")

        # Parsing/markup issues
        parsing_issues = robust_data.get('parsing_issues', {})

        html_errors = parsing_issues.get('html_errors', 0)
        duplicate_ids = parsing_issues.get('duplicate_ids', 0)

        if html_errors > 0:
            st.warning(f"⚠️ {html_errors} HTML validation errors")
        else:
            st.success("✅ Valid HTML markup")

        if duplicate_ids > 0:
            st.error(f"❌ {duplicate_ids} duplicate ID attributes")

        # Name, role, value
        st.markdown("**4.1.2 Name, Role, Value**")
        aria_issues = robust_data.get('aria_issues', {})

        missing_aria_labels = aria_issues.get('missing_aria_labels', 0)
        invalid_aria = aria_issues.get('invalid_aria', 0)
        missing_roles = aria_issues.get('missing_roles', 0)

        if missing_aria_labels > 0:
            st.warning(f"⚠️ {missing_aria_labels} custom elements without labels")
        if invalid_aria > 0:
            st.error(f"❌ {invalid_aria} invalid ARIA attributes")
        if missing_roles > 0:
            st.warning(f"⚠️ {missing_roles} custom widgets without ARIA roles")

        # Status messages (WCAG 2.1)
        st.markdown("**4.1.3 Status Messages**")
        status_messages = robust_data.get('status_messages', 0)

        if status_messages > 0:
            st.info(f"ℹ️ {status_messages} dynamic updates without aria-live")

    with col2:
        st.markdown("**Robust Guidelines:**")
        st.markdown("""
        **4.1 Compatible**
        - Valid HTML/CSS
        - Unique ID attributes
        - Proper element nesting
        - ARIA roles and properties
        - Name, role, value for custom widgets
        - Status messages (aria-live)

        **Key ARIA Attributes:**
        - `role` - Define element purpose
        - `aria-label` - Accessible name
        - `aria-labelledby` - Reference label
        - `aria-describedby` - Additional description
        - `aria-live` - Dynamic updates
        - `aria-hidden` - Hide from screen readers
        """)


def display_aria_landmarks():
    """Display ARIA landmarks analysis"""
    st.markdown("### 🗺️ ARIA Landmarks & Semantic HTML")

    if not st.session_state.get('audit_results'):
        return

    accessibility_data = st.session_state.audit_results.get('accessibility', {})
    aria_data = accessibility_data.get('aria_landmarks', {})

    st.info("ARIA landmarks and semantic HTML help screen reader users navigate your site efficiently.")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Landmark Analysis")

        landmarks = {
            "Main Content (<main> or role='main')": aria_data.get('has_main', 0),
            "Navigation (<nav> or role='navigation')": aria_data.get('has_navigation', 0),
            "Banner (<header> or role='banner')": aria_data.get('has_banner', 0),
            "Contentinfo (<footer> or role='contentinfo')": aria_data.get('has_contentinfo', 0),
            "Search (role='search')": aria_data.get('has_search', 0),
            "Complementary (<aside> or role='complementary')": aria_data.get('has_complementary', 0)
        }

        total_pages = st.session_state.audit_results.get('pages_analyzed', 0)

        for landmark, count in landmarks.items():
            percentage = (count / total_pages * 100) if total_pages > 0 else 0

            if percentage >= 90:
                st.success(f"✅ {landmark}: {count}/{total_pages} pages ({percentage:.0f}%)")
            elif percentage >= 50:
                st.warning(f"⚠️ {landmark}: {count}/{total_pages} pages ({percentage:.0f}%)")
            else:
                st.error(f"❌ {landmark}: {count}/{total_pages} pages ({percentage:.0f}%)")

    with col2:
        st.markdown("#### Landmark Best Practices")
        st.markdown("""
        **Essential Landmarks:**

        ```
        <header role="banner">
          <!-- Site header -->
        </header>

        <nav role="navigation">
          <!-- Main navigation -->
        </nav>

        <main role="main">
          <!-- Primary content -->
        </main>

        <aside role="complementary">
          <!-- Related content -->
        </aside>

        <footer role="contentinfo">
          <!-- Site footer -->
        </footer>
        ```

        **Benefits:**
        - Quick navigation for screen readers
        - Better document structure
        - Improved SEO
        """)


def display_keyboard_navigation():
    """Display keyboard navigation analysis"""
    st.markdown("### ⌨️ Keyboard Navigation")

    if not st.session_state.get('audit_results'):
        return

    accessibility_data = st.session_state.audit_results.get('accessibility', {})
    keyboard_data = accessibility_data.get('keyboard_navigation', {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Focus Management")

        focus_issues = keyboard_data.get('focus_issues', {})

        missing_focus = focus_issues.get('missing_focus_indicators', 0)
        focus_order = focus_issues.get('illogical_focus_order', 0)
        keyboard_traps = focus_issues.get('keyboard_traps', 0)

        if missing_focus == 0:
            st.success("✅ All interactive elements have visible focus")
        else:
            st.error(f"❌ {missing_focus} elements missing focus indicators")

        if focus_order > 0:
            st.warning(f"⚠️ {focus_order} pages with illogical tab order")

        if keyboard_traps > 0:
            st.error(f"❌ {keyboard_traps} keyboard traps detected")

        # Tab index issues
        st.markdown("#### Tab Index Usage")

        tabindex_data = keyboard_data.get('tabindex', {})

        positive_tabindex = tabindex_data.get('positive_tabindex', 0)

        if positive_tabindex > 0:
            st.warning(f"⚠️ {positive_tabindex} elements using positive tabindex (avoid this)")

    with col2:
        st.markdown("#### Keyboard Best Practices")
        st.markdown("""
        **Essential Requirements:**
        - All functionality via keyboard
        - Visible focus indicators
        - Logical tab order
        - No keyboard traps
        - Skip navigation links

        **Tab Index Guidelines:**
        - `tabindex="0"` - Add to focus order
        - `tabindex="-1"` - Programmatic focus only
        - **Avoid positive values** (breaks natural order)

        **Common Keys:**
        - `Tab` - Navigate forward
        - `Shift+Tab` - Navigate backward
        - `Enter/Space` - Activate
        - `Esc` - Close/Cancel
        - `Arrow keys` - Within widgets
        """)


def display_color_contrast():
    """Display color contrast analysis"""
    st.markdown("### 🎨 Color Contrast & Visual Design")

    if not st.session_state.get('audit_results'):
        return

    accessibility_data = st.session_state.audit_results.get('accessibility', {})
    contrast_data = accessibility_data.get('color_contrast', {})

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Contrast Violations")

        # WCAG AA violations
        aa_failures = contrast_data.get('aa_failures', 0)
        aaa_failures = contrast_data.get('aaa_failures', 0)

        total_checks = contrast_data.get('total_checks', 0)

        if aa_failures == 0:
            st.success(f"✅ All text meets WCAG AA contrast (4.5:1)")
        else:
            aa_pass_rate = ((total_checks - aa_failures) / total_checks * 100) if total_checks > 0 else 0
            st.error(f"❌ {aa_failures} WCAG AA contrast failures ({aa_pass_rate:.0f}% pass rate)")

        if aaa_failures > aa_failures:
            st.info(f"ℹ️ {aaa_failures - aa_failures} additional AAA failures (7:1 contrast)")

        # Contrast issues by element
        st.markdown("#### Elements with Contrast Issues")

        problem_elements = contrast_data.get('problem_elements', [])

        if problem_elements:
            contrast_df = pd.DataFrame([
                {
                    'Element': elem.get('selector', '')[:40],
                    'Foreground': elem.get('foreground', ''),
                    'Background': elem.get('background', ''),
                    'Ratio': f"{elem.get('ratio', 0):.2f}:1",
                    'Required': f"{elem.get('required_ratio', 4.5):.1f}:1"
                }
                for elem in problem_elements[:20]
            ])

            st.dataframe(contrast_df, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("#### Contrast Requirements")
        st.markdown("""
        **WCAG 2.2 Standards:**

        **Level AA (Required):**
        - Normal text: **4.5:1**
        - Large text (18pt+): **3:1**
        - UI components: **3:1**

        **Level AAA (Enhanced):**
        - Normal text: **7:1**
        - Large text: **4.5:1**

        **What counts as "large"?**
        - 18pt (24px) or larger
        - 14pt (19px) bold or larger

        **Non-text Elements:**
        - Icons, buttons, form borders: **3:1**

        **Best Practices:**
        - Don't rely on color alone
        - Test with color blindness simulators
        - Provide alternative visual cues
        """)


def display_form_accessibility():
    """Display form accessibility analysis"""
    st.markdown("### 📝 Form Accessibility")

    if not st.session_state.get('audit_results'):
        return

    accessibility_data = st.session_state.audit_results.get('accessibility', {})
    form_data = accessibility_data.get('forms', {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Form Issues")

        # Labels
        missing_labels = form_data.get('missing_labels', 0)
        implicit_labels = form_data.get('implicit_labels', 0)

        if missing_labels == 0:
            st.success("✅ All form fields have labels")
        else:
            st.error(f"❌ {missing_labels} form fields without labels")

        if implicit_labels > 0:
            st.info(f"ℹ️ {implicit_labels} forms use implicit labels (use explicit)")

        # Instructions and errors
        missing_instructions = form_data.get('missing_instructions', 0)
        missing_error_messages = form_data.get('missing_error_messages', 0)

        if missing_instructions > 0:
            st.warning(f"⚠️ {missing_instructions} required fields without instructions")

        if missing_error_messages > 0:
            st.error(f"❌ {missing_error_messages} forms without error messages")

        # WCAG 2.2 criteria
        st.markdown("#### WCAG 2.2 Form Criteria 🆕")

        redundant_entry = form_data.get('redundant_entry', 0)

        if redundant_entry > 0:
            st.info(f"ℹ️ {redundant_entry} forms ask for same info twice (avoid this)")

    with col2:
        st.markdown("#### Accessible Form Example")
        st.code("""
<form>
  <label for="email">
    Email address *
    <span class="help-text">
      We'll never share your email
    </span>
  </label>
  <input 
    type="email" 
    id="email"
    name="email"
    required
    aria-required="true"
    aria-describedby="email-help"
  >
  <span id="email-help" class="help">
    Example: user@example.com
  </span>

  <!-- Error message -->
  <span 
    id="email-error"
    role="alert"
    aria-live="polite"
    class="error"
  >
    Please enter a valid email
  </span>
</form>
        """, language="html")


def display_multimedia_accessibility():
    """Display multimedia accessibility analysis"""
    st.markdown("### 🎬 Multimedia Accessibility")

    if not st.session_state.get('audit_results'):
        return

    accessibility_data = st.session_state.audit_results.get('accessibility', {})
    media_data = accessibility_data.get('multimedia', {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Video Accessibility")

        total_videos = media_data.get('total_videos', 0)
        videos_with_captions = media_data.get('videos_with_captions', 0)
        videos_with_transcripts = media_data.get('videos_with_transcripts', 0)

        st.metric("Total Videos", total_videos)

        if total_videos > 0:
            caption_rate = (videos_with_captions / total_videos * 100)

            if caption_rate == 100:
                st.success("✅ All videos have captions")
            else:
                st.error(f"❌ {total_videos - videos_with_captions} videos without captions")

            if videos_with_transcripts < total_videos:
                st.warning(f"⚠️ {total_videos - videos_with_transcripts} videos without transcripts")

        st.markdown("#### Audio Accessibility")

        total_audio = media_data.get('total_audio', 0)
        audio_with_transcripts = media_data.get('audio_with_transcripts', 0)

        st.metric("Total Audio Files", total_audio)

        if total_audio > 0 and audio_with_transcripts < total_audio:
            st.warning(f"⚠️ {total_audio - audio_with_transcripts} audio files without transcripts")

    with col2:
        st.markdown("#### Multimedia Requirements")
        st.markdown("""
        **Video Requirements:**
        - **Captions** for all speech and sounds
        - **Transcripts** for searchability
        - **Audio descriptions** for visual content
        - Accessible player controls
        - Keyboard operable

        **Audio Requirements:**
        - **Transcripts** for all content
        - Pause/stop controls
        - Volume control

        **Best Practices:**
        - Use native HTML5 <video> and <audio>
        - Provide multiple caption formats (WebVTT, SRT)
        - Sync captions accurately
        - Include speaker identification
        - Describe important visual information
        """)


def display_seo_benefits():
    """Display SEO benefits of accessibility"""
    st.markdown("### 🚀 Accessibility SEO Benefits")

    st.success("""
    **Accessibility and SEO work together!** Many accessibility best practices directly improve SEO rankings.
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### How Accessibility Improves SEO")
        st.markdown("""
        **1. Alt Text for Images**
        - Screen readers: Describe images to blind users
        - SEO: Help search engines understand image content

        **2. Semantic HTML & Headings**
        - Screen readers: Provide document structure
        - SEO: Help crawlers understand content hierarchy

        **3. Descriptive Link Text**
        - Screen readers: Explain link destination
        - SEO: Provide context for link relevance

        **4. Transcripts & Captions**
        - Users: Access multimedia content
        - SEO: Indexable text from videos/audio

        **5. Mobile-Friendly Design**
        - Accessibility: Touch targets, readable text
        - SEO: Mobile-first indexing requirement

        **6. Site Performance**
        - Accessibility: Faster loading for all users
        - SEO: Core Web Vitals ranking factor
        """)

    with col2:
        st.markdown("#### Shared Principles")
        st.markdown("""
        **User Experience (UX)**
        - Clear navigation
        - Logical structure
        - Readable content
        - Fast loading times
        - Mobile optimization

        **Content Quality**
        - Descriptive headings
        - Clear language
        - Organized information
        - Multimedia alternatives

        **Technical Excellence**
        - Valid HTML
        - Semantic markup
        - Proper metadata
        - Crawlable structure

        **Business Impact:**
        - Larger audience (15%+ have disabilities)
        - Better user engagement
        - Lower bounce rates
        - Higher conversion rates
        - Improved brand reputation
        - Legal compliance
        """)


def display_recommendations():
    """Display prioritized accessibility recommendations"""
    st.markdown("### 💡 Accessibility Recommendations")

    if not st.session_state.get('audit_results'):
        return

    accessibility_data = st.session_state.audit_results.get('accessibility', {})
    recommendations = accessibility_data.get('recommendations', [])

    if not recommendations:
        st.success("🎉 Your website meets WCAG 2.2 AA standards!")
        return

    # Group by priority and WCAG level
    critical_a = [r for r in recommendations if r.get('priority') == 'critical' and r.get('wcag_level') == 'A']
    critical_aa = [r for r in recommendations if r.get('priority') == 'critical' and r.get('wcag_level') == 'AA']
    high_priority = [r for r in recommendations if r.get('priority') == 'high']

    if critical_a:
        st.markdown("#### 🔴 Critical - WCAG Level A (Must Fix)")
        for rec in critical_a:
            with st.expander(f"🚨 {rec.get('title', 'Recommendation')}"):
                st.markdown(rec.get('description', ''))
                st.markdown(f"**WCAG Criterion:** {rec.get('wcag_criterion', 'N/A')}")
                st.markdown(f"**Affected Users:** {rec.get('affected_users', 'All')}")
                st.markdown(f"**Affected Pages:** {rec.get('affected_pages', 0)}")
                if rec.get('solution'):
                    st.markdown(f"**Solution:** {rec.get('solution', '')}")

    if critical_aa:
        st.markdown("#### 🟠 Critical - WCAG Level AA (Required for Compliance)")
        for rec in critical_aa:
            with st.expander(f"⚠️ {rec.get('title', 'Recommendation')}"):
                st.markdown(rec.get('description', ''))
                st.markdown(f"**WCAG Criterion:** {rec.get('wcag_criterion', 'N/A')}")
                st.markdown(f"**Affected Pages:** {rec.get('affected_pages', 0)}")

    if high_priority:
        st.markdown("#### 🟡 High Priority")
        for rec in high_priority[:5]:
            st.markdown(f"- {rec.get('title', 'Recommendation')} (WCAG {rec.get('wcag_criterion', '')})")


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
    """Main function for Accessibility page"""
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

    # Display WCAG principles
    display_wcag_principles()

    st.markdown("---")

    # Display ARIA landmarks
    display_aria_landmarks()

    st.markdown("---")

    # Display keyboard navigation
    display_keyboard_navigation()

    st.markdown("---")

    # Display color contrast
    display_color_contrast()

    st.markdown("---")

    # Display form accessibility
    display_form_accessibility()

    st.markdown("---")

    # Display multimedia accessibility
    display_multimedia_accessibility()

    st.markdown("---")

    # Display SEO benefits
    display_seo_benefits()

    st.markdown("---")

    # Display recommendations
    display_recommendations()


if __name__ == "__main__":
    main()

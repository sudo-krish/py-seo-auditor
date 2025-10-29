"""
Reusable widgets for SEO Auditor
Provides common UI components used across different pages
"""

import streamlit as st
from typing import Optional, Dict, List, Any, Callable
from datetime import datetime
import pandas as pd


# ============================================================================
# METRIC CARDS
# ============================================================================

def score_card(
        label: str,
        score: int,
        max_score: int = 100,
        show_delta: bool = True,
        help_text: Optional[str] = None
):
    """
    Display a score card with color-coded styling

    Args:
        label: Card label/title
        score: Current score value
        max_score: Maximum possible score
        show_delta: Whether to show status delta
        help_text: Optional tooltip text
    """

    score_color = _get_score_color(score)
    status = _get_score_status(score)

    delta = status if show_delta else None

    st.metric(
        label=label,
        value=f"{score}/{max_score}",
        delta=delta,
        help=help_text
    )


def category_score_card(
        category_name: str,
        score: int,
        issues: int = 0,
        icon: str = "📊"
):
    """
    Display a category score card with issues count

    Args:
        category_name: Name of the category
        score: Category score
        issues: Number of issues found
        icon: Icon emoji for the category
    """

    score_color = _get_score_color(score)

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {score_color}15, {score_color}05);
        border-left: 4px solid {score_color};
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h4 style="margin: 0; font-size: 16px;">
                    {icon} {category_name}
                </h4>
                <p style="margin: 5px 0 0 0; color: #6b7280; font-size: 13px;">
                    {issues} issues found
                </p>
            </div>
            <div style="
                font-size: 32px;
                font-weight: 700;
                color: {score_color};
            ">
                {score}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def mini_metric(label: str, value: str, icon: str = "📊"):
    """
    Display a compact mini metric

    Args:
        label: Metric label
        value: Metric value
        icon: Icon emoji
    """

    st.markdown(f"""
    <div style="
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        padding: 10px;
        border-radius: 6px;
        text-align: center;
    ">
        <div style="font-size: 20px; margin-bottom: 5px;">{icon}</div>
        <div style="font-size: 12px; color: #6b7280; margin-bottom: 3px;">{label}</div>
        <div style="font-size: 18px; font-weight: 600;">{value}</div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# ISSUE CARDS
# ============================================================================

def issue_card(
        title: str,
        description: str,
        severity: str = "warning",
        affected_pages: int = 0,
        recommendation: Optional[str] = None,
        expandable: bool = True
):
    """
    Display an issue card with severity indicator

    Args:
        title: Issue title
        description: Issue description
        severity: Severity level (critical, error, warning, info)
        affected_pages: Number of affected pages
        recommendation: Optional recommendation text
        expandable: Whether to make it expandable
    """

    severity_config = {
        'critical': {'icon': '🚨', 'color': '#ef4444', 'label': 'Critical'},
        'error': {'icon': '❌', 'color': '#f59e0b', 'label': 'Error'},
        'warning': {'icon': '⚠️', 'color': '#eab308', 'label': 'Warning'},
        'info': {'icon': 'ℹ️', 'color': '#3b82f6', 'label': 'Info'}
    }

    config = severity_config.get(severity, severity_config['info'])

    if expandable:
        with st.expander(f"{config['icon']} {title} ({affected_pages} pages)", expanded=False):
            st.markdown(f"**Severity:** {config['label']}")
            st.markdown(f"**Description:** {description}")
            if recommendation:
                st.markdown(f"**Recommendation:** {recommendation}")
    else:
        st.markdown(f"""
        <div style="
            border-left: 4px solid {config['color']};
            background: {config['color']}10;
            padding: 12px;
            border-radius: 6px;
            margin: 10px 0;
        ">
            <div style="font-weight: 600; font-size: 14px; margin-bottom: 5px;">
                {config['icon']} {title}
            </div>
            <div style="font-size: 13px; color: #6b7280;">
                {description}
            </div>
            <div style="font-size: 12px; color: #9ca3af; margin-top: 5px;">
                Affects {affected_pages} pages • {config['label']}
            </div>
        </div>
        """, unsafe_allow_html=True)


def issue_list(issues: List[Dict[str, Any]], max_display: int = 10):
    """
    Display a list of issues in a table format

    Args:
        issues: List of issue dictionaries
        max_display: Maximum number of issues to display
    """

    if not issues:
        st.info("✅ No issues found!")
        return

    # Convert to DataFrame
    display_issues = []
    for issue in issues[:max_display]:
        display_issues.append({
            'Severity': _severity_emoji(issue.get('severity', 'info')),
            'Issue': issue.get('title', 'Unknown')[:50],
            'Pages': issue.get('affected_pages', 0),
            'Priority': issue.get('priority', 'Medium')
        })

    df = pd.DataFrame(display_issues)
    st.dataframe(df, use_container_width=True, hide_index=True)

    if len(issues) > max_display:
        st.caption(f"Showing {max_display} of {len(issues)} issues")


# ============================================================================
# PROGRESS & STATUS INDICATORS
# ============================================================================

def progress_bar(
        label: str,
        value: int,
        max_value: int = 100,
        show_percentage: bool = True,
        color: Optional[str] = None
):
    """
    Display a labeled progress bar

    Args:
        label: Progress bar label
        value: Current value
        max_value: Maximum value
        show_percentage: Whether to show percentage
        color: Optional custom color
    """

    percentage = (value / max_value * 100) if max_value > 0 else 0
    display_color = color or _get_score_color(percentage)

    st.markdown(f"""
    <div style="margin: 15px 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span style="font-size: 13px; font-weight: 500;">{label}</span>
            {f'<span style="font-size: 13px; color: #6b7280;">{value}/{max_value}</span>' if show_percentage else ''}
        </div>
        <div style="
            background: #e5e7eb;
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
        ">
            <div style="
                background: {display_color};
                height: 100%;
                width: {percentage}%;
                transition: width 0.3s ease;
            "></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def status_badge(
        status: str,
        style: str = "default"
):
    """
    Display a status badge

    Args:
        status: Status text
        style: Badge style (success, warning, error, info, default)
    """

    styles = {
        'success': {'bg': '#10b981', 'color': 'white'},
        'warning': {'bg': '#f59e0b', 'color': 'white'},
        'error': {'bg': '#ef4444', 'color': 'white'},
        'info': {'bg': '#3b82f6', 'color': 'white'},
        'default': {'bg': '#6b7280', 'color': 'white'}
    }

    config = styles.get(style, styles['default'])

    st.markdown(f"""
    <span style="
        background: {config['bg']};
        color: {config['color']};
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
    ">
        {status}
    </span>
    """, unsafe_allow_html=True)


def loading_spinner(message: str = "Loading..."):
    """
    Display a loading spinner with message

    Args:
        message: Loading message
    """

    with st.spinner(message):
        pass


# ============================================================================
# ALERT BOXES
# ============================================================================

def alert_box(
        message: str,
        alert_type: str = "info",
        icon: Optional[str] = None,
        dismissible: bool = False
):
    """
    Display an alert box

    Args:
        message: Alert message
        alert_type: Type (info, success, warning, error)
        icon: Optional custom icon
        dismissible: Whether alert can be dismissed
    """

    configs = {
        'info': {'bg': '#dbeafe', 'border': '#3b82f6', 'icon': 'ℹ️'},
        'success': {'bg': '#d1fae5', 'border': '#10b981', 'icon': '✅'},
        'warning': {'bg': '#fef3c7', 'border': '#f59e0b', 'icon': '⚠️'},
        'error': {'bg': '#fee2e2', 'border': '#ef4444', 'icon': '❌'}
    }

    config = configs.get(alert_type, configs['info'])
    display_icon = icon or config['icon']

    st.markdown(f"""
    <div style="
        background: {config['bg']};
        border-left: 4px solid {config['border']};
        padding: 12px 16px;
        border-radius: 6px;
        margin: 10px 0;
    ">
        <span style="font-size: 18px; margin-right: 10px;">{display_icon}</span>
        <span style="font-size: 14px;">{message}</span>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# DATA DISPLAY
# ============================================================================

def data_table(
        data: pd.DataFrame,
        title: Optional[str] = None,
        max_height: int = 400,
        show_download: bool = True
):
    """
    Display a styled data table

    Args:
        data: DataFrame to display
        title: Optional table title
        max_height: Maximum table height in pixels
        show_download: Whether to show download button
    """

    if title:
        st.markdown(f"#### {title}")

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
        height=max_height
    )

    if show_download:
        csv = data.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"{title or 'data'}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )


def key_value_list(data: Dict[str, Any], title: Optional[str] = None):
    """
    Display key-value pairs in a styled list

    Args:
        data: Dictionary of key-value pairs
        title: Optional title
    """

    if title:
        st.markdown(f"**{title}**")

    for key, value in data.items():
        st.markdown(f"""
        <div style="
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e5e7eb;
        ">
            <span style="color: #6b7280; font-size: 13px;">{key}</span>
            <span style="font-weight: 600; font-size: 13px;">{value}</span>
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# ACTION CARDS
# ============================================================================

def action_card(
        title: str,
        description: str,
        button_label: str,
        button_callback: Optional[Callable] = None,
        icon: str = "🎯"
):
    """
    Display an action card with button

    Args:
        title: Card title
        description: Card description
        button_label: Button text
        button_callback: Optional callback function
        icon: Icon emoji
    """

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
        border: 1px solid #e5e7eb;
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
    ">
        <h4 style="margin: 0 0 10px 0; font-size: 16px;">
            {icon} {title}
        </h4>
        <p style="margin: 0 0 15px 0; color: #6b7280; font-size: 13px;">
            {description}
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.button(button_label, use_container_width=True):
        if button_callback:
            button_callback()


def recommendation_card(
        title: str,
        priority: str,
        effort: str,
        impact: str,
        description: str,
        steps: Optional[List[str]] = None
):
    """
    Display a recommendation card

    Args:
        title: Recommendation title
        priority: Priority level (high, medium, low)
        effort: Implementation effort
        impact: Expected impact
        description: Recommendation description
        steps: Optional list of implementation steps
    """

    priority_colors = {
        'high': '#ef4444',
        'medium': '#f59e0b',
        'low': '#10b981'
    }

    color = priority_colors.get(priority.lower(), '#6b7280')

    with st.expander(f"💡 {title}", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"**Priority:** {priority.title()}")
        with col2:
            st.markdown(f"**Effort:** {effort}")
        with col3:
            st.markdown(f"**Impact:** {impact}")

        st.markdown("---")
        st.markdown(description)

        if steps:
            st.markdown("**Implementation Steps:**")
            for i, step in enumerate(steps, 1):
                st.markdown(f"{i}. {step}")


# ============================================================================
# EMPTY STATES
# ============================================================================

def empty_state(
        icon: str = "📊",
        title: str = "No Data Available",
        description: str = "Run an audit to see results",
        action_label: Optional[str] = None,
        action_callback: Optional[Callable] = None
):
    """
    Display an empty state

    Args:
        icon: Icon emoji
        title: Empty state title
        description: Empty state description
        action_label: Optional action button label
        action_callback: Optional action callback
    """

    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 60px 20px;
        color: #9ca3af;
    ">
        <div style="font-size: 64px; margin-bottom: 20px;">
            {icon}
        </div>
        <h3 style="margin: 0 0 10px 0; color: #6b7280;">
            {title}
        </h3>
        <p style="margin: 0; font-size: 14px;">
            {description}
        </p>
    </div>
    """, unsafe_allow_html=True)

    if action_label and action_callback:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(action_label, type="primary", use_container_width=True):
                action_callback()


# ============================================================================
# COMPARISON WIDGETS
# ============================================================================

def comparison_card(
        label: str,
        current_value: Any,
        previous_value: Any,
        format_fn: Optional[Callable] = None
):
    """
    Display a comparison card showing before/after values

    Args:
        label: Metric label
        current_value: Current value
        previous_value: Previous value
        format_fn: Optional formatting function
    """

    if format_fn:
        current_display = format_fn(current_value)
        previous_display = format_fn(previous_value)
    else:
        current_display = str(current_value)
        previous_display = str(previous_value)

    # Calculate change
    try:
        change = current_value - previous_value
        change_pct = (change / previous_value * 100) if previous_value != 0 else 0

        if change > 0:
            delta_icon = "📈"
            delta_color = "#10b981"
        elif change < 0:
            delta_icon = "📉"
            delta_color = "#ef4444"
        else:
            delta_icon = "➡️"
            delta_color = "#6b7280"
    except:
        delta_icon = "➡️"
        delta_color = "#6b7280"
        change_pct = 0

    st.markdown(f"""
    <div style="
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    ">
        <div style="font-size: 12px; color: #6b7280; margin-bottom: 8px;">
            {label}
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 24px; font-weight: 700;">
                    {current_display}
                </div>
                <div style="font-size: 12px; color: #9ca3af;">
                    was {previous_display}
                </div>
            </div>
            <div style="
                font-size: 14px;
                font-weight: 600;
                color: {delta_color};
            ">
                {delta_icon} {change_pct:+.1f}%
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_score_color(score: int) -> str:
    """Get color based on score"""
    if score >= 90:
        return "#10b981"
    elif score >= 75:
        return "#3b82f6"
    elif score >= 60:
        return "#f59e0b"
    else:
        return "#ef4444"


def _get_score_status(score: int) -> str:
    """Get status text based on score"""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Fair"
    else:
        return "Needs Work"


def _severity_emoji(severity: str) -> str:
    """Get emoji for severity level"""
    return {
        'critical': '🚨',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️'
    }.get(severity, 'ℹ️')

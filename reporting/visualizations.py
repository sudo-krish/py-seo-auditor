"""
Visualization module for SEO Auditor
Creates charts and graphs for SEO audit data
"""

from __future__ import annotations  # ✅ Enable postponed evaluation of annotations

import logging
from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING, Union
from io import BytesIO
from pathlib import Path

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None  # ✅ Set to None for type checking
    logging.warning("Plotly not installed. Interactive charts unavailable.")

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.figure import Figure
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    Figure = None  # ✅ Set to None for type checking
    logging.warning("Matplotlib not installed. Static charts unavailable.")

from utils.logger import log_execution_time

logger = logging.getLogger(__name__)


class VisualizationError(Exception):
    """Custom exception for visualization errors"""
    pass


class ChartGenerator:
    """
    Main chart generator for SEO audit visualizations
    """

    # Color schemes
    COLORS = {
        'primary': '#667eea',
        'secondary': '#764ba2',
        'success': '#10b981',
        'warning': '#f59e0b',
        'danger': '#ef4444',
        'info': '#3b82f6',
        'light': '#f3f4f6',
        'dark': '#1f2937'
    }

    SCORE_COLORS = {
        'excellent': '#10b981',  # green
        'good': '#3b82f6',  # blue
        'fair': '#f59e0b',  # yellow
        'poor': '#f97316',  # orange
        'critical': '#ef4444'  # red
    }

    def __init__(self, config: Dict = None):
        """
        Initialize chart generator

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # Get visualization configuration
        viz_config = self.config.get('reporting', {}).get('visualizations', {})
        self.default_chart_type = viz_config.get('default_type', 'plotly')
        self.theme = viz_config.get('theme', 'plotly')

        # Set matplotlib style if available
        if MATPLOTLIB_AVAILABLE:
            sns.set_style('whitegrid')
            plt.rcParams['figure.figsize'] = (10, 6)
            plt.rcParams['font.size'] = 10

        logger.info("Chart generator initialized")

    @log_execution_time(logger)
    def create_score_gauge(
            self,
            score: float,
            title: str = "Overall SEO Score",
            chart_type: str = 'plotly'
    ) -> Any:  # ✅ Use Any instead of go.Figure
        """
        Create a gauge chart for displaying score

        Args:
            score: Score value (0-100)
            title: Chart title
            chart_type: 'plotly' or 'matplotlib'

        Returns:
            Chart figure object
        """
        if chart_type == 'plotly' and PLOTLY_AVAILABLE:
            return self._create_plotly_gauge(score, title)
        elif chart_type == 'matplotlib' and MATPLOTLIB_AVAILABLE:
            return self._create_matplotlib_gauge(score, title)
        else:
            raise VisualizationError(f"Chart type {chart_type} not available")

    def _create_plotly_gauge(self, score: float, title: str) -> Any:  # ✅ Changed from go.Figure
        """Create Plotly gauge chart"""
        if not PLOTLY_AVAILABLE:
            raise VisualizationError("Plotly not available")

        # Determine color based on score
        if score >= 80:
            color = self.SCORE_COLORS['excellent']
        elif score >= 60:
            color = self.SCORE_COLORS['fair']
        else:
            color = self.SCORE_COLORS['critical']

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'size': 24}},
            delta={'reference': 80, 'increasing': {'color': self.SCORE_COLORS['excellent']}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkgray"},
                'bar': {'color': color},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 40], 'color': '#fef2f2'},
                    {'range': [40, 60], 'color': '#fffbeb'},
                    {'range': [60, 80], 'color': '#f0f9ff'},
                    {'range': [80, 100], 'color': '#f0fdf4'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))

        fig.update_layout(
            height=300,
            font={'family': "Arial"},
            paper_bgcolor='white'
        )

        return fig

    def _create_matplotlib_gauge(self, score: float, title: str) -> Any:  # ✅ Changed from Figure
        """Create Matplotlib gauge chart"""
        if not MATPLOTLIB_AVAILABLE:
            raise VisualizationError("Matplotlib not available")

        fig, ax = plt.subplots(figsize=(8, 4), subplot_kw={'projection': 'polar'})

        # Create gauge
        theta = (score / 100) * 180  # Convert to degrees
        colors = ['#ef4444', '#f97316', '#f59e0b', '#3b82f6', '#10b981']
        bounds = [0, 36, 72, 108, 144, 180]

        for i in range(len(colors)):
            ax.barh(1, bounds[i + 1] - bounds[i], left=bounds[i], height=0.3,
                    color=colors[i], alpha=0.3)

        # Add score needle
        ax.plot([0, theta], [0, 1], 'k-', linewidth=3)
        ax.scatter([theta], [1], color='black', s=100, zorder=5)

        # Styling
        ax.set_theta_zero_location('W')
        ax.set_theta_direction(1)
        ax.set_ylim(0, 1.5)
        ax.set_title(f"{title}\n{score:.1f}/100", fontsize=16, pad=20)
        ax.axis('off')

        return fig

    @log_execution_time(logger)
    def create_category_scores_chart(
            self,
            category_scores: Dict[str, float],
            chart_type: str = 'plotly'
    ) -> Any:  # ✅ Use Any
        """
        Create bar chart for category scores

        Args:
            category_scores: Dictionary of category: score
            chart_type: 'plotly' or 'matplotlib'

        Returns:
            Chart figure object
        """
        if not category_scores:
            raise VisualizationError("No category scores provided")

        if chart_type == 'plotly' and PLOTLY_AVAILABLE:
            return self._create_plotly_category_bars(category_scores)
        elif chart_type == 'matplotlib' and MATPLOTLIB_AVAILABLE:
            return self._create_matplotlib_category_bars(category_scores)
        else:
            raise VisualizationError(f"Chart type {chart_type} not available")

    def _create_plotly_category_bars(self, category_scores: Dict[str, float]) -> Any:  # ✅ Changed
        """Create Plotly horizontal bar chart for categories"""
        if not PLOTLY_AVAILABLE:
            raise VisualizationError("Plotly not available")

        categories = list(category_scores.keys())
        scores = list(category_scores.values())

        # Assign colors based on scores
        colors = [self._get_score_color(score) for score in scores]

        # Sort by score (ascending for better visual hierarchy)
        sorted_data = sorted(zip(categories, scores, colors), key=lambda x: x[1])
        categories, scores, colors = zip(*sorted_data)

        fig = go.Figure(go.Bar(
            x=scores,
            y=[cat.title() for cat in categories],
            orientation='h',
            marker=dict(
                color=colors,
                line=dict(color='rgba(0,0,0,0.3)', width=1)
            ),
            text=scores,
            texttemplate='%{text:.0f}',
            textposition='outside'
        ))

        fig.update_layout(
            title="SEO Category Scores",
            xaxis_title="Score (0-100)",
            yaxis_title="",
            height=400,
            xaxis=dict(range=[0, 105]),
            font=dict(size=12),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        return fig

    def _create_matplotlib_category_bars(self, category_scores: Dict[str, float]) -> Any:  # ✅ Changed
        """Create Matplotlib horizontal bar chart"""
        if not MATPLOTLIB_AVAILABLE:
            raise VisualizationError("Matplotlib not available")

        fig, ax = plt.subplots(figsize=(10, 6))

        categories = list(category_scores.keys())
        scores = list(category_scores.values())
        colors = [self._get_score_color(score) for score in scores]

        # Sort by score
        sorted_data = sorted(zip(categories, scores, colors), key=lambda x: x[1])
        categories, scores, colors = zip(*sorted_data)

        y_pos = range(len(categories))
        ax.barh(y_pos, scores, color=colors, edgecolor='black', linewidth=0.5)

        ax.set_yticks(y_pos)
        ax.set_yticklabels([cat.title() for cat in categories])
        ax.set_xlabel('Score (0-100)', fontsize=12)
        ax.set_title('SEO Category Scores', fontsize=14, fontweight='bold')
        ax.set_xlim(0, 105)

        # Add score labels
        for i, score in enumerate(scores):
            ax.text(score + 2, i, f'{score:.0f}', va='center', fontsize=10)

        plt.tight_layout()
        return fig

    @log_execution_time(logger)
    def create_issues_distribution_chart(
            self,
            issues: Dict[str, List],
            chart_type: str = 'plotly'
    ) -> Any:
        """
        Create pie/donut chart for issues distribution

        Args:
            issues: Dictionary of severity: issues list
            chart_type: 'plotly' or 'matplotlib'

        Returns:
            Chart figure object
        """
        # Count issues by severity
        issue_counts = {
            severity: len(issue_list)
            for severity, issue_list in issues.items()
            if issue_list
        }

        if not issue_counts:
            raise VisualizationError("No issues to display")

        if chart_type == 'plotly' and PLOTLY_AVAILABLE:
            return self._create_plotly_pie(issue_counts)
        elif chart_type == 'matplotlib' and MATPLOTLIB_AVAILABLE:
            return self._create_matplotlib_pie(issue_counts)
        else:
            raise VisualizationError(f"Chart type {chart_type} not available")

    def _create_plotly_pie(self, issue_counts: Dict[str, int]) -> Any:  # ✅ Changed
        """Create Plotly donut chart"""
        if not PLOTLY_AVAILABLE:
            raise VisualizationError("Plotly not available")

        labels = [label.title() for label in issue_counts.keys()]
        values = list(issue_counts.values())

        colors_map = {
            'critical': self.SCORE_COLORS['critical'],
            'error': self.SCORE_COLORS['poor'],
            'warning': self.SCORE_COLORS['warning'],
            'info': self.SCORE_COLORS['info']
        }
        colors = [colors_map.get(k.lower(), self.COLORS['primary']) for k in issue_counts.keys()]

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker=dict(colors=colors, line=dict(color='white', width=2)),
            textinfo='label+percent+value',
            textposition='outside'
        )])

        fig.update_layout(
            title="Issues Distribution by Severity",
            height=400,
            showlegend=True,
            font=dict(size=12)
        )

        return fig

    def _create_matplotlib_pie(self, issue_counts: Dict[str, int]) -> Any:  # ✅ Changed
        """Create Matplotlib pie chart"""
        if not MATPLOTLIB_AVAILABLE:
            raise VisualizationError("Matplotlib not available")

        fig, ax = plt.subplots(figsize=(8, 6))

        labels = [label.title() for label in issue_counts.keys()]
        values = list(issue_counts.values())

        colors_map = {
            'critical': self.SCORE_COLORS['critical'],
            'error': self.SCORE_COLORS['poor'],
            'warning': self.SCORE_COLORS['warning'],
            'info': self.SCORE_COLORS['info']
        }
        colors = [colors_map.get(k.lower(), self.COLORS['primary']) for k in issue_counts.keys()]

        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops=dict(edgecolor='white', linewidth=2)
        )

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        ax.set_title('Issues Distribution by Severity', fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        return fig

    @log_execution_time(logger)
    def create_radar_chart(
            self,
            category_scores: Dict[str, float],
            chart_type: str = 'plotly'
    ) -> Any:
        """
        Create radar/spider chart for category scores

        Args:
            category_scores: Dictionary of category: score
            chart_type: 'plotly' or 'matplotlib'

        Returns:
            Chart figure object
        """
        if chart_type == 'plotly' and PLOTLY_AVAILABLE:
            return self._create_plotly_radar(category_scores)
        elif chart_type == 'matplotlib' and MATPLOTLIB_AVAILABLE:
            return self._create_matplotlib_radar(category_scores)
        else:
            raise VisualizationError(f"Chart type {chart_type} not available")

    def _create_plotly_radar(self, category_scores: Dict[str, float]) -> Any:  # ✅ Changed
        """Create Plotly radar chart"""
        if not PLOTLY_AVAILABLE:
            raise VisualizationError("Plotly not available")

        categories = [cat.title() for cat in category_scores.keys()]
        scores = list(category_scores.values())

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=categories,
            fill='toself',
            fillcolor='rgba(102, 126, 234, 0.3)',
            line=dict(color=self.COLORS['primary'], width=2),
            marker=dict(size=8, color=self.COLORS['primary'])
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(size=10)
                ),
                angularaxis=dict(tickfont=dict(size=12))
            ),
            title="SEO Performance Radar",
            showlegend=False,
            height=500,
            font=dict(size=12)
        )

        return fig

    def _create_matplotlib_radar(self, category_scores: Dict[str, float]) -> Any:  # ✅ Changed
        """Create Matplotlib radar chart"""
        if not MATPLOTLIB_AVAILABLE:
            raise VisualizationError("Matplotlib not available")

        categories = list(category_scores.keys())
        scores = list(category_scores.values())

        # Number of variables
        num_vars = len(categories)

        # Compute angle for each axis
        angles = [n / float(num_vars) * 2 * 3.14159 for n in range(num_vars)]
        scores += scores[:1]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))

        # Draw the plot
        ax.plot(angles, scores, 'o-', linewidth=2, color=self.COLORS['primary'])
        ax.fill(angles, scores, alpha=0.25, color=self.COLORS['primary'])

        # Fix axis to go in the right order
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([cat.title() for cat in categories], size=10)

        # Set y-axis limits
        ax.set_ylim(0, 100)
        ax.set_title('SEO Performance Radar', size=14, fontweight='bold', pad=20)

        plt.tight_layout()
        return fig

    @log_execution_time(logger)
    def create_trend_chart(
            self,
            historical_data: List[Dict[str, Any]],
            chart_type: str = 'plotly'
    ) -> Any:
        """
        Create line chart for score trends over time

        Args:
            historical_data: List of {date, score} dictionaries
            chart_type: 'plotly' or 'matplotlib'

        Returns:
            Chart figure object
        """
        if not historical_data:
            raise VisualizationError("No historical data provided")

        if chart_type == 'plotly' and PLOTLY_AVAILABLE:
            return self._create_plotly_trend(historical_data)
        elif chart_type == 'matplotlib' and MATPLOTLIB_AVAILABLE:
            return self._create_matplotlib_trend(historical_data)
        else:
            raise VisualizationError(f"Chart type {chart_type} not available")

    def _create_plotly_trend(self, historical_data: List[Dict[str, Any]]) -> Any:  # ✅ Changed
        """Create Plotly line chart"""
        if not PLOTLY_AVAILABLE:
            raise VisualizationError("Plotly not available")

        dates = [item['date'] for item in historical_data]
        scores = [item['score'] for item in historical_data]

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=dates,
            y=scores,
            mode='lines+markers',
            name='Overall Score',
            line=dict(color=self.COLORS['primary'], width=3),
            marker=dict(size=8, color=self.COLORS['primary'])
        ))

        # Add reference line at 80 (good score threshold)
        fig.add_hline(y=80, line_dash="dash", line_color="green",
                      annotation_text="Target (80)", annotation_position="right")

        fig.update_layout(
            title="SEO Score Trend Over Time",
            xaxis_title="Date",
            yaxis_title="Score",
            height=400,
            yaxis=dict(range=[0, 105]),
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        return fig

    def _create_matplotlib_trend(self, historical_data: List[Dict[str, Any]]) -> Any:  # ✅ Changed
        """Create Matplotlib line chart"""
        if not MATPLOTLIB_AVAILABLE:
            raise VisualizationError("Matplotlib not available")

        fig, ax = plt.subplots(figsize=(10, 6))

        dates = [item['date'] for item in historical_data]
        scores = [item['score'] for item in historical_data]

        ax.plot(dates, scores, marker='o', linewidth=2, markersize=8, color=self.COLORS['primary'])
        ax.axhline(y=80, color='green', linestyle='--', label='Target (80)')

        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Score', fontsize=12)
        ax.set_title('SEO Score Trend Over Time', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 105)
        ax.grid(True, alpha=0.3)
        ax.legend()

        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig

    def _get_score_color(self, score: float) -> str:
        """Get color based on score"""
        if score >= 80:
            return self.SCORE_COLORS['excellent']
        elif score >= 60:
            return self.SCORE_COLORS['fair']
        elif score >= 40:
            return self.SCORE_COLORS['poor']
        else:
            return self.SCORE_COLORS['critical']

    def save_chart(
            self,
            fig: Any,
            filename: str,
            output_dir: str = 'data/reports',
            format: str = 'png'
    ) -> str:
        """
        Save chart to file

        Args:
            fig: Figure object
            filename: Output filename (without extension)
            output_dir: Output directory
            format: Output format (png, jpg, svg, html)

        Returns:
            Path to saved file
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        filepath = output_path / f"{filename}.{format}"

        try:
            if PLOTLY_AVAILABLE and hasattr(fig, 'write_html'):
                if format == 'html':
                    fig.write_html(str(filepath))
                else:
                    fig.write_image(str(filepath), format=format)
            elif MATPLOTLIB_AVAILABLE and hasattr(fig, 'savefig'):
                fig.savefig(str(filepath), format=format, dpi=300, bbox_inches='tight')
            else:
                raise VisualizationError("Unknown figure type")

            logger.info(f"Chart saved to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error saving chart: {e}")
            raise VisualizationError(f"Failed to save chart: {e}")

    def get_chart_as_bytes(self, fig: Any, format: str = 'png') -> BytesIO:
        """
        Get chart as bytes for embedding

        Args:
            fig: Figure object
            format: Output format

        Returns:
            BytesIO object with chart data
        """
        buffer = BytesIO()

        try:
            if PLOTLY_AVAILABLE and hasattr(fig, 'write_image'):
                fig.write_image(buffer, format=format)
            elif MATPLOTLIB_AVAILABLE and hasattr(fig, 'savefig'):
                fig.savefig(buffer, format=format, dpi=300, bbox_inches='tight')
            else:
                raise VisualizationError("Unknown figure type")

            buffer.seek(0)
            return buffer

        except Exception as e:
            logger.error(f"Error converting chart to bytes: {e}")
            raise VisualizationError(f"Failed to convert chart: {e}")


# Export
__all__ = ['ChartGenerator', 'VisualizationError']

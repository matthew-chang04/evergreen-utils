from __future__ import annotations

from typing import Dict

import numpy as np
import plotly.graph_objects as go


PERCENTILE_COLORS = {
    10: '#93c5fd',
    25: '#60a5fa',
    50: '#16a34a',
    75: '#2563eb',
    90: '#1e40af',
}


def build_percentile_projection_figure(
    times: np.ndarray,
    percentile_values: Dict[int, np.ndarray],
    liability_values: np.ndarray,
    liability_years: np.ndarray,
) -> go.Figure:
    """Build a projection figure that shows each percentile as a distinct projected path."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=times,
        y=percentile_values[90],
        line=dict(color='rgba(59,130,246,0)', width=0),
        fill='tonexty',
        fillcolor='rgba(96,165,250,0.12)',
        name='10th-90th percentile',
        hoverinfo='skip',
    ))
    fig.add_trace(go.Scatter(
        x=times,
        y=percentile_values[10],
        line=dict(color='rgba(59,130,246,0)', width=0),
        showlegend=False,
        hoverinfo='skip',
    ))
    fig.add_trace(go.Scatter(
        x=times,
        y=percentile_values[75],
        line=dict(color='rgba(59,130,246,0)', width=0),
        fill='tonexty',
        fillcolor='rgba(37,99,235,0.10)',
        name='25th-75th percentile',
        hoverinfo='skip',
    ))
    fig.add_trace(go.Scatter(
        x=times,
        y=percentile_values[25],
        line=dict(color='rgba(59,130,246,0)', width=0),
        showlegend=False,
        hoverinfo='skip',
    ))

    for percentile in (10, 25, 50, 75, 90):
        line_width = 2.5 if percentile == 50 else 1.7
        fig.add_trace(go.Scatter(
            x=times,
            y=percentile_values[percentile],
            mode='lines',
            line=dict(color=PERCENTILE_COLORS[percentile], width=line_width),
            name=f'{percentile}th percentile',
            showlegend=percentile == 50,
            hovertemplate=f'Years: %{{x:.1f}}<br>Portfolio value: %{{y:,.0f}}<extra>{percentile}th percentile</extra>',
        ))

    fig.add_trace(go.Scatter(
        x=liability_years,
        y=liability_values,
        mode='lines',
        line=dict(color='#dc2626', width=2.4),
        name='Liabilities',
    ))

    return fig

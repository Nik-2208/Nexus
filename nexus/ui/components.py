"""UI visualization components for graphs, metrics, and cards."""

from typing import List
import plotly.graph_objects as go
import streamlit as st

from nexus.models.entities import GraphNode, GraphEdge
from nexus.models.findings import Finding
from nexus.security.redaction import sanitize_for_plain_display


def render_graph_figure(nodes: List[GraphNode], edges: List[GraphEdge]) -> go.Figure:
    """
    Renders an interactive decision and assumption graph using Plotly.
    Sanitizes all text labels to prevent XSS.
    """
    node_id_to_idx = {node.id: idx for idx, node in enumerate(nodes)}

    # Define color scheme inspired by scientific editorial clarity
    type_color_map = {
        "goal": "#2b5c8f",          # Slate blue
        "constraint": "#1f4e5b",    # Deep teal
        "claim": "#5c5c5c",         # Neutral dark
        "assumption": "#d97706",    # Amber
        "decision": "#3b82f6",      # Blue
        "action": "#dc2626",        # Red
        "artifact": "#059669",      # Green
        "evidence": "#7c3aed",      # Purple
        "test_result": "#0284c7",   # Sky blue
    }

    # Layout nodes in circular / layered coordinates
    import math
    n = len(nodes)
    xs, ys, colors, labels, hover_texts = [], [], [], [], []

    for i, node in enumerate(nodes):
        angle = (2 * math.pi * i) / max(n, 1)
        x = math.cos(angle)
        y = math.sin(angle)
        xs.append(x)
        ys.append(y)
        colors.append(type_color_map.get(node.type.value, "#475569"))
        labels.append(sanitize_for_plain_display(node.label[:25]))
        hover_texts.append(
            f"<b>{sanitize_for_plain_display(node.label)}</b><br>"
            f"Type: {node.type.value}<br>"
            f"Provenance: {node.provenance.value}<br>"
            f"Description: {sanitize_for_plain_display(node.description[:120])}"
        )

    edge_x = []
    edge_y = []
    for edge in edges:
        if edge.source in node_id_to_idx and edge.target in node_id_to_idx:
            src_i = node_id_to_idx[edge.source]
            tgt_i = node_id_to_idx[edge.target]
            edge_x.extend([xs[src_i], xs[tgt_i], None])
            edge_y.extend([ys[src_i], ys[tgt_i], None])

    fig = go.Figure()

    # Add edges trace
    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=1.5, color="#cbd5e1"),
            hoverinfo="none",
            mode="lines",
        )
    )

    # Add nodes trace
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers+text",
            hoverinfo="text",
            text=labels,
            hovertext=hover_texts,
            textposition="top center",
            marker=dict(
                size=22,
                color=colors,
                line=dict(width=2, color="#ffffff"),
            ),
        )
    )

    fig.update_layout(
        showlegend=False,
        hovermode="closest",
        margin=dict(b=20, l=20, r=20, t=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="#fafaf9",
        paper_bgcolor="#fafaf9",
        height=520,
    )

    return fig


def render_metric_card(title: str, value: str, subtitle: str, delta_color: str = "normal") -> None:
    """Renders a clean metric card adhering to editorial typography."""
    st.metric(label=title, value=value, delta=subtitle, delta_color=delta_color)

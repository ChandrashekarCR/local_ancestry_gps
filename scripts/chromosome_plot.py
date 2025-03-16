import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Function to plot chromosome segments
def plot_chromosome_segments(df, individual):
    test_df = df.copy()
    
    # Ensure chromosome is categorical
    test_df['chromosome'] = test_df['chromosome'].astype(str)

    # Normalize start positions to ensure all chromosomes start at 0
    min_positions = test_df.groupby('chromosome')['start_pos'].min()
    test_df['adjusted_start'] = test_df['start_pos'] - test_df['chromosome'].map(min_positions)
    test_df['adjusted_end'] = test_df['end_pos'] - test_df['chromosome'].map(min_positions)

    # Assign unique colors for different predictions
    unique_predictions = test_df['Prediction'].unique()
    color_map = {pred: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] for i, pred in enumerate(unique_predictions)}

    fig = go.Figure()
    first_occurrence = {}

    for _, row in test_df.iterrows():
        prediction = row["Prediction"]
        sample_id = row['SAMPLE_ID']

        # Show legend only for the first occurrence of each prediction type
        show_legend = False if prediction in first_occurrence else True
        first_occurrence[prediction] = True  

        # Main chromosome segment (Main plot)
        fig.add_trace(go.Scatter(
            x=[row["adjusted_start"], row["adjusted_end"]],
            y=[row["chromosome"], row["chromosome"]],
            mode="lines",
            line=dict(color=color_map[prediction], width=15),
            name=prediction if show_legend else None,
            showlegend=show_legend,
            hoverinfo="text",
            text=[
                f"Sample: {row['SAMPLE_ID']}<br>"
                f"Chromosome: {row['chromosome']}<br>"
                f"Start Position: {row['start_pos']}<br>"
                f"Prediction: {row['Prediction']}<br>"
                f"Population: {row['Population']}"
            ]
        ))

    fig.update_layout(
        title=f"Chromosome Segments of {sample_id}",
        title_x=0.1,  # Centers the title
        title_font=dict(size=28),
        xaxis_title="Normalized Genomic Position",
        yaxis_title="Chromosome",
        hovermode="closest",
        autosize=True,
        height=600,
        dragmode="zoom",
        xaxis=dict(
            showgrid=True,
            zeroline=False,
            showline=True,
            title_font=dict(size=18),
            tickfont=dict(size=14),
        ),
        yaxis=dict(
            showgrid=True,
            zeroline=False,
            showline=True,
            categoryorder="category ascending",
            fixedrange=False,
            title_font=dict(size=18),
            tickfont=dict(size=14),
        ),
        legend_title="Samples and Predictions",
        legend_title_font=dict(size=18),
        legend_font=dict(size=18),
        hoverlabel=dict(
            font_size=14,
        ),
        legend=dict(
            font=dict(size=14)
        ),
        legend_orientation="v",
    )

    return fig

def plot_chromosome_country(df, individual):
    test_df = df.copy()
    
    # Ensure chromosome is categorical
    test_df['chromosome'] = test_df['chromosome'].astype(str)

    # Normalize start positions to ensure all chromosomes start at 0
    min_positions = test_df.groupby('chromosome')['start_pos'].min()
    test_df['adjusted_start'] = test_df['start_pos'] - test_df['chromosome'].map(min_positions)
    test_df['adjusted_end'] = test_df['end_pos'] - test_df['chromosome'].map(min_positions)

    # Assign unique colors for different countries
    unique_countries = test_df['Country'].unique()
    color_map = {country: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] for i, country in enumerate(unique_countries)}

    fig = go.Figure()
    first_occurrence = {}

    for _, row in test_df.iterrows():
        country = row["Country"]
        sample_id = row['SAMPLE_ID']

        # Show legend only for the first occurrence of each country
        show_legend = False if country in first_occurrence else True
        first_occurrence[country] = True  

        # Main chromosome segment (Main plot)
        fig.add_trace(go.Scatter(
            x=[row["adjusted_start"], row["adjusted_end"]],
            y=[row["chromosome"], row["chromosome"]],
            mode="lines",
            line=dict(color=color_map[country], width=15),
            name=country if show_legend else None,
            showlegend=show_legend,
            hoverinfo="text",
            text=[
                f"Sample: {row['SAMPLE_ID']}<br>"
                f"Chromosome: {row['chromosome']}<br>"
                f"Country: {row['Country']}<br>"
                f"Population: {row['Population']}"
            ]
        ))

    fig.update_layout(
        title=f"Chromosome Segments for {sample_id}",
        title_x=0.1,  # Centers the title
        title_font=dict(size=32),
        xaxis_title="Normalized Genomic Position",
        yaxis_title="Chromosome",
        hovermode="closest",
        autosize=True,
        height=600,
        dragmode="zoom",
        xaxis=dict(
            showgrid=True,
            zeroline=False,
            showline=True,
            title_font=dict(size=18),
            tickfont=dict(size=14),
        ),
        yaxis=dict(
            showgrid=True,
            zeroline=False,
            showline=True,
            categoryorder="category ascending",
            fixedrange=False,
            title_font=dict(size=18),
            tickfont=dict(size=14),
        ),
        legend_title="Countries",
        legend_title_font=dict(size=18),
        legend_font=dict(size=18),
        hoverlabel=dict(
            font_size=14,
        ),
        legend=dict(
            font=dict(size=14)
        ),
        legend_orientation="v",
    )

    return fig


def plot_chromosome_continent(df, individual):
    test_df = df.copy()
    
    # Ensure chromosome is categorical
    test_df['chromosome'] = test_df['chromosome'].astype(str)

    # Normalize start positions to ensure all chromosomes start at 0
    min_positions = test_df.groupby('chromosome')['start_pos'].min()
    test_df['adjusted_start'] = test_df['start_pos'] - test_df['chromosome'].map(min_positions)
    test_df['adjusted_end'] = test_df['end_pos'] - test_df['chromosome'].map(min_positions)

    # Assign unique colors for different countries
    unique_countries = test_df['Continent'].unique()
    color_map = {country: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] for i, country in enumerate(unique_countries)}

    fig = go.Figure()
    first_occurrence = {}

    for _, row in test_df.iterrows():
        country = row["Continent"]
        sample_id = row['SAMPLE_ID']

        # Show legend only for the first occurrence of each country
        show_legend = False if country in first_occurrence else True
        first_occurrence[country] = True  

        # Main chromosome segment (Main plot)
        fig.add_trace(go.Scatter(
            x=[row["adjusted_start"], row["adjusted_end"]],
            y=[row["chromosome"], row["chromosome"]],
            mode="lines",
            line=dict(color=color_map[country], width=15),
            name=country if show_legend else None,
            showlegend=show_legend,
            hoverinfo="text",
            text=[
                f"Sample: {row['SAMPLE_ID']}<br>"
                f"Chromosome: {row['chromosome']}<br>"
                f"Start Position: {row['start_pos']}<br>"
                f"Continent: {row['Continent']}<br>"
                f"Population: {row['Population']}"
            ]
        ))

    fig.update_layout(
        title=f"Chromosome Segments for {sample_id}",
        title_x=0.1,  # Centers the title
        title_font=dict(size=32),
        xaxis_title="Normalized Genomic Position",
        yaxis_title="Chromosome",
        hovermode="closest",
        autosize=True,
        height=600,
        dragmode="zoom",
        xaxis=dict(
            showgrid=True,
            zeroline=False,
            showline=True,
            title_font=dict(size=18),
            tickfont=dict(size=14),
        ),
        yaxis=dict(
            showgrid=True,
            zeroline=False,
            showline=True,
            categoryorder="category ascending",
            fixedrange=False,
            title_font=dict(size=18),
            tickfont=dict(size=14),
        ),
        legend_title="Countries",
        legend_title_font=dict(size=18),
        legend_font=dict(size=18),
        hoverlabel=dict(
            font_size=14,
        ),
        legend=dict(
            font=dict(size=14)
        ),
        legend_orientation="v",
    )

    return fig
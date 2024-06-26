from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
from scipy.stats import ttest_ind
from dash import html, dcc

def initialize_text_voice_app(dash_app, dataset_voice, dataset_text):
    def calculate_team_meeting_metrics(meetings):
        unique_speech_frequencies = meetings.groupby(['meeting_number', 'speaker_id'])['speech_frequency'].mean().reset_index()
        meeting_metrics = unique_speech_frequencies.groupby('meeting_number').agg({'speech_frequency': 'sum'}).reset_index()
        interaction_metrics = meetings.groupby('meeting_number').agg({'count': 'sum'}).reset_index()
        self_interactions = meetings[meetings['speaker_id'] == meetings['next_speaker_id']]
        total_self_interactions = self_interactions.groupby('meeting_number')['count'].sum().reset_index()
        interaction_metrics = interaction_metrics.merge(total_self_interactions, on='meeting_number', how='left', suffixes=('', '_self'))
        interaction_metrics['count'] = interaction_metrics['count'] - interaction_metrics['count_self'].fillna(0)
        interaction_metrics.drop(columns=['count_self'], inplace=True)
        combined_metrics = meeting_metrics.merge(interaction_metrics, on='meeting_number')
        return combined_metrics

    def calculate_individual_metrics(meetings, meeting_count):
        unique_speech_frequencies = meetings.groupby(['meeting_number', 'speaker_id'])['speech_frequency'].mean().reset_index()
        individual_metrics = unique_speech_frequencies.groupby('speaker_id').agg({'speech_frequency': 'sum'}).reset_index()
        individual_metrics['speech_frequency'] /= meeting_count
        interaction_metrics = meetings.groupby('speaker_id').agg({'count': 'sum'}).reset_index()
        self_interactions = meetings[meetings['speaker_id'] == meetings['next_speaker_id']]
        total_self_interactions = self_interactions.groupby('speaker_id')['count'].sum().reset_index()
        interaction_metrics = interaction_metrics.merge(total_self_interactions, on='speaker_id', how='left', suffixes=('', '_self'))
        interaction_metrics['count'] = interaction_metrics['count'] - interaction_metrics['count_self'].fillna(0)
        interaction_metrics.drop(columns=['count_self'], inplace=True)
        interaction_metrics['count'] /= meeting_count
        combined_metrics = individual_metrics.merge(interaction_metrics, on='speaker_id')
        return combined_metrics

    def perform_ttest(group1, group2):
        ttest_results = {}
        ttest_results['speech_frequency'] = ttest_ind(group1['speech_frequency'], group2['speech_frequency'], equal_var=False)
        ttest_results['count'] = ttest_ind(group1['count'], group2['count'], equal_var=False)
        return ttest_results

    def dataframe_generator(ttest_results, group1, group2, view_type):
        rows_speech = []
        rows_interaction = []
        if view_type == 'total':
            variables = ['speech_frequency', 'count']
            for var in variables:
                if var == 'speech_frequency':
                    row_voice = {
                        'Group': 'Voice',
                        'Mean': round(group1[var].mean(), 2),
                        'Std': round(group1[var].std(), 2),
                        'df': len(group1[var]) - 1,
                        't-statistic': round(ttest_results[var].statistic, 2),
                        'p-value': round(ttest_results[var].pvalue, 2)
                    }
                    row_text = {
                        'Group': 'Text',
                        'Mean': round(group2[var].mean(), 2),
                        'Std': round(group2[var].std(), 2),
                        'df': len(group2[var]) - 1,
                        't-statistic': '',
                        'p-value': ''
                    }
                    rows_speech.append(row_voice)
                    rows_speech.append(row_text)
                else:
                    row_voice = {
                        'Group': 'Voice',
                        'Mean': round(group1[var].mean(), 2),
                        'Std': round(group1[var].std(), 2),
                        'df': len(group1[var]) - 1,
                        't-statistic': round(ttest_results[var].statistic, 2),
                        'p-value': round(ttest_results[var].pvalue, 2)
                    }
                    row_text = {
                        'Group': 'Text',
                        'Mean': round(group2[var].mean(), 2),
                        'Std': round(group2[var].std(), 2),
                        'df': len(group2[var]) - 1,
                        't-statistic': '',
                        'p-value': ''
                    }
                    rows_interaction.append(row_voice)
                    rows_interaction.append(row_text)
        else:
            for speaker in group1['speaker_id'].unique():
                row_voice = {
                    'Group': f'Voice (Speaker {speaker})',
                    'Mean': round(group1[group1['speaker_id'] == speaker]['speech_frequency'].mean(), 2),
                    'Std': round(group1[group1['speaker_id'] == speaker]['speech_frequency'].std(), 2),
                    'df': len(group1[group1['speaker_id'] == speaker]['speech_frequency']) - 1,
                    't-statistic': round(ttest_results['speech_frequency'].statistic, 2),
                    'p-value': round(ttest_results['speech_frequency'].pvalue, 2)
                }
                row_text = {
                    'Group': f'Text (Speaker {speaker})',
                    'Mean': round(group2[group2['speaker_id'] == speaker]['speech_frequency'].mean(), 2),
                    'Std': round(group2[group2['speaker_id'] == speaker]['speech_frequency'].std(), 2),
                    'df': len(group2[group2['speaker_id'] == speaker]['speech_frequency']) - 1,
                    't-statistic': '',
                    'p-value': ''
                }
                rows_speech.append(row_voice)
                rows_speech.append(row_text)
            for speaker in group1['speaker_id'].unique():
                row_voice = {
                    'Group': f'Voice (Speaker {speaker})',
                    'Mean': round(group1[group1['speaker_id'] == speaker]['count'].mean(), 2),
                    'Std': round(group1[group1['speaker_id'] == speaker]['count'].std(), 2),
                    'df': len(group1[group1['speaker_id'] == speaker]['count']) - 1,
                    't-statistic': round(ttest_results['count'].statistic, 2),
                    'p-value': round(ttest_results['count'].pvalue, 2)
                }
                row_text = {
                    'Group': f'Text (Speaker {speaker})',
                    'Mean': round(group2[group2['speaker_id'] == speaker]['count'].mean(), 2),
                    'Std': round(group2[group2['speaker_id'] == speaker]['count'].std(), 2),
                    'df': len(group2[group2['speaker_id'] == speaker]['count']) - 1,
                    't-statistic': '',
                    'p-value': ''
                }
                rows_interaction.append(row_voice)
                rows_interaction.append(row_text)
        detailed_df_speech = pd.DataFrame(rows_speech)
        detailed_df_interaction = pd.DataFrame(rows_interaction)
        return detailed_df_speech, detailed_df_interaction

    @dash_app.callback(
        [Output('text-voice-graph-speech', 'figure'),
         Output('text-voice-graph-interaction', 'figure'),
         Output('text-voice-table-speech', 'children'),
         Output('text-voice-table-interaction', 'children')],
        [Input('text-voice-view-type', 'value')]
    )
    def update_text_voice_graph_table(view_type):
        voice_meetings = dataset_voice
        text_meetings = dataset_text

        if view_type == 'total':
            voice_metrics = calculate_team_meeting_metrics(voice_meetings)
            text_metrics = calculate_team_meeting_metrics(text_meetings)
        else:
            voice_metrics = calculate_individual_metrics(voice_meetings, 12)
            text_metrics = calculate_individual_metrics(text_meetings, 9)

        ttest_results = perform_ttest(voice_metrics, text_metrics)

        fig_speech = go.Figure()
        fig_interaction = go.Figure()

        if view_type == 'total':
            fig_speech.add_trace(go.Bar(
                x=['Voice', 'Text'],
                y=[voice_metrics['speech_frequency'].mean(), text_metrics['speech_frequency'].mean()],
                error_y=dict(type='data', array=[voice_metrics['speech_frequency'].std(), text_metrics['speech_frequency'].std()]),
                marker_color=['#1f77b4', '#ff7f0e']
            ))

            fig_interaction.add_trace(go.Bar(
                x=['Voice', 'Text'],
                y=[voice_metrics['count'].mean(), text_metrics['count'].mean()],
                error_y=dict(type='data', array=[voice_metrics['count'].std(), text_metrics['count'].std()]),
                marker_color=['#1f77b4', '#ff7f0e']
            ))

            speech_y_max = max(voice_metrics['speech_frequency'].mean() + 1.1 * voice_metrics['speech_frequency'].std(),
                               text_metrics['speech_frequency'].mean() + 1.1 * text_metrics['speech_frequency'].std())
            interaction_y_max = max(voice_metrics['count'].mean() + 1.1 * voice_metrics['count'].std(),
                                    text_metrics['count'].mean() + 1.1 * text_metrics['count'].std())

            fig_speech.update_layout(
                title='A/B Test:  Speech Frequency',
                xaxis_title='Condition',
                yaxis_title=' Speech Frequency',
                yaxis=dict(range=[0, speech_y_max]),
                showlegend=False
            )

            fig_interaction.update_layout(
                title='A/B Test:  Interaction Count',
                xaxis_title='Condition',
                yaxis_title=' Interaction Count',
                yaxis=dict(range=[0, interaction_y_max]),
                showlegend=False
            )
        else:
            for speaker in voice_metrics['speaker_id'].unique():
                fig_speech.add_trace(go.Bar(
                    x=['Voice', 'Text'],
                    y=[voice_metrics[voice_metrics['speaker_id'] == speaker]['speech_frequency'].mean(),
                       text_metrics[text_metrics['speaker_id'] == speaker]['speech_frequency'].mean()],
                    error_y=dict(type='data', array=[voice_metrics[voice_metrics['speaker_id'] == speaker]['speech_frequency'].std(),
                                                     text_metrics[text_metrics['speaker_id'] == speaker]['speech_frequency'].std()]),
                    name=f'Speaker {speaker}'
                ))

                fig_interaction.add_trace(go.Bar(
                    x=['Voice', 'Text'],
                    y=[voice_metrics[voice_metrics['speaker_id'] == speaker]['count'].mean(),
                       text_metrics[text_metrics['speaker_id'] == speaker]['count'].mean()],
                    error_y=dict(type='data', array=[voice_metrics[voice_metrics['speaker_id'] == speaker]['count'].std(),
                                                     text_metrics[text_metrics['speaker_id'] == speaker]['count'].std()]),
                    name=f'Speaker {speaker}'
                ))

            fig_speech.update_layout(
                title='A/B Test:  Speech Frequency by Speaker',
                xaxis_title='Condition',
                yaxis_title=' Speech Frequency',
                showlegend=True
            )

            fig_interaction.update_layout(
                title='A/B Test:  Interaction Count by Speaker',
                xaxis_title='Condition',
                yaxis_title=' Interaction Count',
                showlegend=True
            )

        detailed_df_speech, detailed_df_interaction = dataframe_generator(ttest_results, voice_metrics, text_metrics, view_type)

        speech_table = html.Table([
            html.Thead(
                html.Tr([html.Th(col) for col in ['Group', 'Mean', 'Std', 'df', 't-statistic', 'p-value']])
            ),
            html.Tbody([
                html.Tr([
                    html.Td(detailed_df_speech.iloc[i][col]) for col in ['Group', 'Mean', 'Std', 'df', 't-statistic', 'p-value']
                ]) for i in range(len(detailed_df_speech))
            ])
        ], style={'margin': 'auto', 'text-align': 'center', 'width': '100%', 'white-space': 'nowrap'})

        interaction_table = html.Table([
            html.Thead(
                html.Tr([html.Th(col) for col in ['Group', 'Mean', 'Std', 'df', 't-statistic', 'p-value']])
            ),
            html.Tbody([
                html.Tr([
                    html.Td(detailed_df_interaction.iloc[i][col]) for col in ['Group', 'Mean', 'Std', 'df', 't-statistic', 'p-value']
                ]) for i in range(len(detailed_df_interaction))
            ])
        ], style={'margin': 'auto', 'text-align': 'center', 'width': '100%', 'white-space': 'nowrap'})

        return fig_speech, fig_interaction, speech_table, interaction_table

    dash_app.layout.children.append(html.H2("A/B Test: Text-based vs. Voice-based", style={'text-align': 'center'}))
    dash_app.layout.children.append(html.Div([
        dcc.RadioItems(
            id='text-voice-view-type',
            options=[
                {'label': 'Total', 'value': 'total'},
                {'label': 'By Speakers', 'value': 'by_speakers'}
            ],
            value='total',
            labelStyle={'display': 'inline-block'}
        ),
    ], style={'text-align': 'center', 'margin-bottom': '20px'}))
    dash_app.layout.children.append(html.Div([
        html.Div([
            dcc.Graph(id='text-voice-graph-speech'),
            html.Div(id='text-voice-table-speech')
        ], style={'width': '48%', 'display': 'inline-block'}),
        html.Div([
            dcc.Graph(id='text-voice-graph-interaction'),
            html.Div(id='text-voice-table-interaction')
        ], style={'width': '48%', 'display': 'inline-block'})
    ], style={'display': 'flex', 'justify-content': 'space-between'}))


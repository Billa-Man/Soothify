import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import calendar
import numpy as np

# Page configuration
st.set_page_config(
    page_title="MindfulAI - Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.logo(
    image="media/logo.jpg",
    size="large"
)

# Initialize session state for tracking
if 'mood_history' not in st.session_state:
    st.session_state.mood_history = []
if 'panic_episodes' not in st.session_state:
    st.session_state.panic_episodes = []
if 'chat_durations' not in st.session_state:
    st.session_state.chat_durations = []
if 'stressors' not in st.session_state:
    st.session_state.stressors = {}

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #e0e0ef;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .mood-emoji {
        font-size: 24px;
        margin-right: 10px;
    }
    
    .stButton > button {
        background-color: #7792E3 !important;
        color: white;
        font-weight: bold;
    }
    
    .chart-container {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Mood mapping with emojis
MOODS = {
    "Happy": "😊",
    "Neutral": "😐",
    "Anxious": "😰",
    "Sad": "😢",
    "Depressed": "😔"
}

# Sidebar
with st.sidebar:    
    # Daily Mood Tracker
    st.subheader("Daily Mood Check-in")
    selected_mood = st.selectbox("How are you feeling today?", list(MOODS.keys()))
    if st.button("Log Mood"):
        st.session_state.mood_history.append({
            'timestamp': datetime.now(),
            'mood': selected_mood
        })
        st.success(f"Mood logged: {MOODS[selected_mood]} {selected_mood}")

    st.subheader("Panic Episode Tracker")
    if st.button("🚨 Record Panic Episode"):
        st.session_state.panic_episodes.append(datetime.now())
        st.warning("Panic episode recorded. Would you like to start a chat session?")

# Main Dashboard
st.title("Your Mental Health Dashboard")

# Top Metrics Row
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div class="metric-card">
            <h3>Current Mood Streak</h3>
            <h2>7 days</h2>
            <p>Last check-in: Today</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="metric-card">
            <h3>Panic Episodes</h3>
            <h2>{}</h2>
            <p>↓ 20% from last week</p>
        </div>
    """.format(len([ep for ep in st.session_state.panic_episodes 
                   if ep > datetime.now() - timedelta(days=7)])), 
    unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="metric-card">
            <h3>Check-in Consistency</h3>
            <h2>85%</h2>
            <p>Last 30 days</p>
        </div>
    """, unsafe_allow_html=True)

# Charts Section
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Mood Trends")
    # Create sample mood data for visualization
    if len(st.session_state.mood_history) > 0:
        mood_df = pd.DataFrame(st.session_state.mood_history)
        fig = px.line(mood_df, x='timestamp', y='mood', 
                     title="Mood Over Time",
                     color_discrete_sequence=['#7792E3'])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Start logging your moods to see trends!")

with col2:
    st.subheader("Panic Episode Patterns")
    if len(st.session_state.panic_episodes) > 0:
        # Create time of day distribution
        hours = [ep.hour for ep in st.session_state.panic_episodes]
        fig = px.histogram(x=hours, nbins=24,
                         title="Time of Day Distribution",
                         labels={'x': 'Hour of Day', 'y': 'Number of Episodes'},
                         color_discrete_sequence=['#7792E3'])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No panic episodes recorded yet.")

# Bottom Section
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Average Episode Duration")
    if len(st.session_state.chat_durations) > 0:
        avg_duration = sum(st.session_state.chat_durations) / len(st.session_state.chat_durations)
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_duration,
            title={'text': "Minutes"},
            gauge={'axis': {'range': [0, 60]}}
        ))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No chat sessions recorded yet.")

with col2:
    st.subheader("Activity Impact Analysis")
    if 'activity_impact' not in st.session_state:
        st.session_state.activity_impact = {
            'Exercise': {'positive': 85, 'neutral': 10, 'negative': 5},
            'Meditation': {'positive': 75, 'neutral': 20, 'negative': 5},
            'Social Activities': {'positive': 70, 'neutral': 20, 'negative': 10},
            'Reading': {'positive': 65, 'neutral': 30, 'negative': 5},
            'Creative Work': {'positive': 80, 'neutral': 15, 'negative': 5}
        }
    
    # Prepare data for visualization
    activities = []
    impacts = []
    colors = []
    
    for activity, impact in st.session_state.activity_impact.items():
        activities.extend([activity] * 3)
        impacts.extend([impact['positive'], impact['neutral'], impact['negative']])
        colors.extend(['#7792E3', '#E3E3E3', '#FFB4B4'])  # Blue, Gray, Light Red
    
    fig = go.Figure()
    
    # Add bars for each impact type
    fig.add_trace(go.Bar(
        name='Positive Impact',
        y=activities[:len(activities)//3],
        x=[st.session_state.activity_impact[act]['positive'] for act in st.session_state.activity_impact],
        orientation='h',
        marker_color='#7792E3',
        text=[f"{x}%" for x in [st.session_state.activity_impact[act]['positive'] for act in st.session_state.activity_impact]],
        textposition='auto',
    ))
    
    fig.add_trace(go.Bar(
        name='Neutral Impact',
        y=activities[:len(activities)//3],
        x=[st.session_state.activity_impact[act]['neutral'] for act in st.session_state.activity_impact],
        orientation='h',
        marker_color='#E3E3E3',
        text=[f"{x}%" for x in [st.session_state.activity_impact[act]['neutral'] for act in st.session_state.activity_impact]],
        textposition='auto',
    ))
    
    fig.add_trace(go.Bar(
        name='Negative Impact',
        y=activities[:len(activities)//3],
        x=[st.session_state.activity_impact[act]['negative'] for act in st.session_state.activity_impact],
        orientation='h',
        marker_color='#FFB4B4',
        text=[f"{x}%" for x in [st.session_state.activity_impact[act]['negative'] for act in st.session_state.activity_impact]],
        textposition='auto',
    ))
    
    # Update layout
    fig.update_layout(
        barmode='stack',
        height=300,
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_title="Impact Percentage",
        yaxis_title="",
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Inter, sans-serif"),
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#F0F0F0'),
        yaxis=dict(showgrid=False)
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)
    
    # Add a small explanation
    st.markdown("""
        <div style='font-size: 0.9em; color: #666; margin-top: 10px;'>
        This chart shows how different activities impact your mental well-being based on your logged data.
        Longer blue bars indicate more positive impact.
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if 'coping_strategies_effectiveness' not in st.session_state:
        st.session_state.coping_strategies_effectiveness = {
        'Deep Breathing': {'effective': 75, 'somewhat': 20, 'not effective': 5},
        'Meditation': {'effective': 65, 'somewhat': 25, 'not effective': 10},
        'Physical Exercise': {'effective': 80, 'somewhat': 15, 'not effective': 5},
        'Journaling': {'effective': 60, 'somewhat': 30, 'not effective': 10},
        'Social Connection': {'effective': 70, 'somewhat': 20, 'not effective': 10}
    }
    
    st.subheader("Coping Strategies Effectiveness")
# Create a sunburst chart using plotly
    fig = px.sunburst(
    # Transform the data for sunburst chart
    pd.DataFrame([
        {'strategy': strategy, 'effectiveness': eff, 'value': val}
        for strategy, effs in st.session_state.coping_strategies_effectiveness.items()
        for eff, val in effs.items()
    ]),
    path=['strategy', 'effectiveness'],
    values='value',
    color_discrete_sequence=px.colors.qualitative.Set3
)
fig.update_layout(height=400)
st.plotly_chart(fig, use_container_width=True)

with col2:
    if 'activity_mood_impact' not in st.session_state:
        st.session_state.activity_mood_impact = {
        'dates': pd.date_range(start='2024-01-01', periods=30),
        'activities': {
            'Exercise': [1 if np.random.random() > 0.5 else 0 for _ in range(30)],
            'Meditation': [1 if np.random.random() > 0.6 else 0 for _ in range(30)],
            'Social': [1 if np.random.random() > 0.7 else 0 for _ in range(30)]
        },
        'mood_scores': [np.random.randint(1, 6) for _ in range(30)]
    }

# Add this visualization to your dashboard
st.subheader("Activity Impact on Mood")
# Create a parallel categories diagram
df = pd.DataFrame(st.session_state.activity_mood_impact['activities'])
df['mood'] = st.session_state.activity_mood_impact['mood_scores']
df['date'] = st.session_state.activity_mood_impact['dates']

fig = go.Figure(data=[
    go.Parcats(
        dimensions=[
            {'label': 'Exercise',
             'values': df['Exercise'].map({1: 'Done', 0: 'Not Done'})},
            {'label': 'Meditation',
             'values': df['Meditation'].map({1: 'Done', 0: 'Not Done'})},
            {'label': 'Social',
             'values': df['Social'].map({1: 'Done', 0: 'Not Done'})},
            {'label': 'Mood',
             'values': df['mood'].map({1: 'Very Low', 2: 'Low', 3: 'Neutral', 
                                     4: 'Good', 5: 'Very Good'})}
        ],
        line={'color': df['mood'], 'colorscale': 'Viridis'},
    )
])
fig.update_layout(height=400)
st.plotly_chart(fig, use_container_width=True)

# Weekly Calendar View
st.markdown("---")
st.subheader("Monthly Overview")
current_month = datetime.now().month
current_year = datetime.now().year

# Create calendar heatmap
month_calendar = calendar.monthcalendar(current_year, current_month)
mood_colors = {
    "Happy": "#4CAF50",
    "Neutral": "#FFA726",
    "Anxious": "#7792E3",
    "Sad": "#9575CD",
    "Depressed": "#EF5350"
}

# Display calendar as a table
calendar_data = []
for week in month_calendar:
    week_data = []
    for day in week:
        if day == 0:
            week_data.append("")
        else:
            mood_entry = next((m for m in st.session_state.mood_history 
                          if m['timestamp'].day == day 
                          and m['timestamp'].month == current_month), None)
            if mood_entry:
                formatted_time = mood_entry['timestamp'].strftime('%H:%M')
                week_data.append(f"{day} {MOODS[mood_entry['mood']]} ({formatted_time})")
            else:
                week_data.append(f"{day}")
    calendar_data.append(week_data)

df_calendar = pd.DataFrame(calendar_data, 
                          columns=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
st.table(df_calendar)

# Add legend for moods
st.markdown("### Mood Legend")
cols = st.columns(len(MOODS))
for i, (mood, emoji) in enumerate(MOODS.items()):
    with cols[i]:
        st.markdown(f"{emoji} {mood}")
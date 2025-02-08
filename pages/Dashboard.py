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
        background-color: #EF5350 !important;
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
    st.image("media/logo.png", width=100)
    st.markdown("---")
    
    # Daily Mood Tracker
    st.subheader("Daily Mood Check-in")
    selected_mood = st.selectbox("How are you feeling today?", list(MOODS.keys()))
    if st.button("Log Mood"):
        st.session_state.mood_history.append({
            'timestamp': datetime.now(),
            'mood': selected_mood
        })
        st.success(f"Mood logged: {MOODS[selected_mood]} {selected_mood}")
    
    # Panic Button
    st.markdown("---")
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
            <h3>Panic Episodes (This Week)</h3>
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
    st.subheader("Common Stressors")
    # Sample stressors data
    if len(st.session_state.stressors) > 0:
        fig = px.pie(values=list(st.session_state.stressors.values()),
                    names=list(st.session_state.stressors.keys()),
                    title="Common Triggers")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Start logging stressors to see patterns!")

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
            mood = next((m['mood'] for m in st.session_state.mood_history 
                        if m['timestamp'].day == day 
                        and m['timestamp'].month == current_month), None)
            week_data.append(f"{day} {MOODS[mood] if mood else ''}")
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

import streamlit as st

# Main page configuration
st.set_page_config(
    page_title="CalmNest - Your Mental Health Companion",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.logo(
    image="media/logo.jpg",
    size="large"
)

# Custom CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    /* Main content styles */
    .main {
        background-color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, h4 {
        font-family: 'Inter', sans-serif;
        color: #1f1f1f;
    }
    
    /* Sidebar styles */
    .css-1d391kg {
        background-color: #ffffff;
    }
    
    .sidebar-header {
        display: flex;
        align-items: center;
        padding: 1rem;
        margin-bottom: 2rem;
        border-bottom: 1px solid #f0f0f5;
    }
    
    .nav-item {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        margin: 0.2rem 0;
        border-radius: 8px;
        cursor: pointer;
        transition: background-color 0.2s;
        color: #1f1f1f;
    }
    
    .nav-item:hover {
        background-color: #f8f9fa;
    }
    
    .nav-item.active {
        background-color: #f0f2ff;
    }
    
    .nav-icon {
        margin-right: 12px;
        width: 20px;
        opacity: 0.7;
    }
    
    /* Feature card styles */
    .feature-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e0ef;
        margin: 1rem 0;
    }
    
    /* Button styles */
    .stButton > button {
        background-color: #7792E3;
        color: white;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        border: none;
        font-weight: 500;
        width: 100%;
    }
    
    .stButton > button:hover {
        background-color: #6384dd;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    # Logo and company name
    st.markdown("""
        <div class="sidebar-header">
            <img src="media/logo.jpg" style="width: 32px; margin-right: 10px;">
            <span style="font-size: 1.2rem; font-weight: 600;">CalmNest</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Navigation items
    nav_items = {
        "Dashboard": "📊",
        "Chat": "💭",
        "Assessment": "📋",
        "Resources": "🏥",
        "Progress": "📈",
        "Settings": "⚙️"
    }
    
    for name, icon in nav_items.items():
        st.markdown(f"""
            <div class="nav-item {'active' if name == 'Dashboard' else ''}">
                <span class="nav-icon">{icon}</span>
                {name}
            </div>
        """, unsafe_allow_html=True)

# Main content
col1, col2, col3 = st.columns([1,2,1])

with col2:
    st.markdown("<div style='margin-top: -2rem;'>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>Welcome to CalmNest</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #7792E3;'>Your AI-Powered Mental Health Companion</h3>", unsafe_allow_html=True)
    
col_left, col_right = st.columns(2)
    
with col_left:
    st.markdown("""
    <div class="feature-card">
        <h4>How it works:</h4>
        <ul>
            <li>Complete a quick assessment</li>
            <li>Chat with our AI companion</li>
            <li>Get personalized resources</li>
            <li>Track your wellness journey</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
with col_right:
    st.markdown("""
    <div class="feature-card">
        <h4>Key Features:</h4>
        <ul>
            <li>AI-powered therapeutic conversations</li>
            <li>Personalized mental health assessments</li>
            <li>Healthcare facility recommendations</li>
            <li>Educational resources and self-help tools</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

col1, col2, col3 = st.columns([1,2,1])

with col2:
    # Call to action
    st.markdown("""
    <div class="feature-card" style="text-align: center;">
        <h4>Ready to start your journey?</h4>
    """, unsafe_allow_html=True)
    
    if st.button("Begin Assessment", use_container_width=True):
        st.switch_page("pages/assessment.py")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Info cards
    # col_left, col_right = st.columns(2)
    
    # with col_left:
    #     st.markdown("""
    #     <div class="feature-card">
    #         <h4>24/7 Support</h4>
    #         <p>Always here when you need someone to talk to</p>
    #     </div>
    #     """, unsafe_allow_html=True)
    
    # with col_right:
    #     st.markdown("""
    #     <div class="feature-card">
    #         <h4>Private & Secure</h4>
    #         <p>Your conversations are completely confidential</p>
    #     </div>
    #     """, unsafe_allow_html=True)
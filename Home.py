import streamlit as st

# Main page configuration
st.set_page_config(
    page_title="MindfulAI - Mental Health Support",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main page CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Proxima+Nova:wght@400;600&display=swap');
    
    /* Main styles */
    .main {
        background-color: #f0f0f5;
    }
    
    h1, h2, h3 {
        font-family: 'Proxima Nova', sans-serif;
        color: #262730;
    }
    
    p, div {
        font-family: 'Source Sans Pro', sans-serif;
        color: #262730;
    }
    
    /* Button styles */
    .stButton > button {
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 20px;
        height: 3em;
        background-color: #7792E3 !important;
        color: white;
        border: none;
        border-radius: 5px;
        transition: transform 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
    }
    
    /* Info boxes */
    .stAlert {
        background-color: #e0e0ef;
        border: 1px solid #7792E3;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #e0e0ef;
    }
    
    /* Cards */
    .info-card {
        background-color: #e0e0ef;
        padding: 20px;
        border-radius: 10px;
        height: 100%;
        transition: transform 0.2s ease;
    }
    
    .info-card:hover {
        transform: translateY(-5px);
    }
    
    /* Feature list */
    .feature-list {
        background-color: #e0e0ef;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
    
    .feature-list ul {
        list-style-type: none;
        padding-left: 0;
    }
    
    .feature-list li {
        margin: 10px 0;
        padding-left: 25px;
        position: relative;
    }
    
    .feature-list li:before {
        content: "";
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 18px;
        height: 18px;
        background-size: contain;
        background-repeat: no-repeat;
    }
    </style>
""", unsafe_allow_html=True)

# Main content
col1, col2, col3 = st.columns([1,2,1])

with col2:
    st.markdown("<h1 style='text-align: center; color: #262730;'>🧠 Welcome to MindfulAI</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #7792E3;'>Your AI-Powered Mental Health Companion</h3>", unsafe_allow_html=True)
    
    # Feature list
    st.markdown("""
    <div class="feature-list">
    MindfulAI provides personalized mental health support through:
    <ul style='color: #262730;'>
        <li>💭 AI-powered conversations</li>
        <li>📋 Mental health assessments</li>
        <li>🏥 Healthcare facility recommendations</li>
        <li>📚 Educational resources</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    # Call-to-action button
    st.markdown("""
        <div style='background-color: #e0e0ef; padding: 20px; border-radius: 10px; margin: 20px 0;'>
    """, unsafe_allow_html=True)
    if st.button("Begin Your Journey", type="primary", use_container_width=True):
        st.switch_page("pages/questionnaire.py")
    st.markdown("</div>", unsafe_allow_html=True)

    # Information cards
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("""
        <div class="info-card">
            <h4 style='color: #7792E3; font-family: "Proxima Nova", sans-serif;'>24/7 Support</h4>
            <p style='color: #262730;'>Always here when you need someone to talk to</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_right:
        st.markdown("""
        <div class="info-card">
            <h4 style='color: #7792E3; font-family: "Proxima Nova", sans-serif;'>Private & Secure</h4>
            <p style='color: #262730;'>Your conversations are completely confidential</p>
        </div>
        """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("media/logo.png", width=100)
    st.markdown("---")
    st.markdown("""
    <div style='font-family: "Source Sans Pro", sans-serif;'>
    <h4 style='color: #7792E3;'>How it works:</h4>
    <ol style='color: #262730;'>
        <li>Complete a brief assessment</li>
        <li>Chat with our AI companion</li>
        <li>Get personalized support</li>
        <li>Access helpful resources</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)

import streamlit as st
from openai import OpenAI
from settings import settings
from streamlit_mic_recorder import mic_recorder
import io

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I assist you today?"}]

# Page configuration
st.set_page_config(
    page_title="MindfulAI",
    page_icon="🧠",
    layout="centered"
)

# Custom CSS for styling and interactive speech wave
st.markdown("""
    <style>
    .stApp {
        background-color: #f8f9fa;
    }
    
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        padding-bottom: 120px; /* Space for fixed input area */
    }
    
    .header {
        text-align: center;
        padding: 2rem;
        background-color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        background-color: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .input-area {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 1rem;
        background-color: white;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        z-index: 100; /* Ensure it stays on top */
        display: flex; /* Align elements horizontally */
        align-items: center; /* Center items vertically */
    }

    .record-button {
        margin-left: 10px;
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        cursor: pointer;
    }

    .speech-wave {
        width: 100%;
        height: 50px;
        background-image: url('https://example.com/speech-wave.gif'); /* Replace with actual wave animation URL */
        background-size: cover;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

def process_audio_input():
    """Handle audio input from microphone"""
    audio = mic_recorder(
        start_prompt="Start recording",
        stop_prompt="Stop recording",
        just_once=True
    )
    
    if audio and len(audio["bytes"]) > 0:
        try:
            audio_file = io.BytesIO(audio["bytes"])
            audio_file.name = "audio.wav"
            
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return transcript.text
        except Exception as e:
            st.error(f"Error processing audio: {str(e)}")
            return None
    return None

def get_ai_response(message):
    """Get AI response from OpenAI"""
    try:
        messages = [{"role": "user", "content": message}]
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL_ID,
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error getting AI response: {str(e)}")
        return None

def text_to_speech(text):
    """Convert text to speech"""
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        
        # Simulate interactive speech wave during playback
        st.markdown('<div class="speech-wave"></div>', unsafe_allow_html=True)
        
        return response.content
    except Exception as e:
        st.error(f"Error converting text to speech: {str(e)}")
        return None

def main():
    # Header
    st.markdown("""
        <div class="header">
            <img src="https://em-content.zobj.net/source/apple/354/brain_1f9e0.png" class="brain-icon" />
            <h1>MindfulAI</h1>
            <p>Your AI-Powered Mental Health Companion</p>
        </div>
    """, unsafe_allow_html=True)

    # Chat container
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant" and "audio" in message:
                st.audio(message["audio"], format="audio/mp3")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Input area (fixed at bottom)
    col1, col2 = st.columns([0.8, 0.2])
    
    with col1:
        user_text = st.chat_input("Share your thoughts...")
        
    with col2:
        if st.button("🎤 Record", key="record_button", help="Click to record audio"):
            user_audio = process_audio_input()
            
    # Handle user input
    if user_text or user_audio:
        user_message = user_audio if user_audio else user_text
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_message})
        
        # Get AI response and convert to speech
        ai_response = get_ai_response(user_message)
        
        if ai_response:
            audio_content = text_to_speech(ai_response)
            
            # Add AI response to chat history with audio content
            st.session_state.messages.append({
                "role": "assistant",
                "content": ai_response,
                "audio": audio_content
            })
            
            # Rerun app to update UI with new messages
            st.rerun()

if __name__ == "__main__":
    main()

import streamlit as st
from openai import OpenAI
from audio_recorder_streamlit import audio_recorder
from settings import settings
from streamlit_mic_recorder import mic_recorder

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! How may I assist you today?"}]

def generate_voice_response(text):
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        return response.content
    except Exception as e:
        st.error("Error generating voice response")
        return None

# Custom CSS for dark theme and chat interface
st.markdown(
    """
    <style>
    /* Theme colors */
    .stApp {
        background-color: #e0e0ef !important;
        color: black;
    }
    
    /* Chat container */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }
    
    /* Message styling */
    .stChatMessage {
        background-color: white;
        border-radius: 15px;
        padding: 10px 15px;
        margin: 5px 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Input area */
    .input-container {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px;
        background-color: white;
        border-radius: 25px;
        border: 1px solid #cccccc;
        margin-top: 20px;
    }
    
    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom title */
    .custom-title {
        text-align: center;
        padding: 20px 0;
        font-size: 2.5em;
        font-weight: bold;
        color: black;
    }
    
    /* Chat input */
    .stChatInputContainer {
        background-color: white;
        border-radius: 25px;
        border: 1px solid #cccccc;
        padding: 5px 15px;
    }

    /* Recording button styling */
    button[data-testid="baseButton-secondary"] {
        background-color: #ff4b4b !important;
        color: white !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        border-radius: 0.5rem !important;
    }
    
    button[data-testid="baseButton-secondary"]:hover {
        background-color: #ff3333 !important;
    }

    /* Chat input text color */
    .stChatInput {
        color: black !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# Custom title with microphone emoji
st.markdown('<h1 class="custom-title">Voice Chat Assistant 🎙️</h1>', unsafe_allow_html=True)

def process_audio_input():
    audio = mic_recorder(
        start_prompt="Start recording",
        stop_prompt="Stop recording",
        just_once=True
    )
    if audio:
        try:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=("audio.wav", audio["bytes"]),
                response_format="text"
            )
            return transcript
        except Exception as e:
            st.error("Please record for at least 0.1 seconds")
            return None
    return None

def generate_response(text):
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL_ID,
        messages=[{"role": "user", "content": text}]
    )
    return response.choices[0].message.content

# Chat container
with st.container():
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

# Input area with improved layout
col1, col2 = st.columns([0.8, 0.2])
with col1:
    user_text = st.chat_input("Type your message...")
with col2:
    user_audio = process_audio_input()

# Handle inputs
if user_audio:
    st.session_state.messages.append({"role": "user", "content": user_audio})
    text_response = generate_response(user_audio)
    st.session_state.messages.append({"role": "assistant", "content": text_response})
    
    # Generate and play voice response
    audio_response = generate_voice_response(text_response)
    if audio_response:
        st.audio(audio_response, format="audio/mp3")
    st.rerun()

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    text_response = generate_response(user_text)
    st.session_state.messages.append({"role": "assistant", "content": text_response})
    
    # Generate and play voice response
    audio_response = generate_voice_response(text_response)
    if audio_response:
        st.audio(audio_response, format="audio/mp3")
    st.rerun()

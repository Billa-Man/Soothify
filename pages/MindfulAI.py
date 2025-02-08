import streamlit as st
from openai import OpenAI
from settings import settings
from streamlit_mic_recorder import mic_recorder

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "audio_output" not in st.session_state:
    st.session_state.audio_output = None

def process_audio_input():
    audio = mic_recorder(
        start_prompt="Start recording",
        stop_prompt="Stop recording",
        just_once=True
    )
    
    if audio and len(audio["bytes"]) > 0:
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

def get_complete_response(text):
    messages = [{"role": "user", "content": text}]
    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL_ID,
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return None

def main():
    st.markdown("""
        <style>
        .stApp {
            background-color: #ffffff;
        }
        .main-content {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px 20px 120px 20px;
        }
        .header {
            text-align: center;
            padding: 2rem 0;
            background-color: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        .input-container {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: white;
            padding: 1rem;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="header">
            <h1>🧠 MindfulAI</h1>
            <p>Your AI-Powered Mental Health Companion</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.write(message["content"])
            else:
                st.write(message["content"])
                if st.session_state.audio_output:
                    st.audio(st.session_state.audio_output, format="audio/mp3")
                    st.download_button(
                        label="Download Audio Response",
                        data=st.session_state.audio_output,
                        file_name="ai_response.mp3",
                        mime="audio/mpeg",
                        key=f"download_{len(st.session_state.messages)}"
                    )
    
    # Input container
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        user_text = st.chat_input("Share your thoughts...")
    with col2:
        user_audio = process_audio_input()
    st.markdown('</div>', unsafe_allow_html=True)

    # Handle user input
    if user_audio or user_text:
        input_text = user_audio if user_audio else user_text
        st.session_state.messages.append({"role": "user", "content": input_text})

        # Get complete text response
        full_response = get_complete_response(input_text)
        
        if full_response:
            # Generate audio from response
            try:
                speech_response = client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=full_response,
                    response_format="mp3"
                )
                st.session_state.audio_output = speech_response.content
            except Exception as e:
                st.error(f"Audio generation failed: {str(e)}")
                st.session_state.audio_output = None

            # Add assistant response to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response
            })
            
            st.rerun()

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

if __name__ == "__main__":
    main()

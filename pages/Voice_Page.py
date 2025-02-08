import streamlit as st
from openai import OpenAI

import os
from pathlib import Path
import tempfile

from settings import settings

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful mental health counselling assistant, please answer the mental health questions based on the patient's description. The assistant gives helpful, comprehensive, and appropriate answers to the user's questions."},  # Add your system message here
        {"role": "assistant", "content": "Hello! How can I help you today?"}
    ]

def speech_to_text(audio_file):
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return transcript.text

def text_to_speech(text, voice="alloy"):
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )
    return response

def get_assistant_response(messages):
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL_ID,
        messages=messages
    )
    return response.choices[0].message.content

# Streamlit UI
st.title("Voice Chatbot 🎙️")

# Display chat history
for message in st.session_state.messages[1:]:  # Skip system message
    with st.chat_message(message["role"]):
        if "content" in message:
            st.write(message["content"])

# Voice input
audio_input = st.audio_input("Speak your message")

if audio_input:
    # Create a temporary file to store the audio
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
        tmp_file.write(audio_input.read())
        tmp_file_path = tmp_file.name

    # Convert speech to text
    user_text = speech_to_text(open(tmp_file_path, 'rb'))
    
    # Display user message
    with st.chat_message("user"):
        st.write(user_text)
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_text})
    
    # Get assistant response
    assistant_response = get_assistant_response(st.session_state.messages)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    
    # Display assistant response
    with st.chat_message("assistant"):
        st.write(assistant_response)
        
        # Convert assistant response to speech
        audio_response = text_to_speech(assistant_response)
        
        # Save and play audio response
        speech_file_path = Path("response.mp3")
        audio_response.stream_to_file(speech_file_path)
        
        # Play the audio response
        st.audio(str(speech_file_path))
    
    # Cleanup temporary files
    os.unlink(tmp_file_path)
    os.unlink(speech_file_path)


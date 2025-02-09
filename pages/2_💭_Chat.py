import base64
import json
import streamlit as st
import streamlit.components.v1 as components
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

st.logo(
    image="media/companylogo.png",
    size="large"
)

def lottie_audio_visualizer(audio_bytes: bytes, lottie_json: str):
    """
    Renders a Lottie animation that reacts to the audio's amplitude.
    The animation container is styled so it can be placed above the chat input.
    """
    # Convert audio bytes to a Base64 string
    audio_base64 = base64.b64encode(audio_bytes).decode()
    
    # Build the HTML/JavaScript code.
    # Note: we removed the fixed positioning and use inline styling so that
    # the animation appears where the component is rendered.
    html_code = f"""
    <div id="lottie-container" style="
            width: 300px;
            height: 300px;
            margin: 0 auto 20px auto;
        ">
    </div>
    <!-- Hidden audio element -->
    <audio id="custom-audio" src="data:audio/mp3;base64,{audio_base64}" controls style="display:none;"></audio>
    
    <!-- Include Lottie-web -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bodymovin/5.7.5/lottie.min.js"></script>
    
    <script>
      // Load the Lottie JSON animation
      var lottieData = {lottie_json};
      
      // Initialize the Lottie animation in the container
      var anim = lottie.loadAnimation({{
        container: document.getElementById('lottie-container'),
        renderer: 'svg',
        loop: true,
        autoplay: true,
        animationData: lottieData
      }});
      
      // Set up the Web Audio API to analyze the audio.
      var audioElement = document.getElementById('custom-audio');
      var AudioContext = window.AudioContext || window.webkitAudioContext;
      var audioCtx = new AudioContext();
      var analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      var bufferLength = analyser.frequencyBinCount;
      var dataArray = new Uint8Array(bufferLength);
      
      // Connect the audio element to the analyser node.
      var source = audioCtx.createMediaElementSource(audioElement);
      source.connect(analyser);
      analyser.connect(audioCtx.destination);
      
      // Animate the Lottie container based on audio amplitude.
      function animate() {{
          requestAnimationFrame(animate);
          analyser.getByteFrequencyData(dataArray);
          var sum = 0;
          for (var i = 0; i < bufferLength; i++) {{
              sum += dataArray[i];
          }}
          var average = sum / bufferLength;
          // Compute a scale factor (adjust the math as needed)
          var scale = 1 + average / 256;
          document.getElementById('lottie-container').style.transform = 'scale(' + scale + ')';
      }}
      
      // Start analyzing once the audio starts playing.
      audioElement.onplay = function() {{
          if (audioCtx.state === 'suspended') {{
              audioCtx.resume();
          }}
          animate();
      }};
      
      // Auto-start playback (note: browsers may require a user gesture).
      audioElement.play().catch(function(err) {{
          console.log("Autoplay failed:", err);
      }});
    </script>
    """
    components.html(html_code, height=320)

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
        with st.spinner("Generating response..."):
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
            padding: 20px;
        }
        .header {
            text-align: center;
            padding: 2rem 0;
            background-color: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        .input-container {
            margin-bottom: 2rem;
            padding: 1rem;
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
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

    # Load Lottie animation JSON data for the Siri wave.
    with open("media/siri_wave.json", "r") as f:
        lottie_data = json.load(f)
    lottie_json_str = json.dumps(lottie_data)
    
    # Use generated audio if available; otherwise, use a silent audio file.
    if st.session_state.audio_output:
        audio_bytes = st.session_state.audio_output
    else:
        try:
            with open("media/silence.mp3", "rb") as f:
                audio_bytes = f.read()
        except Exception as e:
            st.error("Missing 'media/silence.mp3' file for default audio.")
            return

    # *** NEW: Place the Lottie animation above the chat input bar ***
    lottie_audio_visualizer(audio_bytes, lottie_json_str)

    # Input container (chat input and mic recorder)
    with st.container():
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            user_text = st.chat_input("Share your thoughts...")
        with col2:
            user_audio = process_audio_input()

    # Handle input: use audio transcription or text input.
    if user_audio or user_text:
        input_text = user_audio if user_audio else user_text
        st.session_state.messages.append({"role": "user", "content": input_text})

        # Get the AI response
        full_response = get_complete_response(input_text)
        
        if full_response:
            # Generate audio from the response
            try:
                speech_response = client.audio.speech.create(
                    model="tts-1",
                    voice="nova",
                    input=full_response,
                    response_format="mp3"
                )
                st.session_state.audio_output = speech_response.content
            except Exception as e:
                st.error(f"Audio generation failed: {str(e)}")
                st.session_state.audio_output = None

            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response
            })
            st.rerun()

    # Main content area: display chat history.
    with st.container():
        st.markdown('<div class="main-content">', unsafe_allow_html=True)
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        st.markdown('</div>', unsafe_allow_html=True)

    # Sidebar with additional information.
    with st.sidebar:
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

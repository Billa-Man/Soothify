import streamlit as st
import asyncio
import pyaudio
import threading
import queue
# from authenticator import Authenticator
# from connection import Connection
# from devices import AudioDevices
from dotenv import load_dotenv
import os
import asyncio
import base64
import json
import tempfile
import logging
import io
import wave
import numpy as np
import websockets
import soundfile
from playsound import playsound
from pyaudio import Stream as PyAudioStream
from concurrent.futures import ThreadPoolExecutor

from typing import List, Tuple
from pyaudio import PyAudio


import base64
import requests

# Audio format and parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_WIDTH = 2
CHUNK_SIZE = 1024


class Authenticator:
    """
    A class to handle authentication with Hume AI's API via OAuth2.

    Attributes:
        api_key (str): The API key provided by Hume AI.
        secret_key (str): The secret key provided by Hume AI.
        host (str): The host URL of the API (default is "test-api.hume.ai").
    """

    def __init__(self, api_key: str, secret_key: str, host: str = "test-api.hume.ai"):
        """
        Initialize the Authenticator with the provided API key, Secret key, and host.

        Args:
            api_key (str): The API key provided by Hume AI.
            secret_key (str): The Secret key provided by Hume AI.
            host (str, optional): The host URL of the API. Defaults to "test-api.hume.ai".
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.host = host

    def fetch_access_token(self) -> str:
        """
        Fetch an access token from Hume AI's OAuth2 service.

        This method constructs the necessary headers and body for the OAuth2 client credentials
        grant, makes the POST request to the OAuth2 token endpoint, and extracts the access token
        from the response.

        Returns:
            str: The access token.

        Raises:
            ValueError: If the access token is not found in the response.
        """
        # Prepare the authorization string
        auth_string = f"{self.api_key}:{self.secret_key}"
        encoded = base64.b64encode(auth_string.encode()).decode()

        # Set up the headers
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded}",
        }

        # Prepare the body
        data = {
            "grant_type": "client_credentials",
        }

        # Make the POST request to the OAuth2 token endpoint
        response = requests.post(
            f"https://{self.host}/oauth2-cc/token", headers=headers, data=data
        )

        # Parse the JSON response
        data = response.json()

        # Extract the access token, raise an error if not found
        if "access_token" not in data:
            raise ValueError("Access token not found in response")

        return data["access_token"]





# connection.py



# Set up a thread pool executor for non-blocking audio stream reading
executor = ThreadPoolExecutor(max_workers=1)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.DEBUG
)

class Connection:
    """
    A class to handle the connection to the WebSocket server for streaming audio data.
    """

    @classmethod
    async def connect(
        cls,
        socket_url: str,
        audio_stream: PyAudioStream,
        sample_rate: int,
        sample_width: int,
        num_channels: int,
        chunk_size: int,
    ):
        """
        Establish and maintain a connection to the WebSocket server, handling reconnections as needed.

        Args:
            socket_url (str): The URL of the WebSocket server.
            audio_stream (PyAudioStream): The PyAudio stream to read audio data from.
            sample_rate (int): The sample rate of the audio data.
            sample_width (int): The sample width of the audio data.
            num_channels (int): The number of audio channels.
            chunk_size (int): The size of each audio chunk.

        Raises:
            Exception: If any error occurs during WebSocket connection or data transmission.
        """
        while True:
            try:
                async with websockets.connect(socket_url) as socket:
                    print("Connected to WebSocket")
                    # Create tasks for sending and receiving audio data
                    send_task = asyncio.create_task(
                        cls._send_audio_data(
                            socket,
                            audio_stream,
                            sample_rate,
                            sample_width,
                            num_channels,
                            chunk_size,
                        )
                    )
                    receive_task = asyncio.create_task(cls._receive_audio_data(socket))
                    # Wait for both tasks to complete
                    await asyncio.gather(receive_task, send_task)
            except websockets.exceptions.ConnectionClosed:
                print(
                    "WebSocket connection closed. Attempting to reconnect in 5 seconds..."
                )
                await asyncio.sleep(5)
            except Exception as e:
                print(
                    f"An error occurred: {e}. Attempting to reconnect in 5 seconds..."
                )
                await asyncio.sleep(5)

    @classmethod
    async def _receive_audio_data(cls, socket):
        """
        Receive and process audio data from the WebSocket server.

        Args:
            socket (WebSocketClientProtocol): The WebSocket connection.

        Raises:
            Exception: If any error occurs while receiving or processing audio data.
        """
        try:
            async for message in socket:
                try:
                    # Attempt to parse the JSON message
                    json_message = json.loads(message)
                    print("Received JSON message:", json_message)

                    # Check if the message type is 'audio_output'
                    if json_message.get("type") == "audio_output":
                        # Decode the base64 audio data
                        audio_data = base64.b64decode(json_message["data"])

                        # Write the decoded audio data to a temporary file and play it
                        with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as tmpfile:
                            tmpfile.write(audio_data)
                            tmpfile.flush()  # Ensure all data is written to disk
                            playsound(tmpfile.name)
                            print("Audio played")

                except ValueError as e:
                    print(f"Failed to parse JSON, error: {e}")
                except KeyError as e:
                    print(f"Key error in JSON data: {e}")

        except Exception as e:
            print(f"An error occurred while receiving audio: {e}")

    @classmethod
    async def _read_audio_stream_non_blocking(cls, audio_stream, chunk_size):
        """
        Read a chunk of audio data from the PyAudio stream in a non-blocking manner.

        Args:
            audio_stream (PyAudioStream): The PyAudio stream to read audio data from.
            chunk_size (int): The size of each audio chunk.

        Returns:
            bytes: The audio data read from the stream.
        """
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(
            executor, audio_stream.read, chunk_size, False
        )
        return data

    @classmethod
    async def _send_audio_data(
        cls,
        socket,
        audio_stream: PyAudioStream,
        sample_rate: int,
        sample_width: int,
        num_channels: int,
        chunk_size: int,
    ):
        """
        Read audio data from the PyAudio stream and send it to the WebSocket server.

        Args:
            socket (WebSocketClientProtocol): The WebSocket connection.
            audio_stream (PyAudioStream): The PyAudio stream to read audio data from.
            sample_rate (int): The sample rate of the audio data.
            sample_width (int): The sample width of the audio data.
            num_channels (int): The number of audio channels.
            chunk_size (int): The size of each audio chunk.
        """
        wav_buffer = io.BytesIO()
        headers_sent = False

        while True:
            # Read audio data from the stream
            data = await cls._read_audio_stream_non_blocking(audio_stream, chunk_size)
            if num_channels == 2:  # Stereo to mono conversion if stereo is detected
                # Assuming the sample width is 2 bytes, hence 'int16'
                stereo_data = np.frombuffer(data, dtype=np.int16)
                # Averaging every two samples (left and right channels)
                mono_data = ((stereo_data[0::2] + stereo_data[1::2]) / 2).astype(np.int16)
                data = mono_data.tobytes()

            # Convert audio data to numpy array and write to buffer
            np_array = np.frombuffer(data, dtype="int16")
            soundfile.write(
                wav_buffer,
                np_array,
                samplerate=sample_rate,
                subtype="PCM_16",
                format="RAW",
            )

            wav_content = wav_buffer.getvalue()
            if not headers_sent:
                # Write WAV header if not already sent
                header_buffer = io.BytesIO()
                with wave.open(header_buffer, "wb") as wf:
                    wf.setnchannels(num_channels)
                    wf.setsampwidth(sample_width)
                    wf.setframerate(sample_rate)
                    wf.setnframes(chunk_size)

                    wf.writeframes(b"")

                headers = header_buffer.getvalue()
                wav_content = headers + wav_content
                headers_sent = True

            # Encode audio data to base64 and send as JSON message
            encoded_audio = base64.b64encode(wav_content).decode('utf-8')
            json_message = json.dumps({"type": "audio_input", "data": encoded_audio})
            await socket.send(json_message)

            # Reset buffer for the next chunk of audio data
            wav_buffer = io.BytesIO()




# devices.py



class AudioDevices:
    """
    A class to manage and select audio input and output devices using PyAudio.
    """

    @classmethod
    def list_audio_devices(
        cls, pyaudio: PyAudio
    ) -> Tuple[List[Tuple[int, str]], List[Tuple[int, str]]]:
        """
        List available audio input and output devices.

        Args:
            pyaudio (PyAudio): An instance of PyAudio to interact with the audio system.

        Returns:
            Tuple[List[Tuple[int, str]], List[Tuple[int, str]]]: A tuple containing two lists:
                - A list of tuples for input devices, each containing the device index, name, and default sample rate.
                - A list of tuples for output devices, each containing the device index and name.
        """
        # Get host API info and number of devices
        info = pyaudio.get_host_api_info_by_index(0)
        n_devices = info.get("deviceCount")

        input_devices = []
        output_devices = []

        # Iterate through all devices and classify them as input or output devices
        for i in range(n_devices):
            device = pyaudio.get_device_info_by_host_api_device_index(0, i)
            if device.get("maxInputChannels") > 0:
                input_devices.append(
                    (i, device.get("name"), int(device.get("defaultSampleRate")))
                )
            if device.get("maxOutputChannels") > 0:
                output_devices.append((i, device.get("name"), device))
                
        return input_devices, output_devices

    @classmethod
    def choose_device(cls, devices, device_type="input"):
        """
        Allow the user to select an audio device from a list of available devices.

        Args:
            devices (List[Tuple[int, str, int]]): A list of tuples representing the available devices.
            device_type (str, optional): The type of device to choose ('input' or 'output'). Defaults to 'input'.

        Returns:
            Tuple[int, int] or int: For input devices, returns a tuple containing the chosen device index and sample rate.
                                    For output devices, returns the chosen device index.
        """
        if not devices:
            print(f"No {device_type} devices found.")
            return None

        # Display available devices
        print(f"Available {device_type} devices:")
        for _, (device_index, name, sample_rate) in enumerate(devices):
            print(f"{device_index}: {name}")

        # Prompt the user to select a device by index
        while True:
            try:
                choice = int(input(f"Select {device_type} device by index: "))
                if choice in [d[0] for d in devices]:
                    if device_type == "input":
                        return choice, sample_rate
                    else:
                        return choice
                else:
                    print(
                        f"Invalid selection. Please choose a valid {device_type} device index."
                    )
            except ValueError:
                print("Please enter a numerical index.")






class StreamlitAudioChat:
    def __init__(self):
        self.pyaudio = pyaudio.PyAudio()
        self.audio_stream = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        
    def initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'access_token' not in st.session_state:
            st.session_state.access_token = None
        if 'selected_input_device' not in st.session_state:
            st.session_state.selected_input_device = None
        if 'selected_output_device' not in st.session_state:
            st.session_state.selected_output_device = None

    def get_audio_devices(self):
        """Get available audio input and output devices"""
        return AudioDevices.list_audio_devices(self.pyaudio)

    def authenticate(self):
        """Handle authentication with Hume AI"""
        st.sidebar.header("Authentication")
        
        # Load environment variables
        load_dotenv()
        api_key = os.getenv("HUME_API_KEY") or st.sidebar.text_input("Hume API Key", type="password")
        secret_key = os.getenv("HUME_SECRET_KEY") or st.sidebar.text_input("Hume Secret Key", type="password")
        
        if st.sidebar.button("Authenticate"):
            if api_key and secret_key:
                try:
                    authenticator = Authenticator(api_key, secret_key)
                    access_token = authenticator.fetch_access_token()
                    st.session_state.access_token = access_token
                    st.session_state.authenticated = True
                    st.sidebar.success("Authentication successful!")
                except Exception as e:
                    st.sidebar.error(f"Authentication failed: {str(e)}")
            else:
                st.sidebar.error("Please provide both API Key and Secret Key")

    def setup_audio_devices(self):
        """Setup audio input and output devices"""
        st.sidebar.header("Audio Device Setup")
        
        input_devices, output_devices = self.get_audio_devices()
        
        # Input device selection
        input_device_names = [f"{name} ({idx})" for idx, name, _ in input_devices]
        selected_input = st.sidebar.selectbox(
            "Select Input Device",
            input_device_names,
            index=0 if input_device_names else None
        )
        
        # Output device selection
        output_device_names = [f"{name} ({idx})" for idx, name, _ in output_devices]
        selected_output = st.sidebar.selectbox(
            "Select Output Device",
            output_device_names,
            index=0 if output_device_names else None
        )
        
        if st.sidebar.button("Configure Devices"):
            if selected_input and selected_output:
                input_idx = int(selected_input.split("(")[-1].strip(")"))
                output_idx = int(selected_output.split("(")[-1].strip(")"))
                
                # Find the selected input device's sample rate
                input_device = next((device for device in input_devices if device[0] == input_idx), None)
                if input_device:
                    sample_rate = input_device[2]
                    
                    # Store selected devices in session state
                    st.session_state.selected_input_device = (input_idx, sample_rate)
                    st.session_state.selected_output_device = output_idx
                    
                    st.sidebar.success("Audio devices configured successfully!")
                else:
                    st.sidebar.error("Failed to get input device information")
            else:
                st.sidebar.error("Please select both input and output devices")

    async def start_audio_stream(self):
        """Start the audio stream with WebSocket connection"""
        if not all([
            st.session_state.authenticated,
            st.session_state.selected_input_device,
            st.session_state.selected_output_device
        ]):
            st.error("Please complete authentication and device setup first")
            return

        input_idx, sample_rate = st.session_state.selected_input_device
        output_idx = st.session_state.selected_output_device

        # Initialize audio stream
        self.audio_stream = self.pyaudio.open(
            format=FORMAT,
            channels=CHANNELS,
            frames_per_buffer=CHUNK_SIZE,
            rate=sample_rate,
            input=True,
            output=True,
            input_device_index=input_idx,
            output_device_index=output_idx,
        )

        # Construct WebSocket URL
        socket_url = (
            "wss://api.hume.ai/v0/assistant/chat?"
            f"access_token={st.session_state.access_token}"
        )

        # Start WebSocket connection
        await Connection.connect(
            socket_url,
            self.audio_stream,
            sample_rate,
            SAMPLE_WIDTH,
            CHANNELS,
            CHUNK_SIZE,
        )

    def main(self):
        """Main Streamlit application"""
        st.title("Hume AI Voice Chat")
        
        # Initialize session state
        self.initialize_session_state()
        
        # Setup sidebar components
        self.authenticate()
        self.setup_audio_devices()
        
        # Main chat interface
        st.header("Chat Interface")
        
        # Start/Stop button for audio stream
        if st.button("Start Chat", disabled=not all([
            st.session_state.authenticated,
            st.session_state.selected_input_device,
            st.session_state.selected_output_device
        ])):
            with st.spinner("Starting audio chat..."):
                asyncio.run(self.start_audio_stream())
        
        # Display chat status and instructions
        if st.session_state.authenticated:
            st.info("Status: Connected to Hume AI")
            st.markdown("""
            ### Instructions:
            1. Select your input (microphone) and output (speakers) devices in the sidebar
            2. Click 'Configure Devices' to set up your audio devices
            3. Click 'Start Chat' to begin the conversation
            4. Speak clearly into your microphone
            5. The AI assistant's responses will play through your selected output device
            """)
        else:
            st.warning("Please authenticate using your Hume AI credentials in the sidebar")

if __name__ == "__main__":
    app = StreamlitAudioChat()
    app.main()
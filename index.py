import streamlit as st
import io
import base64
import torch
import torchaudio
import soundfile as sf
from demucs import pretrained
from demucs.apply import apply_model
from pydub import AudioSegment
import os
import subprocess

# Title and description
st.title("Audio Source Separation")
st.write("Upload an audio file and get the instrumental (accompaniment) version.")

# Function to ensure ffmpeg and ffprobe are installed and available
def ensure_ffmpeg_installed():
    try:
        # Check if ffmpeg and ffprobe are available
        subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['ffprobe', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        st.error("FFmpeg or ffprobe not found. Installing now...")
        # Automatically install ffmpeg using pip
        os.system('pip install ffmpeg')
        return True
    except FileNotFoundError:
        st.error("FFmpeg or ffprobe not found. Installing now...")
        # Automatically install ffmpeg using pip
        os.system('pip install ffmpeg')
        return True

# Ensure ffmpeg and ffprobe are installed
if not ensure_ffmpeg_installed():
    st.stop()

# Set the paths for ffmpeg and ffprobe dynamically
def set_ffmpeg_paths():
    try:
        # Find the path to ffmpeg and ffprobe
        ffmpeg_path = subprocess.check_output(['which', 'ffmpeg']).decode().strip()
        ffprobe_path = subprocess.check_output(['which', 'ffprobe']).decode().strip()
        
        # Set the paths for pydub
        os.environ["PATH"] += os.pathsep + os.path.dirname(ffmpeg_path)
        AudioSegment.converter = ffmpeg_path
        AudioSegment.ffmpeg = ffmpeg_path
        AudioSegment.ffprobe = ffprobe_path
        return True
    except subprocess.CalledProcessError:
        st.error("Failed to find ffmpeg and ffprobe after installation.")
        return False

# Set paths for ffmpeg and ffprobe
if not set_ffmpeg_paths():
    st.stop()

# File uploader
uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav"])

if uploaded_file is not None:
    # Save the uploaded file temporarily
    with open("temp_audio.mp3", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Convert MP3 to WAV using pydub
    audio = AudioSegment.from_mp3("temp_audio.mp3")
    audio.export("temp_audio.wav", format="wav")
    
    # Load the converted WAV file
    waveform, sr = torchaudio.load("temp_audio.wav")
    waveform = waveform.unsqueeze(0)  # add batch dimension: now (1, channels, time)

    # Load the Demucs model ('htdemucs') and set it to evaluation mode
    st.write("Loading Demucs model...")
    model = pretrained.get_model('htdemucs')
    model.eval()
    model.cpu()  # ensure the model is on CPU

    # Run source separation using apply_model
    st.write("Running source separation...")
    with torch.no_grad():
        estimates = apply_model(model, waveform, shifts=1, split=True, overlap=0.25)

    # Compute accompaniment (instrumental) by summing the non-vocal stems:
    vocals = estimates[0, 3]
    accompaniment = estimates[0, 0] + estimates[0, 1] + estimates[0, 2]

    # Write the accompaniment audio to an in-memory WAV file
    accompaniment_np = accompaniment.cpu().numpy().T
    buffer = io.BytesIO()
    sf.write(buffer, accompaniment_np, sr, format='WAV')
    buffer.seek(0)  # Rewind the buffer to the beginning

    # Create a download link for the in-memory WAV file
    data = buffer.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:audio/wav;base64,{b64}" download="accompaniment.wav">Download Accompaniment (Instrumental)</a>'
    st.markdown(href, unsafe_allow_html=True)

    st.success("Processing complete! Click the link above to download the instrumental (accompaniment) WAV file.")
else:
    st.info("Please upload an audio file to proceed.")
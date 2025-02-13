import os
import streamlit as st
import io
import base64
import torch
import torchaudio
import soundfile as sf
from demucs import pretrained
from demucs.apply import apply_model
from pydub import AudioSegment
import subprocess

def get_ffmpeg_paths():
    """Retrieve FFmpeg and ffprobe paths from file if available."""
    if os.path.exists("ffmpeg_path.txt"):
        with open("ffmpeg_path.txt", "r") as f:
            paths = f.read().splitlines()
            if len(paths) >= 2:
                return paths[0], paths[1]  # Return ffmpeg and ffprobe paths
    return None, None

def ensure_ffmpeg():
    """Ensure FFmpeg and ffprobe are installed and accessible."""
    ffmpeg_path, ffprobe_path = get_ffmpeg_paths()

    if not ffmpeg_path or not ffprobe_path or not os.path.exists(ffmpeg_path) or not os.path.exists(ffprobe_path):
        st.error("❌ FFmpeg or ffprobe is not installed or not found. Please run `setup.py` to install them.")
        return False

    try:
        subprocess.run([ffmpeg_path, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        subprocess.run([ffprobe_path, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # Set paths for pydub
        os.environ["FFMPEG_PATH"] = ffmpeg_path
        os.environ["FFPROBE_PATH"] = ffprobe_path

        from pydub.utils import which
        os.environ["PATH"] += os.pathsep + os.path.dirname(ffmpeg_path)
        os.environ["PATH"] += os.pathsep + os.path.dirname(ffprobe_path)

        print(f"✅ FFmpeg & ffprobe configured correctly!")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        st.error("❌ FFmpeg or ffprobe was installed but cannot be found. Try running `setup.py` again.")
        return False

# Streamlit App Title
st.title("🎵 Audio Source Separation App")
st.write("Upload an audio file and extract the **instrumental (accompaniment)**.")

# File uploader
uploaded_file = st.file_uploader("🎧 Upload an audio file", type=["mp3", "wav"])

if uploaded_file is not None:
    if not ensure_ffmpeg():
        st.error("⚠️ FFmpeg or ffprobe is missing. Ensure they're installed before proceeding.")
    else:
        # Save uploaded file temporarily
        temp_mp3_path = "temp_audio.mp3"
        temp_wav_path = "temp_audio.wav"

        with open(temp_mp3_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Convert MP3 to WAV using pydub
        st.write("🔄 Converting MP3 to WAV...")
        audio = AudioSegment.from_mp3(temp_mp3_path)
        audio.export(temp_wav_path, format="wav")

        # Load converted WAV file
        st.write("🎶 Loading audio file...")
        waveform, sr = torchaudio.load(temp_wav_path)
        waveform = waveform.unsqueeze(0)  # Add batch dimension

        # Load Demucs model ('htdemucs')
        st.write("⏳ Loading Demucs model...")
        model = pretrained.get_model('htdemucs')
        model.eval()
        model.cpu()  # Run on CPU

        # Run source separation
        st.write("🎧 Running source separation...")
        with torch.no_grad():
            estimates = apply_model(model, waveform, shifts=1, split=True, overlap=0.25)

        # Compute accompaniment (instrumental)
        vocals = estimates[0, 3]
        accompaniment = estimates[0, 0] + estimates[0, 1] + estimates[0, 2]

        # Convert to NumPy array and save as WAV
        accompaniment_np = accompaniment.cpu().numpy().T
        buffer = io.BytesIO()
        sf.write(buffer, accompaniment_np, sr, format='WAV')
        buffer.seek(0)  # Rewind buffer

        # Generate download link
        data = buffer.read()
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:audio/wav;base64,{b64}" download="accompaniment.wav">🎵 Download Instrumental</a>'
        st.markdown(href, unsafe_allow_html=True)

        st.success("✅ Processing complete! Click the link above to download the instrumental version.")
else:
    st.info("📥 Please upload an audio file to proceed.")

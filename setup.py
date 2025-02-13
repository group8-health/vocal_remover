import os
import subprocess

def install_packages():
    """Install required Python packages."""
    packages = [
        'streamlit',
        'demucs',
        'soundfile',
        'torchaudio',
        'pydub',
        'imageio-ffmpeg'  # Ensures ffmpeg is available for pydub
    ]
    
    for package in packages:
        os.system(f'pip install {package}')

def install_ffmpeg():
    """Download and set up FFmpeg and ffprobe manually if missing."""
    ffmpeg_url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    ffmpeg_dir = os.path.join(os.getcwd(), "ffmpeg")
    ffmpeg_bin = os.path.join(ffmpeg_dir, "ffmpeg")
    ffprobe_bin = os.path.join(ffmpeg_dir, "ffprobe")

    if os.path.exists(ffmpeg_bin) and os.path.exists(ffprobe_bin):
        print(f"✅ FFmpeg and ffprobe are already installed at: {ffmpeg_dir}")
    else:
        print("⚠️ FFmpeg and ffprobe not found. Downloading...")

        os.system(f"wget -q {ffmpeg_url} -O ffmpeg.tar.xz")
        os.system("mkdir -p ffmpeg && tar -xf ffmpeg.tar.xz -C ffmpeg --strip-components=1")

        if not os.path.exists(ffmpeg_bin) or not os.path.exists(ffprobe_bin):
            print("❌ FFmpeg installation failed. Please install it manually.")
            return None

        print("✅ FFmpeg and ffprobe installed successfully!")

    # Save paths to a file for app.py to read
    with open("ffmpeg_path.txt", "w") as f:
        f.write(ffmpeg_bin + "\n" + ffprobe_bin)

    return ffmpeg_bin, ffprobe_bin

def set_ffmpeg_paths():
    """Find and set FFmpeg and ffprobe paths dynamically."""
    ffmpeg_bin, ffprobe_bin = install_ffmpeg()
    
    if ffmpeg_bin and ffprobe_bin:
        os.environ["PATH"] += os.pathsep + os.path.dirname(ffmpeg_bin)
        os.environ["FFMPEG_PATH"] = ffmpeg_bin
        os.environ["FFPROBE_PATH"] = ffprobe_bin

        # Explicitly set paths for pydub
        from pydub.utils import which
        os.environ["PATH"] += os.pathsep + ffmpeg_bin
        os.environ["PATH"] += os.pathsep + ffprobe_bin

        print(f"✅ FFmpeg path set: {ffmpeg_bin}")
        print(f"✅ FFprobe path set: {ffprobe_bin}")
    else:
        print("⚠️ FFmpeg setup failed.")

def main():
    install_packages()
    set_ffmpeg_paths()

if __name__ == "__main__":
    main()

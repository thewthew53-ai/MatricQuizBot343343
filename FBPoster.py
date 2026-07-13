import os
import time
import math
import requests
from moviepy.video.io.VideoFileClip import VideoFileClip
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

import subprocess

TOKEN = "8835211619:AAHiQJcsSUfI8eFVeegKhhIkKq7zREjmTSI"
CHANNEL_ID = "@mbalisex"
FOLDER_PATH = "./videos"         # Path to the folder containing your 30 videos
TEMP_DIR = "./temp_chunks"       # Location to hold temporary 49MB clips if needed
TARGET_MAX_SIZE = 49 * 1024 * 1024  # 49 MB safety limit in bytes

url = f"https://api.telegram.org/bot{TOKEN}/sendVideo"

# Safe console text tracker
def create_progress_callback(file_name):
    def progress_callback(monitor):
        bytes_sent = monitor.bytes_read
        total_bytes = monitor.len
        percentage = (bytes_sent / total_bytes) * 100
        sent_mb = bytes_sent / (1024 * 1024)
        total_mb = total_bytes / (1024 * 1024)
        print(f"\rUploading {file_name}: {percentage:.1f}% ({sent_mb:.1f}/{total_mb:.1f} MB)", end="", flush=True)
    return progress_callback

video_extensions = (".mp4", ".mkv", ".avi", ".mov")

if not os.path.exists(FOLDER_PATH):
    print("Videos folder not found.")
    exit(1)

all_files = [f for f in os.listdir(FOLDER_PATH) if f.lower().endswith(video_extensions)]

if not all_files:
    print("No videos found in the folder. Everything has been successfully processed!")
    exit(0)

# Robust numerical sorting so 2.mp4 runs before 10.mp4
try:
    all_files.sort(key=lambda x: int(os.path.splitext(x)[0]))
except ValueError:
    all_files.sort()

# Target strictly the lowest number file remaining
TARGET_VIDEO_NAME = all_files[0]
INPUT_VIDEO_PATH = os.path.join(FOLDER_PATH, TARGET_VIDEO_NAME)

print(f"Found next file to upload: {TARGET_VIDEO_NAME}")
upload_success = True  

# Streaming upload directly to Telegram
with open(INPUT_VIDEO_PATH, "rb") as video_file:
    encoder = MultipartEncoder(
        fields={
            "chat_id": str(CHANNEL_ID),
            "caption": f"Video: {TARGET_VIDEO_NAME}",
            "supports_streaming": "true",
            "video": (TARGET_VIDEO_NAME, video_file, "video/mp4")
        }
    )
    monitor = MultipartEncoderMonitor(encoder, create_progress_callback(TARGET_VIDEO_NAME))
    try:
        response = requests.post(url, data=monitor, headers={"Content-Type": monitor.content_type}, timeout=300)
        result = response.json()
        print() 
        if result.get("ok"):
            print(f"{TARGET_VIDEO_NAME} uploaded successfully!")
        else:
            print(f"Telegram refused file: {result.get('description')}")
            upload_success = False
    except Exception as e:
        print(f"\nNetwork upload exception: {e}")
        upload_success = False

# PERMANENT REPOSITORY CLEANUP
if upload_success:
    try:
        print(f"Upload complete. Committing the deletion of {TARGET_VIDEO_NAME} back to GitHub...")
        
        # Authenticates the GitHub cloud bot instance locally
        subprocess.run(["git", "config", "--global", "user.name", "github-actions[bot]"], check=True)
        subprocess.run(["git", "config", "--global", "user.email", "github-actions[bot]@://github.com"], check=True)
        
        # Track file removal and push live
        subprocess.run(["git", "rm", INPUT_VIDEO_PATH], check=True)
        subprocess.run(["git", "commit", "-m", f"Automated removal of uploaded video: {TARGET_VIDEO_NAME}"], check=True)
        subprocess.run(["git", "push"], check=True)
        
        print("Success! File wiped permanently from repository.")
    except Exception as e:
        print(f"Git execution failed: {e}")
else:
    print(f"Upload issues hit. Keeping {TARGET_VIDEO_NAME} in repository for safety retry.")

import os
import time
import math
import requests
from moviepy.video.io.VideoFileClip import VideoFileClip
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
import subprocess

# Get secrets from GitHub Actions environment variables
TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

FOLDER_PATH = "./videos"
TEMP_DIR = "./temp_chunks"
TARGET_MAX_SIZE = 49 * 1024 * 1024  # 49 MB

url = f"https://api.telegram.org/bot{TOKEN}/sendVideo"


# Safe console progress tracker
def create_progress_callback(file_name):
    def progress_callback(monitor):
        bytes_sent = monitor.bytes_read
        total_bytes = monitor.len

        percentage = (bytes_sent / total_bytes) * 100
        sent_mb = bytes_sent / (1024 * 1024)
        total_mb = total_bytes / (1024 * 1024)

        print(
            f"\rUploading {file_name}: "
            f"{percentage:.1f}% "
            f"({sent_mb:.1f}/{total_mb:.1f} MB)",
            end="",
            flush=True
        )

    return progress_callback


video_extensions = (".mp4", ".mkv", ".avi", ".mov")


if not os.path.exists(FOLDER_PATH):
    print("Videos folder not found.")
    exit(1)


all_files = [
    f for f in os.listdir(FOLDER_PATH)
    if f.lower().endswith(video_extensions)
]


if not all_files:
    print("No videos found in the folder. Everything has been successfully processed!")
    exit(0)


# Sort numerically so 2.mp4 comes before 10.mp4
try:
    all_files.sort(
        key=lambda x: int(os.path.splitext(x)[0])
    )
except ValueError:
    all_files.sort()


# Select the lowest-numbered remaining video
TARGET_VIDEO_NAME = all_files[0]
INPUT_VIDEO_PATH = os.path.join(
    FOLDER_PATH,
    TARGET_VIDEO_NAME
)


print(f"Found next file to upload: {TARGET_VIDEO_NAME}")

upload_success = True


# Upload video directly to Telegram
with open(INPUT_VIDEO_PATH, "rb") as video_file:

    encoder = MultipartEncoder(
        fields={
            "chat_id": str(CHANNEL_ID),
            "caption": f"Video: {TARGET_VIDEO_NAME}",
            "supports_streaming": "true",
            "video": (
                TARGET_VIDEO_NAME,
                video_file,
                "video/mp4"
            )
        }
    )

    monitor = MultipartEncoderMonitor(
        encoder,
        create_progress_callback(TARGET_VIDEO_NAME)
    )

    try:

        response = requests.post(
            url,
            data=monitor,
            headers={
                "Content-Type": monitor.content_type
            },
            timeout=300
        )

        result = response.json()

        print()

        if result.get("ok"):
            print(
                f"{TARGET_VIDEO_NAME} uploaded successfully!"
            )
        else:
            print(
                f"Telegram refused file: "
                f"{result.get('description')}"
            )

            upload_success = False

    except Exception as e:

        print(
            f"\nNetwork upload exception: {e}"
        )

        upload_success = False


# Delete video from repository ONLY after successful upload
if upload_success:

    try:

        print(
            f"Upload complete. Committing the deletion of "
            f"{TARGET_VIDEO_NAME} back to GitHub..."
        )

        # Git identity
        subprocess.run(
            [
                "git",
                "config",
                "--global",
                "user.name",
                "github-actions[bot]"
            ],
            check=True
        )

        subprocess.run(
            [
                "git",
                "config",
                "--global",
                "user.email",
                "41898282+github-actions[bot]@users.noreply.github.com"
            ],
            check=True
        )

        # Remove uploaded video
        subprocess.run(
            [
                "git",
                "rm",
                INPUT_VIDEO_PATH
            ],
            check=True
        )

        # Commit removal
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f"Automated removal of uploaded video: {TARGET_VIDEO_NAME}"
            ],
            check=True
        )

        # Push change back to GitHub
        subprocess.run(
            ["git", "push"],
            check=True
        )

        print(
            "Success! File wiped permanently from repository."
        )

    except Exception as e:

        print(
            f"Git execution failed: {e}"
        )

else:

    print(
        f"Upload issues hit. Keeping "
        f"{TARGET_VIDEO_NAME} in repository for safety retry."
    )

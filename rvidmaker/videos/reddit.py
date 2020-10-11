"""Implements a reference for videos hosted on Reddit"""

import asyncio
from ffmpeg import FFmpeg
import os
import requests

from rvidmaker.utils import get_random_path
from .interface import VideoRef

_TEMP_DOWNLOAD_DIR = "/tmp/rvidmaker"

if not os.path.exists(_TEMP_DOWNLOAD_DIR):
    os.mkdir(_TEMP_DOWNLOAD_DIR)


class RedditVideoRef(VideoRef):
    """References videos hosted on Reddit"""

    def __init__(self, title, author, video_url, audio_url):
        self.title = title
        self.author = author
        self.video_url = video_url
        self.audio_url = audio_url

    def download(self, output_path):
        """
        Downloads the referenced video.

        Args:
            output_path (str): Path to write the video to. Must have a valid video format extension.
        """
        # Check video extension
        base, ext = os.path.splitext(output_path)
        if ext != "mp4":
            output_path = "{}.mp4".format(base)

        # Download video and audio to temporary files.
        temp_video_path = get_random_path(_TEMP_DOWNLOAD_DIR, "mp4")
        temp_audio_path = get_random_path(_TEMP_DOWNLOAD_DIR, "mp4")
        with open(temp_video_path, "wb") as f:
            req = requests.get(self.video_url)
            # TODO: Check `req.status_code`
            f.write(req.content)
        with open(temp_audio_path, "wb") as f:
            req = requests.get(self.audio_url)
            # TODO: Check `req.status_code`
            f.write(req.content)

        # Combine video and audio
        ffmpeg = (
            FFmpeg()
            .option("y")
            .input(temp_video_path)
            .input(temp_audio_path)
            .output(output_path, {"codec:v": "copy", "codec:a": "aac"})
        )
        loop = asyncio.get_event_loop()
        loop.run_until_complete(ffmpeg.execute())

        # Delete temporary files
        os.remove(temp_video_path)
        os.remove(temp_audio_path)

        return output_path

    def get_title(self):
        return self.title

    def get_author(self):
        return self.author

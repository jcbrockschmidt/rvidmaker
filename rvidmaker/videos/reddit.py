"""Implements a reference for videos hosted on Reddit"""

import ffmpeg
import os
import requests
import shutil

from rvidmaker.utils import get_random_path
from .interface import DownloadException, VideoRef

_TEMP_DOWNLOAD_DIR = "/tmp/rvidmaker"

if not os.path.exists(_TEMP_DOWNLOAD_DIR):
    os.mkdir(_TEMP_DOWNLOAD_DIR)


class RedditVideoRef(VideoRef):
    """References videos hosted on Reddit"""

    def __init__(self, title, author, video_url, audio_url=None):
        """
        Args:
            title (str): Title of the video.
            author (str): Author of the video.
            video_url (str): Remote URL for video.
            audio_url (str): Remote URL for audio. `None` if there is no audio.
        """
        self.title = title
        self.author = author
        self.video_url = video_url
        self.audio_url = audio_url

    def download(self, output_path):
        # Check video extension
        base, ext = os.path.splitext(output_path)
        if ext != "mp4":
            output_path = "{}.mp4".format(base)

        # Download video and audio to temporary files.
        temp_video_path = get_random_path(_TEMP_DOWNLOAD_DIR, "mp4")
        # TODO: Download video and audio asynchronously
        with open(temp_video_path, "wb") as f:
            req = requests.get(self.video_url)
            if req.status_code != 200:
                raise DownloadException(
                    "Failed to download video from {}: {} response".format(
                        self.video_url, req.status_code
                    )
                )
            f.write(req.content)
        if self.audio_url is not None:
            temp_audio_path = get_random_path(_TEMP_DOWNLOAD_DIR, "mp4")
            with open(temp_audio_path, "wb") as f:
                req = requests.get(self.audio_url)
                if req.status_code != 200:
                    raise DownloadException(
                        "Failed to download video from {}: {} response".format(
                            self.audio_url, req.status_code
                        )
                    )
                f.write(req.content)

            # Combine video and audio
            video = ffmpeg.input(temp_video_path)
            audio = ffmpeg.input(temp_audio_path)
            try:
                ffmpeg.concat(video, audio, v=1, a=1).output(output_path).run(
                    quiet=True, overwrite_output=True
                )
            except ffmpeg.Error:
                if os.path.exists(output_path):
                    os.remove(output_path)
                print("ERROR:", output_path)  # DEBUG
                raise DownloadException("Failed to combine video and audio with FFmpeg")
            finally:
                # Delete temporary files
                os.remove(temp_video_path)
                os.remove(temp_audio_path)
        else:
            shutil.move(temp_video_path, output_path)

        return output_path

    def get_title(self):
        return self.title

    def get_author(self):
        return self.author

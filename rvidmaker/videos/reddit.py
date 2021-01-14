"""Implements a reference for videos hosted on Reddit"""

import ffmpeg
import os
import requests
import shutil
import tempfile

from rvidmaker.utils import get_random_path
from .interface import DownloadException, VideoRef


class RedditVideoRef(VideoRef):
    """
    References videos hosted on Reddit.

    Attributes:
        title (str): Title of the video.
        author (str): Author of the video.
        duration (float): Duration of the video. None if not known.
    """

    def __init__(self, title, author, video_url, audio_url=None, duration=None):
        """
        Args:
            title (str): Title of the video.
            author (str): Author of the video.
            video_url (str): Remote URL for video.
            audio_url (str): Remote URL for audio. None if there is no audio.
            duration (float): Duration of the video if known, and None otherwise.
        """
        self._title = title
        self._author = author
        self._video_url = video_url
        self._audio_url = audio_url
        self._duration = duration

    def download(self, output_path):
        """
        Downloads the video to disk.

        Args:
            output_path (str): Path to write video to. The extension may be changed.

        Returns:
            str: Path the video is written to. Extension may differ from `output_path`.
        """
        # Check video extension
        base, ext = os.path.splitext(output_path)
        if ext != "mp4":
            output_path = "{}.mp4".format(base)

        # Download video and audio to temporary files.
        temp_video_file = tempfile.NamedTemporaryFile(suffix=".mp4")
        print("temp video name:", temp_video_file.name)  # DEBUG
        # TODO: Download video and audio asynchronously
        video_req = requests.get(self._video_url)
        if video_req.status_code != 200:
            raise DownloadException(
                "Failed to download video from {}: {} response".format(
                    self._video_url, video_req.status_code
                )
            )
        temp_video_file.write(video_req.content)
        if self._audio_url is not None:
            temp_audio_file = tempfile.NamedTemporaryFile(suffix=".mp4")
            print("temp audio name:", temp_audio_file.name)  # DEBUG
            audio_req = requests.get(self._audio_url)
            if audio_req.status_code != 200:
                raise DownloadException(
                    "Failed to download video from {}: {} response".format(
                        self._audio_url, audio_req.status_code
                    )
                )
            temp_audio_file.write(audio_req.content)

            # Combine video and audio
            video = ffmpeg.input(temp_video_file.name)
            audio = ffmpeg.input(temp_audio_file.name)
            try:
                ffmpeg.concat(video, audio, v=1, a=1).output(output_path).run(
                    quiet=True, overwrite_output=True
                )
            except ffmpeg.Error:
                if os.path.exists(output_path):
                    os.remove(output_path)
                raise DownloadException("Failed to combine video and audio with FFmpeg")
            finally:
                # Delete temporary files
                temp_video_file.close()
                temp_audio_file.close()
        else:
            shutil.move(temp_video_file.name, output_path)
            temp_video_file.close()

        return output_path

    @property
    def title(self):
        return self._title

    @property
    def author(self):
        return self._author

    @property
    def duration(self):
        return self._duration

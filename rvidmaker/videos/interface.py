"""Provides an interface for references to remote videos"""


class DownloadException(Exception):
    """Raised when downloading a video fails"""


class VideoRef:
    """
    References a remote video.

    Attributes:
        title (str): Title of the video.
        author (str): Author of the video.
        duration (float): Duration of a video in seconds. None if the duration is not known.
    """

    def download(self, output_path):
        """
        Downloads the referenced video.

        Args:
            output_path (str): Path to write the video to. If a valid extension is not provided it
                will be appended.

        Returns:
            str/None: Path video is written to. Extension may differ from `output_path`.
                `None` on failure.

        Raises:
            DownloadException: If something fails.
        """
        raise NotImplementedError

    @property
    def thumb(self):
        raise NotImplementedError

    @property
    def author(self):
        raise NotImplementedError

    @property
    def duration(self):
        return None

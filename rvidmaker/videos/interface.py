"""Provides an interface for references to remote videos"""


class DownloadException(Exception):
    """Raised when downloading a video fails"""


class VideoRef:
    """References a remote video"""

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

    def get_title(self):
        """
        Returns:
            str: The title of the video.
        """
        raise NotImplementedError

    def get_author(self):
        """
        Returns:
            str: The author of the video.
        """
        raise NotImplementedError

    def get_duration(self):
        """
        Returns:
           float: The duration of a video in seconds. None if the duration is not known.
        """
        return None

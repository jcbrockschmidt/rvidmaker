"""Provides a payload that can be used with any uploader"""

import os
import toml
from toml import TomlDecodeError

from rvidmaker.utils import toml_get_and_check, TomlGetCheckException


class PayloadEncodeException(Exception):
    """Raised when encoding fails"""


class PayloadDecodeException(Exception):
    """Raised when decoding fails"""


class Payload:
    """
    Stores metadata for a video for use by uploaders.

    Attributes:
        video (str): Path to the video file.
        thumb (str): Path to the thumbnail image.
        title (str): Title of the video.
        desc (str): Description for the video.
        tags (:obj:`list` of :obj:`str`): Tags describing the video.
    """

    _KEYS_TYPES = (
        ("video", str, None),
        ("thumbnail", str, None),
        ("title", str, None),
        ("description", str, None),
        ("tags", list, str),
    )

    def __init__(self):
        self._video_path = ""
        self._thumb_path = ""
        self._title = ""
        self._desc = ""
        self._tags = tuple()

    @property
    def video(self):
        return self._video_path

    @video.setter
    def video(self, value):
        if not isinstance(value, str):
            raise TypeError("video must be a str")
        self._video_path = value

    @property
    def thumb(self):
        return self._thumb_path

    @thumb.setter
    def thumb(self, value):
        if not isinstance(value, str):
            raise TypeError("thumb must be a str")
        self._thumb_path = value

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        if not isinstance(value, str):
            raise TypeError("title must be a str")
        self._title = value

    @property
    def desc(self):
        return self._desc

    @desc.setter
    def desc(self, value):
        if not isinstance(value, str):
            raise TypeError("desc must be a str")
        self._desc = value

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, value):
        if not isinstance(value, (list, tuple)):
            raise TypeError("tags must be a list or tuple")
        for tag in value:
            if type(tag) != str:
                raise TypeError("tags must contain only strings")
        self._tags = tuple(value)

    def loads(s):
        """
        Load a payload from a string.

        Args:
            s (str): String to be parsed.

        Returns:
            Payload: The loaded payload.

        Raises:
            PayloadDecodeException: If decoding the payload fails.
        """
        try:
            data = toml.loads(s)
        except TomlDecodeError as e:
            raise PayloadDecodeException("Failed to decode payload: {}".format(e))
        payload = Payload()
        try:
            payload.video = toml_get_and_check(data, "video", str, required=True)
            payload.thumb = toml_get_and_check(data, "thumbnail", str, required=True)
            payload.title = toml_get_and_check(data, "title", str, required=True)
            payload.desc = toml_get_and_check(data, "description", str, required=True)
            payload.tags = toml_get_and_check(data, "tags", list, str, required=True)
        except TomlGetCheckException as e:
            raise PayloadDecodeException("Failed to decode payload: {}".format(e))
        return payload

    def load(path):
        """
        Load a payload from a file.

        Args:
            path (str): Path to the file to open.

        Returns:
            Payload: The loaded payload.

        Raises:
            FileNotFoundError: If the path does not point to a file.
            TypeError: If `path` is not of the proper type.
            PayloadDecodeException: If decoding the payload fails.
        """
        with open(path, "r") as f:
            return Payload.loads(f.read())

    def dumps(self):
        """
        Encodes the payload as a string.

        Return:
            str: The encoded payload as a string.

        Raises:
            PayloadEncodeException: If encoding the payload fails.
        """
        try:
            data = {
                "video": self.video,
                "thumbnail": self.thumb,
                "title": self.title,
                "description": self.desc,
                "tags": self.tags,
            }
            return toml.dumps(data)
        except (TypeError, ValueError) as e:
            raise PayloadEncodeException("Failed to encode as TOML: {}".format(e))

    def dump(self, path):
        """
        Encodes the payload as a string and writes to a file.

        Args:
            path (str): Path to the file to open.

        Returns:
            Payload: The loaded payload.

        Raises:
            FileNotFoundError: If the path does not point to a file.
            TypeError: If `path` is not of the proper type.
            PayloadEncodeException: If encoding the payload fails.
        """
        with open(path, "w") as f:
            f.write(self.dumps())

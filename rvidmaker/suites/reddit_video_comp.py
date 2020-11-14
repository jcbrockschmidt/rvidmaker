"""Provides a suite for generating compilations of videos from subreddits"""

import os
import toml
from toml import TomlDecodeError

from .interface import Suite, SuiteConfigException, SuiteGenerateException
from .utils import get_and_check, GetCheckTypeException


class RedditVideoCompSuite(Suite):
    """Suite for generating compilations of videos from subreddits"""

    # TODO: Describe fields for profile TOML file in docstring.

    def __init__(self):
        self.configured = False

    def config(self, profile_path, censor_path=None, block_path=None):
        if not os.path.isfile(profile_path):
            raise SuiteConfigException('"{}" is not a file'.format(profile_path))
        if censor_path is not None and not os.path.isfile(censor_path):
            raise SuiteConfigException('"{}" is not a file'.format(censor_path))
        if block_path is not None and not os.path.isfile(block_path):
            raise SuiteConfigException('"{}" is not a file'.format(block_path))

        try:
            data = toml.load(profile_path)
        except TomlDecodeError as e:
            raise SuiteConfigException('Failed to decode "{}"'.format(profile_path))

        # Check profile fields.
        if ("reddit" not in data) or ("compilation" not in data["reddit"]):
            raise SuiteConfigException(
                '"{}" has no "reddit.compilation" section'.format(profile_path)
            )
        profile = data["reddit"]["compilation"]
        if "subreddit" not in profile:
            raise SuiteConfigException(
                'Profile has no "subreddit" field'.format(profile_path)
            )

        try:
            self._subreddit = get_and_check(profile, "subreddit", str)
            self._min_score = get_and_check(profile, "min_score", int)
            self._min_clip_dur = get_and_check(profile, "min_clip_duration", int)
            self._max_clip_dur = get_and_check(profile, "max_clip_duration", int)
            self._clip_limit = get_and_check(profile, "clip_limit", int, default=50)
            self._res = get_and_check(
                profile, "resolution", list, int, default=[1920, 1080]
            )
            self._censor_video = get_and_check(
                profile, "censor_video", bool, default=False
            )
            self._censor_metadata = get_and_check(
                profile, "censor_metadata", bool, default=False
            )
            self._default_tags = get_and_check(profile, "default_tags", list, str)
        except GetCheckTypeException as e:
            raise SuiteConfigException("Invalid TOML profile: {}".format(str(e)))

        if self._censor_video and censor_path is None:
            raise SuiteConfigException("Profile requires a censor for the video")
        if self._censor_metadata and block_path is None:
            raise SuiteConfigException("Profile requires a censor for metadata")

        self.configured = True

    def generate(self, output_dir):
        if not self.configured:
            raise SuiteGenerateException("Suite not configured yet")
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except e:
                raise SuiteGenerateException(
                    'Failed to create output directory "{}"'.format(output_dir)
                )
        elif not os.path.isdir(output_dir):
            raise SuiteGenerateException('"{}" is not a directory'.format(output_dir))
        raise NotImplementedError

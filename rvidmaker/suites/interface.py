"""Provides an interface for video generating suites"""


class SuiteConfigException(Exception):
    """Raised when configuring a suite failed"""


class SuiteGenerateException(Exception):
    """Raised when generating a video with a suite fails"""


class Suite:
    """Interface for video generating suites"""

    def config(self, profile_path, censor=None, blocker=None):
        """
        Configures the suite.

        Args:
            profile_path (str): Path to a TOML file containing profile information.
            censor_path (better_profanity.Profanity): File containing words and phrases to censor
                in the video. `None` to not censor the video.
            block_path (better_profanity.Profanity): File containing words and phrases to exclude
                from metadata. `None` to not exclude anything.

        Raises:
            SuiteConfigException: If configuration fails.
        """
        raise NotImplementedError

    def generate(self, output_dir):
        """
        Args:
            output_dir: Directory to output generated files to.

        Raises:
            SuiteConfigException: If generation fails.
        """
        raise NotImplementedError

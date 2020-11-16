"""Provides a suite for generating compilations of videos from subreddits"""

from datetime import timedelta
import os
import toml
from toml import TomlDecodeError

from rvidmaker.editor import VideoCompiler
from rvidmaker.readers.reddit import RedditReader
from rvidmaker.thumbnails import create_split_thumbnail
from rvidmaker.utils import extract_tags, get_random_path, shorten_title
from .interface import Suite, SuiteConfigException, SuiteGenerateException
from .utils import get_and_check, GetCheckTypeException

# TODO: Move tag limits to YouTubeUploader
# Maximum number of characters for a single tag on YouTube.
YT_TAG_MAX_CHARS = 30
# Maximum number of characters for YouTube tags.
YT_TAGS_MAX_TOTAL_CHAR = 500
# Maximum number of articles to scrape in a batch.
ARTICLE_LIMIT = 100
# Maximum character length of the title in the thumbnail.
MAX_TITLE_LEN = 20
# Directory to temporarily download videos from a subreddit to.
TEMP_DIR = "/tmp/rvidmaker/reddit-video-comp/"
# Valid time frames in the TOML profile file.
VALID_TIME_FRAMES = ("all", "day", "hour", "month", "week", "year")

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)


class RedditVideoCompSuite(Suite):
    """Suite for generating compilations of videos from subreddits"""

    # TODO: Describe fields for profile TOML file in docstring.

    def __init__(self):
        self.configured = False

    def config(self, profile_path, censor=None, blocker=None):
        if not os.path.isfile(profile_path):
            raise SuiteConfigException('"{}" is not a file'.format(profile_path))

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
            self._time_frame = get_and_check(profile, "time_frame", str, default="week")
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
            self._default_tags = set(
                get_and_check(profile, "default_tags", list, str, default=list())
            )
        except GetCheckTypeException as e:
            raise SuiteConfigException("Invalid TOML profile: {}".format(str(e)))

        if self._time_frame not in VALID_TIME_FRAMES:
            raise SuiteConfigException(
                "Invalid TOML profile: time_frame must be one of {}".format(
                    VALID_TIME_FRAMES
                )
            )

        if self._censor_video and censor is None:
            raise SuiteConfigException("Profile requires a censor for the video")
        if self._censor_metadata and blocker is None:
            raise SuiteConfigException("Profile requires a censor for metadata")

        if self._censor_video:
            self._censor = censor
        if self._censor_metadata:
            self._blocker = blocker

        self.configured = True

    def _get_videos_from_reddit(self):
        """
        Gets videos from a subreddit.

        Returns:
            list: List of `rvidmaker.videos.VideoRef` in ascending order of score.
        """
        reader = RedditReader()
        articles = reader.get_top_articles(
            self._subreddit,
            time_filter=self._time_frame,
            limit=ARTICLE_LIMIT,
            min_score=self._min_score,
        )
        videos = []
        for art in articles:
            if not art.nsfw and art.has_video(
                min_duration=self._min_clip_dur,
                max_duration=self._max_clip_dur,
                include_youtube=False,
            ):
                videos.append(art.get_video())
                if self._clip_limit is not None:
                    if len(videos) >= self._clip_limit:
                        break
        return videos

    def _make_thumbnail(self, vid, title, output_path):
        """
        Creates a thumbnail from a single video.

        Args:
            vid (rvidmaker.videos.VideoRef): Video to create thumbnail from.
            title (str): Title to render on thumbnail.
            output_path (str): Path to write the thumbnail to.
        """
        short_title = shorten_title(title, MAX_TITLE_LEN)
        temp_vid_dl = vid.download(get_random_path(TEMP_DIR))
        thumb = create_split_thumbnail(temp_vid_dl, short_title)
        thumb.save(output_path)
        os.remove(temp_vid_dl)

    def _make_description(self, message, manifest):
        """
        Creates a description for a compilation video.

        Args:
            message (str): Message to display at the top of the description.
            manifest (rvidmaker.editor.videocomp.Manifest): Manifest of videos in the compilation.
        """
        if self._censor_video:
            process = lambda s: self._censor.censor(s)
        else:
            process = lambda s: s
        desc_lines = [process(message), ""]
        for entry in manifest:
            title = process(entry.video.get_title())
            timestamp = timedelta(seconds=int(entry.timestamp))
            line = "{ts} - {title}".format(ts=timestamp, title=title)
            desc_lines.append(line)
        desc_lines.append("")
        desc = "\n".join(desc_lines)
        return desc

    def _make_tags(self, videos):
        """
        Creates tags using the default tags and video titles.

        Args:
            videos (list): List of `rvidmaker.videos.VideoRef` to extract tags from.

        Returns:
            set: Set of tags as `str`s.
        """
        tags = self._default_tags.copy()
        tags_len = sum([len(t) for t in tags])
        chars_left = YT_TAGS_MAX_TOTAL_CHAR - tags_len
        blocklist = self._censor_metadata and self._blocker or None
        extra_tags = extract_tags(
            videos,
            blocklist=blocklist,
            max_tag_len=YT_TAG_MAX_CHARS,
            max_total_chars=chars_left,
        )
        tags.update(extra_tags)
        return tags

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

        vid_path = os.path.join(output_dir, "video.mp4")
        desc_path = os.path.join(output_dir, "description.txt")
        tags_path = os.path.join(output_dir, "tags.txt")
        thumb_path = os.path.join(output_dir, "thumbnail.png")

        print("Scaping subreddit r/{} for videos...".format(self._subreddit))
        videos = self._get_videos_from_reddit()
        if len(videos) < 2:
            print("Not enough videos gathered for a compilation")
            return

        print("Rendering compilation of {} videos...".format(len(videos)))
        censor = self._censor_video and self._censor or None
        compiler = VideoCompiler(censor=censor)
        for v in videos:
            compiler.add_video(v)
        manifest = compiler.render_video(self._res, vid_path)
        used_videos = [entry.video for entry in manifest]

        print("Creating description...")
        desc = self._make_description(
            "Subscribe for more video compilations!",
            manifest,
        )
        with open(desc_path, "w") as f:
            f.write(desc)

        print("Creating tags...")
        tags = self._make_tags(used_videos)
        with open(tags_path, "w") as f:
            f.write(",".join(tags))

        # Create our thumbnail using the top-scored video with no words or phrases in the blocklist.
        print("Creating thumbnail...")
        thumb_made = False
        for v in used_videos:
            if self._censor_metadata:
                if self._blocker.contains_profanity(v.get_title()):
                    continue
            print('Using "{}" for thumbnail...'.format(v.get_title()))
            self._make_thumbnail(v, v.get_title(), thumb_path)
            thumb_made = True
            break
        # No video had a safe title. Use a default title on top of a thumbnail of the first video.
        if not thumb_made:
            print("Using default title for thumbnail...")
            self._make_thumbnail(used_videos[0], self._subreddit, thumb_path)

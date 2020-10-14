#!/usr/bin/env python3

"""Creates a compilation of top videos from r/dankvideos"""

from better_profanity import Profanity
from datetime import timedelta
import os
from rvidmaker.editor import VideoCompiler
from rvidmaker.readers.reddit import RedditReader
from rvidmaker.thumbnails import create_split_thumbnail
from rvidmaker.utils import extract_tags, shorten_title

SUBREDDIT = "dankvideos"
OUTPUT_DIR = "output"
VID_PATH = os.path.join(OUTPUT_DIR, "video.mp4")
DESC_PATH = os.path.join(OUTPUT_DIR, "description.txt")
TAGS_PATH = os.path.join(OUTPUT_DIR, "tags.txt")
THUMB_PATH = os.path.join(OUTPUT_DIR, "thumbnail.png")
# Path to text file containing words to censor.
CENSOR_PATH = "censor.txt"
# Path to text file containing words and phrases to avoid using in titles and tags. This is
# included as there may not be a 1:1 overlap with words and phrases we want to censor and words
# that a video hosting site or search engines may flag as undesirable.
BLOCKLIST_PATH = "blocklist.txt"


MIN_SCORE = 100
MAX_DURATION = 40
MIN_DURATION = 2
LIMIT = 100
SIZE = (1920, 1080)
MAX_VIDEOS = 50
MAX_TITLE_LEN = 20
DEF_TAGS = {
    "reddit",
    "dankvideos",
    "dank videos",
    "dank memes",
    "compilation",
    "reddit compilation",
    "funny meme compilation",
    "videos i found on reddit",
}
# Maximum number of characters for a single tag on YouTube.
YT_TAG_MAX_CHARS = 30
# Maximum number of characters for YouTube tags.
YT_TAGS_MAX_TOTAL_CHAR = 500


def get_videos_from_reddit(subreddit, max_videos=None):
    """
    Gets videos from a subreddit.

    Args:
        subreddit (str): Subreddit to get articles from.
        max_videos (int): Maximum number of videos to gather. None if no maximum.

    Returns:
        list: List of `rvidmaker.videos.VideoRef` in ascending order of score.
    """
    reader = RedditReader()
    articles = reader.get_top_articles(
        SUBREDDIT, time_filter="week", limit=LIMIT, min_score=MIN_SCORE
    )
    videos = []
    for art in articles:
        if not art.nsfw and art.has_video(
            min_duration=MIN_DURATION, max_duration=MAX_DURATION, include_youtube=False
        ):
            videos.append(art.get_video())
            if not max_videos is None:
                if len(videos) >= max_videos:
                    break
    return videos


def make_thumbnail(vid, title, output_path):
    """
    Creates a thumbnail from a single video.

    Args:
        vid (rvidmaker.videos.VideoRef): Video to create thumbnail from.
        title (str): Title to render on thumbnail.
        output_path (str): Path to write the thumbnail to.
    """
    short_title = shorten_title(title, MAX_TITLE_LEN)
    temp_vid_dl = vid.download(os.path.join(OUTPUT_DIR, "temp-video"))
    thumb = create_split_thumbnail(temp_vid_dl, short_title)
    thumb.save(output_path)
    os.remove(temp_vid_dl)


def make_description(message, manifest, censor):
    """
    Creates a description for a compilation video.

    Args:
        message (str): Message to display at the top of the description.
        manifest (rvidmaker.editor.videocomp.Manifest): Manifest of videos in the compilation.
        censor (better_profanity.Profanity): Used to censor words in the description.
    """
    desc_lines = [censor.censor(message), ""]
    for entry in manifest:
        title = censor.censor(entry.video.get_title())
        timestamp = timedelta(seconds=int(entry.timestamp))
        line = "{ts} - {title}".format(ts=timestamp, title=title)
        desc_lines.append(line)
    desc_lines.append("")
    desc = "\n".join(desc_lines)
    return desc


def make_tags(videos, blocklist, def_tags={}):
    """
    Creates tags using the default tags and video titles.

    Args:
        videos (list): List of `rvidmaker.videos.VideoRef` to extract tags from.
        blocklist (better_profanity.Profanity): Filters out undesirable tags.
        def_tags (set): Set of tags to include before generating tags from videos.

    Returns:
        set: Set of tags as `str`s.
    """
    tags = def_tags.copy()
    tags_len = sum([len(t) for t in tags])
    chars_left = YT_TAGS_MAX_TOTAL_CHAR - tags_len
    extra_tags = extract_tags(
        videos,
        blocklist=blocklist,
        max_tag_len=YT_TAG_MAX_CHARS,
        max_total_chars=chars_left,
    )
    tags.update(extra_tags)
    return tags


def main():
    # Load filters.
    print("Loading censor and blocklist...")
    censor = Profanity()
    censor.load_censor_words_from_file(CENSOR_PATH)
    blocklist = Profanity()
    blocklist.load_censor_words_from_file(BLOCKLIST_PATH)

    print("Scaping subreddit r/{} for videos...".format(SUBREDDIT))
    videos = get_videos_from_reddit(SUBREDDIT, MAX_VIDEOS)
    if len(videos) < 2:
        print("Not enough videos gathered for a compilation")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

    print("Rendering compilation of {} videos...".format(len(videos)))
    compiler = VideoCompiler(censor=censor)
    for v in videos:
        compiler.add_video(v)
    manifest = compiler.render_video(SIZE, VID_PATH)

    print("Creating description...")
    desc = make_description(
        "Subscribe for more video compilations!", manifest, blocklist
    )
    with open(DESC_PATH, "w") as f:
        f.write(desc)

    print("Creating tags...")
    tags = make_tags(videos, blocklist, def_tags=DEF_TAGS)
    with open(TAGS_PATH, "w") as f:
        f.write(",".join(tags))

    # Create our thumbnail using the top-scored video with no words or phrases in the blocklist.
    print("Creating thumbnail...")
    thumb_made = False
    for v in videos:
        if blocklist.contains_profanity(v.get_title()):
            continue
        print('Using "{}" for thumbnail...'.format(v.get_title()))
        make_thumbnail(v, v.get_title(), THUMB_PATH)
        thumb_made = True
        break
    # No video had a safe title. Use a default title on top of a thumbnail of the first video.
    if not thumb_made:
        print("Using default title for thumbnail...")
        def_title = SUBREDDIT
        make_thumbnail(videos[0], def_title, THUMB_PATH)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

"""Creates a compilation of top videos from r/dankvideos"""

import os
from rvidmaker.editor import VideoCompiler
from rvidmaker.readers.reddit import RedditReader
from rvidmaker.thumbnails import create_split_thumbnail
from rvidmaker.utils import shorten_title

SUBREDDIT = 'dankvideos'
OUTPUT_DIR = 'output'
VID_PATH = os.path.join(OUTPUT_DIR, 'video.mp4')
THUMB_PATH = os.path.join(OUTPUT_DIR, 'thumbnail.png')

MIN_SCORE = 100
MAX_DURATION = 40
MIN_DURATION = 2
LIMIT = 100
SIZE = (1920, 1080)
MAX_VIDEOS = 50
MAX_TITLE_LEN = 20

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
    articles = reader.get_top_articles(SUBREDDIT, time_filter='week', limit=LIMIT, min_score=MIN_SCORE)
    videos = []
    for art in articles:
        if not art.nsfw and art.has_video(min_duration=MIN_DURATION, max_duration=MAX_DURATION, include_youtube=False):
            videos.append(art.get_video())
            if not max_videos is None:
                if len(videos) >= max_videos:
                    break
    return videos

def make_thumbnail(vid, output_path):
    """
    Creates a thumbnail from a single video.

    Args:
        vid (rvidmaker.videos.VideoRef): Video to create thumbnail from.
        output_path (str): Path to write the thumbnail to.
    """
    short_title = shorten_title(vid.get_title(), MAX_TITLE_LEN)
    temp_vid_dl = vid.download(os.path.join(OUTPUT_DIR, 'temp-video'))
    thumb = create_split_thumbnail(temp_vid_dl, short_title)
    thumb.save(output_path)
    os.remove(temp_vid_dl)

def main():
    videos = get_videos_from_reddit(SUBREDDIT, MAX_VIDEOS)
    if len(videos) < 2:
        print('Not enough videos gathered for a compilation')
        return

    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

    print('Rendering compilation of {} videos...'.format(len(videos)))
    compiler = VideoCompiler()
    for v in videos:
        compiler.add_video(v)
    compiler.render_video(SIZE, VID_PATH)

    print("Creating thumbnail...")
    # We use the top-scored video to create our thumbnail.
    make_thumbnail(videos[0], THUMB_PATH)

if __name__ == '__main__':
    main()

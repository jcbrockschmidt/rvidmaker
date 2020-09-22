#!/usr/bin/env python3

"""Creates a compilation of top videos from r/dankvideos"""

import rvidmaker
from rvidmaker.editor import VideoCompiler

SUBREDDIT = 'dankvideos'
OUTPUT = 'example.mp4'

MIN_SCORE = 100
MIN_AGE = 0
MAX_DURATION = 40
MIN_DURATION = 2
LIMIT = 100
SIZE = (1920, 1080)

if __name__ == '__main__':
    reader = rvidmaker.readers.reddit.RedditReader()
    articles = reader.get_top_articles(SUBREDDIT, time_filter='week', limit=LIMIT, min_score=MIN_SCORE)
    vid_num = 0
    videos = []
    compiler = VideoCompiler()
    for art in articles:
        if not art.nsfw and art.has_video(max_duration=MAX_DURATION, include_youtube=False):
            compiler.add_video(art.get_video())
    vid_count = compiler.get_video_count()
    if vid_count < 2:
        print('Not enough videos gathered for a compilation')
    else:
        print('Rendering compilation of {} videos...'.format(compiler.get_video_count()))
        compiler.render_video(SIZE, OUTPUT)

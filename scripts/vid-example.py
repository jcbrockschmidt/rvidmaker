#!/usr/bin/env python3

"""Creates a compilation of top videos from r/dankvideos"""

from glob import glob
from moviepy.editor import afx, CompositeVideoClip, concatenate_videoclips, TextClip, VideoFileClip
import os
import rvidmaker

SUBREDDIT = 'dankvideos'
OUTPUT = 'example.mp4'

MIN_SCORE = 100
MIN_AGE = 0
MAX_DURATION = 40
MIN_DURATION = 2 # TODO: Use this
LIMIT = 100
BACK_COLOR = (0, 0, 0)
SIZE = (1920, 1080)
AUDIO_LEVEL = 0.7
OUTPUT_DIR = '.downloaded'

if __name__ == '__main__':
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
    reader = rvidmaker.readers.reddit.RedditReader()
    articles = reader.get_top_articles(SUBREDDIT, time_filter='week', limit=LIMIT, min_score=MIN_SCORE)
    vid_num = 0
    videos = []
    for art in articles:
        if not art.nsfw and art.has_video(max_duration=MAX_DURATION, include_youtube=False):
            output_path = os.path.join(OUTPUT_DIR, 'vid{:04d}.mp4'.format(vid_num))
            print('Downloading "{}" ({}) to {}...'.format(art.title, art.score, output_path))
            try:
                vid_ref = art.get_video()
                vid_ref.download(output_path)
                videos.append((vid_ref, output_path))
                vid_num += 1
            except:
                print('WARNING: Failed to download "{}"'.format(art.title))
                for path in glob('{}.*'.format(output_path)):
                    os.remove(path)

    clips = []
    w, h = SIZE
    for vid_ref, path in videos:
        title = vid_ref.get_title()
        author = vid_ref.get_author()
        clip = VideoFileClip(path)

        # Adjust audio levels
        audio = clip.audio.fx(afx.audio_normalize)
        max_volume = clip.audio.max_volume()
        volume_mult = AUDIO_LEVEL / max_volume
        clip.set_audio(audio)
        clip = clip.fx(afx.volumex, volume_mult)

        # Resize video
        cw, ch = clip.size
        size_mult = min(w / cw, h / ch)
        new_size = (cw * size_mult, ch * size_mult)
        clip = clip.resize(newsize=new_size).on_color(size=SIZE, color=BACK_COLOR, pos='center')
        
        # Add text
        title_clip = TextClip(title, font='IBM Plex Sans', fontsize=60, color='white')
        title_clip = title_clip.set_position((10, 10)).set_duration(clip.duration)
        title_clip_shadow = TextClip(title, font='IBM Plex Sans', fontsize=60, color='black')
        title_clip_shadow = title_clip_shadow.set_position((12, 12)).set_duration(clip.duration)
        author_text = 'u/{}'.format(author)
        author_clip = TextClip(author_text, font='IBM Plex Sans', fontsize=40, color='grey')
        author_clip = author_clip.set_position((40, 75)).set_duration(clip.duration)

        clip = CompositeVideoClip(
            [
                clip,
                title_clip_shadow,
                title_clip,
                author_clip
            ],
            size=SIZE
        )

        clips.append(clip)
    final = concatenate_videoclips(clips)
    final.write_videofile(OUTPUT)

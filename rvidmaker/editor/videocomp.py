"""Creates a compilation of video clips"""

from glob import glob
from moviepy.editor import afx, CompositeVideoClip, concatenate_videoclips, TextClip, VideoFileClip
import os
from shutil import rmtree

# Temporary directory for storing downloaded videos.
_DOWNLOAD_DIR = '.downloaded'


class NotEnoughVideos(Exception):
    """Raised when there are not enough videos for a compilation"""


class VideoCompiler:
    """Creates a compilation of video clips"""

    def __init__(self, censor):
        """
        Args:
            censor (better_profanity.Profanity): Used to censor undesirable words in rendered text.
                None to not censor words.
        """
        self._videos = []
        self._censor = censor

    def add_video(self, video):
        """
        Adds a video to the compilation in a first-in-first-out order.

        Args:
            video (VideoRef): Video to add to the compilation.
        """
        self._videos.append(video)

    def get_video_count(self):
        """
        Returns:
           int: Number of videos added by `add_video`, ready to be compiled.
        """
        return len(self._videos)

    def render_video(self, res, output_path, audio_level=0.7, bg_color=(0, 0, 0)):
        """
        Renders all added videos into a complete compilation.

        Args:
            res (int, int): Width and height of video.
            output_path (str): Path to write video to.
            audio_level (float): Audio level to normalize all videos around, (0, 1].
            bg_color (int, int, int): Color of background as RGB, [0, 255].

        Raises:
            NotEnoughVideos: There are fewer than two videos.
        """
        if self.get_video_count() < 2:
            raise NotEnoughVideos

        # Download videos.
        if not os.path.exists(_DOWNLOAD_DIR):
            os.mkdir(_DOWNLOAD_DIR)
        vid_num = 0
        dl = []
        for v in self._videos:
            dl_path = os.path.join(_DOWNLOAD_DIR, 'vid{:04d}'.format(vid_num))
            try:
                print('Downloading "{}"...'.format(v.title))
                actual_dl_path = v.download(dl_path)
                dl.append((v, actual_dl_path))
                vid_num += 1
            except:
                # TODO: Handle deleting in the download function itself
                print('WARNING: Failed to download "{}"'.format(v.title))
                for path in glob('{}.*'.format(dl_path)):
                    os.remove(path)

        # Load all clips.
        clips = []
        w, h = res
        for v, path in dl:
            title = v.get_title()
            author = v.get_author()
            if self._censor is not None:
                title = self._censor.censor(title)
                author = self._censor.censor(author)
            clip = VideoFileClip(path)

            # Adjust audio levels.
            if clip.audio.max_volume() > 0:
                audio = clip.audio.fx(afx.audio_normalize)
                max_volume = clip.audio.max_volume()
                volume_mult = audio_level / max_volume
                clip.set_audio(audio)
                clip = clip.fx(afx.volumex, volume_mult)

            # Resize video.
            cw, ch = clip.size
            size_mult = min(w / cw, h / ch)
            new_size = (cw * size_mult, ch * size_mult)
            clip = clip.resize(newsize=new_size).on_color(size=res, color=bg_color, pos='center')

            # Add text.
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
                size=res
            )
            clips.append(clip)

        final = concatenate_videoclips(clips)
        final.write_videofile(output_path)

        # Delete all downloaded videos.
        rmtree(_DOWNLOAD_DIR)

"""Implements function for creating a split thumbnail of a single video"""

from moviepy.editor import afx, CompositeVideoClip, concatenate_videoclips, TextClip, VideoFileClip
from PIL import Image

# Size of a thumbnail.
SIZE = (1280, 720)

def _make_pane(img, size):
    """
    Crops and resizes and image to half the width of the desired resolution

    Args:
        img (PIL.Image): Image to modify.
        size (int, int): Resolution of a full image.
    """
    w, h = img.size
    sw, sh = int(size[0] / 2), size[1]
    ratio = w / h
    sratio = sw / sh

    # Crop and resize around center.
    if ratio > sratio:
        w2 = sw * h / sh
        trim = int((w - w2) / 2)
        box = (trim, 0, w - trim, h)
    else:
        h2 = sh * w / sw
        trim = int((h - h2) / 2)
        box = (0, trim, w, h - trim)
    pane = img.resize((sw, sh), box=box)
    return pane

def create_split_thumbnail(video_path):
    """
    Creates a split thumbnail from a single video. A frame early in the video is placed next to a
    frame later in the video.

    Args:
        video_path (str): Path to a video to generate thumbnail with.
    """
    clip = VideoFileClip(video_path)
    lt_t = clip.duration * 0.2
    rt_t = clip.duration * 0.5
    lt_frame = Image.fromarray(clip.get_frame(lt_t))
    rt_frame = Image.fromarray(clip.get_frame(rt_t))
    lt_pane = _make_pane(lt_frame, SIZE)
    rt_pane = _make_pane(rt_frame, SIZE)
    final = Image.new('RGB', SIZE)
    final.paste(lt_pane, (0, 0))
    xoffset = int(SIZE[0] / 2)
    final.paste(rt_pane, (xoffset, 0))
    return final

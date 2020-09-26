"""Implements function for creating a split thumbnail of a single video"""

import math
from moviepy.editor import afx, CompositeVideoClip, concatenate_videoclips, TextClip, VideoFileClip
from PIL import Image, ImageDraw, ImageFont

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

def create_split_thumbnail(
        video_path, title,
        size=(1280, 720),
        max_font_size=150,
        font_color=(255, 255, 255),
        box_fill=(255, 69, 0),
        padding=20,
        text_rotate=5
):
    """
    Creates a split thumbnail from a single video. A frame early in the video is placed next to a
    frame later in the video.

    Args:
        video_path (str): Path to a video to generate thumbnail with.
        title (str): Title to place on thumbnail.
        size (int, int): Width and height of thumbnail.
        max_font_size (int): Maximum font size of title text. The title font size may be changed
            to better fit within the thumbnail.
        font_color (int, int, int): RGB color of the title text.
        box_fill (int, int, int): RGB color of the box around the title text.
        padding (int): Padding of the box around the title text in pixels.
        text_rotate (float): Degrees to rotate the title text.
    """
    w, h = size

    # Get two frames and place them side-by-side.
    clip = VideoFileClip(video_path)
    lt_t = clip.duration * 0.2
    rt_t = clip.duration * 0.5
    lt_frame = Image.fromarray(clip.get_frame(lt_t))
    rt_frame = Image.fromarray(clip.get_frame(rt_t))
    lt_pane = _make_pane(lt_frame, size)
    rt_pane = _make_pane(rt_frame, size)
    final = Image.new('RGBA', size)
    final.paste(lt_pane, (0, 0))
    xoffset = int(w / 2)
    final.paste(rt_pane, (xoffset, 0))

    # Try to find a font size that fits within the thumbnail's width. Does not check height.
    # The final width may not necessarily fit within the thumbnail's width.
    for div in range(1, 8):
        font_size = int(max_font_size / div)
        if font_size < 20:
            break
        font = ImageFont.truetype('Impact', size=font_size)
        txt_w, txt_h = font.getsize(title)
        # Get approximate width of rotated text.
        rot_w = txt_w * abs(math.cos(math.degrees(text_rotate)))
        if rot_w <= w:
            break

    # Create title frame.
    yoffset = int(-font_size / 6)
    title_size = (txt_w + padding * 2, txt_h + padding * 2 + yoffset)
    title_img = Image.new('RGB', title_size, color=box_fill)
    draw = ImageDraw.Draw(title_img)
    draw.text((padding, padding + yoffset), title, font=font, fill=font_color)

    # Rotate text and create alpha mask.
    title_rot = title_img.rotate(text_rotate, expand=True)
    mask = Image.new('RGB', title_img.size, (255, 255, 255))
    mask = mask.rotate(text_rotate, expand=True).convert('L').resize(title_rot.size)

    # Place title frame in center.
    tw = title_size[0]
    pos = (int((w - tw) / 2), 20)
    final.paste(title_rot, pos, mask)

    return final

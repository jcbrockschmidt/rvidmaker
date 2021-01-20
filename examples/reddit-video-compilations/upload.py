#!/usr/bin/env python3

import argparse
from datetime import datetime
import os
from rvidmaker.uploaders import (
    Payload,
    PayloadDecodeException,
    UploadException,
    YouTubeUploader,
)
import sys
from sys import stderr
from time import time


def main(payload_path):
    if not os.path.isfile(payload_path):
        print('"{}" is not a file'.format(payload_path), file=stderr)
        sys.exit(1)

    uploader = YouTubeUploader()
    if not uploader.is_authed():
        print("Not authenticated", file=stderr)
        sys.exit(1)

    try:
        payload = Payload.load(payload_path)
    except PayloadDecodeException as e:
        print("Failed to decode payload: {}".format(e), file=stderr)
        sys.exit(1)

    pay_dir = os.path.dirname(payload_path)
    video_path = os.path.join(pay_dir, payload.video)
    thumb_path = os.path.join(pay_dir, payload.thumb)
    if not os.path.exists(video_path):
        print("Video not found", file=stderr)
        sys.exit(1)
    if not os.path.exists(thumb_path):
        print("Thumbnail not found", file=stderr)
        sys.exit(1)

    print('Uploading video at "{}"...'.format(video_path))
    start = datetime.now()
    try:
        yt_video_id = uploader.upload(
            video_path,
            payload.title,
            payload.desc,
            payload.tags,
            privacy_status="unlisted",
        )
    except UploadException as e:
        print("Failed to upload video: {}".format(e), file=stderr)
        sys.exit(1)
    elapsed = datetime.now() - start
    print("Uploaded in {}".format(elapsed))
    print("Video uploaded to YouTube with ID {}".format(yt_video_id))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Uploads a video to YouTube")
    parser.add_argument(
        "payload",
        type=str,
        help="payload containing video information as a TOML file",
    )
    args = parser.parse_args()
    main(args.payload)

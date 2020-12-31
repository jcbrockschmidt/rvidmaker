#!/usr/bin/env python3

import argparse
from better_profanity import Profanity
import os
from rvidmaker.suites import (
    RedditVideoCompSuite,
    SuiteConfigException,
    SuiteGenerateException,
)
import sys
from sys import stderr
import toml
from toml import TomlDecodeError


def main(profile_path, output_dir, censor_path=None, block_path=None):
    if not os.path.isfile(profile_path):
        print('"{}" is not a file'.format(profile_path), file=stderr)
        sys.exit(1)
    if censor_path and not os.path.isfile(censor_path):
        print('"{}" is not a file'.format(censor_path), file=stderr)
        sys.exit(1)
    if block_path and not os.path.isfile(block_path):
        print('"{}" is not a file'.format(block_path), file=stderr)
        sys.exit(1)

    reddit = RedditVideoCompSuite()
    try:
        if censor_path:
            censor = Profanity()
            censor.load_censor_words_from_file(censor_path)
        else:
            censor = None
        if block_path:
            blocker = Profanity()
            blocker.load_censor_words_from_file(block_path)
        else:
            blocker = None
        reddit.config(profile_path, censor, blocker)
    except SuiteConfigException as e:
        print("Failed to configure suite: {}".format(e), file=stderr)
        sys.exit(1)
    try:
        reddit.generate(output_dir)
    except SuiteGenerateException as e:
        print("Failed to generate video: {}".format(e), file=stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generates a video compilation from a subreddit"
    )
    parser.add_argument(
        "profile",
        type=str,
        help="TOML file containing profile for scraping and rendering the video",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="output",
        help="directory to output files to",
    )
    parser.add_argument(
        "-c",
        "--censor",
        type=str,
        help="file containing words and phrases to censor in the video",
    )
    parser.add_argument(
        "-b",
        "--block",
        type=str,
        help="file containing words and phrases to exclude from metadata",
    )
    args = parser.parse_args()
    main(args.profile, args.output, args.censor, args.block)

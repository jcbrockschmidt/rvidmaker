#!/usr/bin/env python3

import argparse
import os
from rvidmaker.suites import (
    RedditVideoCompSuite,
    SuiteConfigException,
    SuiteGenerateException,
)
import sys
import toml
from toml import TomlDecodeError


def main(profile_path, output_dir, censor_path=None, block_path=None):
    if not os.path.isfile(profile_path):
        print('"{}" is not a file'.format(profile_path))
        return

    reddit = RedditVideoCompSuite()
    try:
        reddit.config(profile_path, censor_path, block_path)
    except SuiteConfigException as e:
        print("Failed to configure suite: {}".format(e))
        return
    try:
        reddit.generate(output_dir)
    except SuiteGenerateException as e:
        print("Failed to generate video: {}".format(e))
        return


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

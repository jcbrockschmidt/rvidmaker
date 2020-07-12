"""Provides objects for parsing subreddits articles"""

import asyncio
from copy import copy
from datetime import datetime
from ffmpeg import FFmpeg
import json
import os
import praw
import requests
from urllib.parse import urlsplit, urlunsplit

from rvidmaker.utils import random_string

CONFIG_PATH = 'config.json'
USER_AGENT = 'rvidmaker 0.0.1'

_TEMP_DOWNLOAD_DIR = '/tmp/rvidmaker'
if not os.path.exists(_TEMP_DOWNLOAD_DIR):
    os.mkdir(_TEMP_DOWNLOAD_DIR)

class ConfigNotFound(Exception):
    """Raised when no config file is found"""

class RedditApiException(Exception):
    """Raised when no config file is found"""
    def __init__(self, msg):
        super().__init__(msg)

class RedditVideoNotFound(Exception):
    """Raised if no Reddit video is found for an article"""

class RedditComment:
    """Represents a comment to a Reddit article"""

    def __init__(self, author, text, score):
        """
        Args:
            text: The comment's text.
        """
        self.author = author
        self.text = text
        self.score = score
        self._child = None

    @staticmethod
    def from_praw(praw_comment):
        """
        Args:
            praw_comment (praw.models.reddit.comment.Comment): PRAW generated comment.
        """
        author = praw_comment.author
        text = praw_comment.body
        score = praw_comment.score
        return RedditComment(author, text, score)

    def set_child(self, child):
        """
        Sets the child comment for a comment. Can only set one child.

        Args:
            child (RedditComment): The child comment. None to set no child.
        """
        self._child = None

    def get_child(self):
        """
        Gets the child comment if one exists.

        Returns:
            (RedditComment): The child comment, if it exists.
            (None): If there is no child.
        """
        return copy(self._child)

class RedditArticle:
    """Represents a Reddit article"""

    def __init__(self, praw_article):
        """
        Args:
            praw_article (praw.models.reddit.submission.Submission): The original PRAW generated
                article.
        """
        self._article = praw_article
        self.title = self._article.title
        self.author = self._article.author
        self.text = self._article.selftext
        self.category = self._article.category
        self.id = self._article.id
        self.url = self._article.url
        self.score = self._article.score
        self.nsfw = self._article.over_18
        self._time_created = self._article.created_utc
        self._media = self._article.media

    def get_age(self):
        """
        Gets the time that has elapse since the article was posted.

        Returns:
            (float) Hours since posting.
        """
        curtime = datetime.now().timestamp()
        hours = (curtime - self._time_created) / (60 * 60)
        return hours

    def _expand_comment(self, comment, praw_comment, max_depth, percent_thres):
        if max_depth <= 0:
            return

        # Get highest-scored reply
        best_reply = None
        for reply in praw_comment.replies:
            if not isinstance(reply, praw.models.reddit.comment.Comment):
                continue
            if best_reply is None:
                best_reply = reply
            elif reply.score > best_reply.score:
                best_reply = reply

        if not best_reply is None:
            if best_reply.score > comment.score * percent_thres:
                child = RedditComment.from_praw(best_reply)
                comment.set_child(child)
                self._expand_comment(child, best_reply, max_depth - 1, percent_thres)

    def get_comments(self, max_comments=10, max_depth=2, percent_thres=0.5):
        """
        Gets the best comments.

        Args:
            max_comments (int): Maximum number of comments to return.
            max_depth (int): Maximum depth of comments to expand to.
            percent_thres (float): What proportion of a parent comment's score a child comment must
                have to be included.

        Returns:
            (list) List of `RedditComment`s.
        """
        max_comments = max(1, max_comments)
        max_depth = max(0, max_depth)
        percent_thres = max(0, percent_thres)

        # Sort comments by score (descending order)
        praw_comments = []
        for comment in self._article.comments:
            if not isinstance(comment, praw.models.reddit.comment.Comment):
                continue
            praw_comments.append(comment)
        praw_comments.sort(key=lambda x: x.score, reverse=True)

        cnt = 0
        comments = []
        for praw_comment in praw_comments[:max_comments]:
            comment = RedditComment.from_praw(praw_comment)
            if comment.author is None or comment.text == '[deleted]':
                continue
            self._expand_comment(comment, praw_comment, max_depth, percent_thres)
            comments.append(comment)

        return comments

    def has_video(self, max_duration=None, include_youtube=True):
        """
        Checks if an article has a video that can be scraped. Only videos hosted by Reddit or
        YouTube videos can be scraped. GIFs are ignored.

        Args:
            max_duration (int): Maximum duration of video in seconds. None if duration does not
                matter.
            include_youtube (bool): Whether to recognize YouTube videos.

        Returns:
            (bool) True if the article has a valid video, and false otherwise.
        """
        if self._media is not None:
            if 'reddit_video' in self._media:
                reddit_video = self._media['reddit_video']
                if not reddit_video['is_gif']:
                    dur = reddit_video['duration']
                    if max_duration is None or dur <= max_duration:
                        return True
            elif 'type' in self._media:
                # TODO: Check the duration
                if self._media['type'] == 'youtube.com' and include_youtube:
                    return True
        return False

    def _get_random_path(self, root, ext):
        while True:
            rand_str = random_string(10)
            path = os.path.join(root, '{}.{}'.format(rand_str, ext))
            if not os.path.exists(path):
                return path

    def get_video(self, output):
        """
        Downloads a video from an article. Assumes the article has a video.
        Use 'has_video' to check that the articles has a video that can be scraped.

        Args:
            output (str): Path to write video to. File extension should be omitted.

        Raises:
            RedditVideoNotFound: If no video is found for the article.

        Returns:
            (str, str, str): The output path, title, and author. For Reddit videos, this will be the
                articles title and user who posted. For YouTube videos, this will be the video's
                title and uploader on YouTube.
        """
        if not self.has_video():
            raise RedditVideoNotFound

        if 'reddit_video' in self._media:
            # Scrape a video hosted by Reddit
            output_path = output + '.mp4'
            reddit_video = self._media['reddit_video']

            # Get video and audio URLs
            video_url = reddit_video['fallback_url']
            audio_url = list(urlsplit(video_url))
            audio_url_path = audio_url[2]
            audio_ext = os.path.splitext(audio_url_path)[1]
            if audio_ext == '.mp4':
                audio_basename = 'DASH_audio.mp4'
            else:
                audio_basename = 'audio'
            audio_url[2] = os.path.join(os.path.dirname(audio_url_path), audio_basename)
            audio_url[3] = ''
            audio_url[4] = ''
            audio_url = urlunsplit(audio_url)

            # Download video and audio
            temp_video_path = self._get_random_path(_TEMP_DOWNLOAD_DIR, 'mp4')
            temp_audio_path = self._get_random_path(_TEMP_DOWNLOAD_DIR, 'mp4')
            with open(temp_video_path, 'wb') as f:
                req = requests.get(video_url)
                # TODO: Check `req.status_code`
                f.write(req.content)
            with open(temp_audio_path, 'wb') as f:
                req = requests.get(audio_url)
                # TODO: Check `req.status_code`
                f.write(req.content)

            # Combine video and audio
            ffmpeg = FFmpeg().option('y').input(
                temp_video_path
            ).input(
                temp_audio_path
            ).output(
                output_path,
                {
                    'codec:v': 'copy',
                    'codec:a': 'aac'
                }
            )
            loop = asyncio.get_event_loop()
            loop.run_until_complete(ffmpeg.execute())

            # Delete temporary files
            os.remove(temp_video_path)
            os.remove(temp_audio_path)

            return output_path, self.author, self.title
        else:
            # Scrape a YouTube video
            raise NotImplementedError

class RedditReader:
    """Reads popular articles from a subreddit"""

    def __init__(self):
        """
        Raises:
            ConfigNotFound: If no config file is found.
            RedditApiException: If calls to the Reddit API fail.
        """

        if not os.path.exists(CONFIG_PATH):
            raise ConfigNotFound

        with open(CONFIG_PATH) as f:
            config = json.load(f)

        try:
            self.reddit = praw.Reddit(
                client_id=config['client_id'],
                client_secret=config['client_secret'],
                username=config['username'],
                password=config['password'],
                user_agent=USER_AGENT
            )
        except praw.exceptions.PRAWException as e:
            raise RedditApiException(str(e))

    def get_hot_articles(self, subreddit, limit=10, min_score=None, min_age=None):
        """
        Gets a collection of popular (hot) articles from a subreddit.

        Args:
            subreddit (str): Name of subreddit.
            limit (int): Maximum number of articles to read where 1 <= `limit` <= 100.
            min_score (int): Minimum score of articles to include. None for no minimum.
            min_age (int): Minimum age in hours of articles to include. None for no minimum.

        Raises:
            RedditApiException: If calls to the Reddit API fail.

        Returns:
            (list) List of `RedditArticle`s sorted in descending order by score.
        """
        limit = max(0, min(limit, 100))
        try:
            sub = self.reddit.subreddit(subreddit)
            raw_articles = sub.hot(limit=limit)
        except praw.exceptions.PRAWException as e:
            raise RedditApiException(str(e))

        articles = []
        for raw_art in raw_articles:
            art = RedditArticle(raw_art)
            if not min_score is None:
                if art.score < min_score:
                    continue
            if not min_age is None:
                if art.get_age() < min_age:
                    continue
            articles.append(art)

        articles.sort(key=lambda x: x.score, reverse=True)
        return articles

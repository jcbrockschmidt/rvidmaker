"""Provides objects for parsing subreddits articles"""

from datetime import datetime
import json
import os
import praw

CONFIG_PATH = 'config.json'
USER_AGENT = 'rvidmaker 0.0.1'

class ConfigNotFound(Exception):
    """Raised when no config file is found"""

class RedditApiException(Exception):
    """Raised when no config file is found"""
    def __init__(self, msg):
        super().__init__(msg)

class RedditArticle:
    """Represents a Reddit article"""

    def __init__(self, praw_article):
        """
        Arguments:
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

    def get_age(self):
        """
        Gets the time that has elapse since the article was posted.

        Returns:
            (float) Hours since posting.
        """
        curtime = datetime.now().timestamp()
        hours = (curtime - self._time_created) / (60 * 60)
        return hours

    def get_comments(self):
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

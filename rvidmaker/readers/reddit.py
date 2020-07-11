"""Provides objects for parsing subreddits articles"""

from copy import copy
from datetime import datetime
import json
import os
import praw

from rvidmaker.exceptions import ConfigNotFound, RedditApiException

CONFIG_PATH = 'config.json'
USER_AGENT = 'rvidmaker 0.0.1'

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

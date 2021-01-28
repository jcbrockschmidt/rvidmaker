"""
Provides an object that uploads videos to YouTube

Code derived from https://developers.google.com/youtube/v3/guides/uploading_a_video
"""

import httplib2
from json import JSONDecodeError
import json
import os
import random
import time

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

_VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

# Maximum number of times to retry before giving up.
_MAX_RETRIES = 10

# Always retry when these exceptions are raised.
_RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
_RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# File that contains OAuth 2.0 information, including its client_id and client_secret.
_CLIENT_SECRETS_FILE = "client_secrets.json"

# File that contains OAuth 2.0 information for the authenticated user.
_OAUTH_FILE = "rvidmaker-youtube-oauth2.json"

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
_YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
_YOUTUBE_API_SERVICE_NAME = "youtube"
_YOUTUBE_API_VERSION = "v3"

# This variable defines a message to display if the _CLIENT_SECRETS_FILE is
# missing.
_MISSING_CLIENT_SECRETS_MSG = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   {}

with information from the API Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""".format(
    os.path.abspath(os.path.join(os.path.dirname(__file__), _CLIENT_SECRETS_FILE))
)


class UploadException(Exception):
    """Raised when uploading a video fails"""


class AuthException(Exception):
    """Raised when authentication fails"""


class YouTubeUploader:
    """Uploads videos to YouTube"""

    # Maximum total number of characters for all tags.
    _TAGS_MAX_CHARS_TOTAL = 500

    # Maximum number of characters for a single tag.
    _TAGS_MAX_CHARS = 30

    def _get_creds(self, oauth_file):
        if os.path.exists(oauth_file):
            storage = Storage(oauth_file)
            creds = storage.get()
            if creds is not None and not creds.invalid:
                return creds

    def _truncate_tags(self, tags):
        """
        Truncates at list of tags to fit within YouTube's tag restrictions.

        Args:
            tags (:obj:`list` of :obj:`str`): Original tags in descending order of importance.

        Returns:
            list: The modified list of tags.
        """
        new_tags = []
        total_len = 0
        for t in tags:
            if len(t) > self._TAGS_MAX_CHARS:
                continue
            extra_len = len(t)
            if len(t.split()) > 1:
                # YouTube puts quotation marks around tags with whitespace / multiple words.
                extra_len += 2
            if len(new_tags) > 0:
                # YouTube puts commas between each tag.
                extra_len += 1
            if total_len + extra_len < self._TAGS_MAX_CHARS_TOTAL:
                total_len += extra_len
                new_tags.append(t)
            # Less importance tags near the end of the list might be included because they are
            # shorter than preceding tags.
        return new_tags

    def _resumable_upload(self, insert_request):
        """
        Uploads a video in a way that is robust to various errors.

        Raises:
            UploadException: If the video fails to upload.

        Returns:
            str: ID of the uploaded video.
        """
        # Uses an exponential backoff strategy to resume a failed upload.
        response = None
        error = None
        retry = 0
        while response is None:
            try:
                status, response = insert_request.next_chunk()
                if response is not None:
                    if "id" in response:
                        return response["id"]
                    else:
                        raise UploadException(
                            "The upload failed with an unexpected response: {}".format(
                                response
                            )
                        )
            except HttpError as e:
                if e.resp.status in _RETRIABLE_STATUS_CODES:
                    error = "A retriable HTTP error {} occurred: {}".format(
                        e.resp.status, e.content
                    )
                else:
                    code = e.resp.status
                    try:
                        content = json.loads(e.content.decode("utf-8"))
                    except JSONDecodeError:
                        raise UploadException(
                            "Failed to parse JSON for HTTP {} error".format(code)
                        )
                    if "error" in content and "message" in content["error"]:
                        raise UploadException(
                            "An HTTP error {} occurred: {}".format(
                                code, content["error"]["message"]
                            )
                        )
                    else:
                        raise UploadException("An HTTP error {} occurred".format(code))
            except _RETRIABLE_EXCEPTIONS as e:
                error = "A retriable error occurred: {}".format(e)
            except BaseException as e:
                raise UploadException("An unexpected error occurred: {}".format(e))

            if error is not None:
                print(error)
                retry += 1
                if retry > _MAX_RETRIES:
                    raise UploadException("No longer attempting to retry")
                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                print(
                    "Sleeping {:0.2f} seconds and then retrying...".format(
                        sleep_seconds
                    )
                )
                time.sleep(sleep_seconds)

    def is_authed(self):
        """
        Checks whether OAuth 2.0 authentication has been completed.

        Returns:
            bool: Whether authentication has been completed.
        """
        return self._get_creds(_OAUTH_FILE) is not None

    def auth(self):
        """
        Runs the user through the OAuth 2.0 authentication process.

        Raises:
            AuthException: If authentication fails.
        """
        if self.is_authed():
            print("Already authenticated")
        else:
            print("Authenticating...")
            storage = Storage(_OAUTH_FILE)
            try:
                flow = flow_from_clientsecrets(
                    _CLIENT_SECRETS_FILE,
                    scope=_YOUTUBE_UPLOAD_SCOPE,
                    message=_MISSING_CLIENT_SECRETS_MSG,
                )
            except JSONDecodeError as e:
                raise AuthException(
                    "Failed to decode client secrets file: {}".format(e)
                )
            run_flow(flow, storage)

    def upload(
        self, path, title, desc="", tags=list(), category=24, privacy_status="unlisted"
    ):
        """
        Uploads a video to YouTube.

        Args:
            path (str): Path to the video to upload.
            title (str): Title for the video.
            desc (str): Description for the video.
            tags (list): Tags for the video in descending order of importance. May be truncated.
            category (int): Category to upload under. Defaults to 24 for "Entertainment".
                See https://developers.google.com/youtube/v3/docs/videoCategories/list for
                different category numbers.
            privacy_status (str): Whether the video is "public", "private", or "unlisted".

        Returns:
            str: ID of the uploaded video.

        Raises:
            AuthException: If no user has been authenticated for this application yet.
            TypeError: If one of the arguments is an inappropriate type.
            UploadException: If the video fails to upload.
            ValueError: If one of the arguments' values is invalid.
        """
        if not isinstance(path, str):
            raise TypeError("path must be of type str")
        if not isinstance(title, str):
            raise TypeError("title must be of type str")
        if not isinstance(desc, str):
            raise TypeError("desc must be of type str")
        if not isinstance(tags, (list, tuple)):
            raise TypeError("tags must be a list or tuple")
        if not isinstance(category, int):
            raise TypeError("category must be of type int")
        if not os.path.isfile(path):
            raise ValueError('"{}" is not a file'.format(path))
        if category <= 0:
            raise ValueError("category must be greater than 0")
        if privacy_status not in _VALID_PRIVACY_STATUSES:
            raise ValueError(
                'privacy_status must be either "public", "private", or "unlisted"'
            )

        old_tag_count = len(tags)
        tags = self._truncate_tags(tags)
        tag_diff = old_tag_count - len(tags)
        if tag_diff > 0:
            print("{} tags excluded".format(tag_diff))
        creds = self._get_creds(_OAUTH_FILE)
        if creds is None:
            return AuthException("Application has not been authenticated yet")
        youtube_api = build(
            _YOUTUBE_API_SERVICE_NAME,
            _YOUTUBE_API_VERSION,
            http=creds.authorize(httplib2.Http()),
        )
        body = {
            "snippet": {
                "title": title,
                "description": desc,
                "tags": tags,
                "categoryId": category,
            },
            "status": {"privacyStatus": privacy_status},
        }
        insert_request = youtube_api.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=MediaFileUpload(path, chunksize=-1, resumable=True),
        )
        video_id = self._resumable_upload(insert_request)
        return video_id

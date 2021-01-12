# Reddit Video Maker

Generates videos of narrated Reddit articles or compilations of videos from subreddits.

## Installation

### Debian/Ubuntu

Install the necessary system packages.

```bash
sudo apt install ffmpeg imagemagick
```

Configure ImageMagick by opening `/etc/ImageMagick-<VERSION>/policy.xml` and commenting out or removing the line that reads
```
<policy domain="path" rights="none" pattern="@*" />
```
*(This allows us to write text on images and videos. See [this comment](https://github.com/Zulko/moviepy/issues/401#issuecomment-278679961) for more details.)*


Install the Python package.
```bash
./setup.py install
```

## Example Usage

### Setup

#### Debian/Ubuntu

Navigate to the example directory for generating compilations of videos from subreddits.

```bash
cd examples/reddit-video-compilations
```

Install the fonts this example uses
```bash
sudo apt install ttf-mscorefonts-installer
```

#### Reddit API Authorization

Sign up for the Reddit API with a registered Reddit account and create an application. [See this guide](https://alpscode.com/blog/how-to-use-reddit-api/). Then copy the client ID and client secret for the application into `reddit_api_config.toml`.

#### YouTube API Authorization

Obtain OAuth 2.0 authorization credentials for the YouTube API through the Google API Console. [See this guide](https://developers.google.com/youtube/registering_an_application). Then download and place your OAuth 2.0 client secrets in `client_secrets.json`.

Now that OAuth 2.0 is setup, authorize a YouTube account using the authorization script. This account will have a video uploaded to its YouTube channel later in this guide.

```bash
./auth.py
```

### Generating a Video

Now we can generate a video. Here we use the configuration profile defined in `profile.toml`. Words will be censored in the video using words and phrases in `censor.txt`, and metadata like the video's title and tags will exclude words and phrases in `blocklist.txt`. All generated files will be placed in the directory `output`. You will want to populate `censor.txt` and `blocklist.txt` with your own words. Here is a [list of English swear words](https://github.com/RobertJGabriel/Google-profanity-words) and here's a [list of demonitized words for YouTube](https://docs.google.com/spreadsheets/d/1ozg1Cnm6SdtM4M5rATkANAi07xAzYWaKL7HKxyvoHzk/edit#gid=674179785).

```bash
./create.py profile.toml -o output -c censor.txt -b blocklist.txt
```

The underlying video rendered, `moviepy`, can sometimes mess up the terminal. Use the command `reset` to fix this (the command may be invisible as you type it).


### Uploading a Video

**WARNING**: Unverified Google APIs services will result in any videos uploaded with it being ["locked as private"](https://support.google.com/youtube/answer/7300965?hl=en). This can be fixed by
 * Setting your API service as "Internal", which requires you pay for G Suite.
 * Requesting an audit of your API service, which requires you have a business and pay for G Suite.

**NOTE**: The following script does not currently upload the thumbnail.

Run the upload script with the created video payload.

```bash
./upload.py output/payload.toml
```

Shortly after, you should see your video being uploaded and processed. This will of course take some time, with time varying based on your internet speed and video size.

# RedditMonitor

Get notified for new Reddit posts that match your search criteria with included/excluded support.

![](/assets/screenshot.jpg)

## Prerequisites
- A [Reddit](https://www.reddit.com/) account
- Reddit API `client_id` and `client_secret`, see [here](https://github.com/reddit-archive/reddit/wiki/OAuth2-Quick-Start-Example#first-steps) for more detailed instructions. When you create the RedditApp, give it any name, and make sure it's set to "script". The decription/about url/redirect url don't matter, but you need something in the redirect url for it to save, so put localhost or some shit.
	1. The `client_id` will be the text underneath the "personal use script". It's a bunch of jumbled text just like the secret
	2. The `client_secret` is the secret. 
- A notification service supported by [Apprise](https://github.com/caronc/apprise#popular-notification-services) and the required API keys or other configuration for your chosen services
	This was tested using Discord webhooks, it should work on other Apprise notification services, but I am not 100% sure, nor do I have the time to test it out. Changing a few lines of code for this already took me a good portion of my day because I am caught in the Infinite monkey theorem as it stands already.
- Have [Python](https://www.python.org/) 3.8+ or [Docker](https://www.docker.com/) installed

## Installation
This app can be used stand-alone and run with Python, or it is also available as a Docker image.
If using Python, install the requirements first:
`pip install -r requirements.txt`

## Configuration
The configuration is stored inside a yaml file, you can copy the example`config.yaml` into a new file `config.yaml` use that as a base, the following sections are all required:
1. Apprise configuration urls as a list, for your chosen providers
	```
	apprise:
	  - discord://webhook_id/webhook_token
	  - join://apikey/device
	  - slack://TokenA/TokenB/TokenC/
	```
2. Reddit configuration with your [app](https://www.reddit.com/prefs/apps) details, it is also [recommended](https://github.com/reddit-archive/reddit/wiki/API#rules) to put your username in the `agent` field but it can be anything you want
	```
	reddit:
	  client: xxxxxxxxxx
	  secret: xxxxxxxxxxxxxxxxxxxx_xxxxxxxxxx
	  agent: reddit-post-notifier (u/xxxxxx)
	```
3. Subreddit configuration with your desired search terms for each subreddit you want to monitor, the following example monitors r/GameDeals for any post that includes the words 'free' OR '100%' in the title (make sure this key appears under the `reddit` key, with [proper indentation](http://www.yamllint.com/), and using [single quotes](https://stackoverflow.com/questions/19109912/yaml-do-i-need-quotes-for-strings-in-yaml) if needed)
	```
   subreddits:
     gamedeals:
      include:
       - 'free'
       - '100%'
      exclude:
       - 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
	```

 Currently an issue where each subreddit must include an include and exclude trigger, so just make sure your have some mumbojumbo bullshit text that will never get called in the excluded. 

## Configuration for Unraid
This was specially made so I could run it on my Unraid server. 
1. The config.py goes in the appdata folder at /mnt/user/appdata/redditmonitor. Put the config.yaml in the root folder of redditmonitor.
2. Create a path variable with the following:
	```
 	Name: Path: /app/config.yaml
	Container Path: /app/config.yaml
	Host Path: /mnt/user/appdata/redditmonitor/config.yaml
	Default Value: /mnt/user/appdata/redditmonitor/config.yaml
 	```
3. Go to the shares -> user/appdata and make sure that redditmonitor's owner is set to nobody. Click the checkbox next to it, click permissions, and permissions are set to owner: read/write, group: read/write, and other: read/write. This is just because I wanted to edit the config from the windows explorer on Windows. Do this, or don't do this, honestly not sure; but it's what works for me. 

### Optional
- `RPN_CONFIG` environment variable can be used to change the location of the config file, the default is `config.yaml` relative to where `app.py` is, `app/config.yaml` in the Docker image.
- `RPN_LOGGING` environment variable can be set to `TRUE` to enable logging each matched post to the console as well.
- [Docker-Compose](https://docs.docker.com/compose/) configuration:
```
version: "1.0"

services:
    redditmonitor:
        container_name: redditmonitor
        image: ghcr.io/jamessampsan/redditmonitor
        restart: unless-stopped
        volumes:
            - ./config.yaml:/app/config.yaml

```

## Usage
- Stand-alone:
	`python app.py`
- Docker:
	`docker run -v /path/to/your/config.yaml:/app/config.yaml ghcr.io/rafhaanshah/reddit-post-notifier:latest`

## Troubleshooting
- Check your `yaml` configuration is valid: http://www.yamllint.com
- Apprise does not log even if your configuration is invalid or not working, you can check if your urls work by installing the Apprise CLI: https://github.com/caronc/apprise/wiki/CLI_Usage
- Check the console logs for API errors, the app uses PRAW for accessing the Reddit API and you may find something in their docs: https://praw.readthedocs.io/en/latest/

- I am a complete idiot. This is what I made for myself. Don't expect me to fix issues unless you specifically note what needs to be changed. It's a goddamn miracle that I got this working in the first place.
- I got this working on Docker for Unraid, with Discord webhook integration. Don't expect this to work on Telegram or other services. It should, but I don't know for sure.
- If anyone finds out how to support multiple Discord webhooks, let me know.
- Copy the example config file and go from there. 

## License
[MIT](https://choosealicense.com/licenses/mit/)

"""Stream new Reddit posts and notify for matching posts."""
import datetime
import os
import sys
import time

import apprise
import praw
import prawcore
import yaml

CONFIG_PATH = os.getenv("RPN_CONFIG", "config.yaml")
LOGGING = os.getenv("RPN_LOGGING", "FALSE")

YAML_KEY_APPRISE = "apprise"
YAML_KEY_REDDIT = "reddit"
YAML_KEY_SUBREDDITS = "subreddits"
YAML_KEY_CLIENT = "client"
YAML_KEY_SECRET = "secret"
YAML_KEY_AGENT = "agent"


def main():
    """Run application."""
    print("Starting Reddit Post Notifier")
    config = get_config()
    apprise_config = config[YAML_KEY_APPRISE]
    reddit_config = config[YAML_KEY_REDDIT]

    subreddits = reddit_config[YAML_KEY_SUBREDDITS]
    apprise_client = get_apprise_client(apprise_config)
    reddit_client = get_reddit_client(
        reddit_config[YAML_KEY_CLIENT],
        reddit_config[YAML_KEY_SECRET],
        reddit_config[YAML_KEY_AGENT]
    )

    validate_subreddits(reddit_client, subreddits)
    stream_submissions(reddit_client, subreddits, apprise_client)


def stream_submissions(reddit, subreddits, apprise_client):
    """Monitor and process new Reddit submissions in given subreddits."""
    subs = subreddits.keys()
    subs_joined = "+".join(subs)
    subreddit = reddit.subreddit(subs_joined)

    # Maintain a set of already processed submission IDs
    processed_ids = set()

    while True:
        try:
            for submission in subreddit.stream.submissions(pause_after=None, skip_existing=True):
                if submission.id not in processed_ids:
                    process_submission(submission, subreddits, apprise_client)
                    # Mark the submission as processed
                    processed_ids.add(submission.id)

        except KeyboardInterrupt:
            sys.exit("\tStopping application, bye bye")

        except (praw.exceptions.PRAWException,
                prawcore.exceptions.PrawcoreException) as exception:
            print("Reddit API Error: ")
            print(exception)
            print("Pausing for 30 seconds...")
            time.sleep(30)


def process_submission(submission, subreddits, apprise_client):
    """Notify if given submission matches search and doesn't match exclude."""
    title = submission.title
    sub = submission.subreddit.display_name.lower()
    subreddit_config = subreddits[sub]

    include_terms = subreddit_config.get("include", [])
    exclude_terms = subreddit_config.get("exclude", [])

    # Check if title contains any include terms but no exclude terms
    if any(term in title.lower() for term in include_terms) and not any(term in title.lower() for term in exclude_terms):
        notify(apprise_client, title, submission.permalink)
        if LOGGING != "FALSE":
            print(datetime.datetime.fromtimestamp(submission.created_utc),
                  " " + "r/" + sub + ": " + title + "\n" + submission.permalink)


def notify(apprise_client, title, submission_id):
    """Send apprise notification."""
    apprise_client.notify(
        title=title,
        body="https://www.reddit.com" + submission_id,
    )


def get_reddit_client(cid, secret, agent):
    """Return PRAW Reddit instance."""
    return praw.Reddit(
        client_id=cid,
        client_secret=secret,
        user_agent=agent
    )


def get_apprise_client(config):
    """Return Apprise instance."""
    apprise_client = apprise.Apprise()

    for conf in config:
        apprise_client.add(conf)

    return apprise_client


def get_config():
    """Returns application configuration."""
    check_config_file()
    config = load_config()
    return validate_config(config)


def check_config_file():
    """Check if config file exists."""
    if not os.path.exists(CONFIG_PATH):
        sys.exit("Missing config file: " + CONFIG_PATH)

    print("Using config file: " + CONFIG_PATH)


def load_config():
    """Load config into memory."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_yaml:
        config = None

        try:
            config = yaml.safe_load(config_yaml)

        except yaml.YAMLError as exception:
            if hasattr(exception, "problem_mark"):
                mark = exception.problem_mark # pylint: disable=no-member
                print(f"Invalid yaml, line {mark.line + 1}, column {mark.column + 1}")

            sys.exit("Invalid config: failed to parse yaml")

        if not config:
            sys.exit("Invalid config: empty file")

        return config


def validate_config(config):
    """Validate required config keys."""
    if YAML_KEY_REDDIT not in config or not isinstance(config[YAML_KEY_REDDIT], dict):
        sys.exit("Invalid config: missing reddit config")

    reddit = config[YAML_KEY_REDDIT]

    if YAML_KEY_CLIENT not in reddit or not isinstance(reddit[YAML_KEY_CLIENT], str):
        sys.exit("Invalid config: missing reddit -> client config")

    if YAML_KEY_SECRET not in reddit or not isinstance(reddit[YAML_KEY_SECRET], str):
        sys.exit("Invalid config: missing reddit -> secret config")

    if YAML_KEY_AGENT not in reddit or not isinstance(reddit[YAML_KEY_AGENT], str):
        sys.exit("Invalid config: missing reddit -> agent config")

    if YAML_KEY_SUBREDDITS not in reddit or not isinstance(reddit[YAML_KEY_SUBREDDITS], dict):
        sys.exit("Invalid config: missing reddit -> subreddits config")

    if YAML_KEY_APPRISE not in config or not isinstance(config[YAML_KEY_APPRISE], list):
        sys.exit("Invalid config: missing apprise config")

    print("Monitoring Reddit for:")

    subs = reddit[YAML_KEY_SUBREDDITS]
    for conf, filters in subs.items():
        if not isinstance(filters, dict):
            sys.exit(f"Invalid config: '{conf}' must contain 'include' and/or 'exclude' as dictionaries")

        include = filters.get("include", [])
        exclude = filters.get("exclude", [])

        if not isinstance(include, list) or not all(isinstance(item, str) for item in include):
            sys.exit(f"Invalid config: 'include' in '{conf}' must be a list of strings")

        if not isinstance(exclude, list) or not all(isinstance(item, str) for item in exclude):
            sys.exit(f"Invalid config: 'exclude' in '{conf}' must be a list of strings")

        subs[conf] = {
            "include": [x.lower() for x in include],
            "exclude": [x.lower() for x in exclude]
        }

        print(f"\tr/{conf}: include={include}, exclude={exclude}")

    reddit[YAML_KEY_SUBREDDITS] = {k.lower(): v for k, v in subs.items()}
    return config


def validate_subreddits(reddit, subreddits):
    """Validate subreddits."""
    for sub in subreddits:
        try:
            reddit.subreddit(sub).id

        except prawcore.exceptions.Redirect:
            sys.exit("Invalid Subreddit: " + sub)

        except (praw.exceptions.PRAWException,
                prawcore.exceptions.PrawcoreException) as exception:
            print("Reddit API Error: ")
            print(exception)


if __name__ == "__main__":
    main()

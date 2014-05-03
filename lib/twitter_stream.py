from ConfigParser import ConfigParser
from argparse import ArgumentParser
from lockfile import FileLock
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener
import json
import logging
import os
import re
import redis
import sys

"""
The folowing Object acts as a listener to the Twitter stream
of Tweets. Every time it receives a new tweet it checks if
hashtags are present. If so, it increments a counter per hashtag
in redis.
"""
class Listener(StreamListener):
    # Constructor
    def __init__(self, tweet_filter, redis_host, redis_port):
        self.tweet_count = 0
        self.redis = redis.Redis(
            host = redis_host,
            port = redis_port,
            db = 0
        )
        self.tweet_filter = tweet_filter
        self.tweet_regex = re.compile(r"#([^\s|#]+)")

    # Callback function when twitter pushes a new tweet successfully
    def on_data(self, data):
        # Get the Redis connection and the tweet filter
        redis = self.redis
        tweet_filter = self.tweet_filter
        tweet_regex = self.tweet_regex

        # JSON decode the tweet
        try:
            decoded = json.loads(data)
        except ValueError:
            print "Could not JSON decode Twitter response"
            return False

        # Fetch the text content of the Tweet
        text = ''
        try:
            text = decoded['text']
        except KeyError:
            print 'No key text in Twitter response'
            return False

        # Find all the hashtags and update Redis
        hashtags = re.findall(tweet_regex, text)
        for hashtag in hashtags:
            v = redis.incr('%s:%s' % (tweet_filter, hashtag.lower()))
            print "%s => %s" % (hashtag, v)

        # Increment the overall Tweet count
        self.tweet_count += 1
        if (self.tweet_count % 100 == 0):
            print "Received %s Tweets" % self.tweet_count

        return True

    def on_error(self, status):
        print status

if __name__ == '__main__':
    # Create a config and an argument parser
    # All the config parameters can be also specified (and will
    # be overridden) by command line flags
    conf_parser = ArgumentParser(add_help = False)
    conf_parser.add_argument(
        "--conf",
        help="Alternative Config File Location",
        metavar="FILE"
    )

    # Get the path to the root directory of the repo
    rootdir = os.path.realpath(os.path.join(os.path.dirname(sys.argv[0]), '..'))

    args, args_rest = conf_parser.parse_known_args()
    config = ConfigParser()
    config.readfp(open(args.conf or '%s/config/hashtag_counter.cfg' % rootdir))

    # Get the default config values
    defaults = {}
    for section in config.sections():
        defaults = dict(defaults.items() + config.items(section))

    parser = ArgumentParser(parents=[conf_parser])
    parser.set_defaults(**defaults)

    parser.add_argument(
        "--debug",
        help="Debug mode",
        action="store_true"
    )
    parser.add_argument(
        "--filter",
        help="Keyword filter for tweets",
        required=True
    )
    parser.add_argument(
        "--verbose",
        help="Verbose mode",
        action="store_true"
    )

    args = parser.parse_args(args_rest)

    l = Listener(
        tweet_filter = args.filter,
        redis_host = args.redis_host,
        redis_port = int(args.redis_port)
    )
    auth = OAuthHandler(args.consumer_key, args.consumer_secret)
    auth.set_access_token(args.access_token, args.access_token_secret)

    stream = Stream(auth, l)
    stream.filter(track=[args.filter])


from ConfigParser import ConfigParser
from argparse import ArgumentParser
from flask import request, Flask
from flask.ext.cache import Cache
from operator import itemgetter
from redis import Redis
import json
import os
import re
import sys

app = Flask(__name__)

app.config['CACHE_TYPE'] = 'simple'
app.cache = Cache(app)

# Read a configuration file
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

args = parser.parse_args(args_rest)


"""
############### ROUTES ###############
"""
# Get a count of hashtags from tweets that include
# the word charity
@app.route("/count", methods=["GET"])
@app.route("/count/<num_results>", methods=["GET"])
@app.cache.cached(timeout=10)
def count(num_results=100):
    redis = Redis(
        host = args.redis_host,
        port = int(args.redis_port),
        db = 0
    )

    keys = redis.keys("%s:*" % "charity")
    values = redis.mget(keys)
    regex = re.compile(r':(.+)$')
    response = []

    # Check if "num_results" param exists and check if
    # the keys are less than num_results
    length = len(keys)

    for i in range(0, length):
        key = keys[i]
        value = values[i]

        match = re.search(regex, key)
        response.append(
            {
                'hashtag'   : match.group(1),
                'count'     : int(value)
            }
        )

    response = sorted(
        response,
        key = itemgetter('count'),
        reverse = True
    )

    # Trim the response appropriately
    num_results = int(num_results)
    if (length > num_results): length = num_results

    response = response[:length]

    return json.dumps(response)

# Flush Redis stats by tweet filter
@app.route("/reset/<tweet_filter>", methods=["DELETE"])
def reset(tweet_filter):
    redis = Redis(
        host = args.redis_host,
        port = int(args.redis_port),
        db = 0
    )

    if (not tweet_filter):
        return json.dumps(
            {
                'response'  : 'error',
                'reason'    : 'No tweet filter',
            }
        )

    keys = redis.keys("%s:*" % tweet_filter)
    count = len(keys)

    redis.delete(*keys)

    return json.dumps(
        {
            'response'  : 'ok',
            'debug'     : 'Deleted %s keys' % count,
        }
    )

if __name__ == '__main__':
    app.run(
        debug = True,
        host = args.api_host,
        port = int(args.api_port)
    )

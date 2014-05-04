# Twitter HashTag Count
--------------

## Summary
This repository includes a script that connects to the Twitter Streaming API and uses a generic filter to pull tweets. The hashtags are pulled out of those tweets and a count per hashtag is recorded in a Redis database.

## Requirements
Packages Required:

* redis-server
* python (version 2.7 and above)
* python-argparse
* python-lockfile
* python-redis
* python-twitter
* Flask
* Flask-Cache

## Usage
The `twitter_stream.py` script stores the hashtags it sees in Redis. So before starting the script make sure your Redis server is running:

```sh
$ sudo service redis-server start
```

---

Fill in your configuration file under `config/hashtag_counter.cfg`.

Start the Twitter API stream script:

```sh
~/twitter-hashtag-count $ python lib/twitter_stream.py --filter=charity
```

More flags:

* `--debug`
* `--verbose`

If `--verbose` is not specified the script will write under `/tmp/twitter_hashtag_count.log` by default.

---

The API reads the Redis keys that the `twitter_stream.py` script is setting.

By default it uses 0.0.0.0:80.

Start the API:

```sh
~/twitter-hashtag-count $ python api/hashtag_count_api.py
```

Note: You might need root provileges to start the API if you want to use port 80.

## API Routes

#### GET /count/${tweet_filter}
#### GET /count/${tweet_filter}/${num_results}
Returns an array of hashes containing a hashtag count and a hashtag name for all tweets containing the word represented by the variable `tweet_filter`.

`num_results` defaults to 100 elements.

#### DELETE /reset/${term_filter}
Deletes all the Redis keys collected for the specific filter.

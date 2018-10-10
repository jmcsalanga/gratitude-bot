import numpy as np
import logging
import time
import tweepy


class twitterAPI():
    def __init__(self, consumer_key, consumer_secret, access_key, access_secret):
        self._logger = logging.getLogger(__name__)
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._access_key = access_key
        self._access_secret = access_secret
        self._authorization = None
        if consumer_key is None:
            self.tweet = lambda x : self._logger.info("Test tweet: " + x)
            self._login = lambda x : self._logger.debug("Test Login completed.")

    def _login(self):
        auth = tweepy.OAuthHandler(self._consumer_key, self._consumer_secret)
        auth.set_access_token(self._access_key, self._access_secret)
        self._authorization = auth

    def tweet(self, tweet):
        if self._authorization is None:
            self._login()
            pass
        api = tweepy.API(self._authorization)
        stat = api.update_status(tweet)
        self._logger.info("Tweeted: " + tweet)
        self._logger.info(stat)

    def disconnect(self):
        self._authorization = None


class Bot:
    def __init__(self,
                 documents,
                 twitter_api,
                 max_document_length=1000,
                 burn_in=250,
                 tweets_per_hr=1):
        self._documents = documents
        self._twitter_api = twitter_api
        self._corpus = {}
        self._logger = logging.getLogger(__name__)
        self._max_sentence_length = max_document_length
        self._burn_in = burn_in

        # Calculate sleep timer
        self.sleep_timer = int(60 * 60 / tweets_per_hr)

    def _line_to_array(self, line):
        if len(line) < 1:
            return [], False
        line = line.strip()
        line = line.split()
        return line, True

    def _add_to_corpus(self, parsed, key, k, next_key):
        if next_key is None:
            addition = 2
        else:
            addition = 0

        word = parsed[k + addition]

        if key in self._corpus:
            self._corpus[key].append(word)
        else:
            self._corpus[key] = [word]

    def _load_data(self):
        next_key = None
        for doc in self._documents:
            with open(doc, "r") as f:
                for line in f.readlines():
                    parsed, add = self._line_to_array(line)
                    if add:
                        if next_key is None:
                            a = -2
                        # else:
                        #   a = 0
                        for k in range(0, (len(parsed) + a)):
                           # if next_key is not None:
                           #     key = next_key
                           #     next_key = (next_key[1], parsed[k])
                           # else:
                                key = (parsed[k], parsed[k + 1])

                                self._add_to_corpus(parsed, key, k, next_key)  # You can imagine what this function does
                        if k == len(parsed) - 3 and next_key is None:
                            next_key = (parsed[k + 1], parsed[k + 2])
        self.last_key = next_key

    def _generate_text(self):
        start_word = self._grab_random_two_words()

        return start_word[0] + " & " + start_word[1]

    def _grab_random_two_words(self):
        start = np.random.randint(0, len(self._corpus))
        start_word = list(self._corpus.keys())[start]
        return start_word

    def _get_tweet(self):
        tweet = ''
        while tweet == '':
                pos_tweet = self._generate_text()
                if len(pos_tweet) < 280:
                    tweet = "today i am grateful for " + pos_tweet
                    break

        return tweet.strip().replace("\"","")

    def run(self):
        self._load_data()  # Here it loads the corpora and converts them into a transition matrix
        while True:
            try:
                tweet = self._get_tweet()  # Samples
                self._twitter_api.tweet(tweet)  # Posts to twitter
            except Exception as e:
                self._logger.error(e, exc_info=True)
                self._twitter_api.disconnect()
            time.sleep(self.sleep_timer)  # Every 10 minutes


def main():
    # Configure Logger
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # Get these from twitter, read tweepy's docs
    consumer_key = "vRQrPih3ZUSuy9PTdKlgD1W0y"
    consumer_secret = "cHbHpFjIFrITpURKDbeoPWwEO0kN5bzxk9addYnKQWOZuhtvHq"
    access_key = "1032048965942824960-a0JUz832vRqT80Sb5RPQ4xlPN14Byr"
    access_secret = "ia2vIDRGdpE1GVq7KT9trsHdsYHtSeSSIj9lVTPnuMAmp"

    documents = ["pride_and_prejudice.txt"]  # Specify the documents

    twitter_api = twitterAPI(consumer_key, consumer_secret, access_key, access_secret)
    bot = Bot(documents, twitter_api)

    bot.run()


if __name__ == "__main__":
    main()
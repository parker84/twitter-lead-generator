from decouple import config
import coloredlogs, logging
import time
import requests
import numpy as np
import pandas as pd
from tqdm import tqdm
import json
from datetime import datetime
logger = logging.getLogger(__name__)
coloredlogs.install(level=config('LOG_LEVEL'))

def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """
    r.headers["Authorization"] = f"Bearer {config('BEARER_TOKEN')}"
    r.headers["User-Agent"] = "v2UserTweetsPython"
    return r

def connect_to_endpoint(url, params=''):
    response = requests.request("GET", url, auth=bearer_oauth, params=params)
    if response.status_code == 429:
        logger.warn('429 status code, sleeping for 15 minutes')
        time.sleep(60*15)
        response = requests.request("GET", url, auth=bearer_oauth, params=params)
    if response.status_code != 200:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )
    return response.json()

def get_user_id_from_user_name(user_name):
    user_dict = connect_to_endpoint("https://api.twitter.com/2/users/by?usernames={}".format(user_name))
    return user_dict['data'][0]['id']

def clean_df(in_df):
    out_df = in_df.copy()
    for col in out_df.columns:
        if (
            isinstance(out_df[col].iloc[0], dict) or
            isinstance(out_df[col].iloc[0], list)
        ):
            out_df[col] = out_df[col].apply(json.dumps).astype(str)
        else:
            out_df[col] = out_df[col].astype(str)
    out_df.reset_index(inplace=True, drop=True)
    return out_df

def clean_user_df(in_df):
    out_df = in_df.copy()
    for metric in ['followers_count', 'following_count', 'tweet_count', 'listed_count']:
        out_df[metric] = [
            eval(row['public_metrics'])[metric]
            for ix, row in out_df.iterrows()
        ]
    out_df.drop('public_metrics', axis=1, inplace=True)
    links_in_bio = []
    for ix, row in out_df.iterrows():
        try:
            links_in_bio.append(eval(row['entities'])['url']['urls'][0]['expanded_url'])
        except Exception as err:
            links_in_bio.append(np.nan)
    out_df['link_in_bio'] = links_in_bio
    links_in_description = []
    for ix, row in out_df.iterrows():
        try:
            links_in_description.append(eval(row['entities'])['description']['urls'][0]['expanded_url'])
        except Exception as err:
            links_in_description.append(np.nan)
    out_df['link_in_description'] = links_in_description
    out_df.drop('entities', axis=1, inplace=True)
    out_df = out_df[[
        'username',  'followers_count', 'following_count',
        'description', 'name', 'location', 'url', 
        'tweet_count', 'listed_count',
        'link_in_bio', 'link_in_description',
        'id', 'verified', 'created_at', 'profile_image_url',
        'pinned_tweet_id', 'protected', 'scraped_at',
    ]]
    return out_df
    

class Scraper():

    def __init__(self, user_name, start_time=None, end_time=None) -> None:
        self.user_name = user_name
        self.start_time = start_time
        self.end_time = end_time
        logger.info(f'Getting user_id for {user_name}')
        self.user_id = get_user_id_from_user_name(user_name)

    def scrape_user_meta_data(self):
        params = {
            "user.fields": "created_at,description,public_metrics,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,url,username,verified,withheld"
        }
        url = f"https://api.twitter.com/2/users?ids={self.user_id}"
        json_response = connect_to_endpoint(url, params)
        user_meta_data_df = pd.DataFrame(json_response['data'])
        user_meta_data_df['scraped_at'] = str(datetime.now())
        return clean_df(user_meta_data_df)

    def scrape_followings_for_user(self):
        hundo_followings = self._scrape_100_followings_for_user()
        raw_users_followings = pd.DataFrame(hundo_followings['data'])
        while True:
            if "next_token" not in hundo_followings["meta"]:
                break
            else:
                next_token = hundo_followings["meta"]["next_token"]
                hundo_followings = self._scrape_100_followings_for_user(next_token)
                raw_users_followings = raw_users_followings.append(
                    pd.DataFrame(hundo_followings['data'])
                )
        users_followings = clean_df(raw_users_followings)
        users_followings['scraped_at'] = str(datetime.now())
        users_followings = clean_user_df(users_followings)
        return users_followings

    def scrape_followers_for_user(self):
        hundo_followers = self._scrape_100_followers_for_user()
        raw_users_followers = pd.DataFrame(hundo_followers['data'])
        while True:
            if "next_token" not in hundo_followers["meta"]:
                break
            else:
                next_token = hundo_followers["meta"]["next_token"]
                hundo_followers = self._scrape_100_followers_for_user(next_token)
                raw_users_followers = raw_users_followers.append(
                    pd.DataFrame(hundo_followers['data'])
                )
        users_followers = clean_df(raw_users_followers)
        users_followers['scraped_at'] = str(datetime.now())
        users_followers = clean_user_df(users_followers)
        return users_followers

    def scrape_tweets_for_user(self, last_n_hundred_tweets=1) -> pd.DataFrame:
        hundo_tweets = self._get_100_tweets_from_user()
        raw_user_timeline_df = pd.DataFrame(hundo_tweets['data'])
        for i in tqdm(range(last_n_hundred_tweets-1)):
            if "next_token" not in hundo_tweets["meta"]:
                break
            else:
                next_token = hundo_tweets["meta"]["next_token"]
                hundo_tweets = self._get_100_tweets_from_user(next_token)
                raw_user_timeline_df = raw_user_timeline_df.append(
                    pd.DataFrame(hundo_tweets['data'])
                )
        user_timeline_df = clean_df(raw_user_timeline_df)
        user_timeline_df['row_created_at'] = str(datetime.now())
        return user_timeline_df

    def _get_100_tweets_from_user(self, pagination_token=None) -> dict:
        url = "https://api.twitter.com/2/users/{}/tweets".format(self.user_id)
        params = {
            "tweet.fields": "attachments,author_id,context_annotations,created_at,entities,id,in_reply_to_user_id,lang,possibly_sensitive,public_metrics,referenced_tweets,source,text,withheld",            "max_results": 100,
            "pagination_token": pagination_token,
            "start_time": self.start_time,
            "end_time": self.end_time
        }
        json_response = connect_to_endpoint(url, params)
        return json_response
    
    def _scrape_100_followers_for_user(self, pagination_token=None) -> dict:
        params = {
            "user.fields": "created_at,description,public_metrics,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,url,username,verified,withheld",
            "pagination_token": pagination_token
        }
        url = f"https://api.twitter.com/2/users/{self.user_id}/followers"
        json_response = connect_to_endpoint(url, params)
        return json_response
    
    def _scrape_100_followings_for_user(self, pagination_token=None) -> dict:
        params = {
            "user.fields": "created_at,description,public_metrics,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,url,username,verified,withheld",
            "pagination_token": pagination_token
        }
        url = f"https://api.twitter.com/2/users/{self.user_id}/following"
        json_response = connect_to_endpoint(url, params)
        return json_response
    
if __name__ == '__main__':
    scraper = Scraper('parker_brydon')
    user_meta_data = scraper.scrape_user_meta_data()
    user_timeline = scraper.scrape_tweets_for_user(last_n_hundred_tweets=2)
    user_followers = scraper.scrape_followers_for_user()
    user_followings = scraper.scrape_followings_for_user()
    import ipdb; ipdb.set_trace()
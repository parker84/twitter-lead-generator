from decouple import config
import coloredlogs, logging
import time
import requests
import pandas as pd
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
    return out_df

def scrape_user_meta_data(user_id):
    params = {
        "user.fields": "created_at,description,public_metrics,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,url,username,verified,withheld"
    }
    url = f"https://api.twitter.com/2/users?ids={user_id}"
    json_response = connect_to_endpoint(url, params)
    user_meta_data_df = pd.DataFrame(json_response['data'])
    user_meta_data_df['scraped_at'] = str(datetime.now())
    return clean_df(user_meta_data_df)
    
if __name__ == '__main__':
    user_id = get_user_id_from_user_name('parker_brydon')
    user_meta_data_df = scrape_user_meta_data(user_id)
    import ipdb; ipdb.set_trace()
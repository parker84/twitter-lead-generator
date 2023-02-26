import streamlit as st
from PIL import Image
import pandas as pd
from scraper import Scraper, ScrapeEngagement
import coloredlogs, logging
from decouple import config
logger = logging.getLogger(__name__)
coloredlogs.install(level=config('LOG_LEVEL'))

# ----helpers
@st.experimental_memo
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')



st.set_page_config(page_icon='./assets/eagle_1f985.png', page_title='Twitter Lead Generator')

st.markdown('## 🦅 Generate Leads from Twitter')
col1, col2 = st.columns((2,1))
with col1:
    st.markdown(
        f"""
        **Generate Leads From Twitter by Looking Up and Downloading to CSV any User's**:
        1. **Followers** (ex: if you want to find and reach out to everyone who is following a specific user)
        2. **Following** (ex: if you want to find and reach out to everyone who a specific user is following)
        3. **Tweets** (ex: if you want to lookup and download tweets from a user to get a pulse on their engagement)
        """
    )
with col2:
    image = Image.open('./assets/DALL·E 2023-01-08 17.53.04 - futuristic knight robot on a horse in cyberpunk theme.png')
    st.image(image)

submitted = False
with st.form("my_form"):
    username = st.text_input('Enter a Username', '@parker_brydon')
    username = username.strip('@')
    get_following = st.checkbox("Get Who They're Following", True)
    get_followers = st.checkbox("Get Their Followers")
    get_engagement_metrics = st.checkbox('Get Engagment Metrics per User')
    min_follower_count_to_get_engagement_metrics = st.slider('Min Follower Count for Engagement Metrics', min_value=0, max_value=100000, step=1000)
    if min_follower_count_to_get_engagement_metrics > 0 and get_engagement_metrics == False:
        st.warning(f"You've indicated a min follower count ({min_follower_count_to_get_engagement_metrics}), but you haven't checked off the box to get engagement metrics, so we no engagement metrics will be added. If you want them added, please check the Engagement Metrics box.")
    get_tweets = st.checkbox("Get Their Tweets")
    # Every form must have a submit button.
    submitted = st.form_submit_button("Generate Leads")

with st.form('upload_form'):
    st.markdown('Already have the followers scraped and want to add engagement metrics 👇🏻')
    username_for_upload = st.text_input('Enter a Username', '@parker_brydon')
    username_for_upload = username_for_upload.strip('@')
    min_follower_count_to_get_engagement_metrics_upload_form = st.slider('Min Follower Count for Engagement Metrics', min_value=0, max_value=100000, step=1000)
    uploaded_file = st.file_uploader("Upload a csv of followers to add engagement metrics", type='csv')
    submitted_upload_form = st.form_submit_button('Get Engagement Metrics')

if submitted:
    st.success(
        f"""Successfully submitted, now scraping: for user: {username}, getting their: {'followers, ' if get_followers else ''}{'following, ' if get_following else ''}{'tweets, ' if get_tweets else ''}
        """
    )

    scraper = Scraper(username)
    engagement_scraper = ScrapeEngagement(username)

    if get_following:
        st.markdown('## 🔭 Following')
        with st.spinner(text=f"Scraping who `{username}` is following"):
            followings_df = scraper.scrape_followings_for_user()
        if get_engagement_metrics:
            with st.spinner(text=f"Scraping engagement metrics for followings, with follower counts >= {min_follower_count_to_get_engagement_metrics}"):
                metrics_df = engagement_scraper.scrape_metrics_for_last_hundred_tweets_for_users(
                    followings_df[followings_df.followers_count >= min_follower_count_to_get_engagement_metrics],
                    followers_or_followings='followings'
                )
                followings_df = followings_df.merge(metrics_df, on='username', how='left')
        st.dataframe(followings_df)
        followings_df.to_csv(f'./data/{username}_followings_df.csv')
        csv = convert_df(followings_df)
        st.download_button(
            "Press to Download",
            csv,
            f"{username}_followings.csv",
            "text/csv"
        )
    
    if get_followers:
        st.markdown('## 🔬 Followers')
        with st.spinner(text=f"Scraping `{username}`'s followers"):
            followers_df = scraper.scrape_followers_for_user()
        if get_engagement_metrics:
            logger.info('Getting engagement metrics for followers')
            with st.spinner(text=f"Scraping engagement metrics_df for followers, with follower counts >= {min_follower_count_to_get_engagement_metrics}"):
                metrics_df = engagement_scraper.scrape_metrics_for_last_hundred_tweets_for_users(
                    followers_df[followers_df.followers_count >= min_follower_count_to_get_engagement_metrics],
                    followers_or_followings='followers'
                )
                followers_df = followers_df.merge(metrics_df, on='username', how='left')
        st.dataframe(followers_df)
        followings_df.to_csv(f'./data/{username}_followers_df.csv')
        csv = convert_df(followers_df)
        st.download_button(
            "Press to Download",
            csv,
            f"{username}_followers.csv",
            "text/csv"
        )
    
    if get_tweets:
        st.markdown('## 🗣 Tweets')
        with st.spinner(text=f"Scraping `{username}`'s tweets"):
            tweets_df = scraper.scrape_tweets_for_user(last_n_hundred_tweets=2)
        st.dataframe(tweets_df)
        tweets_df.to_csv(f'./data/{username}_tweets_df.csv')
        csv = convert_df(tweets_df)
        st.download_button(
            "Press to Download",
            csv,
            f"{username}_tweets.csv",
            "text/csv"
        )


if submitted_upload_form:
    followers_df = pd.read_csv(uploaded_file)
    followers_df = followers_df[
        [isinstance(val, int) for val in followers_df['followers_count']]
    ].infer_objects()
    followers_df['user_id'] = followers_df['user_id'].astype(int)
    followers_df['followers_count'] = followers_df['followers_count'].astype(int)
    engagement_scraper = ScrapeEngagement(username_for_upload)
    with st.spinner(text=f"Scraping engagement metrics_df for followers, with follower counts >= {min_follower_count_to_get_engagement_metrics_upload_form}"):
        metrics_df = engagement_scraper.scrape_metrics_for_last_hundred_tweets_for_users(
            followers_df[followers_df.followers_count >= min_follower_count_to_get_engagement_metrics_upload_form],
            followers_or_followings='followers'
        )
    followers_df = followers_df.merge(metrics_df, on='username', how='left')
    st.dataframe(followers_df)
    followers_df.to_csv(f'./data/{username_for_upload}_followers_df.csv')
    csv = convert_df(followers_df)
    st.download_button(
        "Press to Download",
        csv,
        f"{username_for_upload}_followers.csv",
        "text/csv"
    )
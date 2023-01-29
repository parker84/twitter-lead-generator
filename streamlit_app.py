import streamlit as st
from PIL import Image
from scraper import Scraper, scrape_metrics_for_last_hundred_tweets_for_users

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

if submitted:
    st.success(
        f"""Successfully submitted, now scraping: for user: {username}, getting their: {'followers, ' if get_followers else ''}{'following, ' if get_following else ''}{'tweets, ' if get_tweets else ''}
        """
    )

    scraper = Scraper(username)

    if get_following:
        st.markdown('## 🔭 Following')
        with st.spinner(text=f"Scraping who `{username}` is following"):
            followings_df = scraper.scrape_followings_for_user()
        if get_engagement_metrics:
            with st.spinner(text=f"Scraping engagement metrics for followings, with follower counts >= {min_follower_count_to_get_engagement_metrics}"):
                metrics_df = scrape_metrics_for_last_hundred_tweets_for_users(
                    followings_df[followings_df.followers_count >= min_follower_count_to_get_engagement_metrics]
                )
                followings_df = followings_df.merge(metrics_df, on='username', how='left')
        st.dataframe(followings_df)

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
            with st.spinner(text=f"Scraping engagement metrics_df for followers, with follower counts >= {min_follower_count_to_get_engagement_metrics}"):
                metrics_df = scrape_metrics_for_last_hundred_tweets_for_users(
                    followers_df[followers_df.followers_count >= min_follower_count_to_get_engagement_metrics]
                )
                followers_df = followers_df.merge(metrics_df, on='username', how='left')
        st.dataframe(followers_df)

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

        csv = convert_df(tweets_df)
        st.download_button(
            "Press to Download",
            csv,
            f"{username}_tweets.csv",
            "text/csv"
        )




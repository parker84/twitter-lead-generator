import streamlit as st
from decouple import config
from PIL import Image
from scraper import Scraper

# ----helpers
@st.experimental_memo
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')



st.set_page_config(page_icon='🦅', page_title='Twitter Lead Generator')

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




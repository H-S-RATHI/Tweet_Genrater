from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
import google.generativeai as genai
import os
import logging
import traceback

# Flask setup
app = Flask(__name__)
CORS(app)  # Add CORS support

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Configure Gemini API using environment variable
API_KEY ="AIzaSyCAfrJKPuP1GpBEdUl1j0vWAevWBXuTSlA"
if not API_KEY:
    logging.error("Gemini API key is not set in environment variables")
    API_KEY = ""  # Fallback, though this will cause issues

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TWEETS_FILE = os.path.join(BASE_DIR, "tweets.csv")
LINKEDIN_FILE = os.path.join(BASE_DIR, "linkedin.csv")
FACEBOOK_FILE = os.path.join(BASE_DIR, "facebook.csv")
BIODATA_FILE = os.path.join(BASE_DIR, "biodata.txt")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate_tweet", methods=["POST"])
def generate_tweet():
    try:
        # Get the topic from the request
        data = request.get_json()
        topic = data.get("topic", "").strip() if data else ""

        # Log received topic for debugging
        logging.debug(f"Received topic: {topic}")

        # Validate file existence and required columns
        if not os.path.exists(TWEETS_FILE):
            logging.error(f"tweets.csv not found at {TWEETS_FILE}")
            return jsonify({"error": "tweets.csv file not found!"}), 400

        tweets_df = pd.read_csv(TWEETS_FILE)
        if "TweetText" not in tweets_df.columns:
            return jsonify({"error": "'TweetText' column missing in tweets.csv!"}), 400

        # Load context from different sources
        linkedin_context = ""
        if os.path.exists(LINKEDIN_FILE):
            linkedin_df = pd.read_csv(LINKEDIN_FILE)
            for _, row in linkedin_df.iterrows():
                linkedin_context += f"LinkedIn Post: {row.get('postText', '')}\n\n"

        facebook_context = ""
        if os.path.exists(FACEBOOK_FILE):
            facebook_df = pd.read_csv(FACEBOOK_FILE)
            for _, row in facebook_df.iterrows():
                facebook_context += f"Facebook Author: {row.get('Author', '')}\nContent: {row.get('Content', '')}\nPostedAt: {row.get('Posted At', '')}\n\n"

        biodata_context = ""
        if os.path.exists(BIODATA_FILE):
            with open(BIODATA_FILE, "r") as file:
                biodata_context = file.read().strip()

        # Combine all contexts
        context = ""
        for _, row in tweets_df.iterrows():
            context += f"Author: {row.get('Author', '')}\nType: {row.get('Type', '')}\nTweet: {row.get('TweetText', '')}\nCreatedAt: {row.get('CreatedAt', '')}\nMedia: {row.get('Media', '')}\n\n"
        context += linkedin_context + facebook_context + f"Biodata:\n{biodata_context}\n\n"

        # Add the user's topic to the prompt if provided
        if topic:
            context += f"Topic: {topic}\n\n"

        # Refined Prompt for Gemini API
        prompt = (
        f"forgot previous all data that you have stored"
        f"DO NOT WRITE THE TWEET THAT YOU WROTE LAST TIME"
        f"if Topic is provided by the user, generate tweets specifically based on the topic {topic}, derived from all available data, that is in {context},{linkedin_context},{facebook_context},{biodata_context} \n"
        f"Based on the following information from this person's past posts across multiple platforms {context},{linkedin_context},{facebook_context},{biodata_context} create 10 realistic tweets that sound like they were written by this person themselves. "
        f"The tone, style, and beliefs should be consistent with the person's previous posts. Please ensure the following:\n"
        f"- Do **not** generate any tweets that mention the current or recent activities, events, or achievements (e.g., 'Just finished a presentation,' 'Launched a new product,' 'Had a meeting,' 'Sold out,' etc.). You do not have any knowledge of what the person is doing at this moment.\n"
        f"- The tweet must not include any references to real-time events, or anything that would imply immediate action or recent accomplishments.\n"
        f"Here’s the data to help create the tweets:\n"
        f"- Previous Tweets: {context}\n"
        f"- LinkedIn Posts: {linkedin_context}\n"
        f"- Facebook Posts: {facebook_context}\n"
        f"- Biodata: {biodata_context}\n\n"
        f"Generate tweets that reflect the person’s **past** actions, thoughts, or ideas, without any real-time or current event mentions."
        )



        # Generate tweets using Gemini API
        response = model.generate_content(prompt)
        
        # Ensure valid response and split tweets
        if response and response.text:
            generated_tweets = [tweet.strip() for tweet in response.text.split("\n") if tweet.strip()]
            
            # Log generated tweets for debugging
            logging.debug(f"Generated tweets: {generated_tweets}")

            return jsonify({"tweets": generated_tweets}), 200
        else:
            return jsonify({"error": "No tweets could be generated"}), 400

    except Exception as e:
        # More detailed error logging
        logging.error(f"Error in generate_tweet: {str(e)}")
        logging.error(traceback.format_exc())
        
        return jsonify({
            "error": f"An unexpected error occurred: {str(e)}"
        }), 500

if __name__ == "__main__":
    app.run(debug=True)
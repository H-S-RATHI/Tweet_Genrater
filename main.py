from flask import Flask, render_template, request, jsonify
import pandas as pd
import google.generativeai as genai
import os

# Flask setup
app = Flask(__name__)

# Configure Gemini API
genai.configure(api_key="AIzaSyCAfrJKPuP1GpBEdUl1j0vWAevWBXuTSlA")  # Replace with your Gemini API key
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
        topic = data.get("topic", "").strip()  # Get topic, default to empty if not provided

        # Load tweets.csv
        if not os.path.exists(TWEETS_FILE):
            return jsonify({"error": "tweets.csv file not found!"}), 400
        tweets_df = pd.read_csv(TWEETS_FILE)
        if "TweetText" not in tweets_df.columns:
            return jsonify({"error": "'TweetText' column missing in tweets.csv!"}), 400

        # Load linkedin.csv
        linkedin_context = ""
        if os.path.exists(LINKEDIN_FILE):
            linkedin_df = pd.read_csv(LINKEDIN_FILE)
            for _, row in linkedin_df.iterrows():
                linkedin_context += f"LinkedIn Post: {row['postText']}\n\n"

        # Load facebook.csv
        facebook_context = ""
        if os.path.exists(FACEBOOK_FILE):
            facebook_df = pd.read_csv(FACEBOOK_FILE)
            for _, row in facebook_df.iterrows():
                facebook_context += f"Facebook Author: {row['Author']}\nContent: {row['Content']}\nPostedAt: {row['Posted At']}\n\n"

        # Load biodata.txt
        biodata_context = ""
        if os.path.exists(BIODATA_FILE):
            with open(BIODATA_FILE, "r") as file:
                biodata_context = file.read().strip()

        # Combine all contexts
        context = ""
        for _, row in tweets_df.iterrows():
            context += f"Author: {row['Author']}\nType: {row['Type']}\nTweet: {row['TweetText']}\nCreatedAt: {row['CreatedAt']}\nMedia: {row['Media']}\n\n"
        context += linkedin_context + facebook_context + f"Biodata:\n{biodata_context}\n\n"

        # Add the user's topic to the prompt if provided
        if topic:
            context += f"Topic: {topic}\n\n"

# Refined Prompt for Gemini API
        prompt = (
            f"Based on the following information from this person's past posts across multiple platforms "
            f"(Twitter, LinkedIn, Facebook, and personal bio), create 10 realistic tweets that sound like they were written by this person themselves. "
            f"The tone, style, and beliefs should be consistent with the person's previous posts. "
            f"Ensure that:\n"
            f"- The content of the tweet is relevant to the context from their past posts, including any topics they've previously discussed.\n"
            f"- The tweet reflects the person’s usual interests, expertise, or lifestyle.\n"
            f"- The tweet doesn't include any fictional or inaccurate statements like locations, new projects, or unrelated ventures unless those are part of their past content.\n"
            f"- The tweets should not repeat or replicate previous posts, but should feel like a natural continuation of their conversation or public persona.\n\n"
            f"Here’s the data:\n"
            f"if Topic is provided by the user, generate tweets specifically based on the topic {topic}, derived from all available data:\n"
            f"- Previous Tweets: {context}\n"
            f"- LinkedIn Posts: {linkedin_context}\n"
            f"- Facebook Posts: {facebook_context}\n"
            f"- Biodata: {biodata_context}\n\n"
            f"Generate tweets that align with the above content and maintain the person’s authentic voice."
        )

        # Generate tweets using Gemini API
        response = model.generate_content(prompt)
        generated_tweets = response.text.strip()

        return jsonify({"tweets": generated_tweets.split("\n")}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)

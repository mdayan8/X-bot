# app.py
import os
import logging
from flask import Flask
import telebot
import tweepy
import requests
import threading
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Your API Credentials
TELEGRAM_TOKEN = "7159155946:AAE15MlJDyUqpEFpORHooSa4HLQ2c6qOORQ"
TWITTER_CREDS = {
    "bearer_token": "AAAAAAAAAAAAAAAAAAAAAHSozgEAAAAAJy3DxVngUV0bJ7g%2F4F0OULdo%2FjY%3DidljfAcwPrQSOCFmtFzKObgBurPlXdgHJor6dUz3WqXPdrGZ6r",
    "consumer_key": "i9D4LJKHBpdsurAjOj2BGFpVf",
    "consumer_secret": "GOTR0aRkfUVxH5Em0xlNa5vFQWsstAkoZu0TkbcL8km9BPiYJR",
    "access_token": "1566361997029289984-GbIoSst9C2zmTxuJ29Y71FxfYjUE31",
    "access_secret": "k9h7PjiptE4CTTPnPFDk1ImbbCorfsA6H6Mmfw1mtKay7"
}
DEEPSEEK_API_KEY = "sk-beef174c9b364990bd05db8498802282"

# Initialize Twitter Client
try:
    twitter_client = tweepy.Client(
        bearer_token=TWITTER_CREDS["bearer_token"],
        consumer_key=TWITTER_CREDS["consumer_key"],
        consumer_secret=TWITTER_CREDS["consumer_secret"],
        access_token=TWITTER_CREDS["access_token"],
        access_token_secret=TWITTER_CREDS["access_secret"]
    )
    logger.info("Twitter client initialized successfully")
except Exception as e:
    logger.error(f"Twitter initialization failed: {e}")
    raise

# Initialize Telegram Bot
try:
    bot = telebot.TeleBot(TELEGRAM_TOKEN)
    logger.info("Telegram bot initialized")
except Exception as e:
    logger.error(f"Telegram bot initialization failed: {e}")
    raise

def get_trending_topics():
    """Fetch trending topics in India"""
    try:
        response = twitter_client.get_place_trends(id=23424848)  # India WOEID
        return [trend['name'] for trend in response[0]['trends'][:5]
    except Exception as e:
        logger.error(f"Trending topics error: {e}")
        return ["AI Innovation", "SaaS Trends", "Tech Startups"]

def generate_tweet_content(topic: str) -> str:
    """Generate human-like tweet content"""
    try:
        trends = get_trending_topics()
        prompt = f"""Create a viral tweet about {topic} with:
        - Engaging story hook
        - 1 surprising statistic
        - 2 relevant emojis
        - 1-2 hashtags from: {', '.join(trends)}
        - Conversational tone
        
        Example:
        "Automated 100+ hours with AI 🤖
        Our tool boosted productivity by 40% ↑
        Key insight: Simple > complex
        #TechInnovation #AI"
        
        Now create about: {topic}"""

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.75,
                "max_tokens": 280
            },
            timeout=20
        )
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        logger.error(f"Generation error: {e}")
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Welcome message with instructions"""
    help_text = """🚀 AI Tweet Assistant\n\nUsage:\n/post [topic]\nExample:\n/post AI-Powered Analytics"""
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['post'])
def handle_post_request(message):
    """Handle tweet creation"""
    try:
        topic = message.text.split('/post', 1)[-1].strip()
        if not topic or len(topic) < 5:
            raise ValueError("Provide a valid topic (min 5 chars)")
            
        bot.send_message(message.chat.id, "🔄 Crafting your tweet...")
        content = generate_tweet_content(topic)
        
        if not content:
            raise ValueError("Failed to generate quality content")
            
        response = twitter_client.create_tweet(text=content)
        tweet_url = f"https://twitter.com/user/status/{response.data['id']}"
        
        confirmation = f"""✅ Tweet Published!\n\n{content}\n\n🔗 {tweet_url}"""
        bot.send_message(message.chat.id, confirmation)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        bot.send_message(message.chat.id, f"❌ Error: {str(e)}")

def run_bot():
    """Run Telegram bot with restart logic"""
    logger.info("Starting bot polling...")
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            logger.error(f"Polling error: {e}")
            logger.info("Restarting bot in 5 seconds...")
            time.sleep(5)

@app.route('/')
def health_check():
    return "🤖 Bot Operational - Send /start to Telegram bot"

if __name__ == '__main__':
    # Start bot thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000)

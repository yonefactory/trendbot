import os
import asyncio
import json
import datetime
import telegram
import tweepy
import time
from dotenv import load_dotenv
from googleapiclient.discovery import build
from pytrends.request import TrendReq

# 환경 변수 로드
load_dotenv()

# API 키 및 텔레그램 설정
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHAT_ID_GROUP = os.getenv("CHAT_ID_GROUP")
TEST_MODE = os.getenv("TEST_MODE", "True").lower() == "true"

YOUTUBE_DATA_FILE = "youtube_trends.json"

# Twitter API v2 클라이언트 설정
twitter_client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)

# Google Trends API 설정
pytrends = TrendReq(hl="ko-KR", tz=540, requests_args={"headers": {"User-Agent": "Mozilla/5.0"}})

# Twitter 트렌드 검색 (Rate Limit Handling 추가)
async def fetch_twitter_trends():
    trending_keywords = []
    retry_count = 3

    for attempt in range(retry_count):
        try:
            response = twitter_client.search_recent_tweets(query="유튜브", max_results=5)
            if response.data:
                trending_keywords = [tweet.text.split(" ")[0] for tweet in response.data[:3]]
            break
        except tweepy.TooManyRequests:
            wait_time = 15 * (attempt + 1)
            print(f"🚨 Twitter API 요청 제한 초과. {wait_time}초 대기 후 재시도...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"트위터 검색 오류: {e}")
            break
    
    return trending_keywords

# Google Trends 검색 (User-Agent 변경)
async def fetch_google_trends():
    try:
        pytrends.build_payload(kw_list=["트렌드"], geo="KR", timeframe="now 1-d")
        trending_searches = pytrends.trending_searches()
        return trending_searches[0].tolist()[:3]
    except Exception as e:
        print(f"Google Trends 오류: {e}")
        return []

# Telegram 메시지 전송
async def send_trend_message():
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    message = "🔥 *지금 핫이슈* 🔥\n\n"

    twitter_trends = await fetch_twitter_trends()
    google_trends = await fetch_google_trends()

    if twitter_trends:
        message += "\n🐦 *트위터 실시간 키워드*\n"
        for keyword in twitter_trends:
            message += f"- {keyword}\n"

    if google_trends:
        message += "\n📈 *Google Trends 실시간 검색어*\n"
        for keyword in google_trends:
            message += f"- {keyword}\n"

    chat_ids = [CHAT_ID] if TEST_MODE else [CHAT_ID, CHAT_ID_GROUP]
    for chat_id in chat_ids:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown", disable_web_page_preview=True)

if __name__ == "__main__":
    asyncio.run(send_trend_message())

import os
import asyncio
import requests
import telegram
from dotenv import load_dotenv
from googleapiclient.discovery import build
import tweepy

# 환경 변수 로드
load_dotenv()

# API 키 및 텔레그램 설정
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET_KEY = os.getenv("TWITTER_API_SECRET_KEY")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHAT_ID_GROUP = os.getenv("CHAT_ID_GROUP")

# 비동기 YouTube 트렌드 가져오기
async def fetch_youtube_trends():
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        chart="mostPopular",
        regionCode="KR",
        maxResults=1
    )
    response = request.execute()

    videos = [
        (item["snippet"]["title"], f"https://www.youtube.com/watch?v={item['id']}", item["snippet"]["thumbnails"]["high"]["url"])
        for item in response.get("items", [])
    ]
    return videos

# Twitter 트렌드 가져오기 (동기 방식)
def fetch_twitter_trends():
    try:
        auth = tweepy.OAuth1UserHandler(
            TWITTER_API_KEY, TWITTER_API_SECRET_KEY,
            TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
        )
        api = tweepy.API(auth)
        
        trends = api.get_place_trends(id=1)  # 전 세계 트렌드
        trends_data = [
            (trend["name"], f"https://twitter.com/search?q={trend['name'].replace(' ', '%20')}&src=trend_click")
            for trend in trends[0]["trends"][:1]  # 상위 1개만 가져옴
        ]
        return trends_data
    
    except Exception as e:
        print(f"트위터 트렌드 오류: {e}")
        return []

# 비동기 Twitter 트렌드 실행
async def fetch_twitter_trends_async():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, fetch_twitter_trends)

# 텔레그램 메시지 보내기
async def send_trend_message():
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    message = "🔥 *지금 핫이슈* 🔥\n\n"

    youtube_trends, twitter_trends = await asyncio.gather(
        fetch_youtube_trends(),
        fetch_twitter_trends_async()
    )

    if youtube_trends:
        message += "🎥 *유튜브 인기 영상*\n"
        for title, link, _ in youtube_trends:
            message += f"- [{title}]({link})\n"

    if twitter_trends:
        message += "\n🐦 *트위터 실시간 트렌드*\n"
        for title, link in twitter_trends:
            message += f"- [{title}]({link})\n"

    # 텔레그램 메시지 전송 (비동기 병렬 전송)
    await asyncio.gather(
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown", disable_web_page_preview=True),
        bot.send_message(chat_id=CHAT_ID_GROUP, text=message, parse_mode="Markdown", disable_web_page_preview=True),
    )

    # 썸네일 전송 (유튜브 영상)
    for title, link, thumbnail in youtube_trends:
        await asyncio.gather(
            bot.send_photo(chat_id=CHAT_ID, photo=thumbnail, caption=f"[{title}]({link})", parse_mode="Markdown"),
            bot.send_photo(chat_id=CHAT_ID_GROUP, photo=thumbnail, caption=f"[{title}]({link})", parse_mode="Markdown"),
        )

# 메인 실행
if __name__ == "__main__":
    asyncio.run(send_trend_message())

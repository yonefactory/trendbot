import os
import requests
import telegram
from googleapiclient.discovery import build
import tweepy
from dotenv import load_dotenv
import asyncio

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

# YouTube Data API로 트렌드 가져오기
async def fetch_youtube_trends():
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    # 트렌딩 영상 리스트 가져오기
    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        chart="mostPopular",
        regionCode="KR",  # 한국(KR)으로 설정
        maxResults=3  # 상위 3개만 가져옴
    )
    response = request.execute()
    
    videos = []
    for item in response.get("items", []):
        title = item["snippet"]["title"]
        link = f"https://www.youtube.com/watch?v={item['id']}"
        thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
        # 여기서 릴스를 필터링하려면 더 세부적인 필터링이 필요하지만, 일단 인기 영상만 가져옵니다.
        videos.append((title, link, thumbnail))
    
    return videos

# Twitter API로 트렌드 가져오기
async def fetch_twitter_trends():
    try:
        auth = tweepy.OAuth1UserHandler(
            TWITTER_API_KEY, TWITTER_API_SECRET_KEY,
            TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
        )
        api = tweepy.API(auth)
        
        # 트렌드 가져오기 (WOEID: Worldwide, 지역별 트렌드를 가져올 수 있음)
        trends = api.get_place_trends(id=1)  # 1은 전세계 트렌드 (Worldwide)
        
        trends_data = []
        for trend in trends[0]["trends"][:5]:  # 상위 5개 트렌드
            title = trend["name"]
            link = f"https://twitter.com/search?q={title.replace(' ', '%20')}&src=trend_click"
            trends_data.append((title, link))
        
        return trends_data
    
    except Exception as e:
        print(f"트위터 트렌드 가져오기 중 오류 발생: {e}")
        return []  # 오류 발생 시 빈 리스트 반환

# 텔레그램 메시지 보내기
async def send_trend_message():
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    
    # 메시지 초기화
    message = "\U0001F4E2 *오늘의 SNS 트렌드*\n\n"
    
    youtube_trends = await fetch_youtube_trends()  # 비동기 함수 호출
    if youtube_trends:
        message += "\U0001F525 *유튜브 인기 영상*\n"
        for title, link, thumbnail in youtube_trends:
            message += f"- [{title}]({link})\n"
    
    twitter_trends = await fetch_twitter_trends()  # 비동기 함수 호출
    if twitter_trends:
        message += "\n\U0001F426 *트위터 실시간 트렌드*\n"
        for title, link in twitter_trends:
            message += f"- [{title}]({link})\n"
    
    # 텔레그램 메시지 전송
    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown", disable_web_page_preview=True)
    
    # 유튜브 썸네일 전송
    for title, link, thumbnail in youtube_trends:
        await bot.send_photo(chat_id=CHAT_ID, photo=thumbnail, caption=f"[{title}]({link})", parse_mode="Markdown")

# 메인 실행 함수
if __name__ == "__main__":
    asyncio.run(send_trend_message())  # 비동기 함수 실행

import os
import asyncio
import json
import datetime
import telegram
import tweepy
from dotenv import load_dotenv
from googleapiclient.discovery import build
from pytrends.request import TrendReq

# 환경 변수 로드
load_dotenv()

# API 키 및 텔레그램 설정
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")  # Twitter API v2 인증용 추가
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHAT_ID_GROUP = os.getenv("CHAT_ID_GROUP")
TEST_MODE = os.getenv("TEST_MODE", "True").lower() == "true"  # 기본값 True

YOUTUBE_DATA_FILE = "youtube_trends.json"

# Twitter API v2 클라이언트 설정
try:
    twitter_client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)
    print("✅ Twitter API 인증 성공!")
except Exception as e:
    print(f"🚨 Twitter API 인증 실패: {e}")

# Google Trends API 설정
pytrends = TrendReq(hl="ko-KR", tz=540)

# 기존 저장된 유튜브 영상 목록 불러오기
def load_previous_videos():
    if os.path.exists(YOUTUBE_DATA_FILE):
        with open(YOUTUBE_DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return []

# 새로운 유튜브 영상 목록 저장
def save_videos(videos):
    with open(YOUTUBE_DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(videos, file, ensure_ascii=False, indent=4)

# 1️⃣ 최근 24시간 내 업로드된 인기 영상 (한국 한정, 3개)
async def fetch_youtube_trends():
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    published_after = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).isoformat() + "Z"

    request = youtube.search().list(
        part="snippet",
        maxResults=3,  # 3개로 제한
        order="viewCount",
        publishedAfter=published_after,
        regionCode="KR",  # 한국 한정
        type="video"
    )
    response = request.execute()

    previous_videos = load_previous_videos()
    videos = []

    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        link = f"https://www.youtube.com/watch?v={video_id}"
        thumbnail = item["snippet"]["thumbnails"]["high"]["url"]

        if video_id not in previous_videos:
            videos.append((title, link, thumbnail))

    save_videos([video[1].split("v=")[-1] for video in videos])
    return videos

# 2️⃣ Twitter API v2를 사용한 트렌드 키워드 검색
async def fetch_twitter_trends():
    trending_keywords = []
    try:
        # "유튜브" 같은 핫한 키워드 검색
        response = twitter_client.search_recent_tweets(query="유튜브", max_results=10)
        if response.data:
            trending_keywords = [tweet.text.split(" ")[0] for tweet in response.data[:3]]
    except Exception as e:
        print(f"트위터 검색 오류: {e}")
    
    return trending_keywords

# 3️⃣ Google Trends API로 한국 인기 검색어 가져오기
async def fetch_google_trends():
    try:
        pytrends.build_payload(kw_list=["트렌드"], geo="KR")
        trending_searches = pytrends.trending_searches(pn="south_korea")
        return trending_searches[0].tolist()[:3]  # 상위 3개 검색어 반환
    except Exception as e:
        print(f"Google Trends 오류: {e}")
        return []

# 4️⃣ Twitter + Google Trends 기반 유튜브 검색
async def fetch_youtube_trends_from_trends():
    twitter_trends, google_trends = await asyncio.gather(
        fetch_twitter_trends(),
        fetch_google_trends()
    )
    
    trends = list(set(twitter_trends + google_trends))[:3]  # 중복 제거 후 3개만 선택
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    videos = []

    for trend in trends:
        request = youtube.search().list(
            part="snippet",
            q=trend,
            maxResults=1,
            order="viewCount",
            type="video",
            regionCode="KR"
        )
        response = request.execute()

        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            link = f"https://www.youtube.com/watch?v={video_id}"
            thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
            videos.append((title, link, thumbnail))

    return videos

# 5️⃣ 모든 트렌드 데이터 통합
async def fetch_all_youtube_trends():
    youtube_trends, trend_based_videos = await asyncio.gather(
        fetch_youtube_trends(),
        fetch_youtube_trends_from_trends()
    )

    all_trends = list({v[1]: v for v in youtube_trends + trend_based_videos}.values())[:3]  # 총 3개로 제한
    return all_trends

# 6️⃣ 텔레그램 메시지 전송
async def send_trend_message():
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    message = "🔥 *지금 핫이슈* 🔥\n\n"

    youtube_trends = await fetch_all_youtube_trends()
    twitter_trends = await fetch_twitter_trends()

    if youtube_trends:
        message += "🎥 *유튜브 인기 영상*\n"
        for title, link, _ in youtube_trends:
            message += f"- [{title}]({link})\n"

    if twitter_trends:
        message += "\n🐦 *트위터 실시간 키워드*\n"
        for keyword in twitter_trends:
            message += f"- {keyword}\n"

    # 채팅 ID 목록 설정 (TEST_MODE가 True면 CHAT_ID_GROUP 제외)
    chat_ids = [CHAT_ID] if TEST_MODE else [CHAT_ID, CHAT_ID_GROUP]

    # 텍스트 메시지 전송
    for chat_id in chat_ids:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown", disable_web_page_preview=True)

    # 이미지(썸네일) 전송
    for title, link, thumbnail in youtube_trends:
        for chat_id in chat_ids:
            await bot.send_photo(chat_id=chat_id, photo=thumbnail, caption=f"[{title}]({link})", parse_mode="Markdown")

# 7️⃣ 메인 실행
if __name__ == "__main__":
    asyncio.run(send_trend_message())

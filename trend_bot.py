import requests
import telegram
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import asyncio

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

async def fetch_youtube_trends():
    try:
        url = "https://www.youtube.com/feed/trending"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        print(f"유튜브 응답 코드: {response.status_code}")
        if response.status_code != 200:
            print("유튜브 응답 오류 발생")
            return []
        
        response.raise_for_status()  
        soup = BeautifulSoup(response.text, "html.parser")
        
        videos = []
        for video in soup.select("ytd-video-renderer")[:5]:
            title = video.select_one("#video-title").text.strip()
            link = "https://www.youtube.com" + video.select_one("#video-title")["href"]
            thumbnail = video.select_one("img")["src"]
            videos.append((title, link, thumbnail))
        
        print(f"유튜브 트렌드 데이터: {videos}")
        return videos
    except Exception as e:
        print(f"YouTube 트렌드 가져오기 실패: {e}")
        return []

async def fetch_twitter_trends():
    try:
        url = "https://trends24.in/"
        response = requests.get(url)
        print(f"트위터 응답 코드: {response.status_code}")
        if response.status_code != 200:
            print("트위터 응답 오류 발생")
            return []
        
        response.raise_for_status()  
        soup = BeautifulSoup(response.text, "html.parser")
        
        trends = []
        for trend in soup.select(".trend-card .trend-card__list li a")[:5]:
            title = trend.text.strip()
            link = f"https://twitter.com/search?q={title.replace(' ', '%20')}&src=trend_click"
            trends.append((title, link))
        
        print(f"트위터 트렌드 데이터: {trends}")
        return trends
    except Exception as e:
        print(f"Twitter 트렌드 가져오기 실패: {e}")
        return []

async def send_trend_message():
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        print("텔레그램 봇 초기화 성공")
        
        # 메시지 초기화
        message = "\U0001F4E2 *오늘의 SNS 트렌드*\n\n"
        print(f"초기 메시지: {message}")
        
        youtube_trends = await fetch_youtube_trends()  # 비동기 함수 호출
        if youtube_trends:
            message += "\U0001F525 *유튜브 인기 영상*\n"
            for title, link, thumbnail in youtube_trends:
                message += f"- [{title}]({link})\n"
                print(f"유튜브 영상 추가: {title}, 링크: {link}")
        else:
            message += "- 유튜브 트렌드 없음\n"
            print("유튜브 트렌드 없음")

        twitter_trends = await fetch_twitter_trends()  # 비동기 함수 호출
        if twitter_trends:
            message += "\n\U0001F426 *트위터 실시간 트렌드*\n"
            for title, link in twitter_trends:
                message += f"- [{title}]({link})\n"
                print(f"트위터 트렌드 추가: {title}, 링크: {link}")
        else:
            message += "- 트위터 트렌드 없음\n"
            print("트위터 트렌드 없음")
        
        print(f"최종 메시지: {message}")
        
        # 텔레그램 메시지 전송
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown", disable_web_page_preview=True)
        print("메시지 텔레그램 전송 성공")
        
        # 유튜브 썸네일 전송
        if youtube_trends:
            for title, link, thumbnail in youtube_trends:
                await bot.send_photo(chat_id=CHAT_ID, photo=thumbnail, caption=f"[{title}]({link})", parse_mode="Markdown")
            print("유튜브 썸네일 텔레그램 전송 성공")
        else:
            print("유튜브 썸네일 없음")
    
    except Exception as e:
        print(f"텔레그램 메시지 전송 실패: {e}")

if __name__ == "__main__":
    asyncio.run(send_trend_message())  # 비동기 함수 실행

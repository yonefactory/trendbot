import requests
import telegram
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def fetch_youtube_trends():
    try:
        url = "https://www.youtube.com/feed/trending"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
        soup = BeautifulSoup(response.text, "html.parser")
        
        videos = []
        for video in soup.select("ytd-video-renderer")[:5]:
            title = video.select_one("#video-title").text.strip()
            link = "https://www.youtube.com" + video.select_one("#video-title")["href"]
            thumbnail = video.select_one("img")["src"]
            videos.append((title, link, thumbnail))
        
        print("YouTube 트렌드 가져오기 성공")
        return videos
    except Exception as e:
        print(f"YouTube 트렌드 가져오기 실패: {e}")
        return []

def fetch_twitter_trends():
    try:
        url = "https://trends24.in/"
        response = requests.get(url)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
        soup = BeautifulSoup(response.text, "html.parser")
        
        trends = []
        for trend in soup.select(".trend-card .trend-card__list li a")[:5]:
            title = trend.text.strip()
            link = f"https://twitter.com/search?q={title.replace(' ', '%20')}&src=trend_click"
            trends.append((title, link))
        
        print("Twitter 트렌드 가져오기 성공")
        return trends
    except Exception as e:
        print(f"Twitter 트렌드 가져오기 실패: {e}")
        return []

def send_trend_message():
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        print("텔레그램 봇 초기화 성공")
        
        message = "\U0001F4E2 *오늘의 SNS 트렌드*\n\n"
        
        message += "\U0001F525 *유튜브 인기 영상*\n"
        for title, link, thumbnail in fetch_youtube_trends():
            message += f"- [{title}]({link})\n"
        
        message += "\n\U0001F426 *트위터 실시간 트렌드*\n"
        for title, link in fetch_twitter_trends():
            message += f"- [{title}]({link})\n"
        
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown", disable_web_page_preview=True)
        print("메시지 텔레그램 전송 성공")
        
        for title, link, thumbnail in fetch_youtube_trends():
            bot.send_photo(chat_id=CHAT_ID, photo=thumbnail, caption=f"[{title}]({link})", parse_mode="Markdown")
        print("유튜브 썸네일 텔레그램 전송 성공")
    
    except Exception as e:
        print(f"텔레그램 메시지 전송 실패: {e}")

if __name__ == "__main__":
    send_trend_message()

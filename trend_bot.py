import requests
import telegram
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def fetch_youtube_trends():
    url = "https://www.youtube.com/feed/trending"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    videos = []
    for video in soup.select("ytd-video-renderer")[:5]:
        title = video.select_one("#video-title").text.strip()
        link = "https://www.youtube.com" + video.select_one("#video-title")["href"]
        thumbnail = video.select_one("img")["src"]
        videos.append((title, link, thumbnail))
    
    return videos

def fetch_twitter_trends():
    url = "https://trends24.in/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    trends = []
    for trend in soup.select(".trend-card .trend-card__list li a")[:5]:
        title = trend.text.strip()
        link = f"https://twitter.com/search?q={title.replace(' ', '%20')}&src=trend_click"
        trends.append((title, link))
    
    return trends

def send_trend_message():
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    
    message = "\U0001F4E2 *오늘의 SNS 트렌드*\n\n"
    
    message += "\U0001F525 *유튜브 인기 영상*\n"
    for title, link, thumbnail in fetch_youtube_trends():
        message += f"- [{title}]({link})\n"
    
    message += "\n\U0001F426 *트위터 실시간 트렌드*\n"
    for title, link in fetch_twitter_trends():
        message += f"- [{title}]({link})\n"
    
    bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown", disable_web_page_preview=True)
    
    for title, link, thumbnail in fetch_youtube_trends():
        bot.send_photo(chat_id=CHAT_ID, photo=thumbnail, caption=f"[{title}]({link})", parse_mode="Markdown")

if __name__ == "__main__":
    send_trend_message()

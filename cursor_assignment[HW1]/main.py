import os
import time
import logging
from datetime import datetime
from typing import List, Tuple

import requests
import schedule
from telegram import Bot


# ========================= 설정 (필수 입력 구간) =========================
# 아래 값들을 실제 값으로 교체하세요.
# 1) 텔레그램 봇 토큰: @BotFather 로부터 발급받은 토큰
TELEGRAM_BOT_TOKEN = "8284833107:AAGJNc0PfloKOp_S63HNivmrkb1k71e5Hqc"  # 예: "123456789:ABCDEF..."

# 2) 텔레그램 채팅 ID: 메시지를 받을 채팅방(개인/그룹/채널)의 chat_id
#    - 개인: @userinfobot 등으로 확인 가능
#    - 그룹: 봇을 초대하고 메시지 보내면 업데이트에서 확인하거나, 외부 도구 활용
TELEGRAM_CHAT_ID = "7685768551"  # 예: "-1001234567890" 또는 "123456789"

# 3) OpenWeatherMap API 키: https://openweathermap.org/api 에서 발급
OPENWEATHER_API_KEY = "531a92c10601431dfddc53dd76a4695a"

# 4) News API 키: https://newsapi.org/ 에서 발급
NEWS_API_KEY = "e9b538bc737940208264c53725d72e5a"

# 5) 스케줄 실행 시각 (로컬 시스템 시간 기준 24시간 형식)
DAILY_RUN_TIME = "08:00"  # 한국 시간대 PC라면 아침 8시 실행
# ======================================================================


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def fetch_seoul_weather(api_key: str) -> Tuple[str, str]:
    """용인 현재 날씨를 가져와 (요약 텍스트, 상세 원문) 튜플로 반환.

    - 단위: 섭씨(metric)
    - 언어: 한국어(lang=kr)
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": "Yongin,KR",
        "appid": api_key,
        "units": "metric",
        "lang": "kr",
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        weather_desc = data.get("weather", [{}])[0].get("description", "-")
        main = data.get("main", {})
        wind = data.get("wind", {})
        temp = main.get("temp")
        feels = main.get("feels_like")
        humidity = main.get("humidity")
        wind_speed = wind.get("speed")

        # 간단 요약
        summary = f"용인 날씨: {weather_desc}, {temp:.1f}°C"

        # 상세 정보
        details_parts: List[str] = []
        details_parts.append(f"체감 {feels:.1f}°C") if isinstance(feels, (int, float)) else None
        details_parts.append(f"습도 {humidity}%") if isinstance(humidity, (int, float)) else None
        details_parts.append(f"풍속 {wind_speed} m/s") if isinstance(wind_speed, (int, float)) else None
        details = ", ".join(details_parts)

        detailed = f"{weather_desc.capitalize()} | 온도 {temp:.1f}°C ({details})"
        return summary, detailed
    except Exception as e:
        logger.exception("Failed to fetch weather: %s", e)
        return "용인 날씨를 가져오지 못했습니다.", "날씨 API 오류"


def fetch_it_news_headlines(api_key: str, max_items: int = 3) -> List[Tuple[str, str, str]]:
    """대한민국 경제 최신 헤드라인 상위 N개를 (제목, 출처, 링크) 리스트로 반환.

    NewsAPI top-headlines 사용: country=kr, category=technology
    """
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "country": "kr",
        "category": "business",
        "pageSize": max_items,
        "apiKey": api_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "ok":
            raise RuntimeError(f"NewsAPI error: {data}")

        articles = data.get("articles", [])[:max_items]
        results: List[Tuple[str, str, str]] = []
        for a in articles:
            title = a.get("title") or "제목 없음"
            source = (a.get("source") or {}).get("name") or "출처 미상"
            url_value = a.get("url") or ""
            results.append((title.strip(), source.strip(), url_value.strip()))
        return results
    except Exception as e:
        logger.exception("Failed to fetch news: %s", e)
        return []


def compose_briefing() -> str:
    """데일리 브리핑 메시지 텍스트 구성."""
    today = datetime.now().strftime("%Y-%m-%d (%a)")

    weather_summary, weather_detail = fetch_seoul_weather(OPENWEATHER_API_KEY)
    news_list = fetch_it_news_headlines(NEWS_API_KEY, max_items=3)

    lines: List[str] = []
    lines.append(f"🌅 데일리 브리핑 | {today}")
    lines.append("")
    lines.append("☁️ 날씨")
    lines.append(f"- {weather_summary}")
    if weather_detail and "오류" not in weather_detail:
        lines.append(f"  · {weather_detail}")
    lines.append("")

    lines.append("📰 경제 뉴스 헤드라인")
    if not news_list:
        lines.append("- 뉴스를 가져오지 못했습니다.")
    else:
        for idx, (title, source, url) in enumerate(news_list, start=1):
            lines.append(f"- {idx}. {title} — {source}")
            if url:
                lines.append(f"  {url}")

    lines.append("")
    lines.append("좋은 하루 되세요! ✨")

    return "\n".join(lines)


def send_briefing_via_telegram(message: str) -> None:
    """텔레그램으로 메시지 전송."""
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info("Briefing sent to Telegram chat %s", TELEGRAM_CHAT_ID)
    except Exception as e:
        logger.exception("Failed to send Telegram message: %s", e)


def job_send_daily_briefing() -> None:
    logger.info("Composing daily briefing...")
    message = compose_briefing()
    send_briefing_via_telegram(message)


def main() -> None:
    # 간단한 유효성 체크
    for key_name, key_value in [
        ("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN),
        ("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID),
        ("OPENWEATHER_API_KEY", OPENWEATHER_API_KEY),
        ("NEWS_API_KEY", NEWS_API_KEY),
    ]:
        if not key_value or "여기에" in str(key_value):
            logger.warning("설정 경고: %s 값이 올바르게 설정되지 않았습니다.", key_name)

    # 매일 지정 시각에 실행 (로컬 시스템 시간 기준)
    schedule.clear()
    schedule.every().day.at(DAILY_RUN_TIME).do(job_send_daily_briefing)
    logger.info("Daily schedule set at %s (system local time)", DAILY_RUN_TIME)

    # 즉시 한 번 실행하고 싶다면 아래 주석 해제
    job_send_daily_briefing()

    # 루프
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == "__main__":
    main()



# 데일리 브리핑 봇 사용법

이 프로젝트는 매일 지정한 시각에 텔레그램으로 날씨(용인)와 경제 뉴스 헤드라인을 보내는 파이썬 스크립트입니다. 기본 실행 시각은 08:00이며, 실행 즉시 1회 전송 후 스케줄에 따라 반복 전송됩니다 [[memory:8978516]].

## 요구 사항
- Python 3.9+ 사용 시 urllib3<2, six가 필요합니다. 이미 requirements.txt 에 포함되어 있습니다. 예전 오류가 있었다면 재설치로 해결됩니다.

## 설정
`main.py` 상단의 설정 값을 실제 값으로 바꿉니다.
- `TELEGRAM_BOT_TOKEN`: @BotFather에서 발급
- `TELEGRAM_CHAT_ID`: 수신할 채팅(개인/그룹/채널)의 chat_id
  - 개인: `@userinfobot` 사용
  - 그룹/채널: 봇 초대 후 메시지 전송 → 업데이트에서 확인
- `OPENWEATHER_API_KEY`: OpenWeatherMap 발급
- `NEWS_API_KEY`: NewsAPI 발급
- `DAILY_RUN_TIME`: 전송 시각(24h, 시스템 로컬 시간 기준). 기본값 "08:00".

보안 주의
- 코드에 토큰/키를 그대로 두지 마세요. 노출 시 즉시 회전(재발급)해야 합니다.
- 가능하면 환경변수로 관리하고 코드에서는 `os.getenv`로 불러오세요.

## 실행
```bash
# Windows CMD에서
python main.py
```

- 실행 즉시 브리핑 1회 전송 후, `DAILY_RUN_TIME`에 맞춰 매일 전송됩니다.
- 중지: 터미널에서 `Ctrl + C`.

## 동작 개요
- 날씨: OpenWeatherMap 현재 날씨(용인, 섭씨, 한국어)
- 뉴스: NewsAPI 상위 경제 헤드라인 N개(기본 3개, 링크 포함)
- 전송: 텔레그램 `send_message`로 텍스트 브리핑 전송

## 커스터마이즈
- 도시 변경: `fetch_seoul_weather`의 `q` 파라미터(예: `"Seoul,KR"`).
- 뉴스 카테고리/국가/개수: `fetch_it_news_headlines` 내부 `params`의 `category`, `country`, `pageSize`.
- 전송 시각: `DAILY_RUN_TIME` 값.

## 트러블슈팅
- `ModuleNotFoundError: urllib3.contrib.appengine`:
  - `pip install -r requirements.txt`로 `urllib3<2`, `six` 재설치.
- 텔레그램 전송 실패:
  - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` 재확인(봇이 초대/시작되었는지 확인).
  - 토큰 노출 이력 있으면 즉시 회전.
- 일정이 안 돈다:
  - 스크립트가 계속 실행 중인지 확인(터미널 닫히면 중단).
  - Windows에서는 작업 스케줄러 등록을 고려.

## 라이선스/크레딧
- OpenWeatherMap, NewsAPI, python-telegram-bot, requests, schedule 사용.

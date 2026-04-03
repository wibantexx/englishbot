# English Teaching Assistant Bot 🎓

Telegram bot for English teachers — generates creative lesson ideas adapted to student level, class size and lesson duration.

## Features

- 🎯 Adapts to student level (A1 → C2)
- ⏱ Considers lesson duration (30–90 min)
- 👥 Adapts to class size (individual → class)
- 📝 Grammar, Speaking, Vocabulary, Writing, Listening activities
- 🎲 Surprise mode — random creative idea
- 🇷🇺 Bilingual — responds in Russian, keeps English terms

## How it works

1. `/start` — choose student level
2. Choose lesson duration
3. Choose number of students
4. Choose activity type
5. Get 3 ready-to-use ideas instantly

## Stack

- Python 3.11
- [python-telegram-bot](https://python-telegram-bot.org/) — Telegram API
- [Groq](https://groq.com/) — fast AI inference
- [Llama 3.3 70B](https://groq.com/) — language model
- Deployed on [Railway](https://railway.app/)

## Setup
```bash
git clone https://github.com/wibantexx/englishbot.git
cd englishbot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file:
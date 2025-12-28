# Galda Telegram Bot

## Overview
A Russian Telegram bot for a fun game where users measure and compare "galda" sizes. The bot includes:
- User registration and stats tracking
- Random galda size changes
- "Cookie" roulette game where a random player loses galda size
- Leaderboard functionality

## Project Architecture
- `bot.py` - Main bot logic with Telegram handlers
- `database.py` - SQLite database wrapper for user data
- `requirements.txt` - Python dependencies

## Tech Stack
- Python 3.11
- pyTelegramBotAPI (telebot) for Telegram API
- SQLite for local database storage
- python-dotenv for environment variables

## Required Environment Variables
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token from @BotFather

## Commands
- `/start` - Register user and get welcome message
- `/help` - Show available commands
- `/galda`, `/galdafon`, `/galdishechka`, `/galdazaraza` - Randomly change galda size
- `/my_stat` - Show personal statistics
- `/all_stat` - Show leaderboard
- `/cookie` - Start cookie roulette game
- `/cookie_stats` - Show active cookie game status

## Workflow
- **Telegram Bot** - Runs the bot with `python bot.py` (console output)

## Recent Changes
- Imported from GitHub
- Configured for Replit environment

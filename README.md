# OLX Telegram Bot

This repository contains the OLX bot script for Telegram.

## Usage

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd olx-telegram-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a Telegram bot and get the `TOKEN` and `CHAT_ID`.

4. Set environment variables:
   ```bash
   export TOKEN=
   export CHAT_ID=
   ```

5. Run the bot:
   ```bash
   python olx_bot.py
   ```

## Deploying on Railway

1. Fork or create this repository on your GitHub account.
2. In Railway, click **New Project** > **Deploy from GitHub Repo**.
3. Connect your GitHub account and select this repo.
4. Add environment variables `TOKEN` and `CHAT_ID` in the Railway dashboard.
5. Set the start command to `python olx_bot.py`.
6. Click **Deploy`.

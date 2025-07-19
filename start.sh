#!/bin/bash

# 🔁 Remove any wrong version first
pip uninstall -y python-telegram-bot

# ✅ Force the correct version
pip install python-telegram-bot==20.7 openai==1.11.1

# ▶️ Start your bot
python main.py

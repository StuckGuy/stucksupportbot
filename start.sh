#!/bin/bash

echo "📦 Installing packages..."
pip install -r requirements.txt

echo "🚀 Launching bot..."
python main.py

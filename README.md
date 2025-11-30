# Telegram Media Exporter 📱💾

A super-fast Python script to download **ALL media** (photos 📸, videos 🎥, files 📄, voice messages 🎤, etc.) from any Telegram chat, group, or channel you can access!

Keeps original filenames & dates · Works with public/private chats · No limits 🚀

## ✨ Features
- Downloads every media type 🖼️🎞️
- Preserves original names & timestamps 🗓️
- Auto-resumes if stopped ⏯️
- Supports channels, supergroups, DMs 💬
- Tiny repo – just 2 files ⚡

## ⚙️ Requirements
- Python 3.8+
- Telethon library 📚

## 🚀 Quick Start

1. Clone the repo  
   ```
   git clone https://github.com/wendirad/t.me.git
   cd t.me
   ```

2. Install Telethon  
   ```
   pip install telethon
   ```

3. Edit `config.ini` (copy from example)  
   ```ini
   [Telethon]
   api_id = 123456
   api_hash = your_api_hash
   session_name = tme_session

   [Settings]
   chat_username = @durov     ; or user/channel ID
   download_path = ./downloads 📂
   ```

   → Get api_id & api_hash at https://my.telegram.org 🔑

4. Run it!  
   ```
   python t_me.py
   ```

   First time: enter phone + code 📲  
   After that: fully automatic 🤖

## 🔥 Ready to backup your memes & files? Start downloading now! ↓

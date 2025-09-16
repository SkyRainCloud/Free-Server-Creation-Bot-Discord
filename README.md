
````
# 🖥️ Pterodactyl Free Hosting Discord Bot

A Discord bot that integrates with **Pterodactyl Panel** to provide **free hosting** services directly from your Discord server.  
Users can register through Discord, and the bot will automatically create their Pterodactyl account. Login credentials are securely sent via DM.  

---

## ✨ Features
- 🔗 Discord integration with Pterodactyl  
- 📝 User registration directly from Discord  
- 🤖 Automatic account creation on Pterodactyl panel  
- 📩 Credentials sent via Discord DM  
- ⚡ Seamless free hosting management  

---

## ⚙️ Setup Guide

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/ptero-discord-bot.git
cd ptero-discord-bot
````

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the root folder and add the following (dummy values shown):

```env
# Discord Bot Settings
DISCORD_TOKEN=your_discord_bot_token
APPLICATION_ID=123456789012345678
OWNER_ID=987654321098765432

# Pterodactyl Settings
PTERO_URL=https://panel.example.com/
PTERO_API_KEY=ptla_exampleapikeyhere
PTERO_NODE_ID=5
PTERO_LOCATION_ID=3
PTERO_NEST_ID=1
PTERO_EGG_ID=1
PTERO_IMAGE=ghcr.io/pterodactyl/yolks:java_21
PANEL_LINK=https://panel.example.com/
```

⚠️ **Important:**

* Replace the dummy values with your actual credentials.
* Resource limits (RAM, CPU, Disk, Max Servers per user, etc.) are **not in `.env`** — they can be configured directly in `bot.py`.

### 4. Run the bot

```bash
python bot.py
```

---

## 📌 Example Usage

1. A user runs `/register` in your Discord server.
2. The bot creates a Pterodactyl account for them.
3. Login credentials are sent to their DM.
4. They log in and manage their free server instantly.

---

## 🛠️ Requirements

* Python 3.9+
* `discord.py`
* `requests`
* `python-dotenv`

(These will be included in `requirements.txt`)

---

## ⚙️ Server Specs

* Default server resources (RAM, Disk, CPU, Ports, etc.)
* Maximum servers per user
* Any special hosting limits

👉 These can be customized in **`bot.py`** according to your hosting resources.

---

## 📜 License

This project is open source. You are free to modify it for your hosting community.

```
MIT License

Copyright (c) 2025 JODVISHAL

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


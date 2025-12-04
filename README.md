# Telegram Bot Configuration

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure the Bot**
   - Get your bot token from [@BotFather](https://t.me/botfather) on Telegram
   - Edit `config.json` and replace `YOUR_BOT_TOKEN_HERE` with your actual token
   - Add your channel links and chat IDs
   - Customize app information and messages as needed

3. **Get Channel Chat IDs**
   - Forward a message from your channel to [@userinfobot](https://t.me/userinfobot)
   - The chat ID will be in the format: `-100` followed by numbers

4. **Run the Bot**
   ```bash
   python bot.py
   ```

## Configuration File (config.json)

The `config.json` file contains:
- **bot_token**: Your Telegram bot token
- **channels**: List of channels with name, link, and chat_id
- **apps**: List of 4 apps with id, name, and info
- **messages**: All bot messages
- **button_labels**: All button text

## Bot Flow

1. `/start` - Shows channels with subscription links and CHECK button
2. User subscribes and clicks CHECK
3. Bot verifies subscription
4. Shows 4 app buttons + Help
5. User selects an app → Shows app info
6. User clicks Next → Asks for user ID
7. User clicks Next → Shows congratulation message
8. User clicks Generate → Generates random number (1-10)
9. User can go back to main menu at any step

## Features

✅ Subscription verification for multiple channels
✅ App selection with detailed information
✅ Multi-step user flow with navigation
✅ Random code generation (1-10)
✅ Fully configurable via JSON
✅ Conversation state management
✅ Easy to customize messages and buttons

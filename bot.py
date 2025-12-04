import logging
import json
import random
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from telegram.error import TelegramError
from database import db, User

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States
MAIN_MENU, CHECKING_SUBSCRIPTION, SENDING_ID, GENERATING_CODE = range(4)

# Load configuration
CONFIG_PATH = Path(__file__).parent / "config.json"

def load_config():
    """Load configuration from JSON file"""
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

config = load_config()

class TelegramBot:
    def __init__(self):
        self.config = config
        
    def get_channels_keyboard(self):
        """Create inline keyboard with channel links and check button"""
        keyboard = []
        
        # Add channel buttons
        for channel in self.config['channels']:
            keyboard.append([
                InlineKeyboardButton(channel['name'], url=channel['link'])
            ])
        
        # Add check button
        keyboard.append([
            InlineKeyboardButton(
                self.config['button_labels']['check'],
                callback_data='check_subscription'
            )
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_apps_keyboard(self):
        """Create reply keyboard with apps and help"""
        keyboard = []
        
        # Add app buttons in 2 rows (2 apps per row)
        for i in range(0, len(self.config['apps']), 2):
            row = []
            row.append(f"{self.config['apps'][i]['name']}")
            if i + 1 < len(self.config['apps']):
                row.append(f"{self.config['apps'][i + 1]['name']}")
            keyboard.append(row)
        
        # Add help button
        keyboard.append([f"{self.config['button_labels']['help']}"])
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    def get_app_action_keyboard(self):
        """Create keyboard for app action (back and next)"""
        keyboard = [
            [
                InlineKeyboardButton(
                    self.config['button_labels']['back'],
                    callback_data='back_to_main'
                ),
                InlineKeyboardButton(
                    self.config['button_labels']['next'],
                    callback_data='next_step'
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_id_submission_keyboard(self):
        """Create keyboard for ID submission step"""
        keyboard = [
            [
                InlineKeyboardButton(
                    self.config['button_labels']['back'],
                    callback_data='back_to_main'
                ),
                InlineKeyboardButton(
                    self.config['button_labels']['next'],
                    callback_data='id_submitted'
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_generate_keyboard(self):
        """Create keyboard with generate and back buttons"""
        keyboard = [
            [
                InlineKeyboardButton(
                    self.config['button_labels']['back'],
                    callback_data='back_to_main'
                ),
                InlineKeyboardButton(
                    self.config['button_labels']['generate'],
                    callback_data='generate_code'
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def check_user_subscription(self, user_id: int) -> bool:
        """Check if user is subscribed to all channels"""
        try:
            for channel in self.config['channels']:
                # Get member status in channel
                member = await self.application.bot.get_chat_member(
                    chat_id=channel['chat_id'],
                    user_id=user_id
                )
                # Check if user is not a member or left
                if member.status == 'left' or member.status == 'kicked':
                    return False
            return True
        except TelegramError as e:
            logger.error(f"Error checking subscription: {e}")
            return False

bot = TelegramBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the bot and show channels"""
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")
    
    # Save or update user in database
    if not db.user_exists(user.id):
        new_user = User(
            telegram_id=user.id,
            fullname=user.full_name or "Unknown",
            status="active"
        )
        db.create_user(new_user)
        logger.info(f"New user created: {user.id}")
    else:
        db.update_user(user.id, fullname=user.full_name)
        logger.info(f"User updated: {user.id}")
    
    await update.message.reply_text(
        config['messages']['start'],
        reply_markup=bot.get_channels_keyboard()
    )
    
    return MAIN_MENU

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Check if user subscribed to all channels"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Simulate subscription check (in production, actually check)
    is_subscribed = await bot.check_user_subscription(user_id)
    
    if is_subscribed or True:  # Set True for testing
        logger.info(f"User {user_id} verified subscription")
        await query.answer()
        await query.message.reply_text(
            text=config['messages']['check_success'],
            reply_markup=bot.get_apps_keyboard()
        )
        # await query.delete_message()
        return CHECKING_SUBSCRIPTION
    else: 
        await query.answer("❌ You are not subscribed to all channels!", show_alert=True)
        return MAIN_MENU

async def app_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle app selection"""
    user = update.effective_user
    text = update.message.text
        
    # Find selected app
    selected_app = None
    for app in config['apps']:
        if app['name'] == text:
            selected_app = app
            break
    
    if not selected_app:
        # Help button pressed
        if text == config['button_labels']['help']:
            await update.message.reply_text(
                config['messages']['help'],
                reply_markup=ReplyKeyboardRemove()
            )
            await update.message.reply_text(
                config['messages']['check_success'],
                reply_markup=bot.get_apps_keyboard()
            )
            return CHECKING_SUBSCRIPTION
        return CHECKING_SUBSCRIPTION
    
    # Store selected app in context
    context.user_data['selected_app'] = selected_app
    
    logger.info(f"User {user.id} selected {selected_app['name']}")
    
    # Send app info with download inline button and "give me id" text
    app_message = f"{selected_app['info']}\n\n{config['messages']['send_me_your_id']}"
    
    keyboard = [
        [InlineKeyboardButton(f"📥 Vzlomlangan {selected_app['name']}", url=selected_app['link'])]
    ]
    
    await update.message.reply_text(
        app_message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    # Send back button as reply keyboard
    reply_keyboard = [[config['button_labels']['back']]]
    await update.message.reply_text(
        "Shart bajarilgan akkaunt id ni yuboring👇",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    )
    
    return SENDING_ID

async def send_id_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle ID submission"""
    user = update.effective_user
    text = update.message.text
    
    selected_app = context.user_data.get('selected_app')
    
    # Check which button was pressed
    if text == config['button_labels']['back']:
        # Go back to main menu
        await update.message.reply_text(
            config['messages']['check_success'],
            reply_markup=bot.get_apps_keyboard()
        )
        return CHECKING_SUBSCRIPTION
    
    # Check if ID equals 10
    if len(text) != 10 or not text.isdigit():
        await update.message.reply_text(
            "❌ Shart bajarilmagan akkaunt id noto'g'ri. Iltimos qayta urinib ko'ring.",
            reply_markup=ReplyKeyboardMarkup(
                [[config['button_labels']['back']]],
                resize_keyboard=True
            )
        )
        return SENDING_ID
    
    # ID is valid - update user in database
    db.update_user(user.id, status="id_verified")
    logger.info(f"User {user.id} verified ID: {text}")
    
    # Show congratulation and generate message
    keyboard = [
        [config['button_labels']['back'], config['button_labels']['generate']]
    ]
    await update.message.reply_text(
        text=f"{config['messages']['congratulation_message_prefix']}",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    
    return GENERATING_CODE

async def generate_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Generate random code"""
    user = update.effective_user
    text = update.message.text
    
    selected_app = context.user_data.get('selected_app')
    
    # Check which button was pressed
    if text == config['button_labels']['back']:
        # Go back to main menu
        await update.message.reply_text(
            config['messages']['check_success'],
            reply_markup=bot.get_apps_keyboard()
        )
        return CHECKING_SUBSCRIPTION
    _numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    # Generate button pressed - send random code
    lucky_number = random.randint(0, 4) 
    message_text = f"{_numbers[lucky_number]} {config['messages']['random_message_prefix']}"
    
    
    
    keyboard = [
        [config['button_labels']['back'], config['button_labels']['generate']]
    ]
    await update.message.reply_text(
        text=message_text,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    
    return GENERATING_CODE

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Go back to main menu"""
    user = update.effective_user
    text = update.message.text
    
    # Back button pressed from any reply keyboard step
    await update.message.reply_text(
        config['messages']['check_success'],
        reply_markup=bot.get_apps_keyboard()
    )
    
    return CHECKING_SUBSCRIPTION

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and go back to start"""
    await update.message.reply_text(
        "Cancelled. Type /start to begin again.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main():
    """Start the bot"""
    # Create the Application
    application = Application.builder().token(config['bot_token']).build()
    
    # Store application in bot instance for subscription checks
    bot.application = application
    
    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(check_subscription, pattern='^check_subscription$'),
            ],
            CHECKING_SUBSCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, app_selected),
            ],
            SENDING_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, send_id_message),
            ],
            GENERATING_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, generate_code),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # Run the bot
    logger.info("Bot started polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

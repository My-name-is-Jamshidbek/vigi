"""Admin panel functionality for the bot"""
import logging
import json
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from database import db

logger = logging.getLogger(__name__)

# Admin states
ADMIN_MENU, SENDING_MESSAGE, CONFIRMING_MESSAGE, VIEWING_STATS = range(4)

# Load configuration
CONFIG_PATH = Path(__file__).parent / "config.json"

def load_config():
    """Load configuration from JSON file"""
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

config = load_config()
ADMIN_IDS = config.get('admin_ids', [])


def is_admin(user_id: int) -> bool:
    """Check if user is an admin"""
    return user_id in ADMIN_IDS


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show admin panel"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Siz admin panelga kirish huquqiga ega emassiz.")
        return -1
    
    keyboard = [
        [InlineKeyboardButton("📤 Barcha foydalanuvchilarga xabar yuborish", callback_data='admin_send_message')],
        [InlineKeyboardButton("📊 Statistikani ko'rish", callback_data='admin_view_stats')],
        [InlineKeyboardButton("❌ Yopish", callback_data='admin_close')]
    ]
    
    await update.message.reply_text(
        "👨‍💼 *Admin Panel*\n\nAmalni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return ADMIN_MENU


async def admin_send_message_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start sending message to all users"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await query.answer("❌ Siz ruxsati yo'q.", show_alert=True)
        return ADMIN_MENU
    
    await query.edit_message_text(
        "📝 Barcha foydalanuvchilarga yuborish uchun xabar yuboring:\n\n"
        "_Admin panelga qaytish uchun /cancel yuboring_",
        parse_mode='Markdown'
    )
    
    return SENDING_MESSAGE


async def admin_message_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle message input from admin"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission.")
        return SENDING_MESSAGE
    
    # Store message in context (store the full message object for copying)
    context.user_data['broadcast_message'] = update.message
    
    # Show confirmation
    keyboard = [
        [InlineKeyboardButton("✅ Tasdiqlash va yuborish", callback_data='confirm_send_message')],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data='admin_cancel_send')]
    ]
    
    await update.message.reply_text(
        "✅ Xabar qabul qilindi.\n\n"
        "Siz bu xabarni barcha foydalanuvchilarga yubormoqchimisiz?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return CONFIRMING_MESSAGE


async def confirm_and_send_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and send message to all users (without sender attribution)"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await query.answer("❌ Siz ruxsati yo'q.", show_alert=True)
        return ADMIN_MENU
    
    message = context.user_data.get('broadcast_message')
    
    if not message:
        await query.edit_message_text("❌ Xabar topilmadi. Iltimos qayta urinib ko'ring.")
        return ADMIN_MENU
    
    # Get all users
    all_users = db.get_all_users()
    
    if not all_users:
        await query.edit_message_text("⚠️ Xabar yuborish uchun foydalanuvchi yo'q.")
        return ADMIN_MENU
    
    # Send message to all users (without forwarding to hide sender)
    success_count = 0
    failed_count = 0
    
    await query.edit_message_text(
        f"📤 {len(all_users)} ta foydalanuvchiga xabar yuborilmoqda...\n"
        f"Iltimos kuting..."
    )
    
    for user in all_users:
        try:
            # Copy message content instead of forwarding (hides sender name)
            if message.text:
                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text=message.text
                )
            elif message.photo:
                await context.bot.send_photo(
                    chat_id=user.telegram_id,
                    photo=message.photo[-1].file_id,
                    caption=message.caption
                )
            elif message.video:
                await context.bot.send_video(
                    chat_id=user.telegram_id,
                    video=message.video.file_id,
                    caption=message.caption
                )
            elif message.document:
                await context.bot.send_document(
                    chat_id=user.telegram_id,
                    document=message.document.file_id,
                    caption=message.caption
                )
            elif message.audio:
                await context.bot.send_audio(
                    chat_id=user.telegram_id,
                    audio=message.audio.file_id,
                    caption=message.caption
                )
            elif message.animation:
                await context.bot.send_animation(
                    chat_id=user.telegram_id,
                    animation=message.animation.file_id,
                    caption=message.caption
                )
            elif message.voice:
                await context.bot.send_voice(
                    chat_id=user.telegram_id,
                    voice=message.voice.file_id,
                    caption=message.caption
                )
            elif message.video_note:
                await context.bot.send_video_note(
                    chat_id=user.telegram_id,
                    video_note=message.video_note.file_id
                )
            elif message.sticker:
                await context.bot.send_sticker(
                    chat_id=user.telegram_id,
                    sticker=message.sticker.file_id
                )
            elif message.location:
                await context.bot.send_location(
                    chat_id=user.telegram_id,
                    latitude=message.location.latitude,
                    longitude=message.location.longitude
                )
            elif message.contact:
                await context.bot.send_contact(
                    chat_id=user.telegram_id,
                    phone_number=message.contact.phone_number,
                    first_name=message.contact.first_name,
                    last_name=message.contact.last_name
                )
            elif message.venue:
                await context.bot.send_venue(
                    chat_id=user.telegram_id,
                    latitude=message.venue.location.latitude,
                    longitude=message.venue.location.longitude,
                    title=message.venue.title,
                    address=message.venue.address
                )
            elif message.poll:
                await context.bot.send_poll(
                    chat_id=user.telegram_id,
                    question=message.poll.question,
                    options=[option.text for option in message.poll.options],
                    is_anonymous=message.poll.is_anonymous,
                    type=message.poll.type,
                    allows_multiple_answers=message.poll.allows_multiple_answers
                )
            elif message.dice:
                await context.bot.send_dice(
                    chat_id=user.telegram_id,
                    emoji=message.dice.emoji
                )
            elif message.game:
                await context.bot.send_game(
                    chat_id=user.telegram_id,
                    game_short_name=message.game.game_short_name
                )
            else:
                logger.warning(f"Unsupported message type for user {user.telegram_id}")
                failed_count += 1
                continue
                
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to send message to user {user.telegram_id}: {e}")
            failed_count += 1
    
    # Show result
    result_text = (
        f"✅ *Yuborish Tamomlandi*\n\n"
        f"📊 Natijalar:\n"
        f"✅ Muvaffaqiyatli yuborildi: {success_count}\n"
        f"❌ Xato: {failed_count}\n"
        f"👥 Jami foydalanuvchilar: {len(all_users)}"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 Admin Panelga Qaytish", callback_data='admin_back_to_panel')]
    ]
    
    await query.edit_message_text(
        result_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return ADMIN_MENU


async def admin_view_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show statistics"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await query.answer("❌ Siz ruxsati yo'q.", show_alert=True)
        return ADMIN_MENU
    
    # Get statistics
    total_users = db.get_users_count()
    active_users = len(db.get_users_by_status('active'))
    id_verified = len(db.get_users_by_status('id_verified'))
    channel_joined = len(db.get_users_by_status('channel_joined'))
    
    # Get date-based stats
    all_users = db.get_all_users()
    
    stats_text = (
        f"📊 *Bot Statistikasi*\n\n"
        f"👥 *Foydalanuvchi Statistikasi:*\n"
        f"• Jami Foydalanuvchilar: {total_users}\n"
        f"• Kanalga Qo'shilganlar: {channel_joined}\n"
        f"• Faol Foydalanuvchilar: {active_users}\n"
        f"• ID Tasdiqlanganlar: {id_verified}\n"
        f"• Tasdiqlanmaganlar: {total_users - id_verified}\n"
    )
    
    # Calculate join date stats
    if all_users:
        from datetime import datetime, timedelta
        now = datetime.now()
        today_users = sum(1 for u in all_users if u.created_at and 
                         (now - datetime.fromisoformat(u.created_at)).days == 0)
        week_users = sum(1 for u in all_users if u.created_at and 
                        (now - datetime.fromisoformat(u.created_at)).days <= 7)
        
        # Channel joined today and this week
        today_channel = sum(1 for u in all_users if u.status == 'channel_joined' and u.created_at and 
                           (now - datetime.fromisoformat(u.created_at)).days == 0)
        week_channel = sum(1 for u in all_users if u.status == 'channel_joined' and u.created_at and 
                          (now - datetime.fromisoformat(u.created_at)).days <= 7)
        
        stats_text += (
            f"\n📅 *Qo'shilish Statistikasi:*\n"
            f"• Bugun (Hammasi): {today_users}\n"
            f"• Bu Hafta (Hammasi): {week_users}\n"
            f"• Kanal Bugun: {today_channel}\n"
            f"• Kanal Bu Hafta: {week_channel}\n"
        )
    
    keyboard = [
        [InlineKeyboardButton("🔙 Admin Panelga Qaytish", callback_data='admin_back_to_panel')],
        [InlineKeyboardButton("❌ Yopish", callback_data='admin_close')]
    ]
    
    await query.edit_message_text(
        stats_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return VIEWING_STATS


async def admin_back_to_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Go back to admin panel"""
    query = update.callback_query
    
    keyboard = [
        [InlineKeyboardButton("📤 Barcha foydalanuvchilarga xabar yuborish", callback_data='admin_send_message')],
        [InlineKeyboardButton("📊 Statistikani ko'rish", callback_data='admin_view_stats')],
        [InlineKeyboardButton("❌ Yopish", callback_data='admin_close')]
    ]
    
    if query:
        # Called from callback query
        await query.answer()
        await query.edit_message_text(
            "👨‍💼 *Admin Panel*\n\nAmalni tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        # Called from message (e.g., /cancel command)
        await update.message.reply_text(
            "👨‍💼 *Admin Panel*\n\nAmalni tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    return ADMIN_MENU


async def admin_cancel_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel sending message"""
    query = update.callback_query
    await query.answer()
    
    return await admin_back_to_panel(update, context)


async def admin_close(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Close admin panel"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("✅ Admin panel yopildi.")
    
    return -1

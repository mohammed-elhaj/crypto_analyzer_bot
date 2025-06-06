import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters,ContextTypes
from src.bot.handlers.analysis_handlers import AnalysisHandler
from src.bot.handlers.callback_handler import CallbackHandler
from src.bot.handlers.message_handler import CustomMessageHandler  # Updated import
from src.bot.keyboards.reply_keyboards import AnalysisKeyboards
from telegram import Update

import asyncio

from src.services.database import AdminTypes, UserType
from src.services.database_manager import DatabaseManager
from src.services.database import AdminTypes
from src.utils.formatters import TelegramFormatter
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)

# Load environment variables
load_dotenv()

# Create shared user_states dictionary
user_states = {}

# Initialize handlers
analysis_handler = AnalysisHandler()
callback_handler = CallbackHandler()
message_handler = CustomMessageHandler()  # Updated class name
keyboards = AnalysisKeyboards()
formatter = TelegramFormatter()
db = DatabaseManager()
db.init_db()

# Share user_states between handlers
callback_handler.user_states = user_states
message_handler.user_states = user_states




async def start_command(update, context):
    user = db.get_user_by_telegram_id(str(update.message.from_user.username))
    
    if not user:
        db.create_user({'telegram_id':str(update.message.from_user.username)})
        user = db.get_user_by_telegram_id(str(update.message.from_user.username))
   
    formatter.set_language(user['language'])
    print(user['telegram_id'])
    if user["user_type"] == UserType.BANNED:
        return await update.message.reply_text(
        formatter._t('error_no_permission'))
    formatter.set_language(user['language'])


    
    """Handle /start command"""
    welcome_text = (
        """Welcome to CryptoAnalyst Bot! 🚀\n\n
        I can help you analyze cryptocurrencies with technical analysis 
        and charts. Select an option below to get started:\n
        Or enter your text and let the agent help you out 🤖!"""
    )
    await update.message.reply_text(
        formatter._t('welcome_text'),
        reply_markup=keyboards.get_main_menu()
    )  
  

async def admin_command(update,context):
    create_first_admins(["abualmun","osmanoor2018","hooibi"])

    # db.update_admin_role(str(update.message.from_user.username),AdminTypes.MASTER,str(update.message.from_user.username))
    # db.sync_with_api(api)
    user = db.get_user_by_telegram_id(str(update.message.from_user.username))
    if not user:
        db.create_user({'telegram_id':str(update.message.from_user.username)})
    try:
        admin = db.get_admin_by_user_id(user["telegram_id"])
        formatter.set_language(user['language'])

        if admin and admin['is_active']:
            welcome_text = (
                    "Welcome to CryptoAnalyst Bot Admin Panel\n\n"
                    "How can I help you? "
                    "Select an option below\n"
                )
            await update.message.reply_text(
                welcome_text,
                reply_markup=keyboards.get_admin_menu()
            )
        else:
            await update.message.reply_text(
                formatter._t("not_authorized")
            )
    except Exception as e:
        print(e)
        pass

async def progress_bar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simulates a loading progress bar in the bot."""
    message = await update.message.reply_text("Loading: [                    ] 0%")
    progress = 0
    
    while progress <= 100:
        # Generate the progress bar
        filled_length = int(20 * progress / 100)  # 20 is the bar length
        bar = "█" * filled_length + " " * (20 - filled_length)
        
        # Edit the message with the new progress
        await message.edit_text(f"Loading: [{bar}] {progress}%")
        
        # Increment progress and wait
        progress += 5
        await asyncio.sleep(0.2)  # Simulate work being done
    
    # Final message when complete
    await message.edit_text("✅ Loading Complete!")

async def print_id(update,context):
    await update.message.reply_text(update.message.from_user.username)
# Create the bot application
# async def main():
#     application = (
#         ApplicationBuilder()
#         .token("YOUR_TELEGRAM_BOT_TOKEN")
#         .build()
#     )

#     # Start the bot
#     await application.run_polling()
def create_first_admins(admins):
    for admin_name in admins:
        new_admin = db.get_admin_by_user_id(admin_name)
        if not new_admin:
            user = db.get_user_by_telegram_id(admin_name)
            if not user:    
                db.create_user({'telegram_id':admin_name})
            new_admin = db.create_admin({'user_id':admin_name,'role':AdminTypes.MASTER,'created_by':"abualmun"})


def main():


    

 
    """Main function to run the bot"""
    # Create application
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Add command handlers
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('analyze', analysis_handler.cmd_analyze))
    application.add_handler(CommandHandler('quick', analysis_handler.cmd_quick))
    application.add_handler(CommandHandler('news', analysis_handler.cmd_news))
    application.add_handler(CommandHandler('chart', analysis_handler.cmd_chart))
    application.add_handler(CommandHandler('admin', admin_command))
# DEBUGGING
    application.add_handler(CommandHandler('id', print_id))
    
    # Add the command handler
    application.add_handler(CommandHandler("progress", progress_bar))

    # Add callback handler for keyboard interactions
    application.add_handler(CallbackQueryHandler(callback_handler.handle_callback))

    # Add message handler for text inputs - Fixed handler
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler.handle_message,
        )
    )

    # Start the bot
    print('Starting bot...')
    application.run_polling()
    
    
    
    # add admin then comment again


# Run the bot
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
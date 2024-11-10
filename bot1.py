import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import requests

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Define constants for your API URLs
REQ_OTP_URL = "https://nomorxlku.my.id/api/req_otp.php"
VER_OTP_URL = "https://nomorxlku.my.id/api/ver_otp.php"
CHECK_QUOTA_URL = "https://nomorxlku.my.id/api/check_quota.php"

# Start command
def start(update: Update, _: CallbackContext) -> None:
    update.message.reply_text("Welcome to the XL OTP Login Solution Bot! Please send your seller code.")

# Function to handle incoming messages
def handle_message(update: Update, _: CallbackContext) -> None:
    user_data = _['user_data']
    if 'seller_code' not in user_data:
        user_data['seller_code'] = update.message.text
        update.message.reply_text("Please send your MSISDN/Num XL.")
    elif 'msisdn' not in user_data:
        user_data['msisdn'] = update.message.text
        update.message.reply_text("Please send the OTP code.")
    elif 'otp' not in user_data:
        user_data['otp'] = update.message.text
        handle_login(update, user_data)
    else:
        update.message.reply_text("You've already input all required data.")

# Handle the login process
def handle_login(update: Update, user_data) -> None:
    msisdn = user_data['msisdn']
    seller_code = user_data['seller_code']
    otp = user_data['otp']

    # Request OTP
    otp_response = requests.post(REQ_OTP_URL, data={'msisdn': msisdn, 'seller_code': seller_code}).json()

    if otp_response['status']:
        auth_id = otp_response['data']['auth_id']
        update.message.reply_text(f"OTP sent. Please verify with the code you received. Auth ID: {auth_id}")

        # Now we would ask for OTP verification
        user_data['auth_id'] = auth_id
        update.message.reply_text("Please send your OTP code for verification.")
    else:
        update.message.reply_text(f"Error: {otp_response['message']}")

# Verify OTP
def verify_otp(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data
    auth_id = user_data.get('auth_id')
    otp = user_data.get('otp')

    if not auth_id:
        update.message.reply_text("No auth_id found. Please try registering again.")
        return 

    verification_response = requests.post(VER_OTP_URL, data={
        'msisdn': user_data['msisdn'],
        'auth_id': auth_id,
        'otp': otp
    }).json()

    if verification_response['status']:
        update.message.reply_text("Verification successful! Now checking quota...")
        check_quota(update, user_data)
    else:
        update.message.reply_text(f"Verification failed: {verification_response['message']}")

# Check quota
def check_quota(update: Update, user_data) -> None:
    access_token = user_data.get('access_token')
    quota_response = requests.post(CHECK_QUOTA_URL, data={'access_token': access_token}).json()

    if quota_response['status']:
        message = "Quota information:\n"
        for quota in quota_response['data']['quotas']:
            message += f"Package: {quota['name']}, Expired: {quota['expired_at']}, Benefits: {', '.join(benefit['name'] for benefit in quota['benefits'])}\n"
        update.message.reply_text(message)
    else:
        update.message.reply_text(f"Error fetching quota: {quota_response['message']}")

def main() -> None:
    updater = Updater("YOUR_BOT_TOKEN")

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
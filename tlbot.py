import os
import glob
import telebot
import yt_dlp

# টোকেন ভ্যারিয়েবল থেকে রিড করবে, না পেলে ব্যাকআপ টোকেন নেবে
BOT_TOKEN = os.getenv("BOT_TOKEN", "8925664065:AAG6G8TCIdv1oeNCfQij-znJ8qULK9Ddm_w")
bot = telebot.TeleBot(BOT_TOKEN)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 স্বাগতম!\n\n"
        "আমাকে যেকোনো ভিডিও বা ফটোর লিংক পাঠান (Instagram Reels/Posts, YouTube, Facebook ইত্যাদি)। "
        "আমি সরাসরি মিডিয়া ডাউনলোড করে আপনাকে পাঠিয়ে দেব।"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    url = message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        bot.reply_to(message, "অনুগ্রহ করে একটি সঠিক ভিডিও লিংক পাঠান।")
        return

    status_msg = bot.reply_to(message, "⏳ মিডিয়া প্রসেস করা হচ্ছে, দয়া করে অপেক্ষা করুন...")

    out_template = os.path.join(DOWNLOAD_DIR, f"{message.chat.id}_%(id)s.%(ext)s")

    ydl_opts = {
        'format': 'best/bestvideo+bestaudio/best',
        'outtmpl': out_template,
        'quiet': True,
        'no_warnings': True,
        'nopart': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        pattern = os.path.join(DOWNLOAD_DIR, f"{message.chat.id}_*")
        files = glob.glob(pattern)

        if not files:
            bot.edit_message_text("❌ মিডিয়া ফাইল পাওয়া যায়নি।", chat_id=message.chat.id, message_id=status_msg.message_id)
            return

        bot.edit_message_text("📤 মিডিয়া পাঠানো হচ্ছে...", chat_id=message.chat.id, message_id=status_msg.message_id)

        for file_path in files:
            ext = os.path.splitext(file_path)[1].lower()
            with open(file_path, 'rb') as f:
                if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    bot.send_photo(message.chat.id, f)
                elif ext in ['.mp4', '.mkv', '.webm', '.mov']:
                    bot.send_video(message.chat.id, f, supports_streaming=True)
                elif ext in ['.mp3', '.m4a', '.wav', '.opus']:
                    bot.send_audio(message.chat.id, f)
                else:
                    bot.send_document(message.chat.id, f)

            if os.path.exists(file_path):
                os.remove(file_path)

        bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
        bot.send_message(message.chat.id, "✅ ডাউনলোড সম্পন্ন!")

    except Exception as e:
        bot.edit_message_text(f"❌ ডাউনলোড করতে সমস্যা হয়েছে: {str(e)}", chat_id=message.chat.id, message_id=status_msg.message_id)

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()

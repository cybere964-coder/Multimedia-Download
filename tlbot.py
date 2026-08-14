import os
import glob
import time
import telebot
import yt_dlp

BOT_TOKEN = "8925664065:AAG6G8TCIdv1oeNCfQij-znJ8qULK9Ddm_w"

# টাইমআউট বাড়িয়ে দেওয়া হয়েছে যাতে আপলোডে ফেইল না করে
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@bot.message_handler(commands=['start', 'help'])
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
        bot.reply_to(message, "⚠️ অনুগ্রহ করে একটি সঠিক লিংক পাঠান।")
        return

    status_msg = bot.reply_to(message, "⏳ প্রসেসিং হচ্ছে, অনুগ্রহ করে অপেক্ষা করুন...")

    # ইউনিক টাইমস্ট্যাম্প দিয়ে ফাইলের নাম যাতে পার্ট ফাইলের ঝামেলা না হয়
    timestamp = int(time.time())
    out_template = os.path.join(DOWNLOAD_DIR, f"{timestamp}_%(id)s.%(ext)s")

    ydl_opts = {
        'format': 'best/bestvideo+bestaudio/best',
        'outtmpl': out_template,
        'quiet': True,
        'no_warnings': True,
        'nopart': True, # .part ফাইলের সমস্যা বন্ধ করার জন্য
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            bot.edit_message_text("📥 ফাইল ডাউনলোড হচ্ছে...", chat_id=status_msg.chat.id, message_id=status_msg.message_id)
            ydl.download([url])

        # ডাউনলোড হওয়া ফাইলটি খুঁজে বের করা
        files = glob.glob(os.path.join(DOWNLOAD_DIR, f"{timestamp}_*"))
        
        if not files:
            bot.edit_message_text("❌ ফাইল পাওয়া যায়নি। লিংকটি প্রাইভেট বা ইনভ্যালিড হতে পারে।", chat_id=status_msg.chat.id, message_id=status_msg.message_id)
            return

        downloaded_file = files[0]
        file_size_mb = os.path.getsize(downloaded_file) / (1024 * 1024)

        if file_size_mb > 50:
            bot.edit_message_text(f"⚠️ ফাইলের সাইজ {file_size_mb:.1f}MB, যা টেলিগ্রামের ৫০MB লিমিটের চেয়ে বড়।", chat_id=status_msg.chat.id, message_id=status_msg.message_id)
            os.remove(downloaded_file)
            return

        bot.edit_message_text("📤 টেলিগ্রামে আপলোড হচ্ছে...", chat_id=status_msg.chat.id, message_id=status_msg.message_id)

        with open(downloaded_file, 'rb') as f:
            if downloaded_file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                bot.send_photo(message.chat.id, f, caption="✅ ডাউনলোড সম্পন্ন!", timeout=60)
            elif downloaded_file.lower().endswith(('.mp3', '.m4a', '.aac', '.wav')):
                bot.send_audio(message.chat.id, f, caption="✅ অডিও ডাউনলোড সম্পন্ন!", timeout=60)
            else:
                bot.send_video(message.chat.id, f, caption="✅ ডাউনলোড সম্পন্ন!", supports_streaming=True, timeout=120)

        bot.delete_message(status_msg.chat.id, status_msg.message_id)
        os.remove(downloaded_file)

    except Exception as e:
        bot.edit_message_text(f"❌ ডাউনলোড করতে সমস্যা হয়েছে: {str(e)}", chat_id=status_msg.chat.id, message_id=status_msg.message_id)
        # ব্যর্থ হলে কোনো অবশিষ্ট ফাইল থাকলে ডিলিট করা
        for f in glob.glob(os.path.join(DOWNLOAD_DIR, f"{timestamp}_*")):
            try:
                os.remove(f)
            except:
                pass

print("🚀 বট সফলভাবে চালু হয়েছে এবং কাজ করছে...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)
      

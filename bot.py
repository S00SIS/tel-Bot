import random
import os
import time
import requests
import json
import sys
import math
import subprocess

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
START_TIME = time.time()
MAX_RUNTIME = 6 * 60 * 60

# مسیر فایل‌ها
DONATED_FILE = 'donated.txt'      # کانفیگ‌های اهدایی
MAIN_FILE = 'proxy.txt'           # کانفیگ‌های اصلی (دلتا)

def check_time():
    if time.time() - START_TIME > MAX_RUNTIME:
        print("6 ساعت تموم شد، ربات خاموش میشه...")
        sys.exit(0)

def get_configs(file_path):
    """خواندن کانفیگ‌ها از فایل"""
    try:
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def save_config(file_path, config):
    """ذخیره کانفیگ جدید در فایل"""
    with open(file_path, 'a') as f:
        f.write(config.strip() + '\n')

def git_commit_and_push(file_path, config_text):
    """کامیت و پوش کردن تغییرات به گیت‌هاب"""
    try:
        # تنظیم git user (برای ورک‌فلو گیت‌هاب)
        subprocess.run(['git', 'config', 'user.name', 'Telegram Bot'], check=False)
        subprocess.run(['git', 'config', 'user.email', 'bot@telegram.com'], check=False)
        
        # اضافه کردن فایل به git
        subprocess.run(['git', 'add', file_path], check=False)
        
        # کامیت کردن
        commit_msg = f"Add donated config: {config_text[:50]}..."
        subprocess.run(['git', 'commit', '-m', commit_msg], check=False)
        
        # پوش به مخزن
        subprocess.run(['git', 'push'], check=False)
        
        return True
    except Exception as e:
        print(f"Git error: {e}")
        return False

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def pin_message(chat_id, message_id):
    url = f"https://api.telegram.org/bot{TOKEN}/pinChatMessage"
    payload = {'chat_id': chat_id, 'message_id': message_id, 'disable_notification': True}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error pinning message: {e}")

def send_configs_in_chunks(chat_id, configs, total_count, source_name):
    """ارسال کانفیگ‌ها در گروه‌های 10 تایی با نام منبع"""
    if not configs:
        send_message(chat_id, f"❌ متاسفانه هیچ کانفیگی در بخش {source_name} موجود نیست.")
        return
    
    chunk_size = 10
    num_chunks = math.ceil(len(configs) / chunk_size)
    
    send_message(chat_id, f"📦 منبع: {source_name}\n✅ {len(configs)} کانفیگ در حال ارسال...")
    time.sleep(0.5)
    
    for i in range(num_chunks):
        start = i * chunk_size
        end = start + chunk_size
        chunk = configs[start:end]
        
        if num_chunks == 1:
            message = "\n".join(chunk)
        else:
            if i == 0:
                message = f"📦 بخش {i+1} از {num_chunks} (کانفیگ {start+1} تا {min(end, total_count)}):\n\n" + "\n".join(chunk)
            else:
                message = f"\n📦 بخش {i+1} از {num_chunks} (کانفیگ {start+1} تا {min(end, total_count)}):\n\n" + "\n".join(chunk)
        
        send_message(chat_id, message)
        time.sleep(0.5)
    
    send_message(chat_id, f"✨ ارسال {len(configs)} کانفیگ از {source_name} به پایان رسید.")

def show_config_menu(chat_id):
    """نمایش منوی انتخاب نوع کانفیگ"""
    keyboard = {
        "keyboard": [
            [{"text": "🎁 کانفیگ‌های اهدایی"}, {"text": "⚡ کانفیگ‌های دلتا"}],
            [{"text": "📡 راهنما و اطلاعات"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
    
    main_configs = get_configs(MAIN_FILE)
    donated_configs = get_configs(DONATED_FILE)
    
    menu_text = f"""🎯 منوی اصلی ربات کانفیگ

لطفاً نوع کانفیگ مورد نظر خود را انتخاب کنید:

🎁 کانفیگ‌های اهدایی: {len(donated_configs)} عدد
⚡ کانفیگ‌های دلتا: {len(main_configs)} عدد

📌 نحوه اهدای کانفیگ:
برای اهدای کانفیگ به ربات، کافیست کانفیگ خود را به صورت مستقیم برای ربات ارسال کنید.
کانفیگ شما پس از بررسی به بخش اهدایی اضافه خواهد شد.

برای شروع، یکی از گزینه‌های بالا را انتخاب کنید."""
    
    send_message(chat_id, menu_text, reply_markup=keyboard)

def main():
    last_update_id = 0
    waiting_for_donate = {}  # دیکشنری برای نگهداری کاربرانی که منتظر دریافت کانفیگ اهدایی هستند
    
    while True:
        check_time()
        
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            params = {'timeout': 30, 'offset': last_update_id + 1}
            response = requests.get(url, params=params, timeout=35)
            updates = response.json().get('result', [])
            
            for update in updates:
                check_time()
                last_update_id = update['update_id']
                
                if 'message' not in update:
                    continue
                
                msg = update['message']
                
                if 'text' not in msg:
                    # اگه پیام کانفیگ اهدایی باشه (متن نیست، مثلاً کپی پیست کرده)
                    if msg.get('caption'):
                        # اگه کپشن داره
                        pass
                    continue
                
                chat_id = msg['chat']['id']
                text = msg.get('text', '')
                
                # دستور start
                if text == '/start':
                    welcome_text = f"""🎯 به ربات کانفیگ خوش آمدید!

این ربات به شما امکان دریافت کانفیگ‌های دلخواه را می‌دهد.

📌 نحوه استفاده:
✅ از طریق دکمه‌های پایین صفحه نوع کانفیگ خود را انتخاب کنید
✅ سپس تعداد کانفیگ مورد نیاز را وارد کنید (عدد بین 1 تا 50)

📊 آمار فعلی:
🎁 کانفیگ‌های اهدایی: {len(get_configs(DONATED_FILE))} عدد
⚡ کانفیگ‌های دلتا: {len(get_configs(MAIN_FILE))} عدد

💝 اهدای کانفیگ:
برای اهدای کانفیگ، کافیست کانفیگ خود را (هر خط یک کانفیگ) برای ربات ارسال کنید.

لطفاً برای ادامه، از دکمه‌های پایین صفحه استفاده کنید."""
                    
                    reply_keyboard = {
                        "keyboard": [
                            [{"text": "🎁 کانفیگ‌های اهدایی"}, {"text": "⚡ کانفیگ‌های دلتا"}],
                            [{"text": "📡 راهنما و اطلاعات"}]
                        ],
                        "resize_keyboard": True,
                        "one_time_keyboard": False
                    }
                    
                    result = send_message(chat_id, welcome_text, reply_markup=reply_keyboard)
                    
                    if result and 'result' in result:
                        message_id = result['result']['message_id']
                        pin_message(chat_id, message_id)
                
                # پردازش دکمه راهنما
                elif text == "📡 راهنما و اطلاعات":
                    main_configs = get_configs(MAIN_FILE)
                    donated_configs = get_configs(DONATED_FILE)
                    
                    help_text = f"""📚 راهنمای استفاده از ربات

🎁 کانفیگ‌های اهدایی:
کانفیگ‌هایی که کاربران دیگر به ربات اهدا کرده‌اند.
تعداد موجود: {len(donated_configs)} عدد

⚡ کانفیگ‌های دلتا:
کانفیگ‌های اصلی و پایدار ربات.
تعداد موجود: {len(main_configs)} عدد

💝 نحوه اهدای کانفیگ:
1. کانفیگ خود را کپی کنید (هر خط یک کانفیگ)
2. برای ربات ارسال کنید
3. کانفیگ شما پس از ذخیره به بخش اهدایی اضافه می‌شود

📊 محدودیت درخواست:
حداکثر 50 کانفیگ در هر بار درخواست

⚠️ توجه:
کانفیگ‌های اهدایی توسط کاربران ارسال می‌شوند و ممکن است پایدار نباشند."""
                    
                    send_message(chat_id, help_text)
                
                # پردازش دکمه کانفیگ اهدایی
                elif text == "🎁 کانفیگ‌های اهدایی":
                    donated_configs = get_configs(DONATED_FILE)
                    if donated_configs:
                        send_message(chat_id, f"🔢 تعداد کانفیگ‌های اهدایی موجود: {len(donated_configs)}\n\nچند تا کانفیگ از بخش اهدایی میخوای؟ (عدد بین 1 تا 50)")
                        waiting_for_donate[chat_id] = 'donated'
                    else:
                        send_message(chat_id, "❌ متاسفانه هیچ کانفیگ اهدایی موجود نیست.\n\nشما می‌توانید اولین نفری باشید که کانفیگ اهدا می‌کند!")
                
                # پردازش دکمه کانفیگ دلتا
                elif text == "⚡ کانفیگ‌های دلتا":
                    main_configs = get_configs(MAIN_FILE)
                    if main_configs:
                        send_message(chat_id, f"🔢 تعداد کانفیگ‌های دلتا موجود: {len(main_configs)}\n\nچند تا کانفیگ از بخش دلتا میخوای؟ (عدد بین 1 تا 50)")
                        waiting_for_donate[chat_id] = 'main'
                    else:
                        send_message(chat_id, "❌ متاسفانه هیچ کانفیگ دلتا موجود نیست!")
                
                # پردازش عدد (تعداد کانفیگ)
                elif text.isdigit():
                    count = int(text)
                    if 1 <= count <= 50:
                        source = waiting_for_donate.get(chat_id, 'main')
                        
                        if source == 'donated':
                            configs = get_configs(DONATED_FILE)
                            source_name = "🎁 کانفیگ‌های اهدایی"
                        else:
                            configs = get_configs(MAIN_FILE)
                            source_name = "⚡ کانفیگ‌های دلتا"
                        
                        if not configs:
                            send_message(chat_id, f"❌ متاسفانه هیچ کانفیگی در {source_name} موجود نیست.")
                            waiting_for_donate.pop(chat_id, None)
                            continue
                        
                        if count > len(configs):
                            send_message(chat_id, f"⚠️ فقط {len(configs)} کانفیگ در {source_name} موجود است. همین تعداد ارسال می‌شود.")
                            count = len(configs)
                        
                        selected = random.sample(configs, count)
                        send_configs_in_chunks(chat_id, selected, count, source_name)
                        
                        # پاک کردن وضعیت انتظار
                        waiting_for_donate.pop(chat_id, None)
                    else:
                        send_message(chat_id, "❌ لطفاً عددی بین 1 تا 50 وارد کنید.")
                
                # پردازش کانفیگ اهدایی (هر متنی که جزو دکمه‌ها و کامندها نباشه)
                elif (text not in ["🎁 کانفیگ‌های اهدایی", "⚡ کانفیگ‌های دلتا", "📡 راهنما و اطلاعات", "/start"] 
                      and len(text) > 10):  # احتمالاً کانفیگ هست
                    
                    # ذخیره کانفیگ اهدایی
                    save_config(DONATED_FILE, text)
                    
                    # کامیت به گیت‌هاب
                    git_commit_and_push(DONATED_FILE, text)
                    
                    send_message(chat_id, "✅ کانفیگ شما با موفقیت به بخش اهدایی اضافه شد!\n\n🙏 ممنون از همکاری شما.\n\nسپس کاربران دیگر نیز می‌توانند از این کانفیگ استفاده کنند.")
                    
                    # آمار جدید
                    total_donated = len(get_configs(DONATED_FILE))
                    send_message(chat_id, f"📊 آمار جدید کانفیگ‌های اهدایی: {total_donated} عدد")
                
                # هر چیز دیگه
                else:
                    send_message(chat_id, "❌ گزینه نامعتبر!\n\nلطفاً از دکمه‌های پایین صفحه استفاده کنید یا یک عدد معتبر وارد کنید.")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()

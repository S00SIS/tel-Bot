import random
import os
import time
import requests
import json
import sys
import math
import subprocess
from collections import deque
from threading import Timer

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
START_TIME = time.time()
MAX_RUNTIME = 6 * 60 * 60

# مسیر فایل‌ها
DONATED_FILE = 'donated.txt'
MAIN_FILE = 'proxy.txt'

# ذخیره پیام‌های کاربر برای پردازش گروهی
user_message_buffer = {}
BUFFER_TIMEOUT = 3  # 3 ثانیه صبر کن تا پیام‌های بعدی برسن

def check_time():
    if time.time() - START_TIME > MAX_RUNTIME:
        print("6 ساعت تموم شد، ربات خاموش میشه...")
        sys.exit(0)

def get_configs(file_path):
    try:
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def save_multiple_configs(file_path, configs_list):
    """ذخیره چندین کانفیگ در فایل"""
    with open(file_path, 'a') as f:
        for config in configs_list:
            if config.strip():
                f.write(config.strip() + '\n')

def git_commit_and_push(file_path, count):
    try:
        subprocess.run(['git', 'config', 'user.name', 'Telegram Bot'], check=False)
        subprocess.run(['git', 'config', 'user.email', 'bot@telegram.com'], check=False)
        subprocess.run(['git', 'add', file_path], check=False)
        subprocess.run(['git', 'commit', '-m', f'Add {count} donated configs'], check=False)
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
    
    # ارسال پیام درخواست اهدا
    send_donation_request(chat_id)

def send_donation_request(chat_id):
    """ارسال پیام درخواست اهدای کانفیگ"""
    donation_text = """💝 کمک به دسترسی آزاد به اینترنت

اگر شما ساب لینک‌ها یا کانفیگ‌های سالمی را تست می‌کنید، لطفاً آنها را به این ربات اهدا کنید.

📌 نحوه اهدا:
کانفیگ‌های خود را (هر خط یک کانفیگ) در یک پیام برای ربات ارسال کنید.

✅ با اهدای کانفیگ‌های سالم، به دیگران در دسترسی آزاد به اینترنت کمک می‌کنید.

🙏 ممنون از همکاری شما"""
    
    send_message(chat_id, donation_text)

def process_donated_configs(chat_id, configs_text):
    """پردازش کانفیگ‌های اهدایی با تاخیر"""
    # جدا کردن خطوط
    lines = [line.strip() for line in configs_text.split('\n') if line.strip() and not line.strip().startswith('/')]
    
    if not lines:
        return
    
    # ذخیره همه کانفیگ‌ها
    save_multiple_configs(DONATED_FILE, lines)
    
    # کامیت به گیت‌هاب
    git_commit_and_push(DONATED_FILE, len(lines))
    
    # آمار جدید
    total_donated = len(get_configs(DONATED_FILE))
    
    # ارسال پیام تشکر
    thank_text = f"""✅ {len(lines)} کانفیگ جدید با موفقیت به بخش اهدایی اضافه شد!

🙏 ممنون از همکاری شما.

📊 آمار جدید کانفیگ‌های اهدایی: {total_donated} عدد

سایر کاربران نیز می‌توانند از این کانفیگ‌ها استفاده کنند."""
    
    send_message(chat_id, thank_text)
    
    # ارسال پیام درخواست اهدا
    send_donation_request(chat_id)

def delayed_process(user_id, chat_id):
    """پردازش تاخیری پیام‌های جمع‌آوری شده"""
    if user_id in user_message_buffer:
        messages = user_message_buffer[user_id]
        if messages:
            # ترکیب همه پیام‌ها
            combined = "\n".join(messages)
            process_donated_configs(chat_id, combined)
        del user_message_buffer[user_id]

def show_config_menu(chat_id):
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
برای اهدای کانفیگ به ربات، کافیست کانفیگ خود را (هر خط یک کانفیگ) در یک پیام برای ربات ارسال کنید.
کانفیگ شما پس از ذخیره به بخش اهدایی اضافه خواهد شد.

برای شروع، یکی از گزینه‌های بالا را انتخاب کنید."""
    
    send_message(chat_id, menu_text, reply_markup=keyboard)

def main():
    last_update_id = 0
    waiting_for_config_type = {}  # {'chat_id': 'donated' or 'main'}
    
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
                    continue
                
                chat_id = msg['chat']['id']
                user_id = msg.get('from', {}).get('id', chat_id)
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
برای اهدای کانفیگ، کافیست کانفیگ خود را (هر خط یک کانفیگ) در یک پیام برای ربات ارسال کنید.

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
                    
                    # پاک کردن بافر این کاربر
                    if user_id in user_message_buffer:
                        del user_message_buffer[user_id]
                
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
کانفیگ‌های خود را (هر خط یک کانفیگ) در یک پیام برای ربات ارسال کنید.

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
                        waiting_for_config_type[chat_id] = 'donated'
                    else:
                        send_message(chat_id, "❌ متاسفانه هیچ کانفیگ اهدایی موجود نیست.\n\nشما می‌توانید اولین نفری باشید که کانفیگ اهدا می‌کند!")
                        send_donation_request(chat_id)
                
                # پردازش دکمه کانفیگ دلتا
                elif text == "⚡ کانفیگ‌های دلتا":
                    main_configs = get_configs(MAIN_FILE)
                    if main_configs:
                        send_message(chat_id, f"🔢 تعداد کانفیگ‌های دلتا موجود: {len(main_configs)}\n\nچند تا کانفیگ از بخش دلتا میخوای؟ (عدد بین 1 تا 50)")
                        waiting_for_config_type[chat_id] = 'main'
                    else:
                        send_message(chat_id, "❌ متاسفانه هیچ کانفیگ دلتا موجود نیست!")
                
                # پردازش عدد (تعداد کانفیگ)
                elif text.isdigit():
                    count = int(text)
                    if 1 <= count <= 50:
                        config_type = waiting_for_config_type.get(chat_id, 'main')
                        
                        if config_type == 'donated':
                            configs = get_configs(DONATED_FILE)
                            source_name = "🎁 کانفیگ‌های اهدایی"
                        else:
                            configs = get_configs(MAIN_FILE)
                            source_name = "⚡ کانفیگ‌های دلتا"
                        
                        if not configs:
                            send_message(chat_id, f"❌ متاسفانه هیچ کانفیگی در {source_name} موجود نیست.")
                            waiting_for_config_type.pop(chat_id, None)
                            continue
                        
                        if count > len(configs):
                            send_message(chat_id, f"⚠️ فقط {len(configs)} کانفیگ در {source_name} موجود است. همین تعداد ارسال می‌شود.")
                            count = len(configs)
                        
                        selected = random.sample(configs, count)
                        send_configs_in_chunks(chat_id, selected, count, source_name)
                        
                        waiting_for_config_type.pop(chat_id, None)
                    else:
                        send_message(chat_id, "❌ لطفاً عددی بین 1 تا 50 وارد کنید.")
                
                # پردازش کانفیگ اهدایی (با بافر و تاخیر)
                elif text not in ["🎁 کانفیگ‌های اهدایی", "⚡ کانفیگ‌های دلتا", "📡 راهنما و اطلاعات", "/start"]:
                    
                    # اضافه کردن به بافر این کاربر
                    if user_id not in user_message_buffer:
                        user_message_buffer[user_id] = []
                    
                    user_message_buffer[user_id].append(text)
                    
                    # اگر تایمر قبلی وجود داشت، کنسل کن
                    if hasattr(process_donated_configs, 'timer_' + str(user_id)):
                        getattr(process_donated_configs, 'timer_' + str(user_id)).cancel()
                    
                    # تنظیم تایمر جدید
                    timer = Timer(BUFFER_TIMEOUT, delayed_process, args=[user_id, chat_id])
                    timer.daemon = True
                    timer.start()
                    setattr(process_donated_configs, 'timer_' + str(user_id), timer)
                    
                    # پیام موقت
                    send_message(chat_id, f"⏳ {len(user_message_buffer[user_id])} پیام دریافت شد. در حال ذخیره‌سازی...")
                
                # هر چیز دیگه
                else:
                    send_message(chat_id, "❌ گزینه نامعتبر!\n\nلطفاً از دکمه‌های پایین صفحه استفاده کنید یا یک عدد معتبر وارد کنید.")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()

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
DONATED_FILE = 'donated.txt'
MAIN_FILE = 'proxy.txt'
SPOOF_FILE = 'spoof.txt'

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

def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    if parse_mode:
        payload['parse_mode'] = parse_mode
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

def send_message_to_all_users(text):
    users_file = 'users.txt'
    try:
        with open(users_file, 'r') as f:
            users = [line.strip() for line in f if line.strip()]
        for chat_id in users:
            try:
                send_message(chat_id, text)
                time.sleep(0.1)
            except:
                pass
    except:
        pass

def save_user(chat_id, first_name, last_name, username):
    users_file = 'users.txt'
    try:
        with open(users_file, 'r') as f:
            existing = f.read()
        if str(chat_id) not in existing:
            with open(users_file, 'a') as f:
                name = first_name if first_name else username
                f.write(f"{chat_id}|{name}\n")
    except:
        with open(users_file, 'a') as f:
            name = first_name if first_name else username
            f.write(f"{chat_id}|{name}\n")

def pin_message(chat_id, message_id):
    url = f"https://api.telegram.org/bot{TOKEN}/pinChatMessage"
    payload = {'chat_id': chat_id, 'message_id': message_id, 'disable_notification': True}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def send_configs_in_chunks(chat_id, configs, total_count, source_name):
    if not configs:
        send_message(chat_id, f"❌ متاسفانه هیچ کانفیگی در بخش {source_name} موجود نیست.")
        return
    
    chunk_size = 10
    num_chunks = math.ceil(len(configs) / chunk_size)
    
    send_message(chat_id, f"📦 منبع: {source_name}\n✅ {len(configs)} کانفیگ در حال ارسال...")
    time.sleep(0.5)
    
    all_configs_text = []
    
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
        all_configs_text.extend(chunk)
        time.sleep(0.5)
    
    # پیام جداگانه برای کپی کردن
    copy_text = "📋 همه کانفیگ‌های درخواستی شما (برای کپی کردن):\n\n" + "\n".join(all_configs_text)
    
    if len(copy_text) > 4000:
        mid = len(copy_text) // 2
        send_message(chat_id, copy_text[:mid])
        send_message(chat_id, copy_text[mid:])
    else:
        send_message(chat_id, copy_text)
    
    send_message(chat_id, f"✨ ارسال {len(configs)} کانفیگ از {source_name} به پایان رسید.")
    
    if source_name != "🎭 کانفیگ‌های اسپوف":
        send_donation_request(chat_id)

def send_donation_request(chat_id):
    donation_text = """💝 کمک به دسترسی آزاد به اینترنت

اگر شما ساب لینک‌ها یا کانفیگ‌های سالمی را تست می‌کنید، لطفاً آنها را به این ربات اهدا کنید.

📌 نحوه اهدا:
1️⃣ روی دکمه "💝 اهدای کانفیگ" کلیک کنید
2️⃣ کانفیگ‌های خود را (هر خط یک کانفیگ) در یک پیام برای ربات ارسال کنید

✅ با اهدای کانفیگ‌های سالم، به دیگران در دسترسی آزاد به اینترنت کمک می‌کنید.

🙏 ممنون از همکاری شما"""
    
    send_message(chat_id, donation_text)

def announce_donation(donor_name, count):
    announcement = f"""🎉 بنازم بنازم {donor_name} جان! 🎉

🙏 {count} تا کانفیگ جدید اهدا کرد!
دمش واقعاً گرم 🌟

به امید دسترسی آزاد برای همه! 🔓🌍"""
    
    send_message_to_all_users(announcement)

def show_config_menu(chat_id):
    keyboard = {
        "keyboard": [
            [{"text": "🎁 کانفیگ‌های اهدایی"}, {"text": "⚡ کانفیگ‌های دلتا"}],
            [{"text": "🎭 کانفیگ‌های اسپوف"}, {"text": "💝 اهدای کانفیگ"}],
            [{"text": "📡 راهنما و اطلاعات"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
        "persistent_keyboard": True
    }
    
    main_configs = get_configs(MAIN_FILE)
    donated_configs = get_configs(DONATED_FILE)
    spoof_configs = get_configs(SPOOF_FILE)
    
    menu_text = f"""🎯 منوی اصلی ربات کانفیگ

لطفاً نوع کانفیگ مورد نظر خود را انتخاب کنید:

🎁 کانفیگ‌های اهدایی: {len(donated_configs)} عدد
⚡ کانفیگ‌های دلتا: {len(main_configs)} عدد
🎭 کانفیگ‌های اسپوف: {len(spoof_configs)} عدد

📌 نحوه اهدای کانفیگ:
روی دکمه "💝 اهدای کانفیگ" کلیک کنید و سپس کانفیگ‌های خود را ارسال کنید.

برای شروع، یکی از گزینه‌های بالا را انتخاب کنید."""
    
    send_message(chat_id, menu_text, reply_markup=keyboard)

def main():
    last_update_id = 0
    waiting_for_config_type = {}
    
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
                text = msg.get('text', '')
                
                # ذخیره کاربر
                user = msg.get('from', {})
                first_name = user.get('first_name', '')
                last_name = user.get('last_name', '')
                username = user.get('username', '')
                save_user(chat_id, first_name, last_name, username)
                
                # نام کاربر برای اهدا
                donor_name = first_name if first_name else (username if username else "کاربر")
                
                # دستور start
                if text == '/start':
                    welcome_text = f"""🎯 به ربات کانفیگ خوش آمدید!

📊 آمار فعلی:
🎁 کانفیگ‌های اهدایی: {len(get_configs(DONATED_FILE))} عدد
⚡ کانفیگ‌های دلتا: {len(get_configs(MAIN_FILE))} عدد
🎭 کانفیگ‌های اسپوف: {len(get_configs(SPOOF_FILE))} عدد

لطفاً برای ادامه، از دکمه‌های پایین صفحه استفاده کنید."""
                    
                    reply_keyboard = {
                        "keyboard": [
                            [{"text": "🎁 کانفیگ‌های اهدایی"}, {"text": "⚡ کانفیگ‌های دلتا"}],
                            [{"text": "🎭 کانفیگ‌های اسپوف"}, {"text": "💝 اهدای کانفیگ"}],
                            [{"text": "📡 راهنما و اطلاعات"}]
                        ],
                        "resize_keyboard": True,
                        "one_time_keyboard": False,
                        "persistent_keyboard": True
                    }
                    
                    result = send_message(chat_id, welcome_text, reply_markup=reply_keyboard)
                    waiting_for_config_type.pop(chat_id, None)
                
                # دکمه اهدای کانفیگ
                elif text == "💝 اهدای کانفیگ":
                    send_message(chat_id, "🔽 لطفاً کانفیگ‌های خود را (هر خط یک کانفیگ) ارسال کنید:")
                    waiting_for_config_type[chat_id] = 'donating'
                
                # دکمه راهنما
                elif text == "📡 راهنما و اطلاعات":
                    help_text = f"""📚 راهنمای استفاده از ربات

🎁 اهدایی: {len(get_configs(DONATED_FILE))} عدد
⚡ دلتا: {len(get_configs(MAIN_FILE))} عدد
🎭 اسپوف: {len(get_configs(SPOOF_FILE))} عدد

💝 اهدا: روی دکمه 💝 کلیک کن و کانفیگ‌ها رو بفرست
📊 محدودیت: 1 تا 100 کانفیگ"""
                    send_message(chat_id, help_text)
                
                # دکمه کانفیگ اهدایی
                elif text == "🎁 کانفیگ‌های اهدایی":
                    configs = get_configs(DONATED_FILE)
                    if configs:
                        send_message(chat_id, f"🔢 چند تا کانفیگ از بخش اهدایی میخوای؟ (1 تا 100)\nموجودی: {len(configs)} عدد")
                        waiting_for_config_type[chat_id] = 'donated'
                    else:
                        send_message(chat_id, "❌ هیچ کانفیگ اهدایی موجود نیست.\nشما می‌تونی اولین نفری باشی که اهدا می‌کنی!")
                        send_donation_request(chat_id)
                
                # دکمه کانفیگ دلتا
                elif text == "⚡ کانفیگ‌های دلتا":
                    configs = get_configs(MAIN_FILE)
                    if configs:
                        send_message(chat_id, f"🔢 چند تا کانفیگ از بخش دلتا میخوای؟ (1 تا 100)\nموجودی: {len(configs)} عدد")
                        waiting_for_config_type[chat_id] = 'main'
                    else:
                        send_message(chat_id, "❌ هیچ کانفیگ دلتا موجود نیست!")
                
                # دکمه کانفیگ اسپوف
                elif text == "🎭 کانفیگ‌های اسپوف":
                    configs = get_configs(SPOOF_FILE)
                    if configs:
                        send_message(chat_id, f"🔢 چند تا کانفیگ از بخش اسپوف میخوای؟ (1 تا 100)\nموجودی: {len(configs)} عدد")
                        waiting_for_config_type[chat_id] = 'spoof'
                    else:
                        send_message(chat_id, "❌ هیچ کانفیگ اسپوف موجود نیست!")
                
                # پردازش عدد
                elif text.isdigit() and waiting_for_config_type.get(chat_id) in ['donated', 'main', 'spoof']:
                    count = int(text)
                    if 1 <= count <= 100:
                        config_type = waiting_for_config_type[chat_id]
                        
                        if config_type == 'donated':
                            configs = get_configs(DONATED_FILE)
                            source_name = "🎁 کانفیگ‌های اهدایی"
                        elif config_type == 'spoof':
                            configs = get_configs(SPOOF_FILE)
                            source_name = "🎭 کانفیگ‌های اسپوف"
                        else:
                            configs = get_configs(MAIN_FILE)
                            source_name = "⚡ کانفیگ‌های دلتا"
                        
                        if not configs:
                            send_message(chat_id, f"❌ کانفیگی در {source_name} موجود نیست!")
                            waiting_for_config_type.pop(chat_id, None)
                            continue
                        
                        if count > len(configs):
                            send_message(chat_id, f"⚠️ فقط {len(configs)} کانفیگ موجود است. همین تعداد ارسال می‌شود.")
                            count = len(configs)
                        
                        selected = random.sample(configs, count)
                        send_configs_in_chunks(chat_id, selected, count, source_name)
                        waiting_for_config_type.pop(chat_id, None)
                    else:
                        send_message(chat_id, "❌ لطفاً عددی بین 1 تا 100 وارد کنید.")
                
                # پردازش کانفیگ اهدایی
                elif waiting_for_config_type.get(chat_id) == 'donating' and text not in ["🎁 کانفیگ‌های اهدایی", "⚡ کانفیگ‌های دلتا", "🎭 کانفیگ‌های اسپوف", "💝 اهدای کانفیگ", "📡 راهنما و اطلاعات", "/start"]:
                    
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    
                    if lines:
                        old_count = len(get_configs(DONATED_FILE))
                        save_multiple_configs(DONATED_FILE, lines)
                        git_commit_and_push(DONATED_FILE, len(lines))
                        total = len(get_configs(DONATED_FILE))
                        
                        send_message(chat_id, f"✅ {len(lines)} کانفیگ جدید به بخش اهدایی اضافه شد!\n📊 آمار جدید: {total} عدد")
                        
                        # اعلام به همه
                        announce_donation(donor_name, len(lines))
                        
                        send_donation_request(chat_id)
                    
                    waiting_for_config_type.pop(chat_id, None)
                    show_config_menu(chat_id)
                
                # هر چیز دیگه
                elif text not in ["🎁 کانفیگ‌های اهدایی", "⚡ کانفیگ‌های دلتا", "🎭 کانفیگ‌های اسپوف", "💝 اهدای کانفیگ", "📡 راهنما و اطلاعات", "/start"]:
                    send_message(chat_id, "❌ گزینه نامعتبر!\n\nلطفاً از دکمه‌های پایین صفحه استفاده کنید یا یک عدد بین 1 تا 100 وارد کنید.")
                    show_config_menu(chat_id)
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()

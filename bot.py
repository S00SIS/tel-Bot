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
    except:
        return []

def save_multiple_configs(file_path, configs_list):
    try:
        with open(file_path, 'a') as f:
            for config in configs_list:
                if config.strip():
                    f.write(config.strip() + '\n')
        return True
    except:
        return False

def git_commit_and_push(file_path, count):
    try:
        subprocess.run(['git', 'config', 'user.name', 'Telegram Bot'], check=False, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'bot@telegram.com'], check=False, capture_output=True)
        subprocess.run(['git', 'add', file_path], check=False, capture_output=True)
        subprocess.run(['git', 'commit', '-m', f'Add {count} donated configs'], check=False, capture_output=True)
        subprocess.run(['git', 'push'], check=False, capture_output=True)
        return True
    except:
        return False

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response
    except:
        return None

def save_user(chat_id, first_name):
    try:
        users_file = 'users.txt'
        with open(users_file, 'a') as f:
            name = first_name if first_name else str(chat_id)
            f.write(f"{chat_id}|{name}\n")
    except:
        pass

def send_message_to_all_users(text):
    try:
        with open('users.txt', 'r') as f:
            users = [line.strip() for line in f if line.strip()]
        for user in users:
            chat_id = user.split('|')[0]
            try:
                send_message(chat_id, text)
                time.sleep(0.1)
            except:
                pass
    except:
        pass

def pin_message(chat_id, message_id):
    url = f"https://api.telegram.org/bot{TOKEN}/pinChatMessage"
    payload = {'chat_id': chat_id, 'message_id': message_id, 'disable_notification': True}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def send_configs_in_chunks(chat_id, configs, total_count, source_name):
    if not configs:
        send_message(chat_id, f"❌ هیچ کانفیگی در بخش {source_name} موجود نیست.")
        return
    
    chunk_size = 10
    num_chunks = (len(configs) + chunk_size - 1) // chunk_size
    
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
            message = f"📦 بخش {i+1} از {num_chunks}:\n\n" + "\n".join(chunk)
        
        send_message(chat_id, message)
        all_configs_text.extend(chunk)
        time.sleep(0.5)
    
    # پیام پایان ارسال
    send_message(chat_id, f"✨ ارسال {len(configs)} کانفیگ از {source_name} به پایان رسید.")
    time.sleep(0.5)
    
    # پیام کپی کردن
    copy_text = "\n".join(all_configs_text)
    send_message(chat_id, copy_text)
    time.sleep(0.5)
    
    # پیام درخواست اهدا
    if source_name != "🎭 کانفیگ‌های اسپوف":
        donation_text = """💝 کمک به دسترسی آزاد به اینترنت

اگر ساب لینک یا کانفیگ سالم داری، به ربات اهدا کن.

روی دکمه "💝 اهدای کانفیگ" کلیک کن و کانفیگ‌ها رو بفرست.

ممنون از همکاریت 🙏"""
        send_message(chat_id, donation_text)

def announce_donation(donor_name, count):
    announcement = f"""🎉 {donor_name} جان! {count} تا کانفیگ اهدا کرد! دمش گرم 🌟"""
    send_message_to_all_users(announcement)

def show_config_menu(chat_id):
    keyboard = {
        "keyboard": [
            [{"text": "🎁 اهدایی"}, {"text": "⚡ دلتا"}],
            [{"text": "🎭 اسپوف"}, {"text": "💝 اهدا"}],
            [{"text": "📡 راهنما"}]
        ],
        "resize_keyboard": True,
        "persistent_keyboard": True
    }
    
    main_count = len(get_configs(MAIN_FILE))
    donated_count = len(get_configs(DONATED_FILE))
    spoof_count = len(get_configs(SPOOF_FILE))
    
    menu_text = f"""🎯 منوی اصلی

🎁 اهدایی: {donated_count} عدد
⚡ دلتا: {main_count} عدد
🎭 اسپوف: {spoof_count} عدد

یکی رو انتخاب کن:"""
    
    send_message(chat_id, menu_text, reply_markup=keyboard)

def main():
    last_update_id = 0
    waiting_for_config_type = {}
    
    while True:
        try:
            check_time()
            
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            params = {'timeout': 30, 'offset': last_update_id + 1}
            response = requests.get(url, params=params, timeout=35)
            data = response.json()
            
            if not data.get('ok'):
                time.sleep(1)
                continue
            
            updates = data.get('result', [])
            
            for update in updates:
                check_time()
                last_update_id = update['update_id'] + 1
                
                if 'message' not in update:
                    continue
                
                msg = update['message']
                
                if 'text' not in msg:
                    continue
                
                chat_id = msg['chat']['id']
                text = msg.get('text', '')
                
                # ذخیره کاربر
                first_name = msg.get('from', {}).get('first_name', 'کاربر')
                save_user(chat_id, first_name)
                
                # start
                if text == '/start':
                    show_config_menu(chat_id)
                    waiting_for_config_type.pop(chat_id, None)
                
                # دکمه اهدا
                elif text == "💝 اهدا":
                    send_message(chat_id, "کانفیگ‌هات رو بفرست (هر خط یکی):")
                    waiting_for_config_type[chat_id] = 'donating'
                
                # دکمه راهنما
                elif text == "📡 راهنما":
                    help_text = """📚 راهنما:
- هر دکمه رو بزن، تعداد مورد نیازت رو وارد کن
- محدودیت: 1 تا 100 کانفیگ
- برای اهدا، اول دکمه 💝 اهدا رو بزن"""
                    send_message(chat_id, help_text)
                
                # دکمه اهدایی
                elif text == "🎁 اهدایی":
                    configs = get_configs(DONATED_FILE)
                    if configs:
                        send_message(chat_id, f"چند تا کانفیگ از اهدایی میخوای؟ (1-100)\nموجودی: {len(configs)}")
                        waiting_for_config_type[chat_id] = 'donated'
                    else:
                        send_message(chat_id, "هیچ کانفیگ اهدایی نداریم. اولین نفری باش که اهدا میکنی!")
                        waiting_for_config_type.pop(chat_id, None)
                
                # دکمه دلتا
                elif text == "⚡ دلتا":
                    configs = get_configs(MAIN_FILE)
                    if configs:
                        send_message(chat_id, f"چند تا کانفیگ از دلتا میخوای؟ (1-100)\nموجودی: {len(configs)}")
                        waiting_for_config_type[chat_id] = 'main'
                    else:
                        send_message(chat_id, "کانفیگ دلتا موجود نیست!")
                        waiting_for_config_type.pop(chat_id, None)
                
                # دکمه اسپوف
                elif text == "🎭 اسپوف":
                    configs = get_configs(SPOOF_FILE)
                    if configs:
                        send_message(chat_id, f"چند تا کانفیگ از اسپوف میخوای؟ (1-100)\nموجودی: {len(configs)}")
                        waiting_for_config_type[chat_id] = 'spoof'
                    else:
                        send_message(chat_id, "کانفیگ اسپوف موجود نیست!")
                        waiting_for_config_type.pop(chat_id, None)
                
                # عدد
                elif text.isdigit() and waiting_for_config_type.get(chat_id) in ['donated', 'main', 'spoof']:
                    count = int(text)
                    if 1 <= count <= 100:
                        ctype = waiting_for_config_type[chat_id]
                        if ctype == 'donated':
                            configs = get_configs(DONATED_FILE)
                            sname = "🎁 اهدایی"
                        elif ctype == 'spoof':
                            configs = get_configs(SPOOF_FILE)
                            sname = "🎭 اسپوف"
                        else:
                            configs = get_configs(MAIN_FILE)
                            sname = "⚡ دلتا"
                        
                        if not configs:
                            send_message(chat_id, f"کانفیگی در {sname} نیست!")
                            waiting_for_config_type.pop(chat_id, None)
                            continue
                        
                        if count > len(configs):
                            count = len(configs)
                        
                        selected = random.sample(configs, count)
                        send_configs_in_chunks(chat_id, selected, count, sname)
                        waiting_for_config_type.pop(chat_id, None)
                    else:
                        send_message(chat_id, "عدد بین 1 تا 100 وارد کن!")
                
                # اهدا کردن
                elif waiting_for_config_type.get(chat_id) == 'donating':
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    if lines:
                        save_multiple_configs(DONATED_FILE, lines)
                        git_commit_and_push(DONATED_FILE, len(lines))
                        total = len(get_configs(DONATED_FILE))
                        send_message(chat_id, f"✅ {len(lines)} کانفیگ اهدا شد!\nمجموع اهدایی: {total}")
                        announce_donation(first_name, len(lines))
                    waiting_for_config_type.pop(chat_id, None)
                    show_config_menu(chat_id)
                
                # بقیه
                elif text not in ["🎁 اهدایی", "⚡ دلتا", "🎭 اسپوف", "💝 اهدا", "📡 راهنما", "/start"]:
                    send_message(chat_id, "❌ نامعتبر!\nاز دکمه‌ها استفاده کن یا عدد بین 1 تا 100 وارد کن")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()

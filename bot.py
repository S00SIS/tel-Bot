import random
import os
import time
import requests
import json
import sys
import math

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
START_TIME = time.time()
MAX_RUNTIME = 6 * 60 * 60

def check_time():
    if time.time() - START_TIME > MAX_RUNTIME:
        print("6 ساعت تموم شد، ربات خاموش میشه...")
        sys.exit(0)

def get_configs():
    with open('proxy.txt', 'r') as f:
        return [line.strip() for line in f if line.strip()]

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

def send_configs_in_chunks(chat_id, configs, total_count):
    """ارسال کانفیگ‌ها در گروه‌های 10 تایی"""
    chunk_size = 10
    num_chunks = math.ceil(len(configs) / chunk_size)
    
    for i in range(num_chunks):
        start = i * chunk_size
        end = start + chunk_size
        chunk = configs[start:end]
        
        # ساخت پیام برای این گروه
        if num_chunks == 1:
            # اگر همه کانفیگ‌ها توی یه پیام جا بشن
            message = "\n".join(chunk)
        else:
            # گروه چندتایی
            if i == 0:
                message = f"📦 بخش {i+1} از {num_chunks} (کانفیگ {start+1} تا {min(end, total_count)}):\n\n" + "\n".join(chunk)
            else:
                message = f"\n📦 بخش {i+1} از {num_chunks} (کانفیگ {start+1} تا {min(end, total_count)}):\n\n" + "\n".join(chunk)
        
        send_message(chat_id, message)
        time.sleep(0.5)  # کمی تاخیر بین پیام‌ها برای جلوگیری از محدودیت تلگرام

def main():
    configs = get_configs()
    last_update_id = 0
    
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
                
                if 'message' in update:
                    msg = update['message']
                    chat_id = msg['chat']['id']
                    text = msg.get('text', '')
                    
                    if text == '/start':
                        welcome_text = f"""🎯 به ربات کانفیگ خوش آمدید!

این ربات به شما امکان دریافت کانفیگ‌های دلخواه را می‌دهد.

📌 نحوه استفاده:
1️⃣ روی دکمه "📡 درخواست کانفیگ" کلیک کنید
2️⃣ تعداد کانفیگ مورد نیاز خود را وارد کنید (عدد بین 1 تا 50)

📊 آمار فعلی: {len(configs)} کانفیگ در مخزن موجود است.

⚠️ نکته: کانفیگ‌ها در گروه‌های ۱۰ تایی برای شما ارسال می‌شوند.

لطفاً برای شروع، روی دکمه زیر کلیک کنید."""
                        
                        keyboard = {
                            "inline_keyboard": [[
                                {"text": "📡 درخواست کانفیگ", "callback_data": "config"}
                            ]]
                        }
                        send_message(chat_id, welcome_text, reply_markup=keyboard)
                    
                    elif text.isdigit():
                        count = int(text)
                        if 1 <= count <= 50:
                            if count > len(configs):
                                send_message(chat_id, f"⚠️ فقط {len(configs)} کانفیگ در مخزن موجود است. همین تعداد ارسال می‌شود.")
                                count = len(configs)
                            
                            # انتخاب رندوم کانفیگ‌ها
                            selected = random.sample(configs, count)
                            
                            # ارسال اولیه (اعلام تعداد کل)
                            send_message(chat_id, f"✅ {count} کانفیگ درخواستی شما در حال ارسال است...")
                            time.sleep(0.5)
                            
                            # ارسال گروهی کانفیگ‌ها
                            send_configs_in_chunks(chat_id, selected, count)
                            
                            # پیام پایان
                            send_message(chat_id, f"✨ ارسال {count} کانفیگ به پایان رسید.")
                        else:
                            send_message(chat_id, "❌ لطفاً عددی بین 1 تا 50 وارد کنید.")
                    elif text != '/start':
                        send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید.\n\nبرای شروع مجدد /start را بزنید.")
                
                elif 'callback_query' in update:
                    query = update['callback_query']
                    chat_id = query['message']['chat']['id']
                    query_id = query['id']
                    requests.get(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery?callback_query_id={query_id}")
                    send_message(chat_id, f"🔢 چند تا کانفیگ میخوای؟ (عدد بین 1 تا 50)\n\n📊 {len(configs)} کانفیگ در مخزن موجود است.\n\n⚠️ کانفیگ‌ها در گروه‌های ۱۰ تایی ارسال می‌شوند.")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()

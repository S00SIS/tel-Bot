import random
import os
import time
import requests
import json
import sys

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
    requests.post(url, json=payload)

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
                        # پیام خوش‌آمدگویی اولیه
                        welcome_text = """🎯 به ربات کانفیگ خوش آمدید!

این ربات به شما امکان دریافت کانفیگ‌های دلخواه را می‌دهد.

📌 نحوه استفاده:
1️⃣ روی دکمه "📡 درخواست کانفیگ" کلیک کنید
2️⃣ تعداد کانفیگ مورد نیاز خود را وارد کنید (عدد بین 1 تا 50)

📊 آمار فعلی: {} کانفیگ در مخزن موجود است.

لطفاً برای شروع، روی دکمه زیر کلیک کنید.""".format(len(configs))
                        
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
                            selected = random.sample(configs, count)
                            response = "\n".join(selected)
                            send_message(chat_id, response)
                        else:
                            send_message(chat_id, "❌ لطفاً عددی بین 1 تا 50 وارد کنید.")
                    elif text != '/start':
                        send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید.\n\nبرای شروع مجدد /start را بزنید.")
                
                elif 'callback_query' in update:
                    query = update['callback_query']
                    chat_id = query['message']['chat']['id']
                    query_id = query['id']
                    requests.get(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery?callback_query_id={query_id}")
                    send_message(chat_id, f"🔢 چند تا کانفیگ میخوای؟ (عدد بین 1 تا 50)\n\n📊 {len(configs)} کانفیگ در مخزن موجود است.")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()

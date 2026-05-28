import random
import os
import time
import requests
import json
import sys

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
START_TIME = time.time()
MAX_RUNTIME = 6 * 60 * 60  # 6 ساعت به ثانیه

def check_time():
    """اگه 6 ساعت گذشت، ربات رو خاموش کن"""
    if time.time() - START_TIME > MAX_RUNTIME:
        print("6 ساعت تموم شد، ربات خاموش میشه...")
        sys.exit(0)

def get_proxies():
    with open('proxy.txt', 'r') as f:
        return [line.strip() for line in f if line.strip()]

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    requests.post(url, json=payload)

def main():
    proxies = get_proxies()
    last_update_id = 0
    
    while True:
        check_time()  # هر بار چک کن 6 ساعت گذشته یا نه
        
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
                        keyboard = {
                            "inline_keyboard": [[
                                {"text": "📡 درخواست پروکسی", "callback_data": "proxy"}
                            ]]
                        }
                        send_message(chat_id, "🎯 به ربات پروکسی خوش آمدید!\n\nروی دکمه کلیک کن:", reply_markup=keyboard)
                    
                    elif text.isdigit():
                        count = int(text)
                        if 1 <= count <= 50:
                            selected = random.sample(proxies, min(count, len(proxies)))
                            response = "\n".join([f"{i+1}. {p}" for i, p in enumerate(selected)])
                            send_message(chat_id, f"✅ {len(selected)} پروکسی:\n\n{response}")
                        else:
                            send_message(chat_id, "❌ عدد بین 1 تا 50 وارد کن")
                    elif text != '/start':
                        send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کن")
                
                elif 'callback_query' in update:
                    query = update['callback_query']
                    chat_id = query['message']['chat']['id']
                    query_id = query['id']
                    requests.get(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery?callback_query_id={query_id}")
                    send_message(chat_id, "🔢 چندتا پروکسی میخوای؟ (عدد بفرست)")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()

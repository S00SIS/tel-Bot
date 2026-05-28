import os
import random
import requests
import json

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    exit("TELEGRAM_BOT_TOKEN environment variable not set!")

# تابعی برای ارسال پیام
def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    try:
        requests.post(url, json=payload, timeout=5).raise_for_status()
    except Exception as e:
        print(f"Error sending message: {e}")

# دریافت آخرین آپدیت‌ها
def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    params = {'timeout': 5, 'allowed_updates': ['message', 'callback_query']}
    if offset:
        params['offset'] = offset
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get('result', [])
    except Exception as e:
        print(f"Error getting updates: {e}")
        return []

# خواندن پروکسی‌ها
def get_proxies():
    try:
        with open('proxy.txt', 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        return proxies
    except Exception as e:
        print(f"Error reading proxies: {e}")
        return []

# عملکرد اصلی
def main():
    last_update_id = 0
    proxies = get_proxies()
    if not proxies:
        print("No proxies found.")
        return

    while True:
        updates = get_updates(offset=last_update_id + 1 if last_update_id else None)
        if not updates:
            break

        for update in updates:
            last_update_id = update.get('update_id')
            print(last_update_id)

            # مدیریت کلیک روی دکمه (callback query)
            if 'callback_query' in update:
                query = update['callback_query']
                chat_id = query['message']['chat']['id']
                callback_data = query['data']
                query_id = query['id']
                # پاسخ به کلیک (برای رفع بارگذاری دکمه)
                requests.get(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery?callback_query_id={query_id}")

                if callback_data == "request_proxy":
                    send_message(chat_id, "🔢 لطفاً تعداد پروکسی مورد نیاز خود را به صورت عدد وارد کنید (مثلاً 5):")
                continue

            # مدیریت پیام‌ها
            if 'message' in update:
                message = update['message']
                chat_id = message['chat']['id']
                text = message.get('text', '')

                if text == '/start':
                    keyboard = {
                        "inline_keyboard": [[{"text": "📡 درخواست پروکسی", "callback_data": "request_proxy"}]]
                    }
                    send_message(chat_id, "🎯 به ربات پروکسی خوش آمدید!\n\nبرای دریافت پروکسی، روی دکمه زیر کلیک کنید:", reply_markup=keyboard)
                elif text.isdigit():
                    count = int(text)
                    if count > 50:
                        send_message(chat_id, "⚠️ حداکثر می‌توانید 50 پروکسی درخواست کنید.")
                    else:
                        selected = random.sample(proxies, min(count, len(proxies)))
                        response = f"✅ {len(selected)} عدد پروکسی درخواستی شما:\n\n" + "\n".join(selected)
                        if count > len(proxies):
                            response += f"\n\n⚠️ توجه: شما {count} عدد درخواست کردید اما فقط {len(proxies)} پروکسی موجود است."
                        response += f"\n\n📊 آمار: {len(proxies)} پروکسی در مخزن موجود است."
                        send_message(chat_id, response)
                else:
                    send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید.")

if __name__ == "__main__":
    main()

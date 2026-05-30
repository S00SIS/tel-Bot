import random
import os
import time
import requests
import sys
import math

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
START_TIME = time.time()
MAX_RUNTIME = 6 * 60 * 60

DONATED_FILE = 'donated.txt'
MAIN_FILE = 'proxy.txt'
SPOOF_FILE = 'spoof.txt'

def check_time():
    if time.time() - START_TIME > MAX_RUNTIME:
        sys.exit(0)

def get_configs(path):
    try:
        with open(path, 'r') as f:
            return [l.strip() for l in f if l.strip()]
    except:
        return []

def send(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={'chat_id': chat_id, 'text': text}, timeout=10)
    except:
        pass

def main():
    last_id = 0
    state = {}  # {chat_id: 'waiting_count' or 'waiting_donate'}
    config_type = {}  # {chat_id: 'main' or 'donated' or 'spoof'}
    
    while True:
        check_time()
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            res = requests.get(url, params={'timeout': 25, 'offset': last_id + 1}, timeout=30)
            data = res.json()
            
            for upd in data.get('result', []):
                last_id = upd['update_id']
                msg = upd.get('message')
                if not msg or 'text' not in msg:
                    continue
                
                cid = msg['chat']['id']
                txt = msg['text']
                name = msg.get('from', {}).get('first_name', 'کاربر')
                
                # ===== START =====
                if txt == '/start':
                    keyboard = {
                        "keyboard": [
                            ["🎁 اهدایی", "⚡ دلتا"],
                            ["🎭 اسپوف", "💝 اهدا"]
                        ],
                        "resize_keyboard": True,
                        "persistent_keyboard": True
                    }
                    welcome = f"""🎯 ربات کانفیگ

🎁 اهدایی: {len(get_configs(DONATED_FILE))}
⚡ دلتا: {len(get_configs(MAIN_FILE))}
🎭 اسپوف: {len(get_configs(SPOOF_FILE))}

یکی رو انتخاب کن:"""
                    send(cid, welcome)
                    try:
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                    json={'chat_id': cid, 'text': welcome, 'reply_markup': keyboard}, timeout=10)
                    except:
                        pass
                    state.pop(cid, None)
                    config_type.pop(cid, None)
                    continue
                
                # ===== دکمه اهدا =====
                if txt == "💝 اهدا":
                    send(cid, "کانفیگ‌هات رو بفرست (هر خط یکی):")
                    state[cid] = 'waiting_donate'
                    continue
                
                # ===== دکمه اهدایی =====
                if txt == "🎁 اهدایی":
                    cfg = get_configs(DONATED_FILE)
                    if cfg:
                        send(cid, f"چند تا؟ (1-{min(100, len(cfg))})\nموجودی: {len(cfg)}")
                        state[cid] = 'waiting_count'
                        config_type[cid] = 'donated'
                    else:
                        send(cid, "کانفیگ اهدایی نداریم. اولین نفری باش که اهدا میکنی!")
                    continue
                
                # ===== دکمه دلتا =====
                if txt == "⚡ دلتا":
                    cfg = get_configs(MAIN_FILE)
                    if cfg:
                        send(cid, f"چند تا؟ (1-{min(100, len(cfg))})\nموجودی: {len(cfg)}")
                        state[cid] = 'waiting_count'
                        config_type[cid] = 'main'
                    else:
                        send(cid, "کانفیگ دلتا نداریم!")
                    continue
                
                # ===== دکمه اسپوف =====
                if txt == "🎭 اسپوف":
                    cfg = get_configs(SPOOF_FILE)
                    if cfg:
                        send(cid, f"چند تا؟ (1-{min(100, len(cfg))})\nموجودی: {len(cfg)}")
                        state[cid] = 'waiting_count'
                        config_type[cid] = 'spoof'
                    else:
                        send(cid, "کانفیگ اسپوف نداریم!")
                    continue
                
                # ===== دریافت تعداد =====
                if state.get(cid) == 'waiting_count' and txt.isdigit():
                    count = int(txt)
                    if count < 1 or count > 100:
                        send(cid, "عدد بین 1 تا 100 باشه!")
                        state.pop(cid, None)
                        continue
                    
                    ct = config_type.get(cid, 'main')
                    if ct == 'donated':
                        cfgs = get_configs(DONATED_FILE)
                        src = "🎁 اهدایی"
                    elif ct == 'spoof':
                        cfgs = get_configs(SPOOF_FILE)
                        src = "🎭 اسپوف"
                    else:
                        cfgs = get_configs(MAIN_FILE)
                        src = "⚡ دلتا"
                    
                    if not cfgs:
                        send(cid, f"{src} کانفیگی نداره!")
                        state.pop(cid, None)
                        continue
                    
                    if count > len(cfgs):
                        count = len(cfgs)
                        send(cid, f"⚠️ فقط {count} تا موجود بود")
                    
                    selected = random.sample(cfgs, count)
                    
                    # ارسال گروهی 10 تایی
                    all_cfgs = []
                    for i in range(0, len(selected), 10):
                        chunk = selected[i:i+10]
                        send(cid, "\n".join(chunk))
                        all_cfgs.extend(chunk)
                        time.sleep(0.3)
                    
                    # پیام پایان
                    send(cid, f"✨ ارسال {len(selected)} کانفیگ از {src} به پایان رسید.")
                    time.sleep(0.3)
                    
                    # پیام کپی همه (همون کانفیگ‌ها بدون هیچ توضیح اضافه)
                    send(cid, "\n".join(all_cfgs))
                    time.sleep(0.3)
                    
                    # پیام درخواست اهدا
                    if src != "🎭 اسپوف":
                        send(cid, "💝 اگه کانفیگ سالم داری، اهدا کن\nروی دکمه 💝 اهدا بزن")
                    
                    state.pop(cid, None)
                    config_type.pop(cid, None)
                    continue
                
                # ===== دریافت کانفیگ اهدایی =====
                if state.get(cid) == 'waiting_donate':
                    lines = [l.strip() for l in txt.split('\n') if l.strip()]
                    if lines:
                        # ذخیره
                        with open(DONATED_FILE, 'a') as f:
                            for l in lines:
                                f.write(l + '\n')
                        # کامیت
                        try:
                            import subprocess
                            subprocess.run(['git', 'add', DONATED_FILE], capture_output=True)
                            subprocess.run(['git', 'commit', '-m', f'add {len(lines)} configs from {name}'], capture_output=True)
                            subprocess.run(['git', 'push'], capture_output=True)
                        except:
                            pass
                        
                        total = len(get_configs(DONATED_FILE))
                        send(cid, f"✅ {len(lines)} تا کانفیگ اهدا شد! ممنون 🙏\nمجموع اهدایی: {total}")
                        
                        # اعلام به همه (ساده)
                        try:
                            with open('users.txt', 'r') as f:
                                users = [u.strip().split('|')[0] for u in f if u.strip()]
                            for u in users:
                                try:
                                    send(u, f"🎉 {name} جان! {len(lines)} تا کانفیگ اهدا کرد! دمش گرم 🌟")
                                    time.sleep(0.1)
                                except:
                                    pass
                        except:
                            pass
                        
                        # ذخیره کاربر
                        try:
                            with open('users.txt', 'a') as f:
                                f.write(f"{cid}|{name}\n")
                        except:
                            pass
                    
                    state.pop(cid, None)
                    # برگردوندن منو
                    keyboard = {
                        "keyboard": [
                            ["🎁 اهدایی", "⚡ دلتا"],
                            ["🎭 اسپوف", "💝 اهدا"]
                        ],
                        "resize_keyboard": True,
                        "persistent_keyboard": True
                    }
                    try:
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                    json={'chat_id': cid, 'text': "منوی اصلی:", 'reply_markup': keyboard}, timeout=10)
                    except:
                        pass
                    continue
                
                # ===== هرچیز دیگه =====
                if txt not in ["🎁 اهدایی", "⚡ دلتا", "🎭 اسپوف", "💝 اهدا", "/start"]:
                    send(cid, "از دکمه‌ها استفاده کن یا عدد بفرست")
            
            time.sleep(1)
        except Exception as e:
            print(e)
            time.sleep(5)

if __name__ == "__main__":
    main()

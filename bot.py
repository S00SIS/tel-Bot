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
    
    # پیام پایان ارسال
    send_message(chat_id, f"✨ ارسال {len(configs)} کانفیگ از {source_name} به پایان رسید.")
    
    # ========== پیام کپی کردن (بعد از پیام پایان) ==========
    copy_text = "\n".join(all_configs_text)
    copy_message = f"""📋 همه کانفیگ‌های بالا رو یکجا کپی کن و داخل برنامه‌ات وارد کن:

{copy_text}"""
    
    if len(copy_message) > 4000:
        send_message(chat_id, copy_message[:4000])
        if len(copy_message) > 4000:
            send_message(chat_id, copy_message[4000:8000])
    else:
        send_message(chat_id, copy_message)
    # ====================================================
    
    # ارسال پیام درخواست اهدا (فقط برای بخش‌های غیر اسپوف)
    if source_name != "🎭 کانفیگ‌های اسپوف":
        send_donation_request(chat_id)

def send_configs_in_chunks(chat_id, configs, total_count, source_name):
    if not configs:
        send_message(chat_id, f"❌ متاسفانه هیچ کانفیگی در بخش {source_name} موجود نیست.")
        return
    
    chunk_size = 10
    num_chunks = math.ceil(len(configs) / chunk_size)
    
    send_message(chat_id, f"📦 منبع: {source_name}\n✅ {len(configs)} کانفیگ در حال ارسال...")
    time.sleep(0.5)
    
    all_configs_text = []  # ذخیره همه کانفیگ‌ها برای کپی کردن
    
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
        all_configs_text.extend(chunk)  # اضافه کردن به لیست کلی
        time.sleep(0.5)
    
    # ========== پیام جداگانه برای کپی کردن ==========
    copy_text = "📋 **همه کانفیگ‌های درخواستی شما (برای کپی کردن):**\n\n```\n" + "\n".join(all_configs_text) + "\n```"
    
    # اگه طول پیام خیلی زیاد بود، تکه تکه کن
    if len(copy_text) > 4000:
        # بدون کد بلاک برای تکه‌های بعدی
        send_message(chat_id, "📋 **همه کانفیگ‌های درخواستی شما (بخش اول):**\n\n```\n" + "\n".join(all_configs_text[:50]) + "\n```")
        remaining = all_configs_text[50:]
        if remaining:
            send_message(chat_id, "📋 **ادامه کانفیگ‌ها:**\n\n```\n" + "\n".join(remaining) + "\n```")
    else:
        send_message(chat_id, copy_text, parse_mode="Markdown")
    # ============================================
    
    send_message(chat_id, f"✨ ارسال {len(configs)} کانفیگ از {source_name} به پایان رسید.")
    
    # ارسال پیام درخواست اهدا (فقط برای بخش‌های غیر اسپوف)
    if source_name != "🎭 کانفیگ‌های اسپوف":
        send_donation_request(chat_id)

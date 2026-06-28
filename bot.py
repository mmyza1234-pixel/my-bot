import os
import json
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8886638574:AAFBxVu-PreNeFSFv46BIq4BzFUpYUdFsBM")
OWNER_ID  = os.environ.get("OWNER_ID",  "8054751209")
API       = f"https://api.telegram.org/bot{BOT_TOKEN}"

# In-memory state per user
user_state = {}

def send(chat_id, text, keyboard=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if keyboard:
        data["reply_markup"] = json.dumps(keyboard)
    requests.post(f"{API}/sendMessage", json=data)

def main_menu():
    return {
        "keyboard": [
            [{"text": "📋 ثبت سفارش"}],
            [{"text": "📞 تماس با ما"}, {"text": "ℹ️ درباره ما"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def service_menu():
    return {
        "keyboard": [
            [{"text": "🌐 طراحی سایت"}],
            [{"text": "🎨 طراحی پوستر"}],
            [{"text": "✦ هر دو (سایت + پوستر)"}],
            [{"text": "🏷 هویت بصری (لوگو)"}],
            [{"text": "🔙 بازگشت"}]
        ],
        "resize_keyboard": True
    }

def handle(update):
    msg = update.get("message")
    if not msg:
        return

    chat_id = str(msg["chat"]["id"])
    text    = msg.get("text", "").strip()
    name    = msg["from"].get("first_name", "کاربر")

    state = user_state.get(chat_id, {})

    # /start
    if text == "/start":
        user_state[chat_id] = {}
        send(chat_id,
             f"سلام <b>{name}</b> عزیز! 👋\n\n"
             "به ربات رسمی <b>AI Studio</b> خوش اومدی.\n"
             "طراحی سایت و پوستر با هوش مصنوعی 🤖✨\n\n"
             "از منو زیر انتخاب کن 👇",
             main_menu())
        return

    # ── ثبت سفارش ──
    if text == "📋 ثبت سفارش":
        user_state[chat_id] = {"step": "service"}
        send(chat_id, "چه خدمتی می‌خوای؟ 👇", service_menu())
        return

    if text == "🔙 بازگشت":
        user_state[chat_id] = {}
        send(chat_id, "به منو اصلی برگشتی 👇", main_menu())
        return

    # ── تماس ──
    if text == "📞 تماس با ما":
        send(chat_id,
             "📬 <b>راه‌های تماس:</b>\n\n"
             "• تلگرام: @mohammadmirzaie13873959\n"
             "• ایتا: @mohammadmirzaie1387",
             main_menu())
        return

    # ── درباره ما ──
    if text == "ℹ️ درباره ما":
        send(chat_id,
             "✨ <b>AI Studio</b>\n\n"
             "طراحی سایت و پوستر تبلیغاتی با هوش مصنوعی\n\n"
             "🎯 تحویل سریع · طراحی اختصاصی · قیمت مناسب\n\n"
             "💰 شروع قیمت از <b>۵۰ هزار تومان</b>",
             main_menu())
        return

    # ── مراحل ثبت سفارش ──
    step = state.get("step")

    if step == "service" and text in ["🌐 طراحی سایت", "🎨 طراحی پوستر", "✦ هر دو (سایت + پوستر)", "🏷 هویت بصری (لوگو)"]:
        user_state[chat_id] = {"step": "name", "service": text}
        send(chat_id,
             f"عالی! انتخاب کردی: <b>{text}</b>\n\n"
             "لطفاً <b>نام و نام خانوادگی</b> خودت رو بنویس:",
             {"remove_keyboard": True})
        return

    if step == "name":
        user_state[chat_id] = {**state, "step": "phone", "full_name": text}
        send(chat_id, "ممنون! حالا <b>شماره تماس</b>ت رو بنویس:")
        return

    if step == "phone":
        user_state[chat_id] = {**state, "step": "business", "phone": text}
        send(chat_id, "نوع <b>کسب‌وکار</b>ت چیه؟ (مثلاً: رستوران، کلینیک، فروشگاه...)")
        return

    if step == "business":
        user_state[chat_id] = {**state, "step": "desc", "business": text}
        send(chat_id, "اگه توضیح یا درخواست خاصی داری بنویس، وگرنه بنویس <b>ندارم</b>:")
        return

    if step == "desc":
        data = {**state, "desc": text}
        user_state[chat_id] = {}

        # Send to owner
        order_text = (
            f"🔔 <b>سفارش جدید از ربات</b>\n\n"
            f"👤 نام: {data.get('full_name','—')}\n"
            f"📞 تماس: {data.get('phone','—')}\n"
            f"🏢 کسب‌وکار: {data.get('business','—')}\n"
            f"🛠 خدمت: {data.get('service','—')}\n"
            f"📝 توضیحات: {data.get('desc','—')}"
        )
        requests.post(f"{API}/sendMessage", json={
            "chat_id": OWNER_ID,
            "text": order_text,
            "parse_mode": "HTML"
        })

        send(chat_id,
             "✅ <b>سفارش شما ثبت شد!</b>\n\n"
             "به زودی با شما تماس می‌گیریم 🙏\n"
             "میانگین زمان پاسخ: <b>۲ ساعت</b>",
             main_menu())
        return

    # Default
    send(chat_id, "از منو زیر انتخاب کن 👇", main_menu())


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)
        try:
            update = json.loads(body)
            handle(update)
        except Exception as e:
            print("Error:", e)
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Bot running on port {port}")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

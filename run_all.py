import subprocess
import time
import webbrowser
import sys

print("🚀 Starting RecoverAI Multi-Process System...\n")

# 1. Start FastAPI Core Backend
p1 = subprocess.Popen([sys.executable, "main.py"])
print("✅ [1/3] Backend (FastAPI) launched on port 8000")
time.sleep(2)

# 2. Start Admin Dashboard (Port 8501)
p2 = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "dashboard.py", "--server.port", "8501", "--server.headless", "true"])
print("✅ [2/3] Admin Dashboard launched on port 8501")
time.sleep(2)

# 3. Start Customer Chat App (Port 8502)
p3 = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "customer_chat.py", "--server.port", "8502", "--server.headless", "true"])
print("✅ [3/3] Customer Chat App launched on port 8502")
time.sleep(2)

# 4. (Optional) Start Telegram Bot
try:
    p4 = subprocess.Popen([sys.executable, "telegram_agent.py"])
    print("✅ [4/4] Telegram Bot Agent launched")
except Exception:
    pass

# Open both screens automatically in your default browser
print("\n🌐 Opening Admin Dashboard and Customer Chat in browser...")
webbrowser.open("http://localhost:8501") # Left Screen / Tab
time.sleep(1)
webbrowser.open("http://localhost:8502") # Right Screen / Tab

print("\n⚡ All systems live! Press Ctrl+C in this terminal to stop everything at once.\n")

try:
    p1.wait()
except KeyboardInterrupt:
    print("\n🛑 Shutting down all RecoverAI processes...")
    p1.terminate()
    p2.terminate()
    p3.terminate()
    try:
        p4.terminate()
    except Exception:
        pass
    print("👋 All services stopped cleanly.")
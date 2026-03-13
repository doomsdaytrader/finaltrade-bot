import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram.ext import ApplicationBuilder, CommandHandler
from config import BOT_TOKEN
from telegram_commands import start_command, price_command, news_command, survival_command, dashboard_command, lunc_command, ustc_command

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Simple health check server so Render free tier keeps the service alive
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status":"alive","bot":"TheFinalTradeBot"}')
    def log_message(self, format, *args):
        pass  # Suppress logs

def run_health_server():
    server = HTTPServer(('0.0.0.0', 10000), HealthHandler)
    server.serve_forever()

if __name__ == '__main__':
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("Please configure BOT_TOKEN in config.py or environment variables.")
        exit(1)

    # Start health check server in background thread
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    print("Health server running on port 10000")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("survival", survival_command))
    app.add_handler(CommandHandler("dashboard", dashboard_command))
    app.add_handler(CommandHandler("lunc", lunc_command))
    app.add_handler(CommandHandler("ustc", ustc_command))

    print("Bot is up and running. All glory to God!")
    app.run_polling()

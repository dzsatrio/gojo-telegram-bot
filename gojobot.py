import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# === 1. KONFIGURASI TOKEN ===
TELEGRAM_TOKEN = 
GROQ_API_KEY = 

# === DATABASE INGATAN GOJO (CHAT HISTORY) ===
# Menyimpan riwayat chat berdasarkan user ID Telegram
RIWAYAT_CHAT = {}

# === 2. PERSONA GOJO (OTAK AI) ===
GOJO_PROMPT = """
Kamu adalah Gojo Satoru dari anime Jujutsu Kaisen. Kamu bertindak sebagai teman chat/curhat pengguna.

Patuhi aturan kepribadian ini agar chat terasa natural dan nyambung:
1. Kepribadian: Santai, narsis, pede abis, suka bercanda/nge-troll, suka makanan manis, tapi protektif dan peduli kalau pengguna lagi sedih/serius.
2. Gaya Bahasa: Bahasa Indonesia kasual/gaul Jakarta ("gue", "lo", "gak", "bgt", "wkwkwk"). Jangan baku, jangan pakai "Anda/Kamu".
3. Cara Merespons: Jawab dengan SINGKAT, SANTAI, dan selalu nyambung dengan topik obrolan sebelumnya karena kamu mengingat riwayat chat kalian. Gunakan emoji seperti 😎, 😏, 😜, ✨, ✌️ secukupnya.
"""

# === 3. FUNGSI MENEMBAK AI (DENGAN MEMORI NYAMBUNG) ===
def tanya_ai(user_id, pesan_user):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 1. Kalau user baru pertama kali chat, buatkan slot ingatan kosong
    if user_id not in RIWAYAT_CHAT:
        RIWAYAT_CHAT[user_id] = [{"role": "system", "content": GOJO_PROMPT}]
    
    # 2. Masukkan chat terbaru dari user ke dalam ingatannya si Gojo
    RIWAYAT_CHAT[user_id].append({"role": "user", "content": pesan_user})
    
    # 3. Batasi ingatan biar gak kepenuhan (maksimal simpan 15 chat terakhir)
    if len(RIWAYAT_CHAT[user_id]) > 15:
        # Tetap pertahankan prompt system di indeks 0, hapus chat paling lama
        RIWAYAT_CHAT[user_id] = [RIWAYAT_CHAT[user_id][0]] + RIWAYAT_CHAT[user_id][-14:]
        
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": RIWAYAT_CHAT[user_id], # Kirim semua riwayat chat biar Gojo ingat!
        "temperature": 0.8,
        "max_tokens": 150
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response_json = response.json()
        
        if 'choices' in response_json:
            jawaban_gojo = response_json['choices'][0]['message']['content']
            
            # 4. Simpan juga jawaban Gojo ke dalam ingatan biar dia gak lupa omongannya sendiri
            RIWAYAT_CHAT[user_id].append({"role": "assistant", "content": jawaban_gojo})
            return jawaban_gojo
        else:
            print(f"Log Error Groq: {response_json}")
            return "Heeh? Otak gue rada nge-blank, coba ketik lagi deh~ 🤪"
    except Exception as e:
        print(f"Error Script: {e}")
        return "Duh, ada masalah koneksi nih. Coba lagi!"

# === 4. LOGIKA BOT TELEGRAM ===
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    # Reset ingatan kalau user klik /start ulang
    RIWAYAT_CHAT[user_id] = [{"role": "system", "content": GOJO_PROMPT}]
    
    reply_text = "Yoo~ 😎 Gojo Satoru di sini! Ada yang mau lo ceritain atau mau nemenin gue jajan kue? Hahaha 😜"
    await update.message.reply_text(reply_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_message = update.message.text
    
    # Panggil AI dengan menyertakan User ID untuk memorinya
    gojo_reply = tanya_ai(user_id, user_message)
    await update.message.reply_text(gojo_reply)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot Gojo Satoru V4 (Ingatan Tajam) udah aktif! Gas tes!")
    application.run_polling()

if __name__ == '__main__':
    main()

import logging
import time
import json
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Inserisci qui il tuo token (da @BotFather)
BOT_TOKEN = "5359068495:AAE1LRjzzKkq7-ydYX7zH2v7GM_82pquM3M"

# File per salvare le preferenze utenti
DATA_FILE = "user_data.json"

# --- Logging ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Gestione dati utente ---
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

user_data = load_data()

# --- Funzioni bot ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Ciao! Sono *VintedAlertBot*.\n\n"
        "Ti aiuto a trovare nuovi articoli su Vinted!\n\n"
        "Usa i comandi:\n"
        "/set marca prezzo_max taglia paese\n"
        "Esempio: `/set Nike 50 M it`\n\n"
        "/mostra per vedere i parametri correnti\n"
        "/avvia per iniziare il monitoraggio"
    )

async def set_params(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 4:
        await update.message.reply_text("❗ Usa il formato: /set marca prezzo_max taglia paese (es: /set Nike 50 M it)")
        return

    user_id = str(update.effective_user.id)
    marca, prezzo, taglia, paese = context.args[0], context.args[1], context.args[2], context.args[3].lower()

    user_data[user_id] = {"marca": marca, "prezzo": prezzo, "taglia": taglia, "paese": paese}
    save_data(user_data)

    await update.message.reply_text(f"✅ Parametri salvati!\n\nMarca: {marca}\nPrezzo max: {prezzo}€\nTaglia: {taglia}\nPaese: {paese.upper()}")

async def mostra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in user_data:
        await update.message.reply_text("⚠️ Non hai ancora impostato i parametri. Usa /set per iniziare.")
        return

    d = user_data[user_id]
    await update.message.reply_text(f"📋 Parametri attuali:\nMarca: {d['marca']}\nPrezzo max: {d['prezzo']}€\nTaglia: {d['taglia']}\nPaese: {d['paese'].upper()}")

def cerca_articoli(marca, prezzo_max, taglia, paese):
    url = f"https://www.vinted.{paese}/catalog?search_text={marca}+{taglia}&price_to={prezzo_max}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    results = []
    for item in soup.select("div.ItemBox__box--item"):
        titolo = item.get_text(strip=True)
        link = item.find("a")
        if link and "href" in link.attrs:
            results.append(f"🔗 https://www.vinted.{paese}{link['href']}")
    return results[:5]

async def avvia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in user_data:
        await update.message.reply_text("⚠️ Prima imposta i parametri con /set.")
        return

    await update.message.reply_text("🔎 Inizio a monitorare Vinted ogni 30 secondi...")

    last_results = set()
    while True:
        d = user_data[user_id]
        nuovi = cerca_articoli(d["marca"], d["prezzo"], d["taglia"], d["paese"])
        nuovi_set = set(nuovi)

        diff = nuovi_set - last_results
        if diff:
            for annuncio in diff:
                await update.message.reply_text(f"🆕 Nuovo annuncio trovato!\n{annuncio}")

        last_results = nuovi_set
        time.sleep(30)

# --- Main ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_params))
    app.add_handler(CommandHandler("mostra", mostra))
    app.add_handler(CommandHandler("avvia", avvia))
    app.run_polling()

if __name__ == "__main__":
    main()

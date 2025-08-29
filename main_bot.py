# main_bot.py (versione semplificata senza risk_management)
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import analysis
# import risk_management # Temporaneamente rimosso

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("ERRORE CRITICO: La variabile d'ambiente TELEGRAM_TOKEN non è stata impostata!")

CAPITALE_INIZIALE_DEMO = 10000.0

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

bot_state = {"is_running": False, "mode": "DEMO", "balance": CAPITALE_INIZIALE_DEMO, "open_positions": []}

async def market_analysis_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    if not bot_state["is_running"]: return

    logger.info("Esecuzione analisi di mercato periodica...")
    chat_id = context.job.chat_id
    decisione, mot_tech, mot_fond, data = analysis.analyze_market()

    if "ERRORE" in decisione:
        await context.bot.send_message(chat_id, text=f"⚠️ Errore durante l'analisi: {mot_tech}")
        return

    await context.bot.send_message(chat_id, text=f"Analisi completata. Decisione: {decisione}")
    logger.info(f"Decisione attuale: {decisione}. Nessuna nuova posizione aperta.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    bot_state["is_running"] = True
    
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs: job.schedule_removal()

    context.job_queue.run_repeating(market_analysis_job, interval=3600, first=10, name=str(chat_id), chat_id=chat_id)
    
    await update.message.reply_html(f'Ciao {user.mention_html()}!\n\n✅ <b>Bot AVVIATO</b>')

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    bot_state["is_running"] = False
    
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs: job.schedule_removal()
        
    await update.message.reply_text('🛑 <b>Bot FERMATO</b>')

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.run_polling()

if __name__ == '__main__':
    main()
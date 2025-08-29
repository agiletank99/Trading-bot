# main_bot.py (versione aggiornata per python-telegram-bot v20+)
import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import analysis
import risk_management

# Leggi le variabili d'ambiente
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("ERRORE CRITICO: La variabile d'ambiente TELEGRAM_TOKEN non è stata impostata!")

# Parametri di trading
CAPITALE_INIZIALE_DEMO = 10000.0
RR_RATIO = 2.0

# Configura il logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Stato del Bot
bot_state = {
    "is_running": False,
    "mode": "DEMO",
    "balance": CAPITALE_INIZIALE_DEMO,
    "open_positions": [],
}

async def market_analysis_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    if not bot_state["is_running"]:
        return

    logger.info("Esecuzione analisi di mercato periodica...")
    chat_id = context.job.chat_id
    decisione, mot_tech, mot_fond, data = analysis.analyze_market()

    if "ERRORE" in decisione:
        await context.bot.send_message(chat_id, text=f"⚠️ Errore durante l'analisi: {mot_tech}")
        return

    if decisione in ["APRI LONG", "APRI SHORT"] and not bot_state["open_positions"]:
        direction = "LONG" if "LONG" in decisione else "SHORT"
        
        last_price = data['D1'].iloc[-1]['Close']
        atr = data['D1'].iloc[-1]['ATRr_14']
        
        sl, tp = risk_management.calculate_sl_tp(last_price, direction, atr, RR_RATIO)
        
        position = {"direction": direction, "entry_price": last_price, "stop_loss": sl, "take_profit": tp}
        bot_state["open_positions"].append(position)
        
        signal_msg = f"""
{'🟢' if direction == 'LONG' else '🔴'} *NUOVO SEGNALE XAU/USD* {'🟢' if direction == 'LONG' else '🔴'}
--------------------
*TIPO:* {direction}
*MODALITÀ:* {bot_state['mode']}

*Entry Price:* ${last_price:,.2f}
*Stop Loss:* ${sl:,.2f}
*Take Profit:* ${tp:,.2f}

*Motivazione Tecnica:* {mot_tech}
*Motivazione Fondamentale:* {mot_fond}

*Stato:* APERTA
        """
        await context.bot.send_message(chat_id, text=signal_msg, parse_mode='Markdown')
    else:
        logger.info(f"Decisione attuale: {decisione}. Nessuna nuova posizione aperta.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    bot_state["is_running"] = True
    
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    context.job_queue.run_repeating(market_analysis_job, interval=3600, first=10, name=str(chat_id), chat_id=chat_id)
    
    await update.message.reply_html(
        rf'Ciao {user.mention_html()}!'
        '\n\n✅ <b>AI Trading Bot AVVIATO</b>'
        '\nCiclo di analisi oraria attivato. Modalità: <b>DEMO</b>.'
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    bot_state["is_running"] = False
    
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()
        
    await update.message.reply_text('🛑 <b>AI Trading Bot FERMATO</b>\nCiclo di analisi disattivato.', parse_mode='HTML')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pos_text = "Nessuna"
    if bot_state["open_positions"]:
        pos = bot_state["open_positions"][0]
        pos_text = f"- {pos['direction']} XAU/USD @ {pos['entry_price']}"

    status_msg = f"""
*STATO SISTEMA*
--------------------
*Stato:* {'ATTIVO' if bot_state['is_running'] else 'FERMO'}
*Modalità:* {bot_state["mode"]}
*Bilancio:* ${bot_state["balance"]:,.2f}
*Posizioni Aperte:* {pos_text}
    """
    await update.message.reply_text(status_msg, parse_mode='Markdown')

def main() -> None:
    """Avvia il bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("status", status))

    application.run_polling()

if __name__ == '__main__':
    main()
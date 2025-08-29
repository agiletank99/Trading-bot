# analysis.py (versione autonoma senza pandas-ta)
import os
import yfinance as yf
import requests
import pandas as pd
import numpy as np

NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

# --- INIZIO NUOVE FUNZIONI PER INDICATORI ---

def calculate_ema(data, length):
    return data['Close'].ewm(span=length, adjust=False).mean()

def calculate_rsi(data, length=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(data, fast=12, slow=26, signal=9):
    ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line

# --- FINE NUOVE FUNZIONI PER INDICATORI ---

def get_market_data(ticker="GC=F"):
    """Recupera e prepara i dati di mercato per XAU/USD in modo robusto."""
    try:
        data_d1 = yf.download(ticker, period="1y", interval="1d", progress=False)
        data_h4 = yf.download(ticker, period="60d", interval="1h", progress=False)

        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in data_d1.columns for col in required_columns) or data_d1.empty:
            return None
        if not all(col in data_h4.columns for col in required_columns) or data_h4.empty:
            return None

        data = {}
        data['D1'] = data_d1
        data['H4'] = data_h4.resample('4h').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
        }).dropna()

        for df in data.values():
            # Calcoliamo gli indicatori manualmente
            df['EMA_50'] = calculate_ema(df, 50)
            df['EMA_200'] = calculate_ema(df, 200)
            df['RSI_14'] = calculate_rsi(df, 14)
            df['MACD_line'], df['MACD_signal'] = calculate_macd(df)
        
        return data
    except Exception as e:
        print(f"Errore critico durante il recupero o l'elaborazione dei dati di mercato: {e}")
        return None

def analyze_market():
    """Funzione principale che orchestra l'analisi e genera una decisione."""
    data = get_market_data()
    if not data or data['D1'].empty:
        return "ERRORE", "Dati di mercato non disponibili.", "", None

    d1 = data['D1'].iloc[-1]
    h4 = data['H4'].iloc[-1]
    
    score = 0
    motivazioni_tecniche = []

    if d1['Close'] > d1['EMA_50'] and d1['EMA_50'] > d1['EMA_200']:
        score += 2; motivazioni_tecniche.append("Trend rialzista D1.")
    elif d1['Close'] < d1['EMA_50'] and d1['EMA_50'] < d1['EMA_200']:
        score -= 2; motivazioni_tecniche.append("Trend ribassista D1.")

    if d1['RSI_14'] > 70:
        score -= 1; motivazioni_tecniche.append("RSI D1 ipercomprato.")
    if d1['RSI_14'] < 30:
        score += 1; motivazioni_tecniche.append("RSI D1 ipervenduto.")
        
    if h4['MACD_line'] > h4['MACD_signal']:
        score += 1; motivazioni_tecniche.append("MACD H4 positivo.")
    else:
        score -= 1; motivazioni_tecniche.append("MACD H4 negativo.")

    # Semplifichiamo temporaneamente senza news per isolare il problema
    motivazione_fondamentale = "Analisi fondamentale non attiva."
    
    decisione = "MANTIENI"
    if score >= 3:
        decisione = "APRI LONG"
    elif score <= -2:
        decisione = "APRI SHORT"
        
    # Il file risk_management non è usato in questa versione semplificata
    # e le funzioni di news sono state rimosse per stabilità
    return decisione, " ".join(motivazioni_tecniche), motivazione_fondamentale, data
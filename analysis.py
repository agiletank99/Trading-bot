# analysis.py (versione corretta e robusta)
import os
import yfinance as yf
import pandas_ta as ta
import requests
import pandas as pd

NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

def get_market_data(ticker="GC=F"):
    """Recupera e prepara i dati di mercato per XAU/USD in modo robusto."""
    try:
        data_d1 = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=False)
        data_h4 = yf.download(ticker, period="60d", interval="1h", progress=False, auto_adjust=False)

        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in data_d1.columns for col in required_columns) or data_d1.empty:
            print("Dati D1 non validi o incompleti da yfinance.")
            return None
        if not all(col in data_h4.columns for col in required_columns) or data_h4.empty:
            print("Dati H4 non validi o incompleti da yfinance.")
            return None

        data = {}
        data['D1'] = data_d1
        data['H4'] = data_h4.resample('4h').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
        }).dropna()
        data['H1'] = data_h4.copy()

        for df in data.values():
            df.ta.ema(length=20, append=True)
            df.ta.ema(length=50, append=True)
            df.ta.ema(length=200, append=True)
            df.ta.rsi(append=True)
            df.ta.macd(append=True)
            df.ta.atr(append=True)
            df.ta.bbands(append=True)

        return data
    except Exception as e:
        print(f"Errore critico durante il recupero o l'elaborazione dei dati di mercato: {e}")
        return None

def get_news_sentiment():
    """Recupera le notizie e restituisce un semplice sentiment."""
    if not NEWS_API_KEY or NEWS_API_KEY == "LA_TUA_CHIAVE_API_PER_LE_NEWS":
        return "NEUTRAL (News API non configurata)"
        
    try:
        query = "gold price OR federal reserve OR inflation OR geopolitical tension"
        url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        articles = response.json().get('articles', [])
        
        sentiment_score = 0
        keywords_bullish = ['rise', 'strong', 'safe-haven', 'cuts rates']
        keywords_bearish = ['fall', 'weak', 'pressure', 'hikes rates']
        
        for article in articles[:10]:
            title = article.get('title', '').lower()
            if any(keyword in title for keyword in keywords_bullish):
                sentiment_score += 1
            if any(keyword in title for keyword in keywords_bearish):
                sentiment_score -= 1
        
        if sentiment_score > 1: return "BULLISH"
        if sentiment_score < -1: return "BEARISH"
        return "NEUTRAL"
    except Exception as e:
        print(f"Errore nel recuperare le notizie: {e}")
        return "NEUTRAL"

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
        score += 2
        motivazioni_tecniche.append("Trend rialzista D1 (Prezzo > EMA50 > EMA200).")
    elif d1['Close'] < d1['EMA_50'] and d1['EMA_50'] < d1['EMA_200']:
        score -= 2
        motivazioni_tecniche.append("Trend ribassista D1 (Prezzo < EMA50 < EMA200).")

    if d1['RSI_14'] > 70:
        score -= 1; motivazioni_tecniche.append("RSI D1 in ipercomprato (>70).")
    if d1['RSI_14'] < 30:
        score += 1; motivazioni_tecniche.append("RSI D1 in ipervenduto (<30).")
        
    if h4['MACD_12_26_9'] > h4['MACDs_12_26_9']:
        score += 1; motivazioni_tecniche.append("MACD H4 positivo.")
    else:
        score -= 1; motivazioni_tecniche.append("MACD H4 negativo.")

    if h4['Close'] > h4['BBU_20_2.0']:
        score -= 1; motivazioni_tecniche.append("Prezzo H4 sopra Banda di Bollinger.")
    if h4['Close'] < h4['BBL_20_2.0']:
        score += 1; motivazioni_tecniche.append("Prezzo H4 sotto Banda di Bollinger.")

    sentiment = get_news_sentiment()
    motivazione_fondamentale = f"Sentiment notizie: {sentiment}."
    if sentiment == "BULLISH":
        score += 1
    elif sentiment == "BEARISH":
        score -= 1
    
    decisione = "MANTIENI"
    if score >= 3:
        decisione = "APRI LONG"
    elif score <= -3:
        decisione = "APRI SHORT"
        
    return decisione, " ".join(motivazioni_tecniche), motivazione_fondamentale, data
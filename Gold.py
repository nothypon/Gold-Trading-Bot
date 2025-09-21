import yfinance as yf
import pandas as pd
import numpy as np
import requests
import json
import os
import math

# Telegram Bot Token from environment
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Forex Pairs to Monitor
FOREX_PAIRS = ["GCU25.CMX"]

# Mapping of symbols to real names
PAIR_NAMES = {
    "GCU25.CMX": "#XAUUSD" 
}

# Function to Fetch Forex Data from Yahoo Finance
def fetch_forex_data(symbol):
    forex_data = yf.download(symbol, period='1d', interval='15m', auto_adjust=False)

    if isinstance(forex_data.columns, pd.MultiIndex):
        forex_data = forex_data.loc[:, pd.IndexSlice[:, symbol]]
        forex_data.columns = forex_data.columns.droplevel(1)
    else:
        forex_data = forex_data[['Open', 'High', 'Low', 'Close']]
    return forex_data

# Function to Calculate Fibonacci Levels
def calculate_fibonacci_levels(data):
    highest_high = data['High'].max()
    lowest_low = data['Low'].min()

    levels = {
        "0.0": round(highest_high, 4),
        "0.25": round(lowest_low + 0.25 * (highest_high - lowest_low), 4),
        "0.5": round(lowest_low + 0.5 * (highest_high - lowest_low), 4),
        "0.75": round(lowest_low + 0.75 * (highest_high - lowest_low), 4),
        "1.0": round(lowest_low, 4)
    }

    return levels

# Function to Identify Trend & Breakouts
def identify_trend(data):
    data = data.copy()
    data['EMA_20'] = data['Close'].rolling(window=20).mean()

    if data['EMA_20'].isna().all():
        return None

    breakout = data['Close'].iloc[-1] > data['EMA_20'].iloc[-1]
    return breakout

# Updated Function to Send Telegram Alerts to fixed user and channel
def send_telegram_message(message):
    recipients = ["1080336066","-1002619198712"]
    for chat_id in recipients:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload)

# Main Function to Run Forex Strategy
def run_forex_strategy():
    for pair in FOREX_PAIRS:
        try:
            print(f"\nProcessing {pair}...")
            data = fetch_forex_data(pair)
            if data.empty:
                print(f"[❌] No data found for {pair}. Skipping...")
                continue

            breakout = identify_trend(data)
            fib_levels = calculate_fibonacci_levels(data)
            current_price = data['Close'].iloc[-1]
            near_25_percent = abs(current_price - fib_levels["0.25"]) / fib_levels["0.25"] < 0.01
            near_75_percent = abs(current_price - fib_levels["0.75"]) / fib_levels["0.75"] < 0.01

            print(f"[🔍] Last Price: {current_price:.4f}")
            print(f"[📈] Breakout: {breakout}")
            print(f"[🔢] Fibonacci Levels: {fib_levels}")
            print(f"[🧐] Near 25% Retracement: {near_25_percent}")
            print(f"[🧐] Near 75% Retracement: {near_75_percent}")

            friendly_name = PAIR_NAMES.get(pair, pair)

            # Buy Setup
            if breakout and near_25_percent:
                entry_price = fib_levels["0.25"]
                sl_price = fib_levels["1.0"] 
                tp_price = entry_price + (2 * (entry_price - sl_price))
                buyrisk= entry_price - sl_price
                buyreward=tp_price - entry_price
                
                message = (
			f"*{friendly_name} : Buy Limit/Stop*"
			f"\n\n*Entry:* `{entry_price:.2f}`"
			f"\n\n*SL:* `{sl_price:.2f}`"
			f"\n\n*TP:* `{tp_price:.2f}` \n"
			f"```\n 0.01 lots, ${buyrisk:.2f} ~ ${buyreward:.2f}```"
			)
                          
                send_telegram_message(message)
                print(f"[✅] Buy Alert Sent for {pair}!")

            # Sell Setup
            elif not breakout and near_75_percent:
                entry_price = fib_levels["0.75"]
                sl_price = fib_levels["0.0"] 
                tp_price = entry_price - (2 * (sl_price - entry_price))
                sellrisk= sl_price - entry_price
                sellreward= entry_price - tp_price

                message = message =( f"*{friendly_name} : Sell Limit/Stop*"
                          f"\n\n*Entry:* `{entry_price:.2f}`"
                          f"\n\n*SL:* `{sl_price:.2f}`"
                          f"\n\n*TP:* `{tp_price:.2f}`\n"
                          f"```\n 0.01 lots: ${sellrisk:.2f} ~ ${sellreward:.2f}```"
				   )
				
                send_telegram_message(message)
                print(f"[✅] Sell Alert Sent for {pair}!")
                print(f"Latest timestamp in data: {data.index[-1]}")

        except Exception as e:
            print(f"[❌] Error processing {pair}: {str(e)}")

# Run the Strategy
run_forex_strategy()
	    

# risk_management.py
import pandas_ta as ta

def calculate_sl_tp(entry_price, direction, atr, rr_ratio):
    """Calcola Stop Loss e Take Profit basandosi sull'ATR."""
    if direction.upper() == 'LONG':
        stop_loss = entry_price - (1.5 * atr)
        take_profit = entry_price + ((entry_price - stop_loss) * rr_ratio)
    elif direction.upper() == 'SHORT':
        stop_loss = entry_price + (1.5 * atr)
        take_profit = entry_price - ((stop_loss - entry_price) * rr_ratio)
    else:
        return None, None
        
    return round(stop_loss, 2), round(take_profit, 2)

def calculate_position_size(balance, risk_percent, entry_price, stop_loss_price):
    """Calcola la dimensione della posizione in base al rischio."""
    capital_at_risk = balance * (risk_percent / 100)
    risk_per_unit = abs(entry_price - stop_loss_price)
    
    if risk_per_unit == 0:
        return 0
        
    position_size = capital_at_risk / risk_per_unit
    return round(position_size, 4)
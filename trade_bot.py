from telethon import TelegramClient, events
import MetaTrader5 as mt5
import re
import time
import datetime
from datetime import datetime
import numpy as np
import asyncio

# Telegram API credentials
API_ID = 
API_HASH = 
PHONE_NUMBER = 
CHANNEL_1 =
CHANNEL_2 = 



# MT5 Account Credentials
MT5_LOGIN =
MT5_PASSWORD = 
MT5_SERVER = 

client = TelegramClient('session_name', API_ID, API_HASH)

# Initialize and check MT5 connection
def mt5_login():
    if not mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
        print("⚠️ MT5 Initialization failed. Check credentials and try again.")
        return False

    account_info = mt5.account_info()
    if account_info is None:
        print("⚠️ MT5 is initialized, but no account is connected. Check MT5 terminal.")
        return False

    print(f"✅ MT5 is connected. Trading on Account: {account_info.login}, Server: {account_info.server}")
    return True


# Parse trading signals from Telegram messages
def parse_signal1(message):
    message = re.sub(r"\s+", " ", message).lower()

    action_match = re.search(r"\b(buy|sell)\s+(\w+)", message)
    if not action_match:
        return None

    action = action_match.group(1).upper()
    symbol = action_match.group(2).capitalize()

    entry_match = re.search(r"@(\d+(\.\d+)?)-(\d+(\.\d+)?)", message)
    if entry_match:
        lower_limit = round(float(entry_match.group(1)), 1)
        upper_limit = round(float(entry_match.group(3)), 1)
    else:
        return None

    sl_match = re.search(r"sl\s*[:\-]?\s*(\d+(\.\d+)?)", message)
    stop_loss = round(float(sl_match.group(1)), 1) if sl_match else None

    tp1_match = re.search(r"tp1\s*[:\-]?\s*(\d+(\.\d+)?)", message, re.IGNORECASE)
    tp2_match = re.search(r"tp2\s*[:\-]?\s*(\d+(\.\d+)?)", message, re.IGNORECASE)

    take_profit_1 = round(float(tp1_match.group(1)), 1) if tp1_match else None
    take_profit_2 = round(float(tp2_match.group(1)), 1) if tp2_match else None

    

    return action, symbol, lower_limit, upper_limit, stop_loss, take_profit_1, take_profit_2


# Cancel all pending orders for a symbol
def cancel_pending_orders1(symbol):
    pending_orders = mt5.orders_get(symbol=symbol)

    if pending_orders is None or len(pending_orders) == 0:
        print(f"⚠️ No pending orders to cancel for {symbol}.")
        return

    for order in pending_orders:
        cancel_request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": order.ticket
        }
        result = mt5.order_send(cancel_request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"✅ Canceled pending order {order.ticket} for {symbol}.")
        else:
            print(f"⚠️ Failed to cancel order {order.ticket}: {result.comment}")


# Place multiple orders in MT5 with varying entry prices and take profits
def place_trade1(action, symbol, lower_price, upper_price, stop_loss, take_profit_1, take_profit_2):
    if not mt5_login():
        return
    
    lot_size = 0.02  # Each trade is 0.02 lots
    tick = mt5.symbol_info_tick(symbol)

    if tick is None:
        print(f"⚠️ Unable to fetch market price for {symbol}. Skipping trade.")
        return

    market_price = tick.ask if action == "BUY" else tick.bid  # Use ask price for buy, bid price for sell
    execution_threshold = 0.03  # 0.3 pips in XAUUSD (0.03 in price)

    if action =="BUY" and (market_price <= lower_price or abs(market_price - entry_price) <= execution_threshold):
        market_exec= '1'
    elif action =="SELL" and (market_price >= lower_price or abs(market_price - entry_price) <= execution_threshold):
        market_exec= '1'
    else:
        market_exec = '0'
        
    entry_prices = np.round(np.linspace(lower_price, upper_price, 7)[1:-1], 1)
    take_profits = np.round(np.linspace(take_profit_1, take_profit_2, 7)[1:-1], 1)

    orders = [
        {"price": lower_price, "tp": take_profit_1, "comment": "Telegram Signal TP1"},
        {"price": lower_price, "tp": take_profit_2, "comment": "Telegram Signal TP2"},
        {"price": lower_price, "tp": round((take_profit_1 + take_profit_2) / 2, 1), "comment": "Telegram Signal Mid TP"},
    ]
    
    for i in range(4, 9):
        orders.append({
            "price": entry_prices[i - 4],
            "tp": take_profits[i - 4],
            "comment": f"Telegram Signal TP Step {i}"
        })

    for i, order in enumerate(orders):
        entry_price = order["price"]
        if market_exec == '1' and i<3:
            order_type = mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL
            execution_type = "Market Execution"
        else:
            order_type = mt5.ORDER_TYPE_BUY_LIMIT if action == "BUY" else mt5.ORDER_TYPE_SELL_LIMIT
            execution_type = "Pending Order"

        request = {
            "action": mt5.TRADE_ACTION_DEAL if execution_type == "Market Execution" else mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type,
            "price": market_price if execution_type == "Market Execution" else entry_price,
            "sl": stop_loss,
            "tp": order["tp"],
            "deviation": 20,
            "magic": 123456 + i,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        print(request)
        # Send order and handle response
        result = mt5.order_send(request)

        if result is None:
            print(f"❌ Order {i+1} failed: MT5 returned None. Last error: {mt5.last_error()}")
        elif result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"⚠️ Order {i+1} failed: {result.comment} (Retcode: {result.retcode})")
        else:
            print(f"✅ Order {i+1} placed: {action} {symbol} @ {request['price']}, SL: {stop_loss}, TP: {order['tp']} ({execution_type})")


    # Start monitoring price conditions
    monitor_price_and_cancel1(symbol, action, lower_price, take_profit_1)


# Monitor price movement and perform actions based on conditions
async def monitor_price_and_cancel1(symbol, action, lower_limit, take_profit_1):
    # Get pending orders and open trades
    pending_orders = mt5.orders_get(symbol=symbol)
    open_positions = mt5.positions_get(symbol=symbol)

    has_pending_orders = pending_orders and len(pending_orders) > 0
    has_open_trades = open_positions and len(open_positions) > 0

    # Condition 1: If no pending orders and no open trades, skip monitoring
    if not has_pending_orders and not has_open_trades:
        print(f"⚠️ No pending orders or open trades for {symbol}. Skipping price monitoring.")
        return

    # Condition 2: If only pending orders exist, monitor price to cancel at 50% to TP1
    if has_pending_orders and not has_open_trades:
        print(f"⏳ Monitoring {symbol}: Pending orders detected, watching for cancellation trigger.")

    # Condition 3: If only open trades exist, monitor price to move SL to breakeven
    if not has_pending_orders and has_open_trades:
        print(f"⏳ Monitoring {symbol}: Open trades detected, watching for breakeven trigger.")

    # Condition 4: If both pending orders and open trades exist, monitor both conditions
    if has_pending_orders and has_open_trades:
        print(f"⏳ Monitoring {symbol}: Both pending orders and open trades detected, watching for cancellation and breakeven triggers.")

    # Define price triggers based on action (BUY/SELL)
    if action == "BUY":
        cancel_trigger = round(lower_limit + ((take_profit_1 - lower_limit) * 0.5), 1)  # 50% to TP1 for cancel
        move_be_trigger = round(take_profit_1 * 1.3, 1)  # TP1 * 1.3 for breakeven
    else:  # SELL
        cancel_trigger = round(lower_limit - ((lower_limit - take_profit_1) * 0.5), 1)  # 50% to TP1 for cancel
        move_be_trigger = round(take_profit_1 - (1.3 * take_profit_1), 1)  # TP1 - (1.3 * TP1) for breakeven

    print(f"📌 {symbol} Cancel Pending Orders at {cancel_trigger} | Move SL to BE at {move_be_trigger}")

    while True:
        time.sleep(3)  # Check price every 5 seconds
        tick = mt5.symbol_info_tick(symbol)

        if tick is None:
            print(f"⚠️ Unable to fetch price data for {symbol}.")
            continue

        current_price = round(tick.bid if tick.bid else tick.ask, 1)

        # If pending orders exist, cancel them when price reaches 50% to TP1
        if has_pending_orders and ((action == "BUY" and current_price >= cancel_trigger) or (action == "SELL" and current_price <= cancel_trigger)):
            print(f"🚨 {symbol} Price reached 50% to TP1 ({cancel_trigger}). Canceling pending orders.")
            cancel_pending_orders1(symbol)
            has_pending_orders = False  # Update status since orders are canceled

        # If open trades exist, move SL to breakeven when price reaches TP1 * 1.3
        if has_open_trades and ((action == "BUY" and current_price >= move_be_trigger) or (action == "SELL" and current_price <= move_be_trigger)):
            print(f"🚨 {symbol} Price reached {move_be_trigger}. Moving SL to breakeven.")
            move_breakeven1()
            return  # Stop monitoring once SL is moved

        # Stop monitoring if both conditions are met
        if not has_pending_orders and not has_open_trades:
            print(f"✅ Monitoring complete for {symbol}. No more actions required.")
            return
 

# Move SL to breakeven (each order's entry price)
def move_breakeven1():
    print(f"🔄 Moving SL to breakeven for all open trades...")

    open_positions = mt5.positions_get()

    if open_positions is None or len(open_positions) == 0:
        print("⚠️ No open trades found to modify.")
        return

    for pos in open_positions:
        be_price = round(pos.price_open, 1)
        modify_request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": pos.ticket,
            "sl": be_price,
            "tp": pos.tp,
        }

        result = mt5.order_send(modify_request)

        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"✅ SL moved to breakeven for trade {pos.ticket} ({pos.symbol}). New SL: {be_price}")
        else:
            print(f"⚠️ Failed to modify SL for trade {pos.ticket}: {result.comment}")


# Handle new Telegram messages
#@client.on(events.NewMessage(chats=CHANNEL_USERNAME))
#async def new_message_handler(event):
def trade_bot1(message):

    signal = parse_signal1(message)
    print(signal)
    if signal:
        action, symbol, lower_limit, upper_limit, stop_loss, take_profit_1, take_profit_2 = signal
        symbol = 'XAUUSDk'
        print(f"✅ Parsed Signal: {action} {symbol} (Lower: {lower_limit}, Upper: {upper_limit}), SL: {stop_loss}, TP1: {take_profit_1}, TP2: {take_profit_2}")

        cancel_pending_orders1(symbol)  # Cancel old pending orders before placing new ones

        if take_profit_1 and take_profit_2:
            print(f"📢 Placing test trade in MT5 for {symbol}...")
            place_trade1(action, symbol, lower_limit, upper_limit, stop_loss, take_profit_1, take_profit_2)
        else:
            print(f"⚠️ Skipping trade for {symbol}: Missing TP1 or TP2.")

"""------------------------ CODE FOR TFXC PREMIUM --------------------------------------------------------------"""

# Parse trading signals from Telegram messages
def parse_signal(message):
    # Normalize spacing
    message = re.sub(r"\s+", " ", message).strip()
    
    # Ensure message contains "SIGNAL ALERT"
    if not re.search(r"\bSIGNAL ALERT\b", message, re.IGNORECASE):
        return None
    
    # Extract action, symbol, and entry price
    action_match = re.search(r"\b(BUY|SELL)\s+([A-Z]+)\s+(\d+(\.\d+)?)", message, re.IGNORECASE)
    if not action_match:
        return None

    action = action_match.group(1).upper()  # BUY or SELL
    symbol = action_match.group(2).upper()  # Symbol (e.g., XAUUSD)
    entry_price = float(action_match.group(3))  # Entry price (e.g., 2916.6)

    # Extract Stop Loss (SL) (🔴SL with or without a colon)
    sl_match = re.search(r"SL\s*:?[\s]*([\d.]+)", message, re.IGNORECASE)
    stop_loss = float(sl_match.group(1)) if sl_match else None

    # Extract Take Profit (TP) levels (🤑TP1, TP2, TP3 with or without a colon)
    tp_matches = re.findall(r"TP\d+\s*:?[\s]*([\d.]+)", message, re.IGNORECASE)
    take_profits = [float(tp) for tp in tp_matches]  # Convert to float

    # Assign TP values dynamically
    take_profit_1 = take_profits[0] if len(take_profits) > 0 else None
    take_profit_2 = take_profits[1] if len(take_profits) > 1 else None
    take_profit_3 = take_profits[2] if len(take_profits) > 2 else None

    

    return action, symbol, entry_price, stop_loss, take_profit_1, take_profit_2, take_profit_3


# Cancel all pending orders for a symbol
def cancel_pending_orders(symbol):
    pending_orders = mt5.orders_get(symbol=symbol)

    if pending_orders is None or len(pending_orders) == 0:
        print(f"⚠️ No pending orders to cancel for {symbol}.")
        return

    for order in pending_orders:
        cancel_request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": order.ticket
        }
        result = mt5.order_send(cancel_request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"✅ Canceled pending order {order.ticket} for {symbol}.")
        else:
            print(f"⚠️ Failed to cancel order {order.ticket}: {result.comment}")


# Place multiple orders in MT5 with varying entry prices and take profits
def place_trade(action, symbol, lower_price, stop_loss, take_profit_1, take_profit_2, take_profit_3):
    if not mt5_login():
        return
    lot_size = 0.01  # Each trade is 0.02 lots
    tick = mt5.symbol_info_tick(symbol)

    if tick is None:
        print(f"⚠️ Unable to fetch market price for {symbol}. Skipping trade.")
        return

    upper_price = lower_price - limit_threshold if action == "BUY" else lower_price + limit_threshold
    
    market_price = tick.ask if action == "BUY" else tick.bid  # Use ask price for buy, bid price for sell
    execution_threshold = 0.03  # 0.3 pips in XAUUSD (0.03 in price)
    limit_threshold =2  if symbol == 'XAUUSD.a' else 0.0003*lower_price
    entry_prices = np.round(np.linspace(lower_price, upper_price, 7)[1:-1], 1)
    take_profits = np.round(np.linspace(take_profit_1, take_profit_3, 7)[1:-1], 1)

    orders = [
        {"price": lower_price, "tp": take_profit_1, "comment": "Telegram Signal TP1"},
        {"price": lower_price, "tp": take_profit_2, "comment": "Telegram Signal TP2"},
        {"price": lower_price, "tp":take_profit_3, "comment": "Telegram Signal TP3"},
    ]
    
    for i in range(4, 9):
        orders.append({
            "price": entry_prices[i - 4],
            "tp": take_profits[i - 4],
            "comment": f"Telegram Signal TP Step {i}"
        })

    for i, order in enumerate(orders):
        entry_price = order["price"]
        if abs(market_price - entry_price) <= execution_threshold:
            order_type = mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL
            execution_type = "Market Execution"
        else:
            order_type = mt5.ORDER_TYPE_BUY_LIMIT if action == "BUY" else mt5.ORDER_TYPE_SELL_LIMIT
            execution_type = "Pending Order"

        request = {
            "action": mt5.TRADE_ACTION_DEAL if execution_type == "Market Execution" else mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type,
            "price": market_price if execution_type == "Market Execution" else entry_price,
            "sl": stop_loss,
            "tp": order["tp"],
            "deviation": 20,
            "magic": 123456 + i,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Send order and handle response
        result = mt5.order_send(request)

        if result is None:
            print(f"❌ Order {i+1} failed: MT5 returned None. Last error: {mt5.last_error()}")
        elif result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"⚠️ Order {i+1} failed: {result.comment} (Retcode: {result.retcode})")
        else:
            print(f"✅ Order {i+1} placed: {action} {symbol} @ {request['price']}, SL: {stop_loss}, TP: {order['tp']} ({execution_type})")


    # Start monitoring price conditions
    monitor_price_and_cancel(symbol, action, lower_price, take_profit_1)


# Monitor price movement and perform actions based on conditions
def monitor_price_and_cancel(symbol, action, lower_limit, take_profit_1):
    # Get pending orders and open trades
    pending_orders = mt5.orders_get(symbol=symbol)
    open_positions = mt5.positions_get(symbol=symbol)

    has_pending_orders = pending_orders and len(pending_orders) > 0
    has_open_trades = open_positions and len(open_positions) > 0

    # Condition 1: If no pending orders and no open trades, skip monitoring
    if not has_pending_orders and not has_open_trades:
        print(f"⚠️ No pending orders or open trades for {symbol}. Skipping price monitoring.")
        return

    # Condition 2: If only pending orders exist, monitor price to cancel at 50% to TP1
    if has_pending_orders and not has_open_trades:
        print(f"⏳ Monitoring {symbol}: Pending orders detected, watching for cancellation trigger.")

    # Condition 3: If only open trades exist, monitor price to move SL to breakeven
    if not has_pending_orders and has_open_trades:
        print(f"⏳ Monitoring {symbol}: Open trades detected, watching for breakeven trigger.")

    # Condition 4: If both pending orders and open trades exist, monitor both conditions
    if has_pending_orders and has_open_trades:
        print(f"⏳ Monitoring {symbol}: Both pending orders and open trades detected, watching for cancellation and breakeven triggers.")

    # Define price triggers based on action (BUY/SELL)
    if action == "BUY":
        cancel_trigger = round(lower_limit + ((take_profit_1 - lower_limit) * 0.5), 1)  # 50% to TP1 for cancel
        move_be_trigger = round(take_profit_1 * 1.3, 1)  # TP1 * 1.3 for breakeven
    else:  # SELL
        cancel_trigger = round(lower_limit - ((lower_limit - take_profit_1) * 0.5), 1)  # 50% to TP1 for cancel
        move_be_trigger = round(take_profit_1 - (1.3 * take_profit_1), 1)  # TP1 - (1.3 * TP1) for breakeven

    print(f"📌 {symbol} Cancel Pending Orders at {cancel_trigger} | Move SL to BE at {move_be_trigger}")

    while True:
        time.sleep(3)  # Check price every 5 seconds
        tick = mt5.symbol_info_tick(symbol)

        if tick is None:
            print(f"⚠️ Unable to fetch price data for {symbol}.")
            continue

        current_price = round(tick.bid if tick.bid else tick.ask, 1)

        # If pending orders exist, cancel them when price reaches 50% to TP1
        if has_pending_orders and ((action == "BUY" and current_price >= cancel_trigger) or (action == "SELL" and current_price <= cancel_trigger)):
            print(f"🚨 {symbol} Price reached 50% to TP1 ({cancel_trigger}). Canceling pending orders.")
            cancel_pending_orders(symbol)
            has_pending_orders = False  # Update status since orders are canceled

        # If open trades exist, move SL to breakeven when price reaches TP1 * 1.3
        if has_open_trades and ((action == "BUY" and current_price >= move_be_trigger) or (action == "SELL" and current_price <= move_be_trigger)):
            print(f"🚨 {symbol} Price reached {move_be_trigger}. Moving SL to breakeven.")
            move_breakeven()
            return  # Stop monitoring once SL is moved

        # Stop monitoring if both conditions are met
        if not has_pending_orders and not has_open_trades:
            print(f"✅ Monitoring complete for {symbol}. No more actions required.")
            return
 

# Move SL to breakeven (each order's entry price)
def move_breakeven():
    print(f"🔄 Moving SL to breakeven for all open trades...")

    open_positions = mt5.positions_get()

    if open_positions is None or len(open_positions) == 0:
        print("⚠️ No open trades found to modify.")
        return

    for pos in open_positions:
        be_price = round(pos.price_open, 1)
        modify_request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": pos.ticket,
            "sl": be_price,
            "tp": pos.tp,
        }

        result = mt5.order_send(modify_request)

        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"✅ SL moved to breakeven for trade {pos.ticket} ({pos.symbol}). New SL: {be_price}")
        else:
            print(f"⚠️ Failed to modify SL for trade {pos.ticket}: {result.comment}")

def trade_bot2(message):
    signal = parse_signal(message)
    if signal:
        action, symbol0, entry_price, stop_loss, take_profit_1, take_profit_2, take_profit_3 = signal
        symbol = symbol0.upper()+ "k"
        print(f"✅ Parsed Signal: {action} {symbol} entry {entry_price}), SL: {stop_loss}, TP1: {take_profit_1}, TP2: {take_profit_2}, TP3: {take_profit_3}")

        #cancel_pending_orders(symbol)  # Cancel old pending orders before placing new ones

        if take_profit_1:
            print(f"📢 Placing test trade in MT5 for {symbol}...")
            place_trade(action, symbol, entry_price, stop_loss, take_profit_1, take_profit_2, take_profit_3)
        else:
            print(f"⚠️ Skipping trade for {symbol}: Missing TP1.")


    
    

@client.on(events.NewMessage(chats=[CHANNEL_1, CHANNEL_2]))
async def new_message_handler(event):
    message = event.raw_text
    chat_id = event.chat_id  
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] Received message: {message}")

    if chat_id == CHANNEL_1:
        print("📩 Signal from BEN VIP")
        trade_bot1(message)  # Calls `monitor_price_and_cancel1()` inside trade_bot1()
    else:
        print("📩 Signal from TFXC PREMIUM")
        trade_bot2(message)  # Calls `monitor_price_and_cancel()` inside trade_bot2()

# 🔹 Run Everything Concurrently
async def main():
    await client.run_until_disconnected()  # Keeps Telegram bot listening while trade_bot handles monitoring

# 🔹 Start Execution
if __name__ == "__main__":
    if mt5_login():  # Ensure MT5 is connected before running
        print("🚀 Bot is live: Listening to Telegram & Monitoring Prices...")
        
        loop = asyncio.get_event_loop()
        with client:
            loop.run_until_complete(main()) 

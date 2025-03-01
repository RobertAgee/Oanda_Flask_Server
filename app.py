from datetime import time
from decimal import Decimal, ROUND_HALF_UP
from pprint import pprint

import os
from dotenv import load_dotenv

from oandapyV20 import API
from oandapyV20.exceptions import V20Error
from oandapyV20.endpoints.accounts import AccountDetails, AccountSummary
from oandapyV20.endpoints.orders import OrderCreate, OrderDetails, OrderCancel, OrdersPending
from oandapyV20.endpoints.positions import OpenPositions, PositionDetails, PositionClose
from oandapyV20.endpoints.trades import TradeClose, TradeDetails, TradesList
from oandapyV20.endpoints.pricing import PricingInfo
from oandapyV20.endpoints.instruments import InstrumentsCandles
from flask import Flask, request, json, jsonify

app = Flask(__name__)
# Load environment variables from the .env file
load_dotenv()

# SIZING VARIABLES
POSITION_SIZE = int(os.getenv("POSITION_SIZE"))
TP_PERCENT = float(os.getenv("TP_PERCENT", "0.01"))  # Default to 1% if unset

# It is a good idea to ensure that the variables are available
if not all([POSITION_SIZE, TP_PERCENT]):
    raise EnvironmentError("One or more sizing variables are not set in the environment variables.")
print(POSITION_SIZE)
print(TP_PERCENT)

# Replace with your API key and account ID
ACCESS_TOKEN = os.getenv("PRACTICE_ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("DEFAULT_ACCOUNT_ID")
SHEET_NAME = os.getenv("SHEET_NAME")

POSITION_SIZE = os.getenv("POSITION_SIZE")
TP_PERCENT = os.getenv("TP_PERCENT")
LIVE_API = os.getenv("LIVE_API")
LIVE_ACCESS_TOKEN = os.getenv("LIVE_ACCESS_TOKEN")
PRACTICE_API = os.getenv("PRACTICE_API")


# Initialize the API client
api = API(access_token=ACCESS_TOKEN, environment="practice")  # Use "live" for real trading

# Helper function to handle API requests
def make_request(endpoint):
    try:
        response = api.request(endpoint)
        # pprint(response)
        return jsonify(response), 200
    except V20Error as e:
        return jsonify({"error": str(e)}), 400

# Cancel Prices for Instrument
def get_mid_price(instrument):
    if not instrument:
        return jsonify({"error": "Instrument parameter is required"}), 400

    # Fetch current price using the PricingInfo endpoint
    params = {"instruments": instrument}
    endpoint = PricingInfo(ACCOUNT_ID, params=params)
    response = make_request(endpoint)
    response_data = response[0]
    response_prices = json.loads(response_data.get_data(as_text=True))
    pprint(response_prices)
    bid = float(response_prices['prices'][0]['closeoutBid'])
    ask = float(response_prices['prices'][0]['closeoutAsk'])
    mid = (bid + ask) / 2
    return mid

def get_ask_price(instrument):
    if not instrument:
        return jsonify({"error": "Instrument parameter is required"}), 400

    # Fetch current price using the PricingInfo endpoint
    params = {"instruments": instrument}
    endpoint = PricingInfo(ACCOUNT_ID, params=params)
    response = make_request(endpoint)
    response_data = response[0]
    response_prices = json.loads(response_data.get_data(as_text=True))
    # pprint(response_prices)
    ask = float(response_prices['prices'][0]['closeoutAsk'])
    return ask

def get_bid_price(instrument):
    if not instrument:
        return jsonify({"error": "Instrument parameter is required"}), 400

    # Fetch current price using the PricingInfo endpoint
    params = {"instruments": instrument}
    endpoint = PricingInfo(ACCOUNT_ID, params=params)
    response = make_request(endpoint)
    response_data = response[0]
    response_prices = json.loads(response_data.get_data(as_text=True))
    # pprint(response_prices)
    ask = float(response_prices['prices'][0]['closeoutBid'])
    return ask

# Cancel Order Methods for Instrument
def cancel_orders(instrument):

    # Step 1: Fetch Open Orders
    endpoint = OrdersPending(ACCOUNT_ID)
    response = api.request(endpoint)
    open_orders = response.get("orders", [])
    # Step 2: Cancel Open Orders for instrument
    canceled_orders = []
    for order in open_orders:
        if order.get("instrument") == instrument:
            order_id = order.get("id")
            cancel_endpoint = OrderCancel(ACCOUNT_ID, orderID=order_id)
            cancel_response = api.request(cancel_endpoint)
            canceled_orders.append({"order_id": order_id, "response": cancel_response})
        print(f"All orders canceled for {instrument}")

    if not canceled_orders:
        print("message: No open orders found for the specified instrument")

    return

def cancel_sell_orders(instrument):
    # Step 1: Fetch Open Orders
    endpoint = OrdersPending(ACCOUNT_ID)
    response = api.request(endpoint)
    open_orders = response.get("orders", [])

    # Step 2: Cancel Only Sell Orders for the Instrument
    canceled_orders = []
    for order in open_orders:
        pprint(order)
        if order.get("instrument") == instrument and order.get("positionFill") == "REDUCE_ONLY":
            order_id = order.get("id")
            cancel_endpoint = OrderCancel(ACCOUNT_ID, orderID=order_id)
            cancel_response = api.request(cancel_endpoint)
            canceled_orders.append({"order_id": order_id, "response": cancel_response})
            print(f"Canceled SELL order {order_id} for {instrument}")

    if not canceled_orders:
        print(f"Message: No open sell orders found for {instrument}")

    return canceled_orders

def cancel_buy_orders(instrument):
    # Step 1: Fetch Open Orders
    endpoint = OrdersPending(ACCOUNT_ID)
    response = api.request(endpoint)
    open_orders = response.get("orders", [])

    # Step 2: Cancel Only Buy Orders for the Instrument
    canceled_orders = []
    for order in open_orders:
        pprint(order)
        if order.get("instrument") == instrument and order.get("positionFill") == "REDUCE_ONLY":
            order_id = order.get("id")
            cancel_endpoint = OrderCancel(ACCOUNT_ID, orderID=order_id)
            cancel_response = api.request(cancel_endpoint)
            canceled_orders.append({"order_id": order_id, "response": cancel_response})
            print(f"Canceled BUY order {order_id} for {instrument}")

    if not canceled_orders:
        print(f"Message: No open sell orders found for {instrument}")

    return canceled_orders

@app.route('/cancel_sell_orders', methods=['GET'])
def cancelling():
    # Cancel Sell Orders for instrument
    endpoint = OpenPositions(ACCOUNT_ID)
    pprint(jsonify(api.request(endpoint)).get_data(as_text=True))
    data = json.loads(jsonify(api.request(endpoint)).get_data(as_text=True))
    instruments = [position["instrument"] for position in data["positions"]]
    pprint(instruments)
    for instrument in instruments:
        cancel_sell_orders(instrument)
    return

# Get Current Price of an Instrument
@app.route('/price', methods=['POST'])
def get_current_price():
    # Get the instrument from the query parameters
    data = request.json
    instrument = data.get("instrument")
    if not instrument:
        return jsonify({"error": "Instrument parameter is required"}), 400

    # Fetch current price using the PricingInfo endpoint
    params = {"instruments": instrument}
    endpoint = PricingInfo(ACCOUNT_ID, params=params)
    return make_request(endpoint)

# 1. Fetch Account Details
@app.route('/account/details', methods=['GET'])
def account_details():
    endpoint = AccountDetails(ACCOUNT_ID)
    return make_request(endpoint)

# 2. Fetch Account Summary
@app.route('/account/summary', methods=['GET'])
def account_summary():
    endpoint = AccountSummary(ACCOUNT_ID)
    return make_request(endpoint)

# 3. Place a Market Order
@app.route('/order/market', methods=['POST'])
def place_market_order():
    data = request.json
    order_data = {
        "order": {
            "type": "MARKET",
            "instrument": data.get("instrument"),
            "units": data.get("units"),
            "timeInForce": "FOK"  # Fill or Kill
        }
    }
    endpoint = OrderCreate(ACCOUNT_ID, data=order_data)
    return make_request(endpoint)

# 4. Fetch Open Positions
@app.route('/positions', methods=['GET'])
def open_positions():
    endpoint = OpenPositions(ACCOUNT_ID)
    return make_request(endpoint)

# 5. Fetch Position Details for a Specific Instrument
@app.route('/positions/<instrument>', methods=['GET'])
def position_details(instrument):
    endpoint = PositionDetails(ACCOUNT_ID, instrument=instrument)
    return make_request(endpoint)

# 6. Close a Trade
@app.route('/trade/close', methods=['POST'])
def close_trade():
    data = request.json
    trade_id = data.get("trade_id")
    endpoint = TradeClose(ACCOUNT_ID, tradeID=trade_id)
    return make_request(endpoint)

# 7. Fetch Historical Candlestick Data
@app.route('/historical/<instrument>', methods=['GET'])
def historical_data(instrument):
    params = {
        "count": request.args.get("count", 100),  # Number of candles
        "granularity": request.args.get("granularity", "M15"),  # Timeframe
        "price": "MBA"  # Mid, Bid, Ask
    }
    endpoint = InstrumentsCandles(instrument=instrument, params=params)
    return make_request(endpoint)

# 8. Fetch Instrument Details
@app.route('/instruments/<instrument>', methods=['GET'])
def instrument_details(instrument):
    params = {
        "instruments": instrument
    }
    endpoint = PricingInfo(ACCOUNT_ID, params=params)
    return make_request(endpoint)

# 9. Set Stop-Loss and Take-Profit for an Order
@app.route('/order/modify', methods=['POST'])
def modify_order():
    data = request.json
    order_id = data.get("order_id")
    stop_loss = data.get("stop_loss")
    take_profit = data.get("take_profit")

    order_data = {
        "order": {
            "stopLossOnFill": {
                "price": stop_loss
            },
            "takeProfitOnFill": {
                "price": take_profit
            }
        }
    }
    endpoint = OrderDetails(ACCOUNT_ID, orderID=order_id, data=order_data)
    return make_request(endpoint)

# 10. Place an IOC Limit Order with Take-Profit
@app.route('/order/ioc-limit-tp', methods=['POST'])
def place_ioc_limit_order_with_tp():
    data = request.json
    # example json would look like {"buy": ["USDCAD", "NZDUSD", "USDJPY"]}
    instruments = data.get("buy", [])
    order_responses = []

    for instrument in instruments:
        instrument = instrument[:3] + "_" + instrument[3:]
        print(instrument)
        if instrument == "USD_TRY":
            continue
        try:
            price = get_ask_price(instrument)  # Limit price
        except:
            print(f"Error retrieving price for {instrument}")
            continue
        units = str(round(float(POSITION_SIZE), 0))
        limit_price = Decimal(price).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        # Step 1: Place the IOC Limit Order
        order_data = {
            "order": {
                "type": "LIMIT",
                "instrument": instrument,
                "units": units,
                "price": str(limit_price),
                "timeInForce": "IOC",  # Immediate or Cancel
                "positionFill": "DEFAULT"
            }
        }
        order_endpoint = OrderCreate(ACCOUNT_ID, data=order_data)
        order_response = api.request(order_endpoint)
        # print("order_response")
        # pprint(order_response)
        if order_response.get("orderFillTransaction", {}):
            order_id = order_response.get("orderFillTransaction", {}).get("orderID")
            print(f"Long order placed for {instrument} of {units} at {limit_price}")

        else:
            print(f"error: Failed to place IOC limit order")
            continue
        order_responses.append(order_response)

    # Step 2: Wait for the order to fill (polling)
    final_orders = []
    print('Beginning sell order placements')
    for order_response in order_responses:
        instrument = order_response['orderCreateTransaction']['instrument']
        if not order_response.get("orderFillTransaction", {}).get("orderID"):
            order_filled = False
            for _ in range(10):  # Poll for 10 seconds

                order_response.get("orderFillTransaction", {}).get("orderID")
                order_details = OrderDetails(ACCOUNT_ID, orderID=order_id)
                order_status = api.request(order_details).get("order", {}).get("state")
                if order_status == "FILLED":
                    print(f"IOC limit order filled for {instrument}")
                    order_filled = True
                    break
                time.sleep(1)  # Wait 1 second before polling again

            if not order_filled:
                print(f"error: IOC limit order did not fill for {instrument}")

        # Cancel Open Sell Orders
        cancel_sell_orders(instrument)
        # Get position details
        position_details = PositionDetails(ACCOUNT_ID, instrument=instrument)
        response = make_request(position_details)
        response_data = response[0]
        response_details = json.loads(response_data.get_data(as_text=True))
        # print("position details")
        # pprint(response_details)
        pprint("placing sell side order")
        # Units in Position
        take_profit_units = "-" + str(response_details['position']['long']['units'])
        # Average Entry Price * Profit %
        try:
            print("avg entry: " + str(response_details['position']['long']['averagePrice']))
            avg_entry = float(response_details['position']['long']['averagePrice'])
            FLOAT_TP_PERCENT = float(TP_PERCENT)
            take_profit_price = str(round(avg_entry * FLOAT_TP_PERCENT, len(str(avg_entry).split('.')[1])))

            # Step 3: Place the Take-Profit Order
            tp_order_data = {
                "order": {
                    "type": "LIMIT",
                    "instrument": instrument,
                    "units": take_profit_units,
                    "price": take_profit_price,
                    "timeInForce": "GTC",
                    "positionFill": "REDUCE_ONLY"
                }
            }
            tp_order_endpoint = OrderCreate(ACCOUNT_ID, data=tp_order_data)
            tp_order_details = make_request(tp_order_endpoint)
            tp_order_data = tp_order_details[0]
            pprint(json.loads(tp_order_data.get_data(as_text=True)))
            print(f"Order placed for {instrument} of {take_profit_units} at {take_profit_price}")
        except Exception as e:
            print(f"error Failed to retrieve trade ID for {instrument} because {e}")
            continue

    return jsonify(final_orders)

# 11. Close All Open Positions
@app.route('/positions/close-all', methods=['POST'])
def close_all_positions():
    # Step 1: Fetch Open Positions
    open_positions_endpoint = OpenPositions(ACCOUNT_ID)
    open_positions_response = api.request(open_positions_endpoint)
    positions = open_positions_response.get("positions", [])

    if not positions:
        return jsonify({"message": "No open positions found"}), 200

    # Step 2: Close Each Position
    closed_positions = []
    for position in positions:
        instrument = position.get("instrument")
        long_units = position.get("long", {}).get("units")
        short_units = position.get("short", {}).get("units")

        # Close Long Position
        if long_units and float(long_units) > 0:
            close_data = {"longUnits": "ALL"}
            close_endpoint = PositionClose(ACCOUNT_ID, instrument=instrument, data=close_data)
            close_response = api.request(close_endpoint)
            closed_positions.append({"instrument": instrument, "side": "long", "response": close_response})

        # Close Short Position
        if short_units and float(short_units) > 0:
            close_data = {"shortUnits": "ALL"}
            close_endpoint = PositionClose(ACCOUNT_ID, instrument=instrument, data=close_data)
            close_response = api.request(close_endpoint)
            closed_positions.append({"instrument": instrument, "side": "short", "response": close_response})

    return jsonify({"message": "All positions closed", "closed_positions": closed_positions}), 200

# 12. Get Trade History
@app.route('/trades', methods=['GET'])
def get_trade_history():
    # Get query parameters
    state = request.args.get('state', 'ALL')  # Default to 'ALL' to get all trades
    instrument = request.args.get('instrument')
    count = request.args.get('count')
    before_id = request.args.get('beforeID')

    # Prepare parameters
    params = {'state': state}
    if instrument:
        params['instrument'] = instrument
    if count:
        params['count'] = count
    if before_id:
        params['beforeID'] = before_id

    endpoint = TradesList(ACCOUNT_ID, params=params)
    return make_request(endpoint)

# 13. Get Current Balance
@app.route('/balance', methods=['GET'])
def balance():
    try:
        # Fetch account details
        r = AccountDetails(ACCOUNT_ID)
        response = api.request(r)
        pprint(response)
    except V20Error as e:
        response = "Error: " + str(e)
        print(response)

    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    balance()
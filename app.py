from autotrader import Order, AutoData
from flask import Flask, Response, request
from autotrader.autotrader import AutoTrader
import yaml
import json

app = Flask(__name__)

# load the keys.yaml file and convert to a JSON
with open("./config/keys.yaml", 'r') as yaml_in, open("keys.json", "w") as json_out:
    yaml_object = yaml.safe_load(yaml_in)
    json.dump(yaml_object, json_out)
keys = json.load(open('keys.json'))
print(keys)

# create Oanda configuration for login
oanda_config = {"data_source": "oanda",
                "API": keys["OANDA"]["LIVE_API"],
                "ACCESS_TOKEN": keys["OANDA"]["LIVE_ACCESS_TOKEN"],
                "ACCOUNT_ID": keys["OANDA"]["DEFAULT_ACCOUNT_ID"],
                "PORT": keys["OANDA"]["PORT"]
                }

# create new instance of Autotrader and login to OANDA
at = AutoTrader()
login = at.configure(broker="oanda", environment="live", account_id=oanda_config["ACCOUNT_ID"])
broker = at.run()

# create new instance of Autodata
ad = AutoData(oanda_config)

# endpoint for fetching balance and open positions
@app.route('/balance', methods=['GET'])
def balance():
    # fetch balance, net account value, and open_positions
    cash_balance = broker.get_balance()
    NAV = broker.get_NAV()
    open_positions = broker.get_positions()
    print('Current Base Currency Balance: $' + str(cash_balance))
    print('Account Net Worth: $' + str(NAV))
    print('Open Positions: \n')

    # prepare response
    message = []
    message.append('Cash Balance: ' + str(cash_balance))
    message.append('Net Account Value: ' + str(NAV))

    for key in open_positions:
        message.append(str(broker.get_position(key) + "\n"))
        print(str(broker.get_position(key)))

    # return response
    return Response(json.dumps(message, indent=4))


# endpoint for placing trades
@app.route('/order', methods=['POST'])
def order():
    # The JSON sent to the endpoint should look like this:

    # {
    # "ticker" : "NZD_USD", // symbol name being traded
    # "percent_stake" : 0.1, // 0.1% of portfolio value staked
    # "stop_loss" : 0.5, // 0.5% stop loss
    # "take_profit" : 1, // 1% profit target
    # "leverage" : 50, // the amount of leverage available to your account
    # }

    # Parse JSON key:values into variables
    letter = request.get_json()
    symbol = letter.get('symbol', '')
    percent_stake = float(letter.get('percent_stake', '')) / 100
    stop_loss = float(letter.get('stop_loss', '')) / 100
    take_profit = float(letter.get('take_profit', '')) / 100
    leverage = int(letter.get('leverage', ''))

    # request last price of asset
    last = ad.fetch(instrument=symbol, granularity="15s", count=2)['Close'].values[0]
    print(last)

    # fetch the cash balance and net account value
    cash_balance = broker.get_balance()
    NAV = broker.get_NAV()
    print(cash_balance)
    print(NAV)

    # calculate the maximum number of contracts affordable
    # Note: perhaps use bal
    max_size = (NAV * leverage) / last
    # calculate the number of contracts to buy
    size = max_size * percent_stake
    # place the order with the variables as parameters
    order = broker.place_order(
        Order(instrument=symbol, direction=1, size=size, order_type="limit", order_limit_price=last,
              stop_loss=last * (1 - stop_loss), take_profit=last * (1 + take_profit))
    )
    # get the open orders on the asset
    orders = broker.get_orders(symbol)
    # find the position outstanding on the asset
    open_positions = broker.get_position(symbol)

    # prepare response
    message = []
    message.append(str(orders) + "\n")
    message.append("Current Position:"+"\n")
    message.append(str(open_positions))

    # return the response
    return Response(message)

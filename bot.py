import datetime
import numpy
import numpy as np
import talib
import time
from binance.websockets import BinanceSocketManager
import config
from binance.client import Client
from binance.enums import *

RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30 
TRADE_SYMBOL = "BTCUSDT"
TRADE_QUANTITY = 0.0035 #dinero expresado en btc
closes = []
in_position = False
order_succeeded = None

client = Client(config.API_KEY, config.API_SECRET, tld='com')


def order_sell(quantity, symbol):
    try:
        print("Mandando orden")
        order = client.order_market_sell(symbol = str(symbol) ,quantity = quantity)
        print(order)
    except Exception as e:
        print("Se ha producido un error - {}".format(e))
        return False

    return True

def order_buy(quantity, symbol):
    try:
        print("Mandando orden")
        order = client.order_market_buy(symbol = str(symbol) ,quantity = quantity)
        print(order)
    except Exception as e:
        print("Se ha producido una excepción - {}".format(e))
        return False

    return True

def on_message(msg):
    global closes, in_position , order_succeeded
    print('\nMensaje Recibido')
    candle = msg['k']
    is_candle_closed = candle['x']
    close = candle['c']
    precioActual = close

    print("--------------------------------")
    print("Trade Symbol: {}".format(candle['s']))
    print("--------------------------------")
    print("Precio Actual: {}".format(float(precioActual)))
    print("Intervalo de las velas: {}".format(candle['i']))
    print("¿La vela esta cerrada?: {}".format(candle['x']))

    if is_candle_closed:
        print("")
        print("--------------------------------")
        print("Vela cerrada en {}".format(close))
        print("--------------------------------")
        closes.append(float(close))
        print("Cerrada")
        print("")
        print(closes)

        if len(closes) > RSI_PERIOD:
            np_closes = numpy.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            print("Todos los RSI calculados hasta ahora")
            print(rsi)
            last_rsi = rsi[-1]
            print("El RSI actual es {}".format(last_rsi))
        
            if last_rsi < RSI_OVERSOLD:
                if in_position == True:
                    print("Está sobrevendido, pero ya tenes, no hay nada que hacer.")
                else:
                    print("Esta en sobreventa, Comprando...")
                    global order_succeeded
                    order_succeeded = order_buy(TRADE_QUANTITY, TRADE_SYMBOL)
                    print("{0} comprado a {1}".format(TRADE_SYMBOL , close))
                    global ultimoPrecio
                    ultimoPrecio = close
                    if order_succeeded:
                        in_position = True

            if last_rsi  > RSI_OVERBOUGHT:
                if in_position:
                    print("Esta en sobrecompra, Vendiendo...")
                    e = client.get_symbol_ticker(symbol=TRADE_SYMBOL)
                    price = e['price']
                    if float(price) >= float(ultimoPrecio):
                        print("Vendiendo {0} a {1}".format(TRADE_SYMBOL , price))
                        order_succeeded = order_sell(TRADE_QUANTITY, TRADE_SYMBOL)
                        if order_succeeded:
                            in_position = False
                    else:
                        while float(price) < float(ultimoPrecio):
                            e = client.get_symbol_ticker(symbol=TRADE_SYMBOL)
                            price = e['price']
                            if float(price) >= float(ultimoPrecio):
                                print("Vendiendo {0} a {1}".format(TRADE_SYMBOL , price))
                                order_succeeded = order_sell(TRADE_QUANTITY, TRADE_SYMBOL)
                                if order_succeeded:
                                    in_position = False
                            else:
                                e = client.get_symbol_ticker(symbol=TRADE_SYMBOL)
                                price = e['price']
                else:
                    print("Está sobrecomprado, pero no tenemos nada. No hay nada que hacer.")

bm = BinanceSocketManager(client)
conn_key = bm.start_kline_socket(TRADE_SYMBOL, on_message, interval=KLINE_INTERVAL_1MINUTE)
bm.start()


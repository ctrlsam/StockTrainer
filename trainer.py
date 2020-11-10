import sharesies
import yfinance
import config
import logic
import pandas
import os
from datetime import datetime, timedelta


class PortfolioItem:
    def __init__(self, symbol, price, shares):
        self.symbol = symbol
        self.price = price
        self.shares = shares
        self.amount = price * shares
        self.amount *= 0.995 # transaction fee
    
    def get_profit(self, current_price):
        new_amount = current_price * self.shares
        return new_amount - self.amount
    
    def get_amount(self, current_price):
        new_amount = current_price * self.shares
        return new_amount


def get_shares_list():
    client = sharesies.Client()
    client = sharesies.Client()
    if client.login(config.username, config.password):
        print('> Connected to Sharesies')
    else:
        print('Failed to login')
        exit(-1)

    return client.get_companies()

def get_histories(shares):
    # get their 5 year history
    histories = {}
    for company in shares:
        symbol = company['code'] + '.NZ'
        cached_path = f'./histories/{symbol}.csv'

        if os.path.exists(cached_path):
            history = pandas.read_csv(cached_path)
            history['Date'] = pandas.to_datetime(history['Date'])
            history = history.set_index('Date')
        else:
            stock = yfinance.Ticker(symbol)
            history = stock.history(period='5y', interval='1d')
            history.to_csv(cached_path)

        histories[company['code']] = history

    return histories

def analyze_stock(symbol, history, portfolio, balance, keep_buying):
    transaction_value = 0
    
    # try to lookup the portfolio record
    item = next(
        (item for item in portfolio if item.symbol == symbol),
        False
    )

    try:
        # try to lookup the market price 
        market_price = history[-1:].Close.values[0]
    except:
        return transaction_value

    # we own this stock and should sell
    if item and logic.should_sell(item.price, market_price):
        print(f'# Selling {item.symbol} for ${market_price}')
        transaction_value = item.get_amount(market_price)
        portfolio.remove(item)
    
    # we don't own and should buy
    if not item and logic.should_buy(market_price, history) and keep_buying:
        quantity = 100
        cost = market_price * quantity
        if balance >= cost:
            print(f'# Buying {symbol} for ${market_price}')
            portfolio.append(PortfolioItem(symbol, market_price, quantity))
            transaction_value -= cost
    
    return transaction_value

def perform_simulation(histories):
    # give yourself $10,000
    inital = 10000
    balance = inital
    portfolio = []
    print('> Mock portfolio created')

    # go from 2017 to 2018 in daily intervals
    start_date = datetime(year=2017, month=1, day=1)
    end_date = datetime(year=2018, month=1, day=1)
    interval = timedelta(days=1)
    print('> Running simulation...')

    # keep looping until past end date and sold everything
    current_date = start_date
    while current_date < end_date or len(portfolio) > 0:
        keep_buying = current_date <= end_date

        # go through each stock daily
        for symbol in histories:
            # get history up till current date
            history = histories[symbol]
            history = history[history.index <= current_date]

            balance += analyze_stock(symbol, history,
                portfolio, balance, keep_buying)

        current_date += interval

    returns = (balance - inital) / inital * 100

    print(f'\nNew balance: ${round(balance, 3)}')
    print(f'Total returns: {round(returns, 3)}%')

def main():
    shares = get_shares_list()
    histories = get_histories(shares)

    perform_simulation(histories)


if __name__ == '__main__':
    main()
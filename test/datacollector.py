import os
import ccxt
import time
import csv
from web3 import Web3
from web3.middleware import geth_poa_middleware
from keys import account, APIprovider, address, chainlink_address, abi, chainlink_abi
import threading
import numpy as np

# initialize ccxt and web3
binance = ccxt.binance()
w3 = Web3(Web3.HTTPProvider(APIprovider))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# initialize chainlink contract and pancake prediction contract
chainlink_contract = w3.eth.contract(address=chainlink_address, abi=chainlink_abi)
contract = w3.eth.contract(address=address, abi=abi)


# write data to CSV file
def write(content):
    with open('history.csv', 'a', newline='') as f:
        w = csv.writer(f)
        w.writerow(content)
        f.flush()


# make sure there is price advantage or at least no price disadvantage
def off_chain():
    # get mean price of the BNB price from on and off chain
    cex_price = (binance.fetch_order_book('BNB/BUSD')['bids'][0][0] +
                 binance.fetch_order_book('BNB/BUSD')['asks'][0][
                     0]) / 2
    onchain_price = chainlink_contract.functions.latestRoundData().call()[1] / 100000000

    price_diff = cex_price - onchain_price
    if price_diff > 0.05:
        return 1
    elif price_diff < -0.05:
        return -1
    else:
        return 0


# All the onchain query and transaction method
class OnChain:

    def __init__(self, ev):
        # set betting parameters. betAmount is the amount you want to bet every round.
        # EV is the threshold to make a bet. A higher EV means that you only make bets with higher expected gain.
        # Since data query through RPC is slow and unstable, a higher EV give a better buffer against loss.
        self.betAmount = 0.001
        self.EV = ev
        # get onchain data
        self.nonce = w3.eth.get_transaction_count(account)
        self.current_epoch = contract.functions.currentEpoch().call()
        self.current_timestamp = w3.eth.get_block('latest')['timestamp']
        self.current_round_info = contract.functions.rounds(self.current_epoch).call()
        self.balance = w3.eth.get_balance(account) / 10 ** 18

    # Check if there is an arb opportunity and bet accordingly
    def bet(self):
        # get info needed for the calculation of payout ratio
        current_total, current_bull, current_bear = self.current_round_info[8], self.current_round_info[9], \
            self.current_round_info[10]
        temp = off_chain()
        # calculate the payout ratio
        ev_bull = current_total / current_bull / 2 - 1.03
        ev_bear = current_total / current_bear / 2 - 1.03

        # bet accordingly and write data
        if ev_bear >= self.EV and temp <= 0:
            print('EV', ev_bear, self.current_epoch, 'bet bear for', self.betAmount, 'bnb')
            # refresh data to get the post-bet correct EV,and bet result
            time.sleep(25)
            bet_round_info = contract.functions.rounds(self.current_epoch).call()
            ev_bear_ex_post = bet_round_info[8] / bet_round_info[10] / 2 - 1.03
            # save info to the csv file
            write([self.current_epoch, 'Bear', self.betAmount, ev_bear, ev_bear_ex_post, bet_round_info[8],
                   self.balance - self.betAmount])

        elif ev_bull >= self.EV and temp >= 0:
            print('EV', ev_bull, self.current_epoch, 'bet bull for', self.betAmount, 'bnb')
            # refresh data to get the post-bet correct EV, and bet result
            time.sleep(25)
            bet_round_info = contract.functions.rounds(self.current_epoch).call()
            ev_bull_ex_post = bet_round_info[8] / bet_round_info[9] / 2 - 1.03
            # save info to the csv file
            write([self.current_epoch, 'Bull', self.betAmount, ev_bull, ev_bull_ex_post, bet_round_info[8],
                   self.balance - self.betAmount])

        else:
            print(self.current_epoch, 'no bet')
            # save info to the csv file
            time.sleep(25)
            write([self.current_epoch, 'No', self.EV, np.float('nan'), float('nan'), float('nan'),
                   self.balance])


def backtest(ev):
    # initialize data writer
    if not os.path.exists('history.csv'):
        with open('history.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Epoch', 'Direction', 'Threshold', 'EV ex ante', 'EV ex post', 'Pool', 'Balance'])
            file.flush()
        file.close()
    else:
        print("History file Exists")

    # run the strategy
    while True:
        try:
            # get time
            onchain = OnChain(ev)
            time_to_lock = onchain.current_round_info[2] - onchain.current_timestamp

            # if the close of betting is near, bet(parameters modifiable)
            if 8 >= time_to_lock > 0:
                onchain.bet()
                time.sleep(250)

        except Exception as e:
            print(e)
            continue


test = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1]

for i in range(8):
    threading.Thread(target=backtest, args=[test[i]]).start()

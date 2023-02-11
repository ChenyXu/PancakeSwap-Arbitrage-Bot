import os
import ccxt
import time
import csv
from web3 import Web3
from web3.middleware import geth_poa_middleware
from keys import account, private_key, APIprovider, address, chainlink_address, abi, chainlink_abi

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

    def __init__(self):
        # set betting parameters. betAmount is the amount you want to bet every round.
        # EV is the threshold to make a bet. A higher EV means that you only make bets with higher expected gain.
        # Since data query through RPC is slow and unstable, a higher EV give a better buffer against loss.
        self.betAmount = 0.2
        self.EV = 0.25
        # get onchain data
        self.nonce = w3.eth.get_transaction_count(account)
        self.current_epoch = contract.functions.currentEpoch().call()
        self.current_timestamp = w3.eth.get_block('latest')['timestamp']
        self.current_round_info = contract.functions.rounds(self.current_epoch).call()
        self.balance = w3.eth.get_balance(account) / 10 ** 18

    # function to bet bull
    def bet_bull(self):
        transaction = contract.functions.betBull(self.current_epoch).buildTransaction({
            'chainId': 56,
            'from': account,
            'gas': 250000,
            'gasPrice': w3.toWei(15, 'gwei'),
            'nonce': self.nonce,
            'value': w3.toWei(self.betAmount, 'ether')
        })
        signed_tx = w3.eth.account.sign_transaction(transaction, private_key)
        data = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return data

    # function to bet bear
    def bet_bear(self):
        transaction = contract.functions.betBear(self.current_epoch).buildTransaction({
            'chainId': 56,
            'from': account,
            'gas': 250000,
            'gasPrice': w3.toWei(15, 'gwei'),
            'nonce': self.nonce,
            'value': w3.toWei(self.betAmount, 'ether')
        })
        signed_tx = w3.eth.account.sign_transaction(transaction, private_key)
        data = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return data

    # Check if there is over 3 unclaimed rewards in the previous 15 rounds
    def claim(self):
        claimable = []
        for i in range(100):
            if contract.functions.claimable(self.current_epoch - i, account).call():
                claimable.append(self.current_epoch - i)

        if len(claimable) >= 3:
            transaction = contract.functions.claim(claimable).buildTransaction({
                'chainId': 56,
                'from': account,
                'gas': 500000,
                'gasPrice': w3.toWei(15, 'gwei'),
                'nonce': self.nonce + 1,
            })
            signed_tx = w3.eth.account.sign_transaction(transaction, private_key)
            result = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            print('Claimed rewards for rounds:', claimable, result)

    # Check if there is an arb opportunity and bet accordingly
    def bet(self):
        # get info needed for the calculation of payout ratio
        current_total, current_bull, current_bear = self.current_round_info[8], self.current_round_info[9], \
            self.current_round_info[10]
        temp = off_chain()
        # calculate the payout ratio
        ev_bull, ev_bear = current_total / current_bull / 2 - 1.03, current_total / current_bear / 2 - 1.03

        # bet accordingly and write data
        if ev_bear >= self.EV and temp <= 0:
            data = self.bet_bear()
            print('EV', ev_bear, self.current_epoch, 'bet bear for', self.betAmount, 'bnb', data)
            # refresh data to get the post-bet correct EV,and bet result
            time.sleep(25)
            bet_round_info = contract.functions.rounds(self.current_epoch).call()
            ev_bear_ex_post = bet_round_info[8] / bet_round_info[10] / 2 - 1.03
            # save info to the csv file
            write([self.current_epoch, 'Bear', self.betAmount, ev_bear,ev_bear_ex_post, self.balance - self.betAmount])

        elif ev_bull >= self.EV and temp >= 0:
            data = self.bet_bull()
            print('EV', ev_bull, self.current_epoch, 'bet bull for', self.betAmount, 'bnb', data)
            # refresh data to get the post-bet correct EV, and bet result
            time.sleep(25)
            bet_round_info = contract.functions.rounds(self.current_epoch).call()
            ev_bull_ex_post = bet_round_info[8] / bet_round_info[9] / 2 - 1.03
            # save info to the csv file
            write([self.current_epoch, 'Bull', self.betAmount, ev_bull, ev_bull_ex_post, self.balance - self.betAmount])

        else:
            print(self.current_epoch, 'no bet')
            # save info to the csv file
            write([self.current_epoch, 'No Bet', 0, float("NAN"), self.balance])
            time.sleep(25)


def main():
    # initialize data writer
    if not os.path.exists('history.csv'):
        with open('history.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Epoch', 'Direction', 'Amount', 'EV ex ante', 'EV ex post', 'Balance'])
            file.flush()
        file.close()
    else:
        print("History file Exists")

    # run the strategy
    while True:
        try:
            # get time
            onchain = OnChain()
            time_to_lock = onchain.current_round_info[2] - onchain.current_timestamp

            # if the close of betting is near, bet(parameters modifiable)
            if 10 > time_to_lock > 3:
                onchain.bet()
                onchain.claim()
                time.sleep(250)

        except Exception as e:
            print(e)
            continue


if __name__ == "__main__":
    main()

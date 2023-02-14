import os
import time
import csv
from web3 import Web3
from web3.middleware import geth_poa_middleware
from keys import account, private_key, APIprovider, address, chainlink_address, abi, chainlink_abi


# initialize web3
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


# All the onchain query and transaction method
class OnChain:

    def __init__(self, amount, ev):
        # set betting parameters. betAmount is the amount you want to bet every round.
        # EV is the threshold to make a bet. A higher EV means that you only make bets with higher expected gain.
        # Since data query through RPC is slow and unstable, a higher EV give a better buffer against loss.
        self.betAmount = amount
        self.EV = ev
        # get onchain data
        self.nonce = w3.eth.get_transaction_count(account)
        self.current_epoch = contract.functions.currentEpoch().call()
        self.current_timestamp = w3.eth.get_block('latest')['timestamp']
        self.current_round_info = contract.functions.rounds(self.current_epoch).call()

    # function to bet bull
    def bet_bull(self):
        transaction = contract.functions.betBull(self.current_epoch).buildTransaction({
            'chainId': 56,
            'from': account,
            'gas': 250000,
            'gasPrice': w3.toWei(5, 'gwei'),
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
            'gasPrice': w3.toWei(5, 'gwei'),
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
            self.nonce = w3.eth.get_transaction_count(account)
            transaction = contract.functions.claim(claimable).buildTransaction({
                'chainId': 56,
                'from': account,
                'gas': 500000,
                'gasPrice': w3.toWei(5, 'gwei'),
                'nonce': self.nonce,
            })
            signed_tx = w3.eth.account.sign_transaction(transaction, private_key)
            result = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            print('Claimed rewards for rounds:', claimable, result)

    # Check if there is an arb opportunity and bet accordingly
    def bet(self):
        # get info needed for the calculation of payout ratio
        current_total, current_bull, current_bear = self.current_round_info[8], self.current_round_info[9], \
            self.current_round_info[10]
        # calculate the payout ratio
        ev_bull = current_total / current_bull / 2 - 1.03
        ev_bear = current_total / current_bear / 2 - 1.03

        # bet accordingly and write data
        if ev_bear >= self.EV:
            self.bet_bear()
            print('EV', ev_bear, self.current_epoch, 'bet bear for', self.betAmount, 'bnb')
            # refresh data to get the post-bet correct EV,and bet result
            time.sleep(25)
            bet_round_info = contract.functions.rounds(self.current_epoch).call()
            ev_bear_ex_post = bet_round_info[8] / bet_round_info[10] / 2 - 1.03
            # save info to the csv file
            write([self.current_epoch, 'Bear', self.betAmount, ev_bear, ev_bear_ex_post, bet_round_info[8] / 10 ** 18,
                   w3.eth.get_balance(account) / 10 ** 18])

        elif ev_bull >= self.EV:
            self.bet_bull()
            print('EV', ev_bull, self.current_epoch, 'bet bull for', self.betAmount, 'bnb')
            # refresh data to get the post-bet correct EV, and bet result
            time.sleep(25)
            bet_round_info = contract.functions.rounds(self.current_epoch).call()
            ev_bull_ex_post = bet_round_info[8] / bet_round_info[9] / 2 - 1.03
            # save info to the csv file
            write([self.current_epoch, 'Bull', self.betAmount, ev_bull, ev_bull_ex_post, bet_round_info[8] / 10 ** 18,
                   w3.eth.get_balance(account) / 10 ** 18])

        else:
            print(self.current_epoch, 'no bet')
            # save info to the csv file
            time.sleep(25)
            write([self.current_epoch, 'No', self.betAmount, float('nan'), float('nan'), float('nan'),
                   w3.eth.get_balance(account) / 10 ** 18])


def run(amount, ev):
    # initialize data writer
    if not os.path.exists('history.csv'):
        with open('history.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Epoch', 'Direction', 'Amount', 'EV ex ante', 'EV ex post', 'Pool', 'Balance'])
            file.flush()
        file.close()
    else:
        print("History file Exists")

    # run the strategy
    while True:
        try:
            # get time
            onchain = OnChain(amount, ev)
            time_to_lock = onchain.current_round_info[2] - onchain.current_timestamp

            # if the close of betting is near, bet(parameters modifiable)
            if 10 >= time_to_lock > 0:
                onchain.bet()
                onchain.claim()
                time.sleep(250)

        except Exception as e:
            print(e)
            continue


if __name__ == "__main__":
    # set config
    bet_amount =   # the amount of bnb you want to bet every round
    EV = 0.25 # only when the expected value exceeds this threshold, this bot will bet for you
    # run the strategy
    run(bet_amount, EV)


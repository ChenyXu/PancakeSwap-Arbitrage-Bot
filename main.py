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
balance = w3.eth.get_balance(account)

# initialize chainlink contract and pancake prediction contract
chainlink_contract = w3.eth.contract(address=chainlink_address, abi=chainlink_abi)
contract = w3.eth.contract(address=address, abi=abi)

# initialize data writer
with open('history.csv', 'a') as file:
    writer = csv.writer(file)
    writer.writerow(['Epoch', 'Direction', 'Amount', 'Balance'])


# make sure there is price advantage or at least no price disadvantage
def OffChain():
    # get mean price of the BNB price from on and off chain
    cex_price = (binance.fetch_order_book('BNB/BUSD')['bids'][0][0] +
                 binance.fetch_order_book('BNB/BUSD')['asks'][0][
                     0]) / 2
    onchain_price = chainlink_contract.functions.latestRoundData().call()[1] / 100000000

    price_diff = cex_price - onchain_price
    if price_diff > 0.1:
        return 1
    elif price_diff < -0.1:
        return -1
    else:
        return 0


# All the onchain query and transaction method
class OnChain:

    def __init__(self):
        # set betting parameters. betAmount is the amount you want to bet every round.
        # EV is the threshold to make a bet. A higher EV means that you only make bets with higher expected gain.
        # Since data query through RPC is slow and unstable, a higher EV give a better buffer against loss.
        self.betAmount = 0.01
        self.EV = 0.1
        # get onchain data
        self.nonce = w3.eth.get_transaction_count(account)
        self.current_epoch = contract.functions.currentEpoch().call()
        self.current_timestamp = w3.eth.get_block('latest')['timestamp']
        self.current_round_info = contract.functions.rounds(self.current_epoch).call()

    # function to bet bull
    def betBull(self):
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
    def betBear(self):
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

    # Check if there is reward to claim in the last 3 rounds, and claim if is
    def claim(self):
        claimable = []
        for i in range(3):
            if contract.functions.claimable(self.current_epoch - i, account).call():
                claimable.append(self.current_epoch - i)

        if claimable:
            print(claimable)
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
        current_total = self.current_round_info[8]
        current_bull = self.current_round_info[9]
        current_bear = self.current_round_info[10]

        # calculate the payouts
        EV_bull = current_total / current_bull / 2 - 1.03
        EV_bear = current_total / current_bear / 2 - 1.03

        # bet accordingly and write data
        if EV_bear >= 0.1 and OffChain() == -1:
            data = self.betBear()
            print('EV', EV_bear, self.current_epoch, 'bet bear for', self.betAmount, 'bnb', data)
            with open('history.csv', 'a') as f:
                w = csv.writer(f)
                w.writerow([self.current_epoch, 'Bear', self.betAmount, balance])

        elif EV_bull >= 0.1 and OffChain() == 1:
            data = self.betBull()
            print('EV', EV_bull, self.current_epoch, 'bet bull for', self.betAmount, 'bnb', data)
            with open('history.csv', 'a') as f:
                w = csv.writer(f)
                w.writerow([self.current_epoch, 'Bull', self.betAmount, balance])

        else:
            print(self.current_epoch, 'no bet')
            with open('history.csv', 'a') as f:
                w = csv.writer(f)
                w.writerow([self.current_epoch, 'No Bet', self.betAmount, balance])


# run the strategy
while True:
    try:
        onchain = OnChain()
        # get data from chainlink in order to bet 10s before the close of this round
        current_round_info = onchain.current_round_info
        current_lock = current_round_info[2]
        current_timestamp = onchain.current_timestamp
        time_to_lock = current_lock - current_timestamp

        # check time before close of this round
        if 12 > time_to_lock > 3:
            onchain.bet()
            onchain.claim()
            time.sleep(250)

    except Exception as e:
        print(e)
        continue

    else:
        continue

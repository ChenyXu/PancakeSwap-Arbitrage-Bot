import ccxt
import json
import time
import csv
from web3 import Web3
from web3.middleware import geth_poa_middleware

# initialize ccxt
binance = ccxt.binance()
ftx = ccxt.ftx()

# initialize web3
w3 = Web3(Web3.HTTPProvider(""))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
account = ''
private_key = ''
balance = w3.eth.get_balance(account)

# initialize chainlink contract
chainlink_abi = json.loads(
    '[{"inputs":[{"internalType":"address","name":"_aggregator","type":"address"},{"internalType":"address","name":"_accessController","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"int256","name":"current","type":"int256"},{"indexed":true,"internalType":"uint256","name":"roundId","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"updatedAt","type":"uint256"}],"name":"AnswerUpdated","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"roundId","type":"uint256"},{"indexed":true,"internalType":"address","name":"startedBy","type":"address"},{"indexed":false,"internalType":"uint256","name":"startedAt","type":"uint256"}],"name":"NewRound","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"}],"name":"OwnershipTransferRequested","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"inputs":[],"name":"acceptOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"accessController","outputs":[{"internalType":"contract AccessControllerInterface","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"aggregator","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_aggregator","type":"address"}],"name":"confirmAggregator","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"description","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_roundId","type":"uint256"}],"name":"getAnswer","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint80","name":"_roundId","type":"uint80"}],"name":"getRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_roundId","type":"uint256"}],"name":"getTimestamp","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"latestAnswer","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"latestRound","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"latestRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"latestTimestamp","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint16","name":"","type":"uint16"}],"name":"phaseAggregators","outputs":[{"internalType":"contract AggregatorV2V3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"phaseId","outputs":[{"internalType":"uint16","name":"","type":"uint16"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_aggregator","type":"address"}],"name":"proposeAggregator","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"proposedAggregator","outputs":[{"internalType":"contract AggregatorV2V3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint80","name":"_roundId","type":"uint80"}],"name":"proposedGetRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"proposedLatestRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_accessController","type":"address"}],"name":"setController","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_to","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"version","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]')
chainlink_address = '0xD276fCF34D54A926773c399eBAa772C12ec394aC'
chainlink_contract = w3.eth.contract(address=chainlink_address, abi=chainlink_abi)

# initialize pancake prediction contract
address = '0x18B2A687610328590Bc8F2e5fEdDe3b582A49cdA'
abi = json.loads(
    '[{"inputs":[{"internalType":"address","name":"_oracleAddress","type":"address"},{"internalType":"address","name":"_adminAddress","type":"address"},{"internalType":"address","name":"_operatorAddress","type":"address"},{"internalType":"uint256","name":"_intervalSeconds","type":"uint256"},{"internalType":"uint256","name":"_bufferSeconds","type":"uint256"},{"internalType":"uint256","name":"_minBetAmount","type":"uint256"},{"internalType":"uint256","name":"_oracleUpdateAllowance","type":"uint256"},{"internalType":"uint256","name":"_treasuryFee","type":"uint256"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"BetBear","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"BetBull","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Claim","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"},{"indexed":true,"internalType":"uint256","name":"roundId","type":"uint256"},{"indexed":false,"internalType":"int256","name":"price","type":"int256"}],"name":"EndRound","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"},{"indexed":true,"internalType":"uint256","name":"roundId","type":"uint256"},{"indexed":false,"internalType":"int256","name":"price","type":"int256"}],"name":"LockRound","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"admin","type":"address"}],"name":"NewAdminAddress","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint256","name":"bufferSeconds","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"intervalSeconds","type":"uint256"}],"name":"NewBufferAndIntervalSeconds","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"minBetAmount","type":"uint256"}],"name":"NewMinBetAmount","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"operator","type":"address"}],"name":"NewOperatorAddress","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"oracle","type":"address"}],"name":"NewOracle","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint256","name":"oracleUpdateAllowance","type":"uint256"}],"name":"NewOracleUpdateAllowance","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"treasuryFee","type":"uint256"}],"name":"NewTreasuryFee","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"}],"name":"Pause","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"account","type":"address"}],"name":"Paused","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"rewardBaseCalAmount","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"rewardAmount","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"treasuryAmount","type":"uint256"}],"name":"RewardsCalculated","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"}],"name":"StartRound","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"token","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"TokenRecovery","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"TreasuryClaim","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"}],"name":"Unpause","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"account","type":"address"}],"name":"Unpaused","type":"event"},{"inputs":[],"name":"MAX_TREASURY_FEE","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"adminAddress","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"epoch","type":"uint256"}],"name":"betBear","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"epoch","type":"uint256"}],"name":"betBull","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"bufferSeconds","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256[]","name":"epochs","type":"uint256[]"}],"name":"claim","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"claimTreasury","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"epoch","type":"uint256"},{"internalType":"address","name":"user","type":"address"}],"name":"claimable","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"currentEpoch","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"executeRound","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"genesisLockOnce","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"genesisLockRound","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"genesisStartOnce","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"genesisStartRound","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"uint256","name":"cursor","type":"uint256"},{"internalType":"uint256","name":"size","type":"uint256"}],"name":"getUserRounds","outputs":[{"internalType":"uint256[]","name":"","type":"uint256[]"},{"components":[{"internalType":"enum PancakePredictionV2.Position","name":"position","type":"uint8"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"bool","name":"claimed","type":"bool"}],"internalType":"struct PancakePredictionV2.BetInfo[]","name":"","type":"tuple[]"},{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getUserRoundsLength","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"intervalSeconds","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"address","name":"","type":"address"}],"name":"ledger","outputs":[{"internalType":"enum PancakePredictionV2.Position","name":"position","type":"uint8"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"bool","name":"claimed","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"minBetAmount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"operatorAddress","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"oracle","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"oracleLatestRoundId","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"oracleUpdateAllowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"pause","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"paused","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_token","type":"address"},{"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"recoverToken","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"epoch","type":"uint256"},{"internalType":"address","name":"user","type":"address"}],"name":"refundable","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"rounds","outputs":[{"internalType":"uint256","name":"epoch","type":"uint256"},{"internalType":"uint256","name":"startTimestamp","type":"uint256"},{"internalType":"uint256","name":"lockTimestamp","type":"uint256"},{"internalType":"uint256","name":"closeTimestamp","type":"uint256"},{"internalType":"int256","name":"lockPrice","type":"int256"},{"internalType":"int256","name":"closePrice","type":"int256"},{"internalType":"uint256","name":"lockOracleId","type":"uint256"},{"internalType":"uint256","name":"closeOracleId","type":"uint256"},{"internalType":"uint256","name":"totalAmount","type":"uint256"},{"internalType":"uint256","name":"bullAmount","type":"uint256"},{"internalType":"uint256","name":"bearAmount","type":"uint256"},{"internalType":"uint256","name":"rewardBaseCalAmount","type":"uint256"},{"internalType":"uint256","name":"rewardAmount","type":"uint256"},{"internalType":"bool","name":"oracleCalled","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_adminAddress","type":"address"}],"name":"setAdmin","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_bufferSeconds","type":"uint256"},{"internalType":"uint256","name":"_intervalSeconds","type":"uint256"}],"name":"setBufferAndIntervalSeconds","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_minBetAmount","type":"uint256"}],"name":"setMinBetAmount","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_operatorAddress","type":"address"}],"name":"setOperator","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_oracle","type":"address"}],"name":"setOracle","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_oracleUpdateAllowance","type":"uint256"}],"name":"setOracleUpdateAllowance","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_treasuryFee","type":"uint256"}],"name":"setTreasuryFee","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"treasuryAmount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"treasuryFee","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"unpause","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"uint256","name":"","type":"uint256"}],"name":"userRounds","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]')
contract = w3.eth.contract(address=address, abi=abi)

# initialize data writer
with open('history.csv', 'a') as file:
    writer = csv.writer(file)
    writer.writerow(['Epoch', 'Direction', 'Amount', 'Balance'])


# function to bet bull
def betBull(i):
    transaction = contract.functions.betBull(current_epoch).buildTransaction({
        'chainId': 56,
        'from': account,
        'gas': 250000,
        'gasPrice': w3.toWei(15, 'gwei'),
        'nonce': nonce,
        'value': w3.toWei(i, 'ether')
    })
    signed_tx = w3.eth.account.sign_transaction(transaction, private_key)
    data = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return data


# function to bet bear
def betBear(i):
    transaction = contract.functions.betBear(current_epoch).buildTransaction({
        'chainId': 56,
        'from': account,
        'gas': 250000,
        'gasPrice': w3.toWei(15, 'gwei'),
        'nonce': nonce,
        'value': w3.toWei(i, 'ether')
    })
    signed_tx = w3.eth.account.sign_transaction(transaction, private_key)
    data = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return data


# make sure there is price advantage or at least no price disadvantage
def check_price():
    # get mean price of the BNB price from FTX and Binance
    BNB_binance = (binance.fetch_order_book('BNB/BUSD')['bids'][0][0] + binance.fetch_order_book('BNB/BUSD')['asks'][0][
        0]) / 2
    BNB_ftx = (ftx.fetch_order_book('BNB/USD')['bids'][0][0] + ftx.fetch_order_book('BNB/USD')['asks'][0][0]) / 2
    BNB_price = (BNB_ftx + BNB_binance) / 2
    # get the current price from chainlink
    BNB_chainlink_data = chainlink_contract.functions.latestRoundData().call()
    BNB_chainlink_price = BNB_chainlink_data[1] / 100000000
    # get the price difference
    price_diff = BNB_price - BNB_chainlink_price

    if price_diff > 0.1:
        return 1
    elif price_diff < -0.1:
        return -1
    else:
        return 0


# see if there is a payout arb opportunity and bet amount i
def check_payout_bet(i):
    # get the bet info from chainlink contract
    current_epoch = contract.functions.currentEpoch().call()
    current_round_info = contract.functions.rounds(current_epoch).call()
    current_total = current_round_info[8]
    current_bull = current_round_info[9]
    current_bear = current_round_info[10]

    # calculate the payouts
    EV_bull = current_total / current_bull / 2 - 1.03
    EV_bear = current_total / current_bear / 2 - 1.03

    # bet accordingly and write data
    if EV_bear >= 0.25 and check_price() == -1:
        data = betBear(i)
        print('EV', EV_bear, current_epoch, 'bet bear for', i, 'bnb', data)
        with open('history.csv', 'a') as file:
            writer = csv.writer(file)
            writer.writerow([current_epoch, 'Bear', i, balance])

    elif EV_bull >= 0.25 and check_price() == 1:
        data = betBull(i)
        print('EV', EV_bull, current_epoch, 'bet bull for', i, 'bnb', data)
        with open('history.csv', 'a') as file:
            writer = csv.writer(file)
            writer.writerow([current_epoch, 'Bull', i, balance])

    else:
        print(current_epoch, 'no bet')
        with open('history.csv', 'a') as file:
            writer = csv.writer(file)
            writer.writerow([current_epoch, 'NoBet', i, balance])


# claim the unclaimed rewards
def claim():

    nonce = w3.eth.get_transaction_count(account)
    current_epoch = contract.functions.currentEpoch().call()
    claimable = []
    for i in range(3):
        if contract.functions.claimable(current_epoch-i, account).call():
            claimable.append(current_epoch-i)

    if claimable != []:
        print(claimable)
        transaction = contract.functions.claim(claimable).buildTransaction({
            'chainId': 56,
            'from': account,
            'gas': 500000,
            'gasPrice': w3.toWei(5, 'gwei'),
            'nonce': nonce,
        })
        signed_tx = w3.eth.account.sign_transaction(transaction, private_key)
        w3.eth.send_raw_transaction(signed_tx.rawTransaction)


# run the strategy
while True:
    try:
        # get data from chainlink in order to bet 10s before the close of this round
        current_epoch = contract.functions.currentEpoch().call()
        current_round_info = contract.functions.rounds(current_epoch).call()
        current_lock = current_round_info[2]
        current_timestamp = w3.eth.get_block('latest')['timestamp']
        time_to_lock = current_lock - current_timestamp

        # check time before close of this round
        if 12 > time_to_lock > 3:
            nonce = w3.eth.get_transaction_count(account)
            # bet certain amount based on the amount of price pool
            if current_round_info[8] >= 30 * 10 ** 18:
                check_payout_bet(1)
                claim()
                time.sleep(250)
            else:
                check_payout_bet(0.5)
                claim()
                time.sleep(250)

    except Exception as e:
        print(e)
        continue

    else:
        continue

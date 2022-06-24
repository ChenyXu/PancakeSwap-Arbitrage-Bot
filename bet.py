import json
from json.decoder import JSONDecodeError
import time
from web3 import Web3
from web3.middleware import geth_poa_middleware

w3 = Web3(Web3.HTTPProvider("https://silent-frosty-cherry.bsc.quiknode.pro/04bacb0dd8715e11376567a881a1af1e4a4dcb69/"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

account1 = '0x33A371cc7a6ca893280956bd25564C789A2557b3'
private_key = 'd6e9b8ec45c72c018cfbd8dbe2de4ef607adea55b0e43f5c21d6d88254d798bb'
nonce = w3.eth.get_transaction_count(account1)

address = '0x18B2A687610328590Bc8F2e5fEdDe3b582A49cdA'
abi = json.loads(
    '[{"inputs":[{"internalType":"address","name":"_oracleAddress","type":"address"},{"internalType":"address","name":"_adminAddress","type":"address"},{"internalType":"address","name":"_operatorAddress","type":"address"},{"internalType":"uint256","name":"_intervalSeconds","type":"uint256"},{"internalType":"uint256","name":"_bufferSeconds","type":"uint256"},{"internalType":"uint256","name":"_minBetAmount","type":"uint256"},{"internalType":"uint256","name":"_oracleUpdateAllowance","type":"uint256"},{"internalType":"uint256","name":"_treasuryFee","type":"uint256"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"BetBear","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"BetBull","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Claim","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"},{"indexed":true,"internalType":"uint256","name":"roundId","type":"uint256"},{"indexed":false,"internalType":"int256","name":"price","type":"int256"}],"name":"EndRound","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"},{"indexed":true,"internalType":"uint256","name":"roundId","type":"uint256"},{"indexed":false,"internalType":"int256","name":"price","type":"int256"}],"name":"LockRound","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"admin","type":"address"}],"name":"NewAdminAddress","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint256","name":"bufferSeconds","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"intervalSeconds","type":"uint256"}],"name":"NewBufferAndIntervalSeconds","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"minBetAmount","type":"uint256"}],"name":"NewMinBetAmount","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"operator","type":"address"}],"name":"NewOperatorAddress","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"oracle","type":"address"}],"name":"NewOracle","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint256","name":"oracleUpdateAllowance","type":"uint256"}],"name":"NewOracleUpdateAllowance","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"treasuryFee","type":"uint256"}],"name":"NewTreasuryFee","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"}],"name":"Pause","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"account","type":"address"}],"name":"Paused","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"rewardBaseCalAmount","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"rewardAmount","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"treasuryAmount","type":"uint256"}],"name":"RewardsCalculated","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"}],"name":"StartRound","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"token","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"TokenRecovery","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"TreasuryClaim","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"epoch","type":"uint256"}],"name":"Unpause","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"account","type":"address"}],"name":"Unpaused","type":"event"},{"inputs":[],"name":"MAX_TREASURY_FEE","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"adminAddress","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"epoch","type":"uint256"}],"name":"betBear","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"epoch","type":"uint256"}],"name":"betBull","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"bufferSeconds","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256[]","name":"epochs","type":"uint256[]"}],"name":"claim","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"claimTreasury","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"epoch","type":"uint256"},{"internalType":"address","name":"user","type":"address"}],"name":"claimable","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"currentEpoch","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"executeRound","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"genesisLockOnce","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"genesisLockRound","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"genesisStartOnce","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"genesisStartRound","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"uint256","name":"cursor","type":"uint256"},{"internalType":"uint256","name":"size","type":"uint256"}],"name":"getUserRounds","outputs":[{"internalType":"uint256[]","name":"","type":"uint256[]"},{"components":[{"internalType":"enum PancakePredictionV2.Position","name":"position","type":"uint8"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"bool","name":"claimed","type":"bool"}],"internalType":"struct PancakePredictionV2.BetInfo[]","name":"","type":"tuple[]"},{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getUserRoundsLength","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"intervalSeconds","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"address","name":"","type":"address"}],"name":"ledger","outputs":[{"internalType":"enum PancakePredictionV2.Position","name":"position","type":"uint8"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"bool","name":"claimed","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"minBetAmount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"operatorAddress","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"oracle","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"oracleLatestRoundId","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"oracleUpdateAllowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"pause","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"paused","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_token","type":"address"},{"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"recoverToken","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"epoch","type":"uint256"},{"internalType":"address","name":"user","type":"address"}],"name":"refundable","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"rounds","outputs":[{"internalType":"uint256","name":"epoch","type":"uint256"},{"internalType":"uint256","name":"startTimestamp","type":"uint256"},{"internalType":"uint256","name":"lockTimestamp","type":"uint256"},{"internalType":"uint256","name":"closeTimestamp","type":"uint256"},{"internalType":"int256","name":"lockPrice","type":"int256"},{"internalType":"int256","name":"closePrice","type":"int256"},{"internalType":"uint256","name":"lockOracleId","type":"uint256"},{"internalType":"uint256","name":"closeOracleId","type":"uint256"},{"internalType":"uint256","name":"totalAmount","type":"uint256"},{"internalType":"uint256","name":"bullAmount","type":"uint256"},{"internalType":"uint256","name":"bearAmount","type":"uint256"},{"internalType":"uint256","name":"rewardBaseCalAmount","type":"uint256"},{"internalType":"uint256","name":"rewardAmount","type":"uint256"},{"internalType":"bool","name":"oracleCalled","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_adminAddress","type":"address"}],"name":"setAdmin","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_bufferSeconds","type":"uint256"},{"internalType":"uint256","name":"_intervalSeconds","type":"uint256"}],"name":"setBufferAndIntervalSeconds","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_minBetAmount","type":"uint256"}],"name":"setMinBetAmount","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_operatorAddress","type":"address"}],"name":"setOperator","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_oracle","type":"address"}],"name":"setOracle","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_oracleUpdateAllowance","type":"uint256"}],"name":"setOracleUpdateAllowance","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_treasuryFee","type":"uint256"}],"name":"setTreasuryFee","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"treasuryAmount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"treasuryFee","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"unpause","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"uint256","name":"","type":"uint256"}],"name":"userRounds","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]')
contract = w3.eth.contract(address=address, abi=abi)


def betBull():
    transaction = contract.functions.betBull(current_epoch).buildTransaction({
        'chainId': 56,
        'from': account1,
        'gas': 250000,
        'gasPrice': w3.toWei(15, 'gwei'),
        'nonce': nonce,
        'value': w3.toWei(0.5, 'ether')
    })
    signed_tx = w3.eth.account.sign_transaction(transaction, private_key)
    data = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return data


def betBear():
    transaction = contract.functions.betBear(current_epoch).buildTransaction({
        'chainId': 56,
        'from': account1,
        'gas': 250000,
        'gasPrice': w3.toWei(15, 'gwei'),
        'nonce': nonce,
        'value': w3.toWei(0.5, 'ether')
    })
    signed_tx = w3.eth.account.sign_transaction(transaction, private_key)
    data = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return data


def bet():
    current_epoch = contract.functions.currentEpoch().call()
    current_round_info = contract.functions.rounds(current_epoch).call()
    current_total = current_round_info[8]
    current_bull = current_round_info[9]
    current_bear = current_round_info[10]
    EV_bull = current_total / current_bull /2 - 1.03
    EV_bear = current_total / current_bear /2 - 1.03

    if EV_bear >= 0.1:
        data = betBear()
        print('EV', EV_bear )
        print(current_epoch, 'bet bear for 0.5 bnb', data)

    elif EV_bull >= 0.1:
        data = betBull()
        print('EV', EV_bull)
        print(current_epoch, 'bet bull for 0.5 bnb', data)

    else:
        print(current_epoch, 'no bet')


while True:
    try:
        current_epoch = contract.functions.currentEpoch().call()
        current_round_info = contract.functions.rounds(current_epoch).call()
        current_locktimestamp = current_round_info[2]
        current_timestamp = w3.eth.get_block('latest')['timestamp']
        time_to_lock = current_locktimestamp - current_timestamp

        if 12 >= time_to_lock > 3:
            nonce = w3.eth.get_transaction_count(account1)
            try:
                bet()
                time.sleep(250)

            except:
                print('error')
                continue

    except JSONDecodeError as e:
        continue

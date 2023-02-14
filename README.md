# pancakeswap arbitrage bot

PancakeSwap has a price prediction game(https://pancakeswap.finance/prediction), and I notice that the payout of Bull and Bear often differ a lot. Therefore, there might be a small arbitrage opportunity. This bot bets and claims rewards automatically. 

You need a BSC address, its private key, and an RPC link for this bot. If you have prepared these items, put them in the key.py file accordingly. If you don't have a RPC link, you might use a public RPC listed here https://docs.bscscan.com/misc-tools-and-utilities/public-rpc-nodes. 

You need to download the liabaries(ccxt and web3) before running the main.py. You might want to set your preferred EV and betAmount paramters in the OnChain class.

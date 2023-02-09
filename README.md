# pancakeswap-arb bot

PancakeSwap has a price prediction game(https://pancakeswap.finance/prediction), and I notice that the payout of Bull and Bear often differ a lot. Apart from that, the chainlink price feed is slower than the Cex price update since the former feeds the price every 21 seconds while people trade BNB in Cex non-stop. Therefore, there might be a small arbitrage opportunity. This bot bets and claims rewards automatically. 

You need a BSC address, its private key, and an RPC link for this bot. If you have prepared these items, put them in the key.py file accordingly. If you don't have a RPC link, you might use a public RPC listed here https://docs.bscscan.com/misc-tools-and-utilities/public-rpc-nodes. 

This bot is my first web3 project which is for education purposes only. You must consider the risk before using this bot.

# pancakeswap arbitrage bot

PancakeSwap has a price prediction game(https://pancakeswap.finance/prediction), and I notice that the payout of Bull and Bear often differs a lot. Therefore, there might be a small arbitrage opportunity. This bot bets and claims rewards automatically. Data shows that the mean return is positive, usually above 15%, based on the config. However, the return variance can be very high, and consecutive losses can drain your fund quickly.

The distribution of EV ex post (the EV that take effect after betting, instead of the expected EV before betting) tends to look like this:
![Alt text]https://github.com/ChenyXu/PancakeSwap-Arbitrage-Bot/blob/main/effective%20ev%20%20distribution.png

You need a BSC address, its private key, and an RPC link for this bot. If you have prepared these items, put them in the key.py file accordingly. If you don't have an RPC link, you might use a public RPC listed here https://docs.bscscan.com/misc-tools-and-utilities/public-rpc-nodes. You also need to download the library web3 before running main.py. You should set your preferred EV and bet amount parameters.

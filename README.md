# pancakeswap arbitrage bot

PancakeSwap has a price prediction game(https://pancakeswap.finance/prediction), and I notice that the payout of Bull and Bear often differs a lot. Therefore, there might be a small arbitrage opportunity. This bot bets and claims rewards automatically. Data shows that the mean return is positive, usually above 15%, based on the config. P value for the null hypothesis (mean return = 0) is almost 0. However, our assumption that win rate is 50% for all the bets is not correct. Evidence shows that the higher the extra return, the lower the posibility of winning, which means that participants can predict the market to some extent. 

The distribution of EV ex post (the EV that takes effect after betting, instead of the expected EV before betting) tends to look like this:
![Alt text](https://github.com/ChenyXu/PancakeSwap-Arbitrage-Bot/blob/main/effective%20ev%20%20distribution.png)

You need a BSC address, its private key, and an RPC link for this bot. If you have prepared these items, put them in the key.py file accordingly. If you don't have an RPC link, you might use a public RPC listed here https://docs.bscscan.com/misc-tools-and-utilities/public-rpc-nodes. You also need to download the library web3 before running main.py. You should set your preferred EV and bet amount parameters.

This is an project for education purpose. The chance of winning money by running this bot, is very small. 

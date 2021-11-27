# -*- coding: utf-8 -*- 
import datetime

import pandas as pd
                 
from ltsim.model import leveraged_token_model

# number of leveraged tokens on issue (constant over time)
n_tokens_issued = 1

# target leverage for the leveraged token to maintain
target_leverage = 3

# annual percentage borrowing rate
borrow_rate = 40

# Loan to value threshold before position is liquidated
liq_thresh = 99

# percentage of collateral that is forfeit as premium to liquidators
liq_premium = 20

# minimum allowable leverage before emergency rebalance is triggered
min_leverage = 2.4

# maximum allowable leverage before emergency rebalance is triggered
max_leverage = 3.5

# minimum number of timesteps before emergency rebalance is executed
congestion_time = 2

# number of timesteps between periodic rebalances
rebalance_interval = 1

# absolute change in leverage for each rebalance
recentering_speed = 0.01

# max trade vol, max slippage, trade delay for periodic rebalancing
trade_params_periodic = (1e9, 4, 1)

# max trade vol, max slippage, trade delay for emergency rebalancing
trade_params_emergency = (1e9, 4, 1)

# percentage fee charged on swaps
swap_fee = 0.3

# arbitrage effectiveness, time to reach effectiveness
arb_params = (99, 1)

# price at each timestep
prices = [100, 105, 110, 115, 120, 125]

# dates for each timestep - these can be omitted if not required
dates = [datetime.datetime(2021, 1, d) for d in range(1,len(prices)+1)]

# price dataframe
price_data = pd.DataFrame({'DATE':dates,
                           'PRICE':prices})

# token pool balances for the Terra Swap (or constant product like DEX) 

# UST balance
pool_x = [1e9] * len(prices)

# token balance
pool_y = [px / price for price, px in zip(prices, pool_x) ]

# pool balance dataframe
pool_liquidity = pd.DataFrame({'DATE':dates,
                               'pool_x_i':pool_x,
                               'pool_y_i':pool_y})

# model results are provided as a dataframe.
res = leveraged_token_model(price_data,
                            pool_liquidity,
                            target_leverage,
                            min_leverage, 
                            max_leverage,
                            congestion_time, 
                            rebalance_interval,
                            recentering_speed,
                            trade_params_periodic,
                            trade_params_emergency,
                            borrow_rate,
                            liq_thresh,
                            liq_premium,
                            n_tokens_issued,
                            swap_fee,
                            arb_params)

# -*- coding: utf-8 -*-
from ltsim import execute_trades

"""
Example simulation for executing a series of trades on TerraSwap. Captures
assumed extent of arbitrage that restores AMM prices.
"""


# Balances of pool tokens - x (UST), y (LUNA)
pool_liquidity = {'pool_x_i': 30160053 , 'pool_y_i':659723}

token_price = 30160053 / 659723

# Maximum percentage slippage 
max_slippage = 2

# Time between each trade
trade_delay = 1

# Effectiveness of arbitrageurs in restoring AMM prices to their pre
# trade state. 
arb_effectiveness = 0.9

# Time required for arb_effectiveness to be reached. 
arb_time = 1

# Percentage fee charged by exchange
trading_fee = 0.3 / 100


# Trade example #1 -  UST to LUNA

# Total volume offered for trade (UST)
trade_vol = 75000 * 10

# Maximum volume of each trade
max_trade = 75000

vol_received = execute_trades(trade_vol, max_trade, max_slippage, trade_delay,
                              arb_effectiveness, arb_time, pool_liquidity, token_price,
                              trading_fee)

print(f'Offered {trade_vol} UST, received {vol_received} UST')


# Trade example #2 - LUNA to UST

# Total UST value of LUNA offered for trade
trade_vol = - 75000 * 10

# Maximum volume of each trade
max_trade = 75000

vol_received = execute_trades(trade_vol, max_trade, max_slippage, trade_delay,
                              arb_effectiveness, arb_time, pool_liquidity, token_price,
                              trading_fee)

print(f'Offered {trade_vol} LUNA, received {vol_received} LUNA')

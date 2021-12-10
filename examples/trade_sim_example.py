# -*- coding: utf-8 -*-
from ltsim import execute_trades

"""
Example simulation for executing a series of trades on TerraSwap. Captures
assumed extent of arbitrage that restores AMM prices.
"""

# Balances of pool tokens - x (UST), y (LUNA)
pool_liquidity = {'pool_x_i': 30160053 , 'pool_y_i':659723}

token_price = 30160053 / 659723

# Maximum percentage slippage allowed to accept trade
max_slippage = 3

# Minimum amount of time between each trade
trade_delay = 1

# Effectiveness of arbitrageurs in restoring AMM prices to their pre
# trade state.
arb_effectiveness = 95

# Time required for arb_effectiveness to be reached.
arb_time = 3

# Percentage fee charged by exchange
trading_fee = 0.3

# Trade example #1 -  UST to LUNA

# Total volume offered for trade (UST)
trade_vol = 75000 * 10

# Maximum volume of each trade
max_trade = 75000

vol_received = execute_trades(trade_vol, max_trade, max_slippage, trade_delay,
                              arb_effectiveness, arb_time, pool_liquidity,
                              trading_fee)

print(f'Offered {vol_received[1]:.1f} UST, received {vol_received[0]:.1f} UST, '
      f'paid {vol_received[2]:.1f} in fees and lost {vol_received[3]:.1f} due to slippage')


# Trade example #2 - LUNA to UST

# Total UST value of LUNA offered for trade
trade_vol = - 95000 * 10

# Maximum volume of each trade
max_trade = 95000

vol_received = execute_trades(trade_vol, max_trade, max_slippage, trade_delay,
                              arb_effectiveness, arb_time, pool_liquidity,
                              trading_fee)

print(f'Offered {-vol_received[1]:.1f} UST worth of LUNA, received {-vol_received[0]:.1f} UST, '
      f'paid {vol_received[2]:.1f} in fees and lost {vol_received[3]:.1f} due to slippage')

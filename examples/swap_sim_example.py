# -*- coding: utf-8 -*-
from ltsim import sim_swap

"""
This script runs example swap simulations based on real trades,
and TerraSwap Pool conditions at the time of trade.
"""

# Terra Swap fee proportion
perc_fee = 0.3 / 100
    
# LUNA trades
pool_x, pool_y = 30123576.064800,  691626.375367

# (UST -> LUNA)
# https://finder.terra.money/mainnet/tx/52088AC08124630A7AD5C1A966697E8A6125210B36A4AE8C9A35AB9BF0F45C80

delta_x = 940

delta_y = delta_x * (pool_y / pool_x)

res_lu_1 = sim_swap(delta_x, delta_y, pool_x, pool_y, perc_fee)

# MIR trades
pool_x, pool_y = 30307424.731656,  10982636.155309

# (UST -> MIR)
# https://finder.terra.money/mainnet/tx/68B71489AF3B05EB679221A367633769F1E95B553FC5ABB237DCC4C572E49EDB

delta_x = 14000

delta_y = delta_x * (pool_y / pool_x)

res_mir_1 = sim_swap(delta_x, delta_y, pool_x, pool_y, perc_fee)

# ANC trades
pool_x, pool_y = 146440951.902936,  46345672.171992

# (UST -> ANC)
# https://finder.terra.money/mainnet/tx/028821BAB5DE9E83C67DB908A4E1714F9A382517B079E6F8AA9D1749952D63BB

delta_x = 2161.613117

delta_y = delta_x * (pool_y / pool_x)

res_anc_1 = sim_swap(delta_x, delta_y, pool_x, pool_y, perc_fee)

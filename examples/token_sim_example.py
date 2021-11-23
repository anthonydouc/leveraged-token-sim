# -*- coding: utf-8 -*-
from ltsim.data import get_all_model_data, get_model_data
                  
from ltsim.model import leveraged_token_model

no_tokens_start = 1

borrow_rate = 40
liq_thresh = 80
liq_premium = 20

min_leverage = 1.5
max_leverage = 2.5
congestion_time = 2
target_leverage = 2 

rebalance_frequency = 24
recentering_speed = 5

# max trade vol, max slippage, trade delay for periodic rebalancing
trade_params_periodic = (1e9, 4, 1)

# max trade vol, max slippage, trade delay for emergency rebalancing
trade_params_emergency = (1e9, 4, 1)

# fee charged on swaps
swap_fee = 0.3

# arbitrage effectiveness, time to reach effectiveness
arb_params = (90, 1)

token = 'MIR'

# read in price and pool balance data
all_price_data, all_pool_liquidity = get_all_model_data()

price_data, pool_liquidity = get_model_data(all_price_data, 
                                            all_pool_liquidity,
                                            token) 

# model results are provided as a dataframe.
res = leveraged_token_model(price_data,
                            pool_liquidity,
                            target_leverage,
                            min_leverage, 
                            max_leverage,
                            congestion_time, 
                            rebalance_frequency,
                            recentering_speed,
                            trade_params_periodic,
                            trade_params_emergency,
                            borrow_rate,
                            liq_thresh,
                            liq_premium,
                            no_tokens_start,
                            swap_fee,
                            arb_params)

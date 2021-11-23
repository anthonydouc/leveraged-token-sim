# -*- coding: utf-8 -*-
from ltsim.data import get_all_model_data, get_model_data
                  
from ltsim.model import leveraged_token_model

buy_date = 0

no_tokens_start = 1
no_tokens_growth = 0

borrow_rate = 4
liq_thresh = 1.2
liq_premium = 0.2

min_leverage = 1.5
max_leverage = 2.5
congestion_time = 24
target_leverage = 2

rebalance_frequency = 24  # no.days
recentering_speed = 5 # time horizon for rebalancing

trade_fee = 0.3 # percentage fee for trading

protocol_fee = 0 # daily percentage fee for everything else


# max trade vol, max slippage, trade delay
trade_params_periodic = (1e9, 4, 1)

trade_params_emergancy = (1e9, 4, 1)

token = 'LUNA'

all_price_data, all_pool_liquidity = get_all_model_data()

price_data, pool_liquidity = get_model_data(all_price_data, 
                                            all_pool_liquidity,
                                            token) 
arb_params = (0.9, 1)

data = leveraged_token_model(price_data,
                             target_leverage,
                             min_leverage, 
                             max_leverage,
                             congestion_time, 
                             rebalance_frequency,
                             recentering_speed,
                             trade_params_periodic,
                             trade_params_emergancy,
                             borrow_rate,
                             liq_thresh,
                             liq_premium,
                             no_tokens_start,
                             no_tokens_growth, 
                             trade_fee,
                             arb_params,
                             pool_liquidity)

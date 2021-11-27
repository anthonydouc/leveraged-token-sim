# -*- coding: utf-8 -*-
import datetime

from ltsim.data import get_all_model_data, get_model_data
                  
from ltsim.model import leveraged_token_model

# number of leveraged tokens on issue (constant over time)
n_tokens_issued = 1

# target leverage for the leveraged token to maintain
target_leverage = 2

# annual percentage borrowing rate
borrow_rate = 40

# Loan to value threshold before position is liquidated
liq_thresh = 90

# percentage of collateral that is forfeit as premium to liquidators
liq_premium = 20

# minimum allowable leverage before emergency rebalance is triggered
min_leverage = 2.4

# maximum allowable leverage before emergency rebalance is triggered
max_leverage = 3.5

# minimum number of timesteps before emergency rebalance is executed
congestion_time = 2

# number of timesteps between periodic rebalances
rebalance_interval = 2

# absolute change in leverage for each rebalance
recentering_speed = 0.1

# max trade vol, max slippage, trade delay for periodic rebalancing
trade_params_periodic = (1e9, 4, 1)

# max trade vol, max slippage, trade delay for emergency rebalancing
trade_params_emergency = (1e9, 4, 1)

# percentage fee charged on swaps
swap_fee = 0.3

# arbitrage effectiveness, time to reach effectiveness
arb_params = (99, 1)


# read data from FLipside API. This only requires specifying the token we 
# want to use, and optionally a UTC date range for the data to use.

token = 'LUNA' # can be one of LUNA/MIR/ANC

min_date = datetime.datetime(2021, 4, 1, tzinfo=datetime.timezone.utc)

max_date = datetime.datetime(2021, 6, 1, tzinfo=datetime.timezone.utc)

# read in hourly price and pool balance data for all tokens
all_price_data, all_pool_liquidity = get_all_model_data()

# read in price and pool balance data for the specified token and dates
price_data, pool_liquidity = get_model_data(all_price_data, 
                                            all_pool_liquidity,
                                            token,
                                            min_date,
                                            max_date) 

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

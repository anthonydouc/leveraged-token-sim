# -*- coding: utf-8 -*-
import os

import numpy as np
import pandas as pd

from .trade_sim import execute_trades

dir_path = os.path.dirname(os.path.realpath(__file__))

def calc_drawdown(data):
    
    data = pd.Series(data)
    
    cummax_data = data.cummax()
    
    return (data - cummax_data) / data

def calc_n_tokens_linear(n_int, n_grad, nt):
    return np.linspace(0, nt-1, nt) * n_grad + n_int

def calc_rebal_lev(leverage, target_leverage, recentering_speed,
                   max_leverage, min_leverage):

    rebalance_leverage = ((1 - recentering_speed / 100) * target_leverage
                              + (recentering_speed / 100) * leverage)

    rebalance_leverage = max(min_leverage, min(max_leverage, rebalance_leverage))

    return rebalance_leverage

def is_periodic_rebal_allowed(t, last_rebalanced, rebalance_interval):
    return t >= last_rebalanced + rebalance_interval

def leveraged_token_model(price_data, pool_liquidity_data,
                          target_leverage, min_leverage,
                          max_leverage, congestion_time,
                          rebalance_interval, recentering_speed,
                          trade_params_periodic, trade_params_emergency,
                          borrow_rate, liq_thresh, liq_premium,
                          n_tokens_start, swap_fee, arb_params):
    """
    

    Parameters
    ----------
    price_data : TYPE
        DESCRIPTION.
    pool_liquidity_data : TYPE
        DESCRIPTION.
    target_leverage : TYPE
        DESCRIPTION.
    min_leverage : TYPE
        DESCRIPTION.
    max_leverage : TYPE
        DESCRIPTION.
    congestion_time : TYPE
        DESCRIPTION.
    rebalance_interval : TYPE
        DESCRIPTION.
    recentering_speed : TYPE
        DESCRIPTION.
    trade_params_periodic : TYPE
        DESCRIPTION.
    trade_params_emergency : TYPE
        DESCRIPTION.
    borrow_rate : TYPE
        DESCRIPTION.
    liq_thresh : TYPE
        DESCRIPTION.
    liq_premium : TYPE
        DESCRIPTION.
    n_tokens_start : TYPE
        DESCRIPTION.
    swap_fee : TYPE
        DESCRIPTION.
    arb_params : TYPE
        DESCRIPTION.

    Returns
    -------
    data : TYPE
        DESCRIPTION.

    """
    price = price_data['PRICE'].values

    dates = price_data['DATE'].values
    
    hours = price_data['DATE'].dt.hour.values

    nt = len(price)

    # total (net) number of leveraged tokens issued over time
    # equal to expected cummulative (subscriptions - redemptions)
    n_tokens = calc_n_tokens_linear(n_tokens_start, 0, nt)

    # number of underlying tokens per leveraged token
    n_underlying = np.zeros(nt)

    # amount borrowed ($) per leveraged token
    borrowed = np.zeros(nt)

    # actual leverage ratio per leveraged token
    leverage = np.zeros(nt)

    # target rebalance amount ($) per leveraged token
    target_rebalance_amount = np.zeros(nt)
    
    # actual rebalance amount ($) per leveraged token
    rebalance_amount = np.zeros(nt)
    
    # boolean variable tracking if emergency rebalance was executed
    emergency_rebalances = np.zeros(nt)
    
    # boolean variable tracking if periodic rebalance was executed
    periodic_rebalances = np.zeros(nt)

    # cummulative duration of time where leverage remains out of bounds
    exceedance_time = np.zeros(nt)
    
    # loan to value ratio
    ltv = np.zeros(nt)
    
    # amount liquidated
    liquidation_amount = np.zeros(nt)

    n_underlying[0:] = target_leverage

    borrowed[0:] = price[0] * (target_leverage - 1)

    last_rebalanced = - 100

    for t in range(nt):
        
        if borrowed[t] > 0:
            ltv[t] = borrowed[t] / (n_underlying[t] * price[t])
        else:
            ltv[t] = np.nan
        
        # liquidation occurs when asset_value / borrowed < liquidation_threshold
        if ltv[t] >= liq_thresh / 100:
            
            # balance before liquidation
            balance_before = n_underlying[t] * price[t] - borrowed[t]
            
            # premium amount claimed by liquidators 
            liquidation_amount[t] = balance_before * liq_premium / 100
            
            # remaining balance after liquidation
            balance_after = balance_before - liquidation_amount[t]
            
            if balance_after <= 0:
                # all issued leveraged tokens are now worth 0 and removed
                n_underlying[t] = 0
                borrowed[t] = 0
            else:
                # % of position value is liquidated and lost.
                # remaining is used to reconstruct tokens based on target leverage
                n_underlying[t:] = balance_after / price[t]
                borrowed[t:] = 0

        current_value = n_underlying[t] * price[t]

        leverage[t] = current_value / (current_value - borrowed[t])

        outside_lev_range = (leverage[t] < min_leverage) | (leverage[t] > max_leverage)

        # Continuous duration that leverage bounds are exceeded for
        if outside_lev_range:
            exceedance_time[t] = 1 + exceedance_time[t-1]
        else:
            exceedance_time[t] = 0

        emergency_rebal_allowed = (outside_lev_range
                                   & (exceedance_time[t] >= congestion_time))

        periodic_rebal_allowed = is_periodic_rebal_allowed(t, last_rebalanced,
                                                           rebalance_interval)
        
        rebal_allowed = ((leverage[t] != target_leverage)
                         and (n_tokens[t] > 0)
                         and (n_underlying[t] > 1e-3)
                         and (emergency_rebal_allowed or periodic_rebal_allowed))

        if rebal_allowed:

            rebalance_leverage = calc_rebal_lev(leverage[t], target_leverage,
                                                recentering_speed, max_leverage,
                                                min_leverage)

            # required change in borrowing for rebalancing
            delta_borrow = (rebalance_leverage * (current_value - borrowed[t])
                            - current_value)

            if emergency_rebal_allowed:
                trade_params = trade_params_emergency
                emergency_rebalances[t] = 1

            elif periodic_rebal_allowed:
                trade_params = trade_params_periodic
                periodic_rebalances[t] = 1
                last_rebalanced = t

            # TODO: maybe change delta borrow to tokens as opposed to USD.
            pool_liquidity = pool_liquidity_data.iloc[t][['pool_x_i','pool_y_i']].to_dict()

            target_rebalance_amount[t] = n_tokens[t] * delta_borrow
            
            rebalance_amount[t] = execute_trades(n_tokens[t] * delta_borrow,
                                                 *trade_params,
                                                 *arb_params,
                                                 pool_liquidity,
                                                 swap_fee)

        # Adjust debt and underlying token positions based on rebalancing
        # amount
        borrowed[t:] += rebalance_amount[t] / n_tokens[t]

        n_underlying[t:] += rebalance_amount[t] / n_tokens[t] / price[t]

        # Debt interest accural
        borrowed[t] *= (1 + borrow_rate / 100 / 365 / 24)

    # hourly value of the leveraged token
    lt_value = (n_underlying * price - borrowed)
    
    # running drawdown for underlying token price
    drawdown_underlying = calc_drawdown(price)
    
    # running drawdown for leveraged token value
    drawdown_lt = calc_drawdown(lt_value)

    min_leverage_arr = np.zeros(nt) + min_leverage

    max_leverage_arr = np.zeros(nt) + max_leverage

    # hour on hour change in leveraged token value 
    hourly_return = np.zeros(len(lt_value))
    
    # percentage daily return
    hourly_return_perc = np.zeros(len(lt_value))

    # cummulative change in leveraged token value
    cummulative_return = np.zeros(len(lt_value))
    
    # percentage cummulative change
    cummulative_return_perc = np.zeros(len(lt_value))

    hourly_return[1:] = (lt_value[1:] - lt_value[:-1])
    
    hourly_return_perc[1:] = (lt_value[1:] - lt_value[:-1]) / lt_value[:-1]

    cummulative_return[1:] = (lt_value[1:] - lt_value[0])
    
    cummulative_return_perc[1:] = (lt_value[1:] - lt_value[0]) / lt_value[0]

    res = pd.DataFrame({'date': dates,
                        'hour': hours,
                        'underlying_token_price': price,
                        'leveraged_token_value': lt_value,
                        'drawdown_underlying': drawdown_underlying,
                        'drawdown_leveraged': drawdown_lt,
                        'n_tokens_per_lt': n_underlying,
                        'underlying_value_per_lt': n_underlying * price,
                        'debt_per_lt': borrowed,
                        'leverage': leverage,
                        'total_underlying_value': n_tokens * n_underlying * price,
                        'total_debt': n_tokens * borrowed,
                        'hourly_return': hourly_return,
                        'hourly_return_perc': hourly_return_perc,
                        'cummulative_return': cummulative_return,
                        'cummulative_return_perc': cummulative_return_perc,
                        'target_rebalance_amount': target_rebalance_amount,
                        'rebalance_amount': rebalance_amount,
                        'loan_to_value_ratio': ltv,
                        'liquidation_amount': liquidation_amount,
                        'emergency_rebalance': emergency_rebalances,
                        'periodic_rebalance': periodic_rebalances,
                        'min_leverage_arr': min_leverage_arr,
                        'max_leverage_arr': max_leverage_arr})
    return res

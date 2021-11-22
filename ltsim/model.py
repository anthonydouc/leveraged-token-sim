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

def is_periodic_rebal_allowed(t, last_rebalanced, rebalance_frequency):
    return t >= last_rebalanced + rebalance_frequency

def leveraged_token_model(price_data, target_leverage, min_leverage,
                          max_leverage, congestion_time,
                          rebalance_frequency, recentering_speed,
                          trade_params_periodic, trade_params_emergancy,
                          borrow_rate, liq_thresh,
                          liq_fee, no_tokens_start,
                          no_tokens_growth, trading_fee,
                          arb_params, pool_liquidity_data):
    """
    Parameters
    ----------
    token : str
        DESCRIPTION.
    target_leverage : float
        DESCRIPTION.
    min_leverage : float
        DESCRIPTION.
    max_leverage : float
        DESCRIPTION.
    rebalance_frequency : float
        DESCRIPTION.
    recentering_speed : float
        DESCRIPTION.

    Returns
    -------
    data : TYPE
        DESCRIPTION.

    """

    price = price_data['AVG_PRICE'].values

    dates = price_data['DATE'].values

    nt = len(price)

    # total (net) number of leveraged tokens issued over time
    # equal to expected cummulative (subscriptions - redemptions)
    no_tokens = calc_n_tokens_linear(no_tokens_start, no_tokens_growth, nt)

    # number of underlying tokens per leveraged token
    n_underlying = np.zeros(nt)

    # amount borrowed ($) per leveraged token
    borrowed = np.zeros(nt)

    # actual leverage ratio per leveraged token
    leverage = np.zeros(nt)

    # rebalance amount ($) per leveraged token
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
            ltv[t] = n_underlying[t] * price[t] / borrowed[t]
        else:
            ltv[t] = np.nan
        
        balance_before = n_underlying[t] * price[t] - borrowed[t]
        # liquidation occurs when asset_value / borrowed < liquidation_threshold
        if ltv[t] <= liq_thresh:
            liquidation_amount[t] = balance_before * liq_fee
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

        emergancy_rebal_allowed = (outside_lev_range
                                   & (exceedance_time[t] >= congestion_time))

        periodic_rebal_allowed = is_periodic_rebal_allowed(t, last_rebalanced,
                                                           rebalance_frequency)
        
        rebal_allowed = ((leverage[t] != target_leverage)
                         and (no_tokens[t] > 0)
                         and (emergancy_rebal_allowed or periodic_rebal_allowed))

        if rebal_allowed:

            rebalance_leverage = calc_rebal_lev(leverage[t], target_leverage,
                                                recentering_speed, max_leverage,
                                                min_leverage)

            # required change in borrowing for rebalancing
            delta_borrow = (rebalance_leverage * (current_value - borrowed[t])
                            - current_value)

            if emergancy_rebal_allowed:
                trade_params = trade_params_emergancy
                emergency_rebalances[t] = 1

            elif periodic_rebal_allowed:
                trade_params = trade_params_periodic
                periodic_rebalances[t] = 1
                last_rebalanced = t

            # TODO: maybe change delta borrow to tokens as opposed to USD.
            pool_liquidity = pool_liquidity_data.iloc[t][['pool_x_i','pool_y_i']].to_dict()

            rebalance_amount[t] = execute_trades(no_tokens[t] * delta_borrow,
                                                 *trade_params,
                                                 *arb_params,
                                                 pool_liquidity,
                                                 price[t],
                                                 trading_fee / 100)

        # Adjust debt and underlying token positions based on rebalancing
        # amount
        borrowed[t:] += rebalance_amount[t] / no_tokens[t]

        n_underlying[t:] += rebalance_amount[t] / no_tokens[t] / price[t]

        # Debt interest accural
        borrowed[t] *= (1 + borrow_rate / 100 / 365 / 24)

    actual_value = (n_underlying * price - borrowed)

    min_leverage_arr = np.zeros(nt) + min_leverage

    max_leverage_arr = np.zeros(nt) + max_leverage

    # hour on hour change in leveraged token value 
    daily_return = np.zeros(len(actual_value))
    
    # percentage daily return
    daily_return_perc = np.zeros(len(actual_value))

    # cummulative change in leveraged token value
    cummulative_return = np.zeros(len(actual_value))
    
    # percentage cummulative change
    cummulative_return_perc = np.zeros(len(actual_value))

    daily_return[1:] = (actual_value[1:]  - actual_value[:-1])
    
    daily_return_perc[1:] = (actual_value[1:]  - actual_value[:-1]) / actual_value[:-1]

    cummulative_return[1:] = (actual_value[1:]  - actual_value[0])
    
    cummulative_return_perc[1:] = (actual_value[1:]  - actual_value[0]) / actual_value[0]

    drawdown_asset = calc_drawdown(price)
    
    drawdown_token = calc_drawdown(actual_value)
    
    data = pd.DataFrame({'date': dates,
                         'asset_price': price,
                         'actual_value': actual_value,
                         'drawdown_asset': drawdown_asset,
                         'drawdown_token': drawdown_token,
                         'actual_leverage': leverage,
                         'amount_borrowed': borrowed,
                         'total_borrowed': no_tokens * borrowed,
                         'total_trade': rebalance_amount,
                         'tokens': n_underlying,
                         'total_value': n_underlying * price,
                         'total_nav': no_tokens * n_underlying * price,
                         'daily_return': daily_return,
                         'daily_return_perc': daily_return_perc,
                         'cummulative_return': cummulative_return,
                         'cummulative_return_perc': cummulative_return_perc,
                         'loan_to_value_ratio': ltv,
                         'liquidation_amount': liquidation_amount,
                         'emergency_rebalance': emergency_rebalances,
                         'periodic_rebalance': periodic_rebalances,
                         'min_leverage_arr': min_leverage_arr,
                         'max_leverage_arr': max_leverage_arr})
    return data

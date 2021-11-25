# -*- coding: utf-8 -*-
import os

import numpy as np
import pandas as pd

from .trade_sim import execute_trades

dir_path = os.path.dirname(os.path.realpath(__file__))

def calc_drawdown(data):
    
    data = pd.Series(data)
    
    cummax_data = data.cummax()
    
    return (data - cummax_data) / cummax_data

def calc_rebal_lev(leverage, target_leverage, recentering_speed):

    if leverage > target_leverage:
        rebalance_leverage = max(target_leverage, leverage - recentering_speed)
    else:
        rebalance_leverage = min(target_leverage, leverage + recentering_speed)

    return rebalance_leverage

def is_periodic_rebal_allowed(t, last_rebalanced, rebalance_interval):
    return t >= last_rebalanced + rebalance_interval

def leveraged_token_model(price_data, pool_liquidity_data,
                          target_leverage, min_leverage,
                          max_leverage, congestion_time,
                          rebalance_interval, recentering_speed,
                          trade_params_periodic, trade_params_emergency,
                          borrow_rate, liq_thresh, liq_premium,
                          n_tokens_issued, swap_fee, arb_params):
    """
    Simulates the performance of leveraged tokens managed through a combination
    of periodic and emergency leverage rebalancing rules.

    Parameters
    ----------
    price_data : pd.DataFrame
        Ordered token prices at each timestep.
    pool_liquidity_data : pd.DataFrame
        Ordered UST and token pool balances at each timestep.
    target_leverage : float
        Target leverage for the leveraged token to maintain.
    min_leverage : float
        Minimum allowable leverage before emergency rebalance is triggered.
    max_leverage : float
        Maximum allowable leverage before emergency rebalance is triggered.
    congestion_time : float
        Minimum number of timesteps before emergency rebalance is executed.
    rebalance_interval : int
        Number of timesteps between periodic rebalances.
    recentering_speed : float
        Absolute change in leverage for each rebalance.
    trade_params_periodic : tuple
        A tuple with the parameters (max_trade_vol, max_slippage, trade_delay)
        for periodic rebalancing.
    trade_params_emergency : tuple
        A tuple with the parameters (max_trade_vol, max_slippage, trade_delay)
        for emergency rebalancing.
    borrow_rate : float
        Annual percentage borrowing rate.
    liq_thresh : float
        Loan to value threshold before position is liquidated.
    liq_premium : float
        Percentage of collateral that is forfeit as premium to liquidators.
    n_tokens_issued : int
        Number of leveraged tokens on issue (constant over time).
    swap_fee : float
        Percentage fee charged by the DEX for swaps.
    arb_params : tuple
        A tuple containing the params (arb_effectiveness, arb_time).

    Returns
    -------
    data : pd.DataFrame
        Dataframe containing key model variables.

    """
    price = price_data['PRICE'].values

    try:
        dates = price_data['DATE'].values
    except:
        dates = np.arange(0, len(price))
    
    try:
        hours = price_data['DATE'].dt.hour.values
    except:
        hours = np.zeros(len(price))

    nt = len(price)

    # total (net) number of leveraged tokens issued over time
    # equal to expected cummulative (subscriptions - redemptions)
    n_tokens = np.zeros(nt) + n_tokens_issued

    # number of underlying tokens per leveraged token
    n_underlying = np.zeros(nt)

    # amount borrowed ($) per leveraged token
    borrowed = np.zeros(nt)

    # actual leverage ratio per leveraged token
    leverage = np.zeros(nt)

    # target rebalance amount ($) for all issued leveraged tokens
    target_rebalance_amount = np.zeros(nt)
    
    # actual rebalance amount ($) for all issued leveraged tokens
    rebalance_amount = np.zeros(nt)
    
    # swap fees paid ($) for all issued leveraged tokens
    swap_fees = np.zeros(nt)
    
    # spread value ($) for all issued leveraged tokens
    swap_spread = np.zeros(nt)
    
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
        
        # liquidation logic
        if ltv[t] >= liq_thresh / 100:
            
            # balance before liquidation
            collateral_before = n_underlying[t] * price[t] - borrowed[t]
            
            # premium amount claimed by liquidators 
            liquidation_amount[t] = collateral_before * liq_premium / 100
            
            # remaining balance after liquidation
            collateral_after = collateral_before - liquidation_amount[t]
            
            if collateral_after <= 0:
                # all issued leveraged tokens are now worth 0 and removed
                n_underlying[t] = 0
                borrowed[t] = 0
            else:
                # % of position value is liquidated and lost.
                # remaining is used to reconstruct tokens based on target leverage
                n_underlying[t:] = collateral_after / price[t]
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
            # leverage target for rebalancing
            rebalance_leverage = calc_rebal_lev(leverage[t], target_leverage,
                                                recentering_speed)
            
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

            pool_liquidity = pool_liquidity_data.iloc[t][['pool_x_i','pool_y_i']].to_dict()

            target_rebalance_amount[t] = n_tokens[t] * delta_borrow
            
            trade = execute_trades(n_tokens[t] * delta_borrow,
                                   *trade_params,
                                   *arb_params,
                                   pool_liquidity,
                                   swap_fee)

            rebalance_amount[t] = trade[0]
            
            swap_fees[t] = trade[1]
            
            swap_spread[t] = trade[2]

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
                        'swap_fees' : swap_fees,
                        'swap_spread': swap_spread,
                        'loan_to_value_ratio': ltv,
                        'liquidation_amount': n_tokens * liquidation_amount,
                        'emergency_rebalance': emergency_rebalances,
                        'periodic_rebalance': periodic_rebalances,
                        'min_leverage_arr': min_leverage_arr,
                        'max_leverage_arr': max_leverage_arr})
    return res

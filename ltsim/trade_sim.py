# -*- coding: utf-8 -*-
import numpy as np

def sim_swap(delta_x, delta_y, pool_x, pool_y, perc_fee):
    """
    Computes the expected receive, spread and commision amounts for 
    Terra Swap style pools (constant product). Based on 
    https://docs.terraswap.io/docs/introduction/mechanism/
    
    
    Parameters
    ----------
    delta_x : float
        Amount of token x being offered.
    delta_y : float
        Amount of token y being offered.
    pool_x : float
        Balance (number of tokens) for token x.
    pool_y : float
        Balance (number of tokens) for token y.
    perc_fee : float
        Percentage fee charged by the exchange for executing a swap.

    """
    if delta_x > 0 :
        ask = abs(delta_y)
        out = delta_x * pool_y / (delta_x + pool_x)
    elif delta_x < 0 :
        ask = abs(delta_x)
        out = delta_y * pool_x / (delta_y + pool_y)
    received  = out  * (1 - perc_fee / 100)
    return received, 100 * (ask - out) / ask
    
def sim_trades(delta_x, max_slippage, time_delay, arb_effectiveness, arb_time, 
               pool_x_i, pool_y_i, perc_fee):
    """
    Occurs within each simulation timestep. E.g. if timestep is 1 hour,
    this considers n sub timesteps based on time delay.
    
    pool_x_i and pool_y_i could be arrays or floats / ints.

    Parameters
    ----------
    max_slippage : TYPE
        DESCRIPTION.
    time_delay : TYPE
        DESCRIPTION.
    arb_effectiveness : TYPE
        DESCRIPTION.
    arb_time : TYPE
        DESCRIPTION.
    pool_x_i : TYPE
        DESCRIPTION.
    pool_y_i : TYPE
        DESCRIPTION.

    Returns
    -------

    """
    # lets assume this is based on AMM price. TODO: THIS IS OK FOR SPREAD, BUT WE NEED TO REVERT BACK.
    delta_y = - delta_x / (pool_x_i / pool_y_i)
    
    nt = len(delta_x)
    
    pool_x = np.zeros(nt) + pool_x_i
    
    pool_y = np.zeros(nt) + pool_y_i
    
    trade_actual = np.zeros(nt)
    
    for t in range(nt):
        received, perc_spread = sim_swap(delta_x[t], delta_y[t], 
                                         pool_x[t], pool_y[t], perc_fee)

        if perc_spread < max_slippage:
    
            arb_offset = (1 - arb_effectiveness / 100) * max(1, (time_delay / arb_time))
            
            pool_x[t:] += delta_x[t]  * arb_offset
        
            pool_y[t:] += delta_y[t]  * arb_offset

            trade_actual[t] = received
            
    return trade_actual

def execute_trades(trade_vol, max_trade, max_slippage, trade_delay,
                   arb_effectiveness, arb_time, pool_liquidity, token_price,
                   trading_fee):
    """
    Attempts to execute trades based on estimated trade slippage.
    Trades are simulated and occur within 1 simulation timestep:
        - During this time step, oracle prices are assumed to remain constant
        - The cummulative spread effect on trades is captured based on
        - pool liquidity and assumed arbitrage effectiveness.

    Parameters
    ----------
    trade_vol : TYPE
        DESCRIPTION.
    max_slippage : TYPE
        DESCRIPTION.
    max_trade : TYPE
        DESCRIPTION.
    cooldown : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """

    # swap direction:
    # if +ve: borrowing more UST and swapping UST for token
    # if -ve: borrowing less UST and swapping token for UST
    direction = abs(trade_vol) / trade_vol

    # number of max_volume trades 
    n = int(abs(trade_vol) // max_trade)

    # remainder volume (assume to be last trade)
    rem_vol = abs(trade_vol) - max_trade * n

    # array of desired USD swap volumes to execute
    if rem_vol > 0:
        trades = direction * np.array([max_trade] * n + [rem_vol])
    else:
        trades = direction * np.array([max_trade] * n)

    # array of tokens recevied from swapping. Not all trades may execute
    # due to maximum slippage, or not enough time due to trade delay.
    received_tokens = sim_trades(trades, max_slippage, trade_delay, 
                                 arb_effectiveness, arb_time,
                                 pool_liquidity['pool_x_i'],
                                 pool_liquidity['pool_y_i'],
                                 trading_fee)
    
    # value of tokens recevied based on oracle price
    if direction > 0:
        received = token_price * received_tokens
    else:
        received = 1 * received_tokens #TODO: get UST prices?

    return direction * received.sum()

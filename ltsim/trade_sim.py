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
    Simulates executing a series of trades, while accounting for AMM
    conditions throughout the time of swapping.

    Parameters
    ----------
    delta_x : float
        Amount of token x to swap for token y. If negative, it assumes that
        the equivalent value of token y is traded for token x.
    max_slippage : float
        Maximum acceptable slippage for accepting each trade.
    time_delay : float
        Time between each trade.
    arb_effectiveness : float
        Maximum effectiveness of arbitrage bots in restoring AMM price to its 
        pre trade level.
    arb_time : float
        Time taken for arbitrage bots to restore AMM price by
        arb_effectiveness.
    pool_x_i : float
        Initial token balance for pool token x.
    pool_y_i : float
        Initial token balance for pool token y.

    Returns
    -------
    trade_actual : float
        USD value of tokens received for executing each trade.

    """
        
    # number of timesteps with duration `time_delay` within each hour
    nt = (60 // time_delay) * 60
    
    # target number of trades to execute
    nte = len(delta_x)
    
    # number of trades executed
    ne = 0

    # USD value of trade to execute at each timestep
    delta_xt = np.concatenate([delta_x, np.zeros(nt - nte)])
    
    # Number of tokens being asked (at AMM price)
    delta_yt = - delta_xt / (pool_x_i / pool_y_i)
    
    # bool balances at each timestep
    pool_x = np.zeros(nt) + pool_x_i
    
    pool_y = np.zeros(nt) + pool_y_i
    
    # trade volume executed at each timestep
    trade_actual = np.zeros(nt)
            
    for t in range(nt):
        
        if ne < nte:
            received, perc_spread = sim_swap(delta_xt[t], delta_yt[t], 
                                             pool_x[t], pool_y[t], perc_fee)
            
            if perc_spread < max_slippage:

                arb_offset = (1 - arb_effectiveness / 100) * max(1, (time_delay / arb_time))
                                
                pool_x[t:] += delta_xt[t] * arb_offset
            
                pool_y[t:] += delta_yt[t] * arb_offset
    
                trade_actual[t] = received
                
                ne += 1
            else:
                # trade is rejected due to slippage exceeding acceptable level.
                # trades are shifted by a length of time equal to time_delay
                # arbitrage continues if time delay is smaller than arb time.
                
               # arb_offset = (1 - arb_effectiveness / 100) * max(1, (time_delay / arb_time))
            
               # pool_x[t:] += delta_xt[t] * arb_offset
            
               # pool_y[t:] += delta_yt[t] * arb_offset

                delta_xt[t+1:] = delta_xt[t:nt-1]
                
                delta_yt[t+1:] = delta_yt[t:nt-1]
            
        
    # convert back to USD
    #print(trade_actual)
    trade_actual[delta_xt > 0] *= pool_x[delta_xt > 0] / pool_y[delta_xt > 0]
    
    return trade_actual

def execute_trades(trade_vol, max_trade, max_slippage, trade_delay,
                   arb_effectiveness, arb_time, pool_liquidity, token_price,
                   swap_fee):
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
   # print(trade_vol)
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
                                 swap_fee)
    
    # value of tokens recevied based on oracle price
    if direction > 0:
        received = received_tokens#token_price * received_tokens
    else:
        received = 1 * received_tokens

    return direction * received.sum()

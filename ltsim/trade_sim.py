# -*- coding: utf-8 -*-
import numpy as np

def sim_swap(delta_x, delta_y, pool_x, pool_y, swap_fee, return_usd=True):
    """
    Computes the expected receive, spread and commision amounts for
    Terra Swap style pools (constant product). Based on
    https://docs.terraswap.io/docs/introduction/mechanism/


    Parameters
    ----------
    delta_x : float
        Amount of token x being offered. If positive swapping x for y. If
        negative swapping y for x.
    delta_y : float
        Amount of token y being offered.
    pool_x : float
        Balance (number of tokens) for token x.
    pool_y : float
        Balance (number of tokens) for token y.
    swap_fee : float
        Percentage fee charged by AMM for swap execution.
    convert_to_usd : bool
        Whether or not to convert token values to USD.
    """

    if delta_x > 0:
        ask = abs(delta_y)
        out = delta_x * pool_y / (delta_x + pool_x)
    elif delta_x < 0:
        ask = abs(delta_x)
        out = delta_y * pool_x / (delta_y + pool_y)

    if return_usd and delta_x > 0:
        ask *= pool_x / pool_y
        out *= pool_x / pool_y

    fee = out * swap_fee / 100

    spread = ask - out

    perc_spread = spread / ask * 100

    received = out - fee

    return received, fee, spread, perc_spread

def sim_trades(delta_x, max_slippage, time_delay, arb_effectiveness, arb_time,
               pool_x_i, pool_y_i, swap_fee):
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
    swap_fee : float
        Percentage fee charged by AMM for swap execution.

    Returns
    -------
    trade_actual : float
        USD value of tokens received for executing each trade.

    """

    # number of timesteps with duration time_delay within each hour
    nt = int((60 * 60) // time_delay)

    # not all trades may able to be executed due to time delay alone
    if len(delta_x) > nt:
        delta_x = delta_x[0:nt]

    # target number of trades to execute
    nte = len(delta_x)

    # number of trades executed
    ne = 0

    # USD value of trade to execute at each timestep
    delta_xt = np.concatenate([delta_x, np.zeros(nt - nte)])

    # Number of tokens being asked (at AMM price)
    delta_yt = np.zeros(nt)

    # UST (x) and token (y) bool balances before each trade
    pool_x = np.zeros(nt) + pool_x_i

    pool_y = np.zeros(nt) + pool_y_i

    # trade volume executed at each timestep
    trade_actual = np.zeros(nt)

    # spread for all trades at each timestep
    swap_spread = np.zeros(nt)

    # maximum percentage spread across all trades at each timestep
    swap_perc_spread = np.zeros(nt)

    # swap fees paid for all trades at each timestep
    swap_fees = np.zeros(nt)

    # no. timesteps to complete arb
    narb = int(np.ceil(arb_time/time_delay))

    # arb effectiveness in each timestep
    arb_offset = np.minimum(1, np.linspace(1, narb, narb) * time_delay / arb_time) * arb_effectiveness / 100

    narb_left = 0

    t = 0

    while (ne < nte) and (t < nt):

        delta_yt[t] = - delta_xt[t] / (pool_x[t] / pool_y[t])

        swap = sim_swap(delta_xt[t], delta_yt[t], pool_x[t], pool_y[t], swap_fee)

        perc_spread = swap[3]

        swap_perc_spread[t] = perc_spread

        # slippage will always exceed max slippage & all trades will fail
        if ((t == 0) or (narb_left == 0)) and (perc_spread > max_slippage):
            break

        if perc_spread < max_slippage:
            pool_x[t:] += delta_xt[t] * (1 - arb_offset[0])

            pool_y[t:] += delta_yt[t] * (1 - arb_offset[0])

            narb_left = narb - 1

            trade_actual[t] = swap[0]

            swap_fees[t] = swap[1]

            swap_spread[t] = swap[2]

            ne += 1
        else:
            # trade is rejected due to slippage exceeding acceptable level.
            # trades are shifted by a length of time equal to time_delay

            if narb_left > 0:
                # arbitrage continues, if time delay is smaller
                # than arb time.
                pool_x[t:] -= delta_xt[t-1] * arb_offset[narb-narb_left]

                pool_y[t:] -= delta_yt[t-1] * arb_offset[narb-narb_left]

                narb_left -= 1

            delta_xt[t+1:] = delta_xt[t:nt-1]

            delta_yt[t+1:] = delta_yt[t:nt-1]

        t += 1

    return trade_actual, swap_fees, swap_spread, swap_perc_spread

def execute_trades(trade_vol, max_trade, max_slippage, trade_delay,
                   arb_effectiveness, arb_time, pool_liquidity, swap_fee):
    """
    Divides trade_vol into a number of equally sized trades for execution.
    Actual swap volumes reflect market conditions including spread and
    arbitrage.


    Parameters
    ----------
    trade_vol : float
        Total value of swaps required to execute. Can be either positive
        or negative (indicates direction of trade).
    max_trade : float
        Maximum value per swap.
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
    pool_liquidity : float
        Dictionary of initial pool token balances.
    swap_fee : float
        Percentage fee charged by AMM for swap execution.

    """
    if trade_vol == 0:
        return 0, 0, 0, 0, 0

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

    # Value of swaps executed. Not all trades may execute
    # due to maximum slippage, or not enough time due to trade delay.
    received, fees, spread, perc_spread = sim_trades(trades, max_slippage, trade_delay,
                                                     arb_effectiveness, arb_time,
                                                     pool_liquidity['pool_x_i'],
                                                     pool_liquidity['pool_y_i'],
                                                     swap_fee)

    received_tot = direction * received.sum()
    
    offered_tot = direction * (received + fees + spread).sum()
    
    return received_tot, offered_tot, fees.sum(), spread.sum(), perc_spread.max()

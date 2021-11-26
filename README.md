# leveraged-token-sim
A python package for simulating the performance and operation of leveraged cryptocurrency tokens on the Terra blockchain.

# Setup

- Ensure you have the required packages installed. This can be done through either:
  - Ensuring your environment packages align with those listed in requirements.txt
  - Or installing and running an anaconda environment using the environment.yaml file. See https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html for instructions on how to setup and use anaconda environments.

# Running

The python model is structured as a python packaged named `ltsim`. The Leveraged token model can be used by importing and running the `leveraged_token_model` function.

## Data
The simulation can be run with either user supplied data, or default data. The default data is sourced from Flipside API through the following data module functions 
- [`get_all_model_data`](https://github.com/anthonydouc/leveraged-token-sim/blob/dc52e6763acd80abd63f6264f42f4604863cd121/ltsim/data.py#L159)
- [`get_model_data`](https://github.com/anthonydouc/leveraged-token-sim/blob/dc52e6763acd80abd63f6264f42f4604863cd121/ltsim/data.py#L168)

## Examples
Example scripts for running the leveraged token simulation, trade and swap simulations and reading data are provided in the `examples` folder.

# Model parameter definitions

See the [docstring for the `leveraged_token_model` module](https://github.com/anthonydouc/leveraged-token-sim/blob/22e663c830d35bd75fd1c1568e314f5f890fca75/ltsim/model.py#L35).

# Model output definitions
Running the model produces a dataframe containing a number of variables, each defined over an hourly timestep.

| Output DataFrame field | Unit | Description |
| ------------- |------------- | ------------- |
| underlying_token_price  | *USD/token* | The value per token of the underlying asset. |
| leveraged_token_price  | *USD/token* | The value of the leveraged token. |
| drawdown_underlying  | *%* | The percentage decrease in underlying token price relative to the last all time high price. |
| drawdown_leveraged | *%* | The percentage decrease in leverage token value relative to the last all time high value. |
| n_tokens_per_lt | *no. tokens* | The number of underlying asset tokens per leveraged token.  |
| underlying_value_per_lt | *USD/token* | The value of all underlying asset tokens per leveraged token.  |
| debt_per_lt | *USD/token* | The amount borrowed per leveraged token.  |
| leverage | *unitless/ratio* | The ratio of the underlying value for all asset tokens and debt.  |
| total_underlying_value | *USD* | The value for all underlying assets for all issued leveraged tokens. |
| total_debt | *USD* | The amount borrowed for all issued leveraged tokens. |
| hourly_return | *USD* | The hour on hour change in leveraged token value |
| hourly_return_perc | *%* | The hour on hour percentage change in leveraged token value |
| cummulative_return | *USD* | The total change in leveraged token value since its creation |
| cummulative_return_perc | *%* | The total percentage change in leveraged token value since its creation |
| target_rebalance_amount | *USD* | The exact value of swaps required to rebalance the leverage ratio |
| rebalance_amount | *USD* | The actual value of swaps executed to rebalance the leverage ratio. This may be less due to fees, slippage, and inability to execute all trades |
| swap_fees | *USD* | The value of fees paid for all executed swaps |
| swap_spread | *USD* | The value lost due to slippage for all executed swaps |
| max_swap_spread_perc | *USD* | The maximum potential percentage slippage |
| rebalance_shortfall | *USD* | The value of swaps that were not executed |
| loan_to_value_ratio | *unitless/ratio* | The ratio of debt to underlying asset value |
| liquidation_amount | *USD* | The total value of collateral forfeit to liquidators |
| emergency_rebalance | *boolean* | Boolean variable indicating whether or not emergency rebalance was undertaken |
| periodic_rebalance | *boolean* | Boolean variable indicating whether or not periodic rebalance was undertaken |



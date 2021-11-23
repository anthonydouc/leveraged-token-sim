# leveraged-token-sim
A python package for simulating the performance and operation of leveraged tokens

# Setup

- Ensure you have the required packages installed. This can be done through either:
  - Ensuring your environment packages align with those listed in requirements.txt
  - Or installing and running an anaconda environment using the environment.yaml file. See https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html for instructions on how to setup and use anaconda environments.

# Running

The python model is structured as a python packaged named `ltsim`. The Leveraged token model can be used by importing and running the `leveraged_token_model` function.

## Data
Data can be read in from Flipside API through data module functions 
- [`get_all_model_data`](https://github.com/anthonydouc/leveraged-token-sim/blob/dc52e6763acd80abd63f6264f42f4604863cd121/ltsim/data.py#L159)
- [`get_model_data`](https://github.com/anthonydouc/leveraged-token-sim/blob/dc52e6763acd80abd63f6264f42f4604863cd121/ltsim/data.py#L168)

## Examples
Example scripts for running the leveraged token simulation, trade and swap simulations and reading data are provided in the `examples` folder.

# Model parameter definitions

See the [docstring for the `leveraged_token_model.py` module](https://github.com/anthonydouc/leveraged-token-sim/blob/22e663c830d35bd75fd1c1568e314f5f890fca75/ltsim/model.py#L35).

# Model output definitions
Running the model produces a dataframe containing a number of variables, each defined over an hourly timestep.

| Output  | Description |
| ------------- | ------------- |
| date  | Content Cell  |
| underlying_token_price  | Content Cell  |
| leveraged_token_price  | Content Cell  |
| drawdown_underlying  | Content Cell  |
| drawdown_leveraged | Content Cell  |
| n_tokens_per_lt | Content Cell  |

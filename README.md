# Sniper Bot

## Overview

Sniper Bot offers an exceptional set of features tailored to meet the client's expectations, providing a powerful and versatile tool for trading activities. Divided into distinct modes, each with its unique capabilities, the Sniper Bot ensures a comprehensive and intelligent approach to cryptocurrency trading.

## Table of Contents

- [God Mode Features](#god-mode-features)
- [Mirror Bot Features](#mirror-bot-features)
- [Deployer’s Token Launch Sniper Features](#deployers-token-launch-sniper-features)
- [Leverage Module](#leverage-module)
- [Additional Features](#additional-features)
- [Installation](#installation)


## God Mode Features

### 1. **Sniper Bot (God Mode) - Features Beyond Limits**

#### a. **Listening for Newly Launched Coins**
   - Proactively scans DeX (UniSwap) for recently launched coins.
   - Initiates token buying thread upon detecting sufficient liquidity.

#### b. **Token Screen and Alpha Scan**
   - Evaluates token safety by calculating a comprehensive token score.
   - Utilizes in-house algorithm and external APIs to analyze factors such as source code verification, owner details, balance checks, renunciation status, and more.

#### c. **Token Score Generator**
   - Employs an in-house algorithm and external APIs to generate a normalized token score.
   - Factors in source code verification, owner details, and renunciation status.
   - Normalizes scores to ensure a consistent 1-5 point scale.

#### d. **Selling the Coin**
   - Implements a profit-based selling strategy based on user-entered profit thresholds.
   - Monitors bought coins and executes sell transactions when accumulated profit reaches the specified threshold.

#### e. **Risk Management**
   - Implements a robust risk management system.
   - Monitors coin prices and activates a stop-loss mechanism to prevent further losses in case of significant price drops.

### 2. **Sniper Bot (Mirror Bot) - Reflecting Excellence**

#### a. **Mirroring Transactions**
   - Mirrors transactions of a specified wallet, including both buy and sell operations.

#### b. **Setting Transaction Limit**
   - Allows users to set a maximum spending limit for buying tokens mirrored from a wallet.

## Deployer’s Token Launch Sniper Features

### 3. **Sniper Bot (Deployer’s Token Launch Sniper) - Trust in Deployment**

#### a. **Deployer Address**
   - Permits users to specify a trusted wallet address for token deployment.
   - Executes token purchases without additional checks based on the trusted deployer's actions.

#### b. **Max Amount**
   - Enables users to set the amount they want to spend when buying tokens deployed by the trusted deployer.

#### c. **User Profit**
   - Similar to the God Mode, sells the token once the desired profit has been reached.

## Leverage Module

### 4. **Leverage Module - Intelligent Leverage Calculation**

#### a. **Leverage Calculation Algorithm**
   - Utilizes an algorithm similar to the token score calculation for intelligent leverage assessment.
   - Offers leverages ranging from 1X to a maximum of 5X based on the calculated token score.

#### b. **Leverage Buying**
   - Allows users to choose leverage from 1X to the maximum, facilitating the purchase of leveraged tokens.

## Additional Features

### 5. **Multi Chain**
   - Currently operational on BSC and ETH testnets.
   - Additional chain functionalities (e.g., ARB) on mainnet pending testing due to a lack of mainnet funds.

### 6. **Limit Buy/Sell**
   - Completed feature allowing users to buy and sell tokens freely.
   - UI updated to include sliders as per client's request.

### 7. **Basic TG Bot**
   - TG Bot includes sections for Sniper Bot and Limit Buy/Sell.
   - Additional features yet to be added.

### 8. **Alpha Scan**
   - Users input the token address to access relevant metrics for informed decision-making.

### 9. **TG Bot UI**
   - User interface updates implemented as per the client's instructions.

## Installation

To install the Sniper Bot, follow these steps:


1. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```


## Usage

To use the Sniper Bot, follow these steps:

1. Configure the bot by editing the `config.json` file (see [Configuration](#configuration) section).


2. Run the bot:

    ```bash
    python app.py
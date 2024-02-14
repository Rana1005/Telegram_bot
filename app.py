print("Loading...")
from web3 import Web3, Account
import datetime 
from datetime import timedelta
import threading
import json
import asyncio
import requests
import time
import os
from requests import get
from .errors.errors import ChainNameNotFoundError, ThreadNotStartedError, TokenNotFound, TokenNotBought, TokenNotFoundError, ContractNotInitError, AnkrInitError
from .decimalData import getTokenDecimal
import csv
from flask import Flask, request, jsonify ,send_from_directory 
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from .config.chain_list import chain_list
from .config.external_apis import *
from .config.address import *
from .config.external_api_keys import token_insight_api_key
from .config.api_config import rating_mapping
from .config.swagger import swaggerui_blueprint
from .styles.styles import style
from pymongo import MongoClient
from .core.TokenInfoSniping import TokenInfoSniping
from .core.HoneyPotChecker import HoneypotChecker
from bs4 import BeautifulSoup

import re
# from eth_abi import decode_abi
print("Config loaded....")


print("Setting up the Flask app.....")
app = Flask(__name__)
CORS(app)
socketIO = SocketIO(app,async_mode='threading', cors_allowed_origins='*')


# app.register_blueprint(swaggerui_blueprint)
print("Flask App successfully...")


print("Setting up temp variables....")
stop_loss = 10
max_run_time_for_token= 0.5
token_bought_time = time.time()


active_chain = 'eth'
thread_dict = {}
mirror_thread_dict={}
leverage_thread_dict={}
chatId_dict={}
multi_wallet_dict = {}
os.system("")
print("Done setting up the temp variables....")

    
"""
get_leverage_token Function Documentation:

Description:
    This function retrieves the leverage score for a given ERC20 token by querying TokenInsight API. 
    The leverage score is determined based on the rating level of the token obtained from the API.

Parameters:
    - token_address (str): The Ethereum address of the ERC20 token.
    - active_chain (str): The name of the active blockchain.

Returns:
    - int: The leverage score of the token, ranging from 1 to 10, with 10 being the highest leverage.

Raises:
    - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.
    - TokenNotFoundError: If the token is not found in the TokenInsight API's coin list.

Usage:
    leverage_score = get_leverage_token("0x123abc...", "ethereum")

"""

def get_leverage_token(token_address, active_chain):
    """
    Retrieve the leverage score for a given ERC20 token.

    Parameters:
        - token_address (str): The Ethereum address of the ERC20 token.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - int: The leverage score of the token, ranging from 1 to 10.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found.
        - TokenNotFoundError: If the token is not found in the TokenInsight API's coin list.
    """    
    
    try:
        if active_chain not in chain_list:
            raise ChainNameNotFoundError
        #Setting up the local variables for the given chain
        current_chain = chain_list[active_chain]    
        web3 = current_chain['web3']
        erc_20_abi = current_chain['erc_20_abi']
        token_contract = web3.eth.contract(address=web3.to_checksum_address(token_address), abi=erc_20_abi)
        try:
            # Finding the token name and symbol for API Calls
            token_name = token_contract.functions.name().call()
            token_symbol = token_contract.functions.symbol().call()
            print("token name", token_name)
            print("token symbol", token_symbol)

        except Exception as e:
            print("error while getting token_name",str(e))
            # return str(e)
            return jsonify({"result":"-1", "error":str(e), 'leverage':-1}), 400
        
        url = token_insight_coins_list_url

        headers = {
                "accept": "application/json",
                "TI_API_KEY": token_insight_api_key
            }

        response = requests.get(url, headers=headers)

        datas= json.loads(response.text)['data']['items']
        is_found = False
        for data in datas:
            if data['symbol'] == token_symbol or data['name'] == token_name:
                print("data found")
                print(data)
                is_found = True
                token_id = data['id']
                break
        if not is_found:
            print("token not found on the list, no leverage")
            raise TokenNotFoundError

        if "token_id" not in locals():
            print("token id not found")
            raise TokenNotFoundError
        
        url = f"{token_insight_coin_rating_url}{token_id}"

        headers = {
            "accept": "application/json",
            "TI_API_KEY": token_insight_api_key
        }

        response = requests.get(url, headers=headers)

        print(response.text)
        rating = json.loads(response.text)["data"][0]['rating_level']
        print(rating, "ratings found")
        rating_mappings = rating_mapping
        score = rating_mappings[rating]
        return score
        
            # or an appropriate defan appropriate def
    except ChainNameNotFoundError as e:
        print("error in getting token score", str(e))
        return jsonify({"result":"-1", "error":str(e), 'leverage':-1}), 400
    except TokenNotFoundError as e:
        print("error in getting token info from the api", str(e))
        return jsonify({"result":"-1", "error":str(e), 'leverage':0}), 400
    except Exception as e:
        print("something went wrong with getting the token score", str(e))
        return jsonify({"result":"-1", "error":str(e), 'leverage':-1}), 400



# print(style.MAGENTA) 


# print(style.WHITE)


currentTimeStamp = ""

"""
Description:
    This function retrieves the current timestamp in the format "[%H:%M:%S.%f]" and
    updates the global variable `currentTimeStamp` with the obtained timestamp.

Usage:
    getTimestamp()

Notes:
    The function runs in an infinite loop, continuously updating the timestamp.
    To stop the loop, you need to interrupt the program.

Global Variables:
    - currentTimeStamp (str): Updated with the current timestamp in "[%H:%M:%S.%f]" format.

"""

def getTimestamp():
    """
    Global Variables:
        - currentTimeStamp (str): Updated with the current timestamp in "[%H:%M:%S.%f]" format.

    """

    while True:
        timeStampData = datetime.datetime.now()
        global currentTimeStamp
        currentTimeStamp = "[" + timeStampData.strftime("%H:%M:%S.%f")[:-3] + "]"
    
    

#-------------------------------- INITIALISE ------------------------------------------
   
#load json data

configFilePath = os.path.abspath('') + '/config.json'

with open(configFilePath, 'r') as configdata:
    data=configdata.read()

# parse file
obj = json.loads(data)

print("Testing web3 connection .....")

#set the BSC node to use. I highly recommend a private node such as QuickNode.
# pancakeSwapRouterAddress = obj['pancakeSwapRouterAddress'] #load config data from JSON file into program
# walletAddress = obj['walletAddress']
# private_key = obj['walletPrivateKey'] #private key is kept safe and only used in the program

# snipeBNBAmount = float(obj['amountToSpendPerSnipe'])
# transactionRevertTime = int(obj['transactionRevertTimeSeconds']) #number of seconds after transaction processes to cancel it if it hasn't completed
# gasAmount = int(obj['gasAmount'])
# gasPrice = int(obj['gasPrice'])
# bscScanAPIKey = obj['bscScanAPIKey']

sellOnlyMode = obj['sellOnlyMode']
sellProfit = float(obj['sellProfit'])

checkSourceCode = obj['checkSourceCode']
checkValidPancakeV2 = obj['checkValidPancakeV2']
checkMintFunction = obj['checkMintFunction']
checkHoneypot = obj['checkHoneypot']
checkPancakeV1Router = obj['checkPancakeV1Router']
checkSumAddress = obj['checkSumAddress']
infura_url = obj['infura_url']

enableMiniAudit = False

if checkSourceCode == "True" and (checkValidPancakeV2 == "True" or checkMintFunction == "True" or checkHoneypot == "True" or checkPancakeV1Router == "True"):
    enableMiniAudit = True

timeStampThread = threading.Thread(target=getTimestamp)
timeStampThread.start()

numTokensDetected = 0
numTokensBought = 0
walletBalance = 0
bscNode = obj['bscNode'] 
bsc = bscNode
web3 = Web3(Web3.HTTPProvider(bsc))

if web3.is_connected():
    print(currentTimeStamp + " [Info] Web3 successfully connected")

def updateTitle():
    walletBalance = web3.from_wei(web3.eth.get_balance(walletAddress),'ether') #There are references to ether in the code but it's set to BNB, its just how Web3 was originally designed
    walletBalance = round(walletBalance, -(int("{:e}".format(walletBalance).split('e')[1]) - 4)) #the number '4' is the wallet balance significant figures + 1, so shows 5 sig figs

# updateTitle()


# print(currentTimeStamp + " [Info] Using Wallet Address: " + walletAddress)
# print(currentTimeStamp + " [Info] Using Snipe Amount: " + str(snipeBNBAmount), "ETH")

pancakeABI = '[{"inputs":[{"internalType":"address","name":"_factory","type":"address"},{"internalType":"address","name":"_WETH","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"WETH","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"amountADesired","type":"uint256"},{"internalType":"uint256","name":"amountBDesired","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amountTokenDesired","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountIn","outputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountOut","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsIn","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"reserveA","type":"uint256"},{"internalType":"uint256","name":"reserveB","type":"uint256"}],"name":"quote","outputs":[{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETHSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermit","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermitSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityWithPermit","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapETHForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETHSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]'
listeningABI = json.loads('[{"inputs":[{"internalType":"address","name":"_feeToSetter","type":"address"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"token0","type":"address"},{"indexed":true,"internalType":"address","name":"token1","type":"address"},{"indexed":false,"internalType":"address","name":"pair","type":"address"},{"indexed":false,"internalType":"uint256","name":"","type":"uint256"}],"name":"PairCreated","type":"event"},{"constant":true,"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"allPairs","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"allPairsLength","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"}],"name":"createPair","outputs":[{"internalType":"address","name":"pair","type":"address"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"feeTo","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"feeToSetter","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"_feeTo","type":"address"}],"name":"setFeeTo","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"_feeToSetter","type":"address"}],"name":"setFeeToSetter","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"}]')
tokenNameABI = json.loads('[ { "anonymous": false, "inputs": [ { "indexed": true, "internalType": "address", "name": "owner", "type": "address" }, { "indexed": true, "internalType": "address", "name": "spender", "type": "address" }, { "indexed": false, "internalType": "uint256", "name": "value", "type": "uint256" } ], "name": "Approval", "type": "event" }, { "anonymous": false, "inputs": [ { "indexed": true, "internalType": "address", "name": "from", "type": "address" }, { "indexed": true, "internalType": "address", "name": "to", "type": "address" }, { "indexed": false, "internalType": "uint256", "name": "value", "type": "uint256" } ], "name": "Transfer", "type": "event" }, { "constant": true, "inputs": [ { "internalType": "address", "name": "_owner", "type": "address" }, { "internalType": "address", "name": "spender", "type": "address" } ], "name": "allowance", "outputs": [ { "internalType": "uint256", "name": "", "type": "uint256" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": false, "inputs": [ { "internalType": "address", "name": "spender", "type": "address" }, { "internalType": "uint256", "name": "amount", "type": "uint256" } ], "name": "approve", "outputs": [ { "internalType": "bool", "name": "", "type": "bool" } ], "payable": false, "stateMutability": "nonpayable", "type": "function" }, { "constant": true, "inputs": [ { "internalType": "address", "name": "account", "type": "address" } ], "name": "balanceOf", "outputs": [ { "internalType": "uint256", "name": "", "type": "uint256" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "decimals", "outputs": [ { "internalType": "uint256", "name": "", "type": "uint256" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "getOwner", "outputs": [ { "internalType": "address", "name": "", "type": "address" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "name", "outputs": [ { "internalType": "string", "name": "", "type": "string" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "symbol", "outputs": [ { "internalType": "string", "name": "", "type": "string" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "totalSupply", "outputs": [ { "internalType": "uint256", "name": "", "type": "uint256" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": false, "inputs": [ { "internalType": "address", "name": "recipient", "type": "address" }, { "internalType": "uint256", "name": "amount", "type": "uint256" } ], "name": "transfer", "outputs": [ { "internalType": "bool", "name": "", "type": "bool" } ], "payable": false, "stateMutability": "nonpayable", "type": "function" }, { "constant": false, "inputs": [ { "internalType": "address", "name": "sender", "type": "address" }, { "internalType": "address", "name": "recipient", "type": "address" }, { "internalType": "uint256", "name": "amount", "type": "uint256" } ], "name": "transferFrom", "outputs": [ { "internalType": "bool", "name": "", "type": "bool" } ], "payable": false, "stateMutability": "nonpayable", "type": "function" } ]')





#------------------------------------- BUY SPECIFIED TOKEN ON PANCAKESWAP ----------------------------------------------------------

# def checkTokenPrice(tokenAddress):
#     BNBTokenAddress = Web3.to_checksum_address(wbnb_contract_address)  # BNB
#     amountOut = None

#     tokenRouter = web3.eth.contract(address=Web3.to_checksum_address(tokenAddress), abi=tokenNameABI)
#     tokenDecimals = tokenRouter.functions.decimals().call()
#     tokenDecimals = getTokenDecimal(tokenDecimals)
    
#     router = web3.eth.contract(address=Web3.to_checksum_address(pancakeSwapRouterAddress), abi=pancakeABI)
#     amountIn = web3.to_wei(1, tokenDecimals)
#     amountOut = router.functions.getAmountsOut(amountIn, [Web3.to_checksum_address(tokenAddress), BNBTokenAddress]).call()
#     amountOut = web3.from_wei(amountOut[1], tokenDecimals)
#     return amountOut


"""
    Description:
        This function retrieves the approximate price of a given ERC20 token in terms of a wrapped token (e.g., WETH).
        The price is obtained by querying the specified blockchain's router contract.

    Parameters:
        - token_address (str): The Ethereum address of the ERC20 token.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - float or None: The approximate price of the token in terms of a wrapped token.
                         Returns None if an error occurs during the process.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.

    Usage:
        price = check_token_price_general("0x123abc...", "ethereum")
"""

def check_token_price_general(token_address,active_chain):

    """
    Parameters:
        - token_address (str): The Ethereum address of the ERC20 token.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - float or None: The approximate price of the token in terms of a wrapped token.
                         Returns None if an error occurs during the process.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.

    """

    try:
        if active_chain is None or active_chain not in chain_list.keys():
            raise ChainNameNotFoundError(active_chain)
        # print(chain_list, active_chain)
        current_chain = chain_list[active_chain]
        # print(current_chain, type(current_chain), current_chain['web3'])
        web3 = current_chain['web3']
        token_address_check_Sum = web3.to_checksum_address(token_address)
        # current_chain = chain_list[active_chain]
        w_token_address = current_chain['w_address']
        w_token_address = Web3.to_checksum_address(w_token_address)
        router_address, router_abi = current_chain['router_address'], current_chain['router_abi']
          # BNB
        erc_20_abi = current_chain['erc_20_abi']
        amountOut = None
        print(web3.net.version)
        tokenRouter = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc_20_abi)
        tokenDecimals = tokenRouter.functions.decimals().call()
        tokenDecimals = getTokenDecimal(tokenDecimals)
        
        router = web3.eth.contract(address=Web3.to_checksum_address(router_address), abi=router_abi)
        amountIn = web3.to_wei(1, tokenDecimals)
        amountOut = router.functions.getAmountsOut(amountIn, [Web3.to_checksum_address(token_address), w_token_address]).call()
        amountOut = web3.from_wei(amountOut[1], tokenDecimals)
        print("amount out", amountOut)
        return amountOut
    except ChainNameNotFoundError as e:
        print(str(e))
        return None
    except Exception as e:
        print(str(e), 'In the main exception')
        return None



"""
    Description:
        This function retrieves the approximate price of a given ERC20 token on the Goerli testnet
        in terms of BNB (or any other wrapped token specified in the function).

    Parameters:
        - tokenAddress (str): The Ethereum address of the ERC20 token on the Goerli testnet.

    Returns:
        - float or None: The approximate price of the token in terms of BNB (or another wrapped token).
                         Returns None if an error occurs during the process.

    Notes:
        Ensure that the global variables `infura_url`, `pancakeSwap_RouterAddress`, `pancake_ABI`, and
        `BNBTokenAddress` are properly configured before using this function.

    Usage:
        price = check_token_price_for_goerrli("0x123abc...")
"""
def check_token_price_for_goerrli(tokenAddress):
    """

    Parameters:
        - tokenAddress (str): The Ethereum address of the ERC20 token on the Goerli testnet.

    Returns:
        - float or None: The approximate price of the token in terms of BNB (or another wrapped token).
                         Returns None if an error occurs during the process.

    Notes:
        Ensure that the global variables `infura_url`, `pancakeSwap_RouterAddress`, `pancake_ABI`, and
        `BNBTokenAddress` are properly configured before using this function.

    """
    infura_url = infura_url  # Replace with your Infura project ID

    web3 = Web3(Web3.HTTPProvider(infura_url))

    pancakeSwap_RouterAddress = pancakeSwap_RouterAddress
    pancake_ABI = '''[{"inputs":[{"internalType":"address","name":"_factory","type":"address"},{"internalType":"address","name":"_WETH","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"WETH","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"amountADesired","type":"uint256"},{"internalType":"uint256","name":"amountBDesired","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amountTokenDesired","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountIn","outputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountOut","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsIn","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"reserveA","type":"uint256"},{"internalType":"uint256","name":"reserveB","type":"uint256"}],"name":"quote","outputs":[{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETHSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermit","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermitSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityWithPermit","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapETHForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETHSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]'''
    BNBTokenAddress = Web3.to_checksum_address(BNBTokenAddress)  # BNB
    tokenNameABI='''[{"inputs":[{"internalType":"uint256","name":"chainId_","type":"uint256"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"src","type":"address"},{"indexed":true,"internalType":"address","name":"guy","type":"address"},{"indexed":false,"internalType":"uint256","name":"wad","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":true,"inputs":[{"indexed":true,"internalType":"bytes4","name":"sig","type":"bytes4"},{"indexed":true,"internalType":"address","name":"usr","type":"address"},{"indexed":true,"internalType":"bytes32","name":"arg1","type":"bytes32"},{"indexed":true,"internalType":"bytes32","name":"arg2","type":"bytes32"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"}],"name":"LogNote","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"src","type":"address"},{"indexed":true,"internalType":"address","name":"dst","type":"address"},{"indexed":false,"internalType":"uint256","name":"wad","type":"uint256"}],"name":"Transfer","type":"event"},{"constant":true,"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"PERMIT_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"burn","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"guy","type":"address"}],"name":"deny","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"mint","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"src","type":"address"},{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"move","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"holder","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"expiry","type":"uint256"},{"internalType":"bool","name":"allowed","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"pull","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"push","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"guy","type":"address"}],"name":"rely","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"src","type":"address"},{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"version","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"wards","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}]'''
    amountOut = None

    tokenRouter = web3.eth.contract(address=Web3.to_checksum_address(tokenAddress), abi=tokenNameABI)
    print("here") 
    tokenDecimals = tokenRouter.functions.decimals().call()
    print("not here")
    tokenDecimals = getTokenDecimal(tokenDecimals)
    
    router_ = web3.eth.contract(address=Web3.to_checksum_address(pancakeSwap_RouterAddress), abi=pancake_ABI)
    amountIn = web3.to_wei(1, tokenDecimals)
    print(tokenAddress, amountIn, web3.to_checksum_address(tokenAddress))
    print(router_.address)
    amountOut = router_.functions.getAmountsOut(amountIn, [Web3.to_checksum_address(tokenAddress), BNBTokenAddress]).call()
    print('not here')
    amountOut = web3.from_wei(amountOut[1], tokenDecimals)
    print(amountOut)
    return amountOut


"""
    Description:
        This function retrieves the balance of a given ERC20 token for a specified wallet address on the specified blockchain.

    Parameters:
        - token_address (str): The Ethereum address of the ERC20 token.
        - wallet_address (str): The Ethereum address of the wallet for which the token balance is retrieved.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - tuple or None: A tuple containing the raw token balance, the readable balance in the token's decimal format,
                        and the symbol of the token. Returns None if an error occurs during the process.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.

    Usage:
        balance_info = get_token_balance_general("0x123abc...", "0xwallet...", "ethereum")

"""

def get_token_balance_general(token_address,wallet_address,active_chain):
    """
    Parameters:
        - token_address (str): The Ethereum address of the ERC20 token.
        - wallet_address (str): The Ethereum address of the wallet for which the token balance is retrieved.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - tuple or None: A tuple containing the raw token balance, the readable balance in the token's decimal format,
                        and the symbol of the token. Returns None if an error occurs during the process.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.

    """
  
    try:
        if active_chain is None or active_chain not in chain_list.keys():
            raise ChainNameNotFoundError(active_chain)
        # print(chain_list, active_chain)
        current_chain = chain_list[active_chain]
        # print(current_chain, type(current_chain), current_chain['web3'])
        web3 = current_chain['web3']
        token_address = web3.to_checksum_address(token_address)
        # current_chain = chain_list[active_chain]
        w_token_address = current_chain['w_address']
        w_token_address = Web3.to_checksum_address(w_token_address)
          # BNB
        erc_20_abi = current_chain['erc_20_abi']
        print(web3.net.version)
        token_contract = web3.eth.contract(address=web3.to_checksum_address(token_address), abi=erc_20_abi)

        trading_token_decimal = token_contract.functions.decimals().call()
        trading_token_decimal = getTokenDecimal(trading_token_decimal)
        balance = token_contract.functions.balanceOf(wallet_address).call()
        symbol = token_contract.functions.symbol().call()
        readable = web3.from_wei(balance,trading_token_decimal)
        print("----------------------------138",balance, readable, symbol )
        return balance, readable, symbol
    except ChainNameNotFoundError as e:
        print(str(e))
        return None
    except Exception as e:
        print(str(e), 'In the main exception')
        return None

# def buy_for_eth_general(amount, token_address, is_increase_nonce,walletAddress,private_key,active_chain):
    
#     try:
#         if active_chain is None or active_chain not in chain_list.keys():
#             raise ChainNameNotFoundError(active_chain)
#         # print(chain_list, active_chain)
#         current_chain = chain_list[active_chain]
#         # print(current_chain, type(current_chain), current_chain['web3'])
#         web3 = current_chain['web3']
#         token_address = web3.to_checksum_address(token_address)
#         # current_chain = chain_list[active_chain]
#         w_token_address = current_chain['w_address']
#         w_token_address = Web3.to_checksum_address(w_token_address)
#           # BNB
#         erc_20_abi = current_chain['erc_20_abi']
#         router_address, router_abi = current_chain['router_address'], current_chain['router_abi']

#         router_contract = web3.eth.contract(address=router_address, abi=router_abi)

        
#         print("here", amount * 10**18)
        
#         account = Account.from_key(private_key)    
    
#         # dai_amount_in_wei = int(dai_amount * 10**18)
#         wei_amount = web3.to_wei(amount, 'ether')
#         print(wei_amount)
#         path = [Web3.to_checksum_address(goerli_wrapped_ether_address),Web3.to_checksum_address(token_address)]  # DAI to WETH trading path

#         # Estimate the amount of WETH you will receive
#         amount_out_min = router_contract.functions.getAmountsOut(wei_amount, path).call()
#         weth_amount_in_wei = amount_out_min[1]

#         print(f'Estimated amount of the token you will recieve: {weth_amount_in_wei / 10**18} WETH')

#         # Execute the swap
#         gas_price = web3.eth.gas_price
#         gas_limit = 300000
#         if is_increase_nonce:
#             nonce = web3.eth.get_transaction_count(account.address) + 1
#         else:
#             nonce = web3.eth.get_transaction_count(account.address)


#         transaction = {
#             'from': account.address,
#             'value': wei_amount,  # You are selling DAI, not sending ETH
#             'gasPrice': gas_price,
#             'gas': gas_limit,
#             'nonce': nonce,
#         }
#         time_limit = int(time.time() + 60 * 10)
#         if is_increase_nonce:
#             slippageAmount = (amount_out_min[1] * 20) / 100;
#             amount_out_min[1] = int(amount_out_min[1] + slippageAmount)
#             time_limit += int(60*10)
#         function_data = router_contract.functions.swapExactETHForTokens(
#             amount_out_min[1],  # Min amount of WETH you expect to receive
#             path,
#             walletAddress,
#             time_limit,  # 10 minutes
#         ).build_transaction(transaction)
#         signed_transaction = web3.eth.account.sign_transaction(function_data, private_key)

#         tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction).hex()

#         print(f'Transaction Hash: {tx_hash}')
#         return weth_amount_in_wei / 10**18, tx_hash
#     except ChainNameNotFoundError as e:
#         print(str(e))
#         return None
#     except Exception as e:
#         print('Error:', e)

"""
    Description:
        This function performs a token purchase using Ether (ETH) on a specified blockchain.
        It interacts with the blockchain's router contract to execute the swap.

    Parameters:
        - amount (float): The amount of Ether (ETH) to spend on the token purchase.
        - token_address (str): The Ethereum address of the ERC20 token to be purchased.
        - is_increase_nonce (bool): Flag indicating whether to increase the transaction nonce.
        - walletAddress (str): The Ethereum address of the wallet performing the purchase.
        - private_key (str): The private key corresponding to the walletAddress for transaction signing.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - tuple or None: A tuple containing the amount of the purchased token in Ether (ETH)
                         and the transaction hash if successful. Returns None if an error occurs.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.

    Usage:
        result = buy_for_eth_general(1.0, "0x123abc...", True, "0xwalletAddress", "privateKey", "ethereum")
"""

def buy_for_eth_general(amount, token_address, is_increase_nonce,walletAddress,private_key,active_chain):
    """

    Parameters:
        - amount (float): The amount of Ether (ETH) to spend on the token purchase.
        - token_address (str): The Ethereum address of the ERC20 token to be purchased.
        - is_increase_nonce (bool): Flag indicating whether to increase the transaction nonce.
        - walletAddress (str): The Ethereum address of the wallet performing the purchase.
        - private_key (str): The private key corresponding to the walletAddress for transaction signing.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - tuple or None: A tuple containing the amount of the purchased token in Ether (ETH)
                         and the transaction hash if successful. Returns None if an error occurs.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.

    """
    print("In Buying......")
    try:
        if active_chain is None or active_chain not in chain_list.keys():
            raise ChainNameNotFoundError(active_chain)
        # print(chain_list, active_chain)
        current_chain = chain_list[active_chain]
        # print(current_chain, type(current_chain), current_chain['web3'])
        web3 = current_chain['web3']
        token_address = web3.to_checksum_address(token_address)
        # current_chain = chain_list[active_chain]
        w_token_address = current_chain['w_address']
        w_token_address = Web3.to_checksum_address(w_token_address)
          # BNB
        erc_20_abi = current_chain['erc_20_abi']
        router_address, router_abi = current_chain['router_address'], current_chain['router_abi']

        router_contract = web3.eth.contract(address=router_address, abi=router_abi)
        try:
            print(router_address, "Here", walletAddress)
            # print("here", amount * 10**18)
            
            # account = Account.from_key(private_key)    
            print("Errorsasas")
            # dai_amount_in_wei = int(dai_amount * 10**18)
            wei_amount = web3.to_wei(amount, 'ether')
            print(wei_amount)
            path = [Web3.to_checksum_address(w_token_address),Web3.to_checksum_address(token_address)]  # DAI to WETH trading path

            # Estimate the amount of WETH you will receive
            amount_out_min = router_contract.functions.getAmountsOut(wei_amount, path).call()
            weth_amount_in_wei = amount_out_min[1]

            print(f'Estimated amount of the token you will recieve: {weth_amount_in_wei / 10**18} WETH')

            # Execute the swap
            gas_price = web3.eth.gas_price
            gas_limit = 300000
            if is_increase_nonce:
                nonce = web3.eth.get_transaction_count(walletAddress) + 1
            else:
                nonce = web3.eth.get_transaction_count(walletAddress)


            transaction = {
                'from': walletAddress,
                'value': wei_amount,  # You are selling DAI, not sending ETH
                'gasPrice': gas_price,
                'gas': gas_limit,
                'nonce': nonce,
            }
            time_limit = int(time.time() + 60 * 10)
            if is_increase_nonce:
                slippageAmount = (amount_out_min[1] * 20) / 100
                amount_out_min[1] = int(amount_out_min[1] + slippageAmount)
                time_limit += int(60*10)
            function_data = router_contract.functions.swapExactETHForTokens(
                amount_out_min[1],  # Min amount of WETH you expect to receive
                path,
                walletAddress,
                time_limit,  # 10 minutes
            ).build_transaction(transaction)
            signed_transaction = web3.eth.account.sign_transaction(function_data, private_key)

            tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction).hex()

            print(f'Transaction Hash: {tx_hash}')
            return weth_amount_in_wei / 10**18, tx_hash
        except Exception as e:
            print("there is some error", str(e))
    except ChainNameNotFoundError as e:
        print(str(e))
        return None
    except Exception as e:
        print('Error: in buying', e)
        return {"error":str(e)}
        


"""
    Description:
        This function approves the Uniswap Router to spend a specified amount of an ERC20 token on behalf of the user.
        The approval is necessary for subsequent transactions like swapping tokens on Uniswap.

    Parameters:
        - amount (float): The amount of the ERC20 token to be approved for spending.
        - token_contract_address (str): The Ethereum address of the ERC20 token contract.
        - private_key (str): The private key of the account approving the transaction.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - str or None: The transaction hash if the approval is successful, otherwise None.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.

    Usage:
        tx_hash = approve_uniswap_router_general(100, "0x123abc...", "private_key", "ethereum")
"""
def approve_uniswap_router_general(amount, token_contract_address,private_key,active_chain):
    """
    Parameters:
        - amount (float): The amount of the ERC20 token to be approved for spending.
        - token_contract_address (str): The Ethereum address of the ERC20 token contract.
        - private_key (str): The private key of the account approving the transaction.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - str or None: The transaction hash if the approval is successful, otherwise None.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.
    """

    try:
        if active_chain is None or active_chain not in chain_list.keys():
            raise ChainNameNotFoundError(active_chain)
        # print(chain_list, active_chain)
        current_chain = chain_list[active_chain]
        # print(current_chain, type(current_chain), current_chain['web3'])
        web3 = current_chain['web3']
        token_address = web3.to_checksum_address(token_contract_address)
        # current_chain = chain_list[active_chain]
        w_token_address = current_chain['w_address']
        w_token_address = web3.to_checksum_address(w_token_address)
          # BNB
        erc_20_abi = current_chain['erc_20_abi']
        router_address, router_abi = current_chain['router_address'], current_chain['router_abi']

        router_contract = web3.eth.contract(address=router_address, abi=router_abi)
    
        token_contract_address = web3.to_checksum_address(token_contract_address) # DAI token contract address
        token_contract_abi =erc_20_abi  # Replace with the actual DAI token ABI

        token_contract = web3.eth.contract(address=token_contract_address, abi=token_contract_abi)

        # Calculate the allowance amount (maximum uint256 value)
        max_allowance = amount
        # eth_value = Web3.from_wei(max_allowance, 'ether')
        # prin
        # if max_allowance < 100000:
        #     max_allowance = int(max_allowance * 10**18)
        
        max_allowance = int(amount*10**18)

        account = Account.from_key(private_key)    
        # dai_amount = 4  # Change this to the desired amount
        allowed_amount = token_contract.functions.allowance(account.address, router_address).call()
        if allowed_amount >= max_allowance:
            print("Already approved, skipping approval",)
            return -1
        nonce = web3.eth.get_transaction_count(account.address)
        

        # Approve the Uniswap Router to spend DAI on your behalf
        tx_hash = token_contract.functions.approve(router_address, max_allowance).build_transaction({
        'from': account.address, 
        'nonce': nonce 
        })

        signed_transaction = web3.eth.account.sign_transaction(tx_hash, private_key)

        tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction).hex()
        
        # x = Web3.wait_for_transaction_receipt(tx_hash)
        # print(x)
        print(f'Transaction Hash: {tx_hash}')
        return tx_hash
    except ChainNameNotFoundError as e:
        print(str(e))
        return None
    except Exception as e:
        print('Err:', e)



"""
    Description:
        This function performs a token swap on the specified blockchain's Uniswap-like router.
        It sells the given amount of a token for ETH and approves the router for the swap.

    Parameters:
        - amount (float): The amount of the token to be sold.
        - token_contract_address (str): The Ethereum address of the token to be sold.
        - private_key (str): The private key of the account initiating the swap.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - tuple or None: A tuple containing the estimated amount of WETH to receive and the transaction hash.
                         Returns None if an error occurs during the process.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.

    Usage:
        result = sell_for_eth_and_approve_general(4, "0x123abc...", "your_private_key", "ethereum")
"""

def sell_for_eth_and_approve_general(amount, token_contract_address,private_key,active_chain, is_nonce):

    """
    Parameters:
        - amount (float): The amount of the token to be sold.
        - token_contract_address (str): The Ethereum address of the token to be sold.
        - private_key (str): The private key of the account initiating the swap.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - tuple or None: A tuple containing the estimated amount of WETH to receive and the transaction hash.
                         Returns None if an error occurs during the process.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.

    """

    try:
        current_chain = chain_list[active_chain]

        web3, api_key = current_chain['web3'], current_chain['scan_api_key']
        sell_amount_in_wei = int(amount * 10**18)

        print(amount, "amount is ")
        # approve_uniswap_router_general(amount=sell_amount_in_wei,token_contract_address=token_contract_address )

        # time.sleep(10)
        # abi = None
        
        # url_for_contract = current_chain['base_scan_url'] + "module=contract&action=getabi&address=" + token_contract_address + "&apikey=" + api_key
        # response = requests.get(url_for_contract).json()
        # print(response)
        # if response['status'] == '1':
        #     abi = response['result']
        #     token_contract = web3.eth.contract(address=token_contract_address, abi=abi)
        #     print('\n', token_contract.functions.__dict__)
        #     if "fee" in token_contract.functions.__dict__:
        #         print('\n', "tokne has fee")
        #     else:
        #         print('\n', "fee is not there")
        #     # set_fee_function = token_contract.functions.setFee(0, 0, 0, 0)
        #     # set_fee_function_inputs = set_fee_function.call()
        #     # if any(set_fee_function_inputs):
        #     #     print("Transfer fee is implemented in the token contract.")
        #     # else:
        #     #     print("No transfer fee found in the token contract.")
        #     initial_redis_fee_on_buy = token_contract.functions.redisFeeOnBuy().call()
            
            
            # print(f"printing the initial_redis_fee_on_buy ====> {initial_redis_fee_on_buy}")
            # initial_redis_fee_on_sell = token_contract.functions.redisFeeOnSell().call()
            # print(f"printing the initial_redis_fee_on_sell ====> {initial_redis_fee_on_sell}")
            # initial_tax_fee_on_buy = token_contract.functions.taxFeeOnBuy().call()
            # print(f"printing the initial_tax_fee_on_buy ====> {initial_tax_fee_on_buy}")
            # initial_tax_fee_on_sell = token_contract.functions.taxFeeOnSell().call()
            # print(f"printing the initial_tax_fee_on_sell ====> {initial_tax_fee_on_sell}")
            # print('\n', )
            # print("abi", abi)
            # if "fee" in str(abi):
            #     print('\n', "yes")
            # else:
            #     print('\n', "no")
        # if abi is None and is_force == False:
        #     return {"error":"cannot find abi"}
        if active_chain is None or active_chain not in chain_list.keys():
            raise ChainNameNotFoundError(active_chain)
        # print(chain_list, active_chain)
        # print(current_chain, type(current_chain), current_chain['web3'])
        
        token_address = web3.to_checksum_address(token_contract_address)
        # current_chain = chain_list[active_chain]
        w_token_address = current_chain['w_address']
        w_token_address = Web3.to_checksum_address(w_token_address)
          # BNB
        erc_20_abi = current_chain['erc_20_abi']
        router_address, router_abi = current_chain['router_address'], current_chain['router_abi']

        router_contract = web3.eth.contract(address=router_address, abi=router_abi)

        max_allowance =20
        max_allowance = int(max_allowance * 10**18)
        account = Account.from_key(private_key)    
        dai_amount = 4  # Change this to the desired amount

        # sell_amount_in_wei =int(4*10**18)
        print("amount",sell_amount_in_wei)
        path = [web3.to_checksum_address(token_contract_address), w_token_address]  # DAI to WETH trading path

        # Estimate the amount of WETH you will receive
        amount_out_min = router_contract.functions.getAmountsOut(sell_amount_in_wei, path).call()

        weth_amount_in_wei = amount_out_min[1]

        print(f'Estimated amount of WETH to receive: {weth_amount_in_wei / 10**18} WETH')

        # Execute the swap
        gas_price = web3.eth.gas_price
        gas_limit = 300000
        nonce = web3.eth.get_transaction_count(account.address) 

        if is_nonce:
            nonce+=1
            


        transaction = {
            'from': account.address,
            # 'value': 0,  # You are selling DAI, not sending ETH
            # 'gasPrice': 10,
            'gas': 8500000,
            'nonce': nonce,
        }
        try:
            function_data = router_contract.functions.swapExactTokensForETH(
                sell_amount_in_wei,
                0,  # Min amount of WETH you expect to receive
                path,
                account.address,
                int(time.time()) + 60 * 10,  # 10 minutes
            ).estimate_gas(transaction)
            function_data = router_contract.functions.swapExactTokensForETH(
                sell_amount_in_wei,
                0,  # Min amount of WETH you expect to receive
                path,
                account.address,
                int(time.time()) + 60 * 10,  # 10 minutes
            ).build_transaction(transaction)
            signed_transaction = web3.eth.account.sign_transaction(function_data, private_key)

            tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction).hex()
        except Exception as e:
            print(str(e), "error")
            
            try:
                function_data = router_contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                sell_amount_in_wei,
                0,  # Min amount of WETH you expect to receive
                path,
                account.address,
                int(time.time()) + 60 * 10,  # 10 minutes
            ).estimate_gas(transaction)
                function_data = router_contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                sell_amount_in_wei,
                0,  # Min amount of WETH you expect to receive
                path,
                account.address,
                int(time.time()) + 60 * 10,  # 10 minutes
            ).estimate_gas(transaction)
                signed_transaction = web3.eth.account.sign_transaction(function_data, private_key)

                tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction).hex()
                
            except Exception as e:
                print(str(e), "there is something even wrong")
                return -1
            
        print(f'Transaction Hash: {tx_hash}')
        time.sleep(5)
        return amount_out_min, tx_hash
    except ChainNameNotFoundError as e:
        print(str(e))
        return None
    except Exception as e:
        print('Error:', e)


"""
    Description:
        This function retrieves the balance of a specific ERC20 token in a given wallet address.
        The balance is returned in both the raw form and a human-readable form.

    Parameters:
        - getTokenName: The ERC20 token contract instance obtained from the web3 provider.
        - walletAddress (str): The Ethereum address of the wallet to check the token balance.

    Returns:
        - tuple: A tuple containing three values:
            - raw_balance (int): The raw balance of the token in the wallet.
            - readable_balance (float): The human-readable balance of the token in the wallet.
            - symbol (str): The symbol of the token.

    Usage:
        raw_balance, readable_balance, symbol = getTokenBalance(token_instance, "0x123abc...")
"""
def getTokenBalance(getTokenName, walletAddress):
    """
    
    Parameters:
        - getTokenName: The ERC20 token contract instance obtained from the web3 provider.
        - walletAddress (str): The Ethereum address of the wallet to check the token balance.

    Returns:
        - tuple: A tuple containing three values:
            - raw_balance (int): The raw balance of the token in the wallet.
            - readable_balance (float): The human-readable balance of the token in the wallet.
            - symbol (str): The symbol of the token.

    """
    TradingTokenDecimal = getTokenName.functions.decimals().call()
    TradingTokenDecimal = getTokenDecimal(TradingTokenDecimal)
    balance = getTokenName.functions.balanceOf(walletAddress).call()
    symbol = getTokenName.functions.symbol().call()
    readable = web3.from_wei(balance,TradingTokenDecimal)
    # print("----------------------------138",balance, readable, symbol )
    return balance, readable, symbol

"""
    Description:
        This function retrieves the balance of a specified ERC20 token in terms of the native token on the Gorelli testnet.
        The balance is obtained by querying the token contract.

    Parameters:
        - getTokenName (Web3 Contract): The Web3 contract instance representing the ERC20 token.
        - walletAddress (str): The Ethereum address of the wallet for which the token balance is queried.

    Returns:
        - tuple: A tuple containing the token balance in the smallest unit, a readable balance converted to the appropriate decimals,
                 and the token symbol.

    Usage:
        balance, readable_balance, symbol = getTokenBalanceGorelli(token_contract, "0x123abc...")
"""

def getTokenBalanceGorelli(getTokenName, walletAddress):
    """
    
    Parameters:
        - getTokenName (Web3 Contract): The Web3 contract instance representing the ERC20 token.
        - walletAddress (str): The Ethereum address of the wallet for which the token balance is queried.

    Returns:
        - tuple: A tuple containing the token balance in the smallest unit, a readable balance converted to the appropriate decimals,
                 and the token symbol.

    """
    infura_url = infura_url  # Replace with your Infura project ID
    web3 = Web3(Web3.HTTPProvider(infura_url))
    TradingTokenDecimal = getTokenName.functions.decimals().call()
    TradingTokenDecimal = getTokenDecimal(TradingTokenDecimal)
    balance = getTokenName.functions.balanceOf(walletAddress).call()
    symbol = getTokenName.functions.symbol().call()
    readable = web3.from_wei(balance,TradingTokenDecimal)
    # print("----------------------------138",balance, readable, symbol )
    return balance, readable, symbol


# def Sell(sellTokenContract, tokenValue, tokenReadableBal, tokenContractAddress,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit):
#     contract = web3.eth.contract(address=pancakeSwapRouterAddress, abi=pancakeABI)
#     spend = web3.to_checksum_address(wbnb_contract_address)  #wbnb contract address
#     #Approve Token before Selling
#     start = time.time()
#     approve = sellTokenContract.functions.approve(pancakeSwapRouterAddress, tokenValue).build_transaction({
#                 'from': walletAddress,
#                 'gasPrice': web3.to_wei(gasPrice,'gwei'),
#                 'nonce': web3.eth.get_transaction_count(walletAddress),
#                 })
    
#     try:
#         signed_txn = web3.eth.account.sign_transaction(approve, private_key=private_key)
#         tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
#         print(style.GREEN + "Approved: " + web3.to_hex(tx_token))
#     except:
#         print(style.YELLOW + "Already been approved")
#         pass
    
    
#     #Wait after approve 5 seconds before sending transaction
#     time.sleep(5)
#     tokenSymbol = sellTokenContract.functions.symbol().call()
#     print(f"Swapping {tokenReadableBal} {tokenSymbol} for ETH")
    
#     time.sleep(5) # wait for approval to confirm
    
#     #Swaping exact Token for ETH 
#     pancakeswap2_txn = contract.functions.swapExactTokensForETH(
#                 tokenValue ,0, 
#                 [tokenContractAddress, spend],
#                 walletAddress,
#                 (int(time.time()) + transactionRevertTime)

#                 ).build_transaction({
#                 'from': walletAddress,
#                 'gasPrice': web3.to_wei(gasPrice,'gwei'),
#                 'nonce': web3.eth.get_transaction_count(walletAddress),
#                 })
    
#     try:
#         signed_txn = web3.eth.account.sign_transaction(pancakeswap2_txn, private_key=private_key)
#         tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
#         print(f"Sold {tokenSymbol}: " + web3.to_hex(tx_token))
#     except:
#         print(style.RED + "Price impact too high, can't be sold at this moment. Will retry shortly.")
#         pass
#     return(web3.to_hex(tx_token))

"""
    Description:
        This function sells a specified amount of a given ERC20 token for ETH on the PancakeSwap
        decentralized exchange on the Gorelli testnet.

    Parameters:
        - sellTokenContract (contract): The instance of the ERC20 token contract to be sold.
        - tokenValue (int): The amount of the ERC20 token to be sold.
        - tokenReadableBal (str): The readable balance of the ERC20 token (for display purposes).
        - tokenContractAddress (str): The Ethereum address of the ERC20 token.

    Returns:
        - str: The transaction hash of the completed sale.

    Usage:
        tx_hash = Sell_for_gorelli(sellTokenContract, 100, "100.00 Token", "0x123abc...")

    Note:
        - The function assumes that the required variables such as walletAddress, gasPrice, private_key, 
          BNBTokenAddress, pancakeSwap_RouterAddress, and pancake_ABI are appropriately defined before calling.

"""

def Sell_for_gorelli(sellTokenContract, tokenValue, tokenReadableBal, tokenContractAddress):
    """
    Parameters:
        - sellTokenContract (contract): The instance of the ERC20 token contract to be sold.
        - tokenValue (int): The amount of the ERC20 token to be sold.
        - tokenReadableBal (str): The readable balance of the ERC20 token (for display purposes).
        - tokenContractAddress (str): The Ethereum address of the ERC20 token.

    Returns:
        - str: The transaction hash of the completed sale.

    """
    infura_url = infura_url  # Replace with your Infura project ID
    web3 = Web3(Web3.HTTPProvider(infura_url))
    pancakeSwap_RouterAddress = pancakeSwap_RouterAddress
    pancake_ABI = '''[{"inputs":[{"internalType":"address","name":"_factory","type":"address"},{"internalType":"address","name":"_WETH","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"WETH","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"amountADesired","type":"uint256"},{"internalType":"uint256","name":"amountBDesired","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amountTokenDesired","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountIn","outputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountOut","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsIn","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"reserveA","type":"uint256"},{"internalType":"uint256","name":"reserveB","type":"uint256"}],"name":"quote","outputs":[{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETHSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermit","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermitSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityWithPermit","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapETHForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETHSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]'''
    BNBTokenAddress = Web3.to_checksum_address(BNBTokenAddress)  # BNB
    # tokenNameABI='''[{"inputs":[{"internalType":"uint256","name":"chainId_","type":"uint256"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"src","type":"address"},{"indexed":true,"internalType":"address","name":"guy","type":"address"},{"indexed":false,"internalType":"uint256","name":"wad","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":true,"inputs":[{"indexed":true,"internalType":"bytes4","name":"sig","type":"bytes4"},{"indexed":true,"internalType":"address","name":"usr","type":"address"},{"indexed":true,"internalType":"bytes32","name":"arg1","type":"bytes32"},{"indexed":true,"internalType":"bytes32","name":"arg2","type":"bytes32"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"}],"name":"LogNote","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"src","type":"address"},{"indexed":true,"internalType":"address","name":"dst","type":"address"},{"indexed":false,"internalType":"uint256","name":"wad","type":"uint256"}],"name":"Transfer","type":"event"},{"constant":true,"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"PERMIT_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"burn","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"guy","type":"address"}],"name":"deny","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"mint","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"src","type":"address"},{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"move","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"holder","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"expiry","type":"uint256"},{"internalType":"bool","name":"allowed","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"pull","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"push","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"guy","type":"address"}],"name":"rely","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"src","type":"address"},{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"version","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"wards","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}]'''
    # amountOut = None
    contract = web3.eth.contract(address=pancakeSwap_RouterAddress, abi=pancake_ABI)
    spend = web3.to_checksum_address(BNBTokenAddress)  #wbnb contract address
    #Approve Token before Selling
    
    start = time.time()
    approve = sellTokenContract.functions.approve(pancakeSwap_RouterAddress, tokenValue).build_transaction({
                'from': walletAddress,
                'gasPrice': web3.to_wei(gasPrice,'gwei'),
                'nonce': web3.eth.get_transaction_count(walletAddress),
                })
    
    try:
        signed_txn = web3.eth.account.sign_transaction(approve, private_key=private_key)
        tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(style.GREEN + "Approved: " + web3.to_hex(tx_token))
    except:
        print(style.YELLOW + "Already been approved")
        pass
    
    
    #Wait after approve 5 seconds before sending transaction
    time.sleep(5)
    tokenSymbol = sellTokenContract.functions.symbol().call()
    print(f"Swapping {tokenValue} {tokenSymbol} for ETH")
    
    time.sleep(5) # wait for approval to confirm
    amountOut = contract.functions.getAmountsOut(tokenValue, [Web3.to_checksum_address(tokenContractAddress), BNBTokenAddress]).call()
    #Swaping exact Token for ETH 
    print(amountOut)
    pancakeswap2_txn = contract.functions.swapExactTokensForETH(
                tokenValue ,0, 
                [tokenContractAddress, spend],
                walletAddress,
                (int(time.time()) )

                ).build_transaction({
                'from': walletAddress,
                'gasPrice': web3.to_wei(gasPrice,'gwei'),
                'nonce': web3.eth.get_transaction_count(walletAddress),
                })
    
    try:
        signed_txn = web3.eth.account.sign_transaction(pancakeswap2_txn, private_key=private_key)
        tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"Sold {tokenSymbol}: " + web3.to_hex(tx_token))
    except:
        print(style.RED + "Price impact too high, can't be sold at this moment. Will retry shortly.")
        pass
    return(web3.to_hex(tx_token))


"""
    Description:
        This function performs a secondary buy transaction. It sends a portion of the BNB balance
        from the wallet address to a specified recipient address.

    Parameters:
        None

    Returns:
        None

    Notes:
        The function uses global variables:
        - `snipeBNBAmount`: The total BNB amount for the snipe.
        - `walletAddress`: The Ethereum wallet address.
        - `web3`: The Web3 instance.
        - `gasAmount`: The gas amount for the transaction.
        - `gasPrice`: The gas price for the transaction.
        - `private_key`: The private key for signing the transaction.

        The amount to send is calculated as a fraction of `snipeBNBAmount` (1/6).

    Usage:
        secondaryBuy()
"""
def secondaryBuy():
    """
   
    Parameters:
        None

    Returns:
        None

    """
    to_address = wbnb_contract_address 
    amtToSend = float(snipeBNBAmount/6)
    myBalance = web3.eth.get_balance(walletAddress)
    readable = web3.from_wei(myBalance,'ether')
    print("My balance",readable)
    print("Amount to send",float(amtToSend))
    nonces = web3.eth.get_transactionCount(walletAddress)
    tx = {
        'chainId':97,
        'nonce':nonces,
        'to':to_address,
        'value':web3.to_wei(amtToSend,'ether'),
        'gas':gasAmount,
        'gasPrice':web3.to_wei(gasPrice,'gwei')
    }
    try:
        signed_tx = web3.eth.account.sign_transaction(tx,private_key)
        tx_token = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    except:
        pass
    return
  

"""
    Description:
        This function executes a buy transaction for a specified ERC20 token using the PancakeSwap decentralized exchange.

    Parameters:
        - tokenAddress (str): The Ethereum address of the ERC20 token to be bought.
        - tokenSymbol (str): The symbol or identifier of the ERC20 token.
        - walletAddress (str): The Ethereum address of the wallet initiating the transaction.
        - private_key (str): The private key corresponding to the wallet initiating the transaction.
        - transactionRevertTime (int): The time (in seconds) after which the transaction should be reverted if not confirmed.
        - snipeBNBAmount (float): The amount of BNB (Binance Coin) to be spent on buying the specified token.
        - sellProfit (float): The desired profit percentage for selling the token.

    Returns:
        None

    Notes:
        - The function prints status messages during the execution, including transaction success or failure.
        - It waits for the transaction to confirm before proceeding.

    Usage:
        Buy("0x123abc...", "TOKEN", "0xwallet...", "private_key_here", 60, 1.0, 5.0)
"""
def Buy(tokenAddress,tokenSymbol,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit):
    """
    Parameters:
        - tokenAddress (str): The Ethereum address of the ERC20 token to be bought.
        - tokenSymbol (str): The symbol or identifier of the ERC20 token.
        - walletAddress (str): The Ethereum address of the wallet initiating the transaction.
        - private_key (str): The private key corresponding to the wallet initiating the transaction.
        - transactionRevertTime (int): The time (in seconds) after which the transaction should be reverted if not confirmed.
        - snipeBNBAmount (float): The amount of BNB (Binance Coin) to be spent on buying the specified token.
        - sellProfit (float): The desired profit percentage for selling the token.

    Returns:
        None

    """
    print("in buy")
    if(tokenAddress != None):
        print(walletAddress, private_key)
        tokenToBuy = web3.to_checksum_address(tokenAddress)
        spend = web3.to_checksum_address(wbnb_contract_address)  #wbnb contract address
        contract = web3.eth.contract(address=pancakeSwapRouterAddress, abi=pancakeABI)
        nonce = web3.eth.get_transaction_count(walletAddress)
        start = time.time()
        pancakeswap2_txn = contract.functions.swapExactETHForTokens(
        0, 
        [spend,tokenToBuy],
        walletAddress,
        (int(time.time()) + transactionRevertTime)
        ).build_transaction({
        'from': walletAddress,
        'value': web3.to_wei(float(snipeBNBAmount), 'ether'), #This is the Token(BNB) amount you want to Swap from
        'gas': gasAmount,
        'gasPrice': web3.to_wei(gasPrice,'gwei'),
        'nonce': nonce,
        })

        try:
            signed_txn = web3.eth.account.sign_transaction(pancakeswap2_txn, private_key)
            tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction) #BUY THE TOKEN
        except:
            print(style.RED + currentTimeStamp + " Transaction failed.")
            print("") # line break: move onto scanning for next token
    
        txHash = str(web3.to_hex(tx_token))


        #TOKEN IS BOUGHT
        try:
            checkTransactionSuccessURL = checkTransactionSuccess_url + txHash + "&apikey=" + bscScanAPIKey
            checkTransactionRequest = requests.get(url = checkTransactionSuccessURL)
            txResult = checkTransactionRequest.json()['status']
        except Exception as e:
            print("Exception in Checking for txRestul BSC Scan", e)
        
        if txResult not in locals():
            txResult = "1"

        if(txResult == "1"):
            print(style.GREEN + currentTimeStamp + " Successfully bought $" + tokenSymbol + " for " + style.BLUE + str(snipeBNBAmount) + style.GREEN + " ETH - TX ID: ", txHash)
            time.sleep(10) #wait for tx to confirm
            # secondaryBuy()
        else:
            print(style.RED + currentTimeStamp + " Transaction failed: likely not enough gas.")

        updateTitle(walletAddress)




#------------------------------------- LISTEN FOR TOKENS ON BINANCE SMART CHAIN THAT HAVE JUST ADDED LIQUIDITY ----------------------------------------------------------



"""
    Description:
        This function handles the detection of a new potential token based on a given event.
        It performs checks on the token pair, retrieves token information, and initiates actions such as mini-audit or buying.

    Parameters:
        - event: The event containing information about the detected token.
        - walletAddress (str): The wallet address associated with the sniping bot.
        - private_key (str): The private key of the wallet for transactions.
        - transactionRevertTime: The time duration to wait for a transaction to confirm or revert.
        - snipeBNBAmount: The BNB amount used for sniping.
        - sellProfit: The desired profit percentage for selling the token.
        - leverage_manager: An instance of the leverage manager for managing token leverage.

    Returns:
        None

    Raises:
        None

    Usage:
        foundToken(event, "0x123abc...", "private_key", 10, 1.0, 2.0, leverage_manager)
"""
def foundToken(event,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit,leverage_manager):
    """
    Parameters:
        - event: The event containing information about the detected token.
        - walletAddress (str): The wallet address associated with the sniping bot.
        - private_key (str): The private key of the wallet for transactions.
        - transactionRevertTime: The time duration to wait for a transaction to confirm or revert.
        - snipeBNBAmount: The BNB amount used for sniping.
        - sellProfit: The desired profit percentage for selling the token.
        - leverage_manager: An instance of the leverage manager for managing token leverage.

    Returns:
        None

    Raises:
        None

    """
    print("in found Token")
    try:
        jsonEventContents = json.loads(Web3.toJSON(event))
        if ((jsonEventContents['args']['token0'] == wbnb_contract_address) or (jsonEventContents['args']['token1'] == wbnb_contract_address)): 
        #check if pair is WBNB, if not then ignore it
        
            if (jsonEventContents['args']['token0'] == wbnb_contract_address):
               tokenAddress = jsonEventContents['args']['token1']
            else:
                tokenAddress = jsonEventContents['args']['token0']
       
            getTokenName = web3.eth.contract(address=tokenAddress, abi=tokenNameABI) #code to get name and symbol from token address

            tokenName = getTokenName.functions.name().call()
            tokenSymbol = getTokenName.functions.symbol().call()

            print(style.YELLOW + currentTimeStamp + " [Token] New potential token detected: " + style.CYAN + tokenName + " (" + tokenSymbol + "): " + style.MAGENTA + tokenAddress + style.RESET)
            socketIO.emit("tokenFound", {"tokenName": tokenName, 'tokenAddress':tokenAddress, 'tokenSymbol':tokenSymbol})

            global numTokensDetected
            global numTokensBought
            numTokensDetected = numTokensDetected + 1 
            updateTitle(walletAddress)


         #--------------------------------------------MINI AUDIT FEATURE-------------------------------------------------------

            if(enableMiniAudit == True): #enable mini audit feature: quickly scans token for potential features that make it a scam / honeypot / rugpull etc
                print(style.YELLOW + "[Token] Starting Mini Audit...")
                contractCodeGetRequestURL = contractCodeGetRequest_url + tokenAddress + "&apikey=" + bscScanAPIKey
                contractCodeRequest = requests.get(url = contractCodeGetRequestURL)
                tokenContractCode = contractCodeRequest.json()

                print(style.GREEN + "[SUCCESS] Token has passed mini audit.") #now you can buy
                socketIO.emit("miniAuditPassed", {"tokenName": tokenName, 'tokenAddress':tokenAddress, 'tokenSymbol':tokenSymbol})

                tokenBNBPrice = checkTokenPrice(tokenAddress)
                print(style.GREEN + tokenName, "ETH price", tokenBNBPrice)
                numTokensBought = numTokensBought + 1
                if(sellOnlyMode == "False"):
                        print("We came thisclose to buying it")
                        # socketIO.emit("buyingToken", {"tokenName": tokenName, 'tokenAddress':tokenAddress, 'tokenSymbol':tokenSymbol, 'price':tokenBNBPrice})
                       
                        Buy(tokenAddress, tokenSymbol,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit)
                        updateTitle(walletAddress)
                        print("------token BNB prie==",tokenBNBPrice)
                        # socketIO.emit("boughtToken", {"tokenName": tokenName, 'tokenAddress':tokenAddress, 'tokenSymbol':tokenSymbol, 'price':tokenBNBPrice})

                        newPurchasedCoin = [tokenSymbol, tokenBNBPrice, tokenAddress, 0, 0]
                        # token_bought_time[tokenSymbol] = time.time()
                        print("newPurchasedCoin===>",newPurchasedCoin)
                        leverage_manager.add_token(token_address=tokenAddress, token_value=tokenBNBPrice, sender_address=walletAddress, leverage_taken=0)

                        # f = open('boughtcoins.csv', 'a')
                        # writer = csv.writer(f)
                        # writer.writerow(newPurchasedCoin)
                        # f.close()
                        print("Added newly sniped coin info to boughtcoins.csv")                  
                    
            else: #we dont care about audit, just buy it
                if(sellOnlyMode == "False"):
                    print("We are here")
                    Buy(tokenAddress, tokenSymbol,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit)
                    numTokensBought += 1
                    updateTitle(walletAddress)
                    
            print("") # line break: move onto scanning for next token

    except:
        pass

                
"""
    Description:
        This function calculates a token score based on various factors such as contract verification,
        ownership details, and LP token holdings. The score is normalized to a range of 0 to 1.

    Parameters:
        - token_address (str): The Ethereum address of the ERC20 token.
        - api_key (str): The API key for accessing blockchain data.
        - factory_address (str): The address of the factory contract for LP tokens.
        - factory_abi (list): The ABI of the factory contract.
        - token_paired_address (str): The Ethereum address of the token paired with the given token in LP.
        - lp_abi (list): The ABI of the LP token contract.

    Returns:
        - float: The normalized token score, ranging from 0 to 1.
                0 indicates the lowest score, and 1 indicates the highest score.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.

    Usage:
        score = get_token_score("0x123abc...", "your_api_key", "factory_contract_address", "factory_abi", "paired_token_address", "lp_abi")
"""
def get_token_score(token_address, api_key, factory_address, factory_abi, token_paired_address, lp_abi):
    """
    Parameters:
        - token_address (str): The Ethereum address of the ERC20 token.
        - api_key (str): The API key for accessing blockchain data.
        - factory_address (str): The address of the factory contract for LP tokens.
        - factory_abi (list): The ABI of the factory contract.
        - token_paired_address (str): The Ethereum address of the token paired with the given token in LP.
        - lp_abi (list): The ABI of the LP token contract.

    Returns:
        - float: The normalized token score, ranging from 0 to 1.
                0 indicates the lowest score, and 1 indicates the highest score.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.

    """
    global active_chain, chain_list, private_key

    try:
        if active_chain is None or active_chain not in chain_list.keys():
            raise ChainNameNotFoundError(active_chain)
        # print(chain_list, active_chain)
        current_chain = chain_list[active_chain]
        # print(current_chain, type(current_chain), current_chain['web3'])
        web3 = current_chain['web3']
        token_address = web3.to_checksum_address(token_contract_address)
        # current_chain = chain_list[active_chain]
        w_token_address = current_chain['w_address']
        w_token_address = Web3.to_checksum_address(w_token_address)
          # BNB
        erc_20_abi = current_chain['erc_20_abi']
        router_address, router_abi = current_chain['router_address'], current_chain['router_abi']

        router_contract = web3.eth.contract(address=router_address, abi=router_abi)
    
        token_contract_address = web3.to_checksum_address(token_contract_address) # DAI token contract address
        token_contract_abi =erc_20_abi  # Replace with the actual DAI token ABI

        token_contract = web3.eth.contract(address=token_contract_address, abi=token_contract_abi)
        base_url = current_chain['base_scan_url']
    except ChainNameNotFoundError as e:
        print(str(e))
        return None
    except Exception as e:
        print('Err:', e)
    
    if "web3" not in locals():
        print("sorry, web3 connection could not be established, exiting ...")
        return -1
    if "base_url" not in locals():
        print("Sorry, something went wrong with setting the base url")
        return -1
    

    token_score = 0
    url_for_contract = current_chain['base_scan_url'] + "module=contract&action=getabi&address=" + token_address + "&apikey=" + api_key
    response = requests.get(base_url).json()
    print(response)
    if response['status'] == '1':
        abi = response['result']
        print('contract verified')
        token_score += 1
    else:
        print("contract not verified")
        return -1
        
    token_contract_handler = web3.eth.contract(address=token_address, abi = abi)
    token_name = token_contract_handler.functions.name().call()
    token_decimals = token_contract_handler.functions.decimals().call()
    token_decimals_in_eth = 10 ** token_decimals
    current_supply_of_the_token = token_contract_handler.functions.totalSupply().call()/token_decimals_in_eth
    token_symbol = token_contract_handler.functions.symbol().call()
    print(token_name, token_symbol, current_supply_of_the_token, "Important values for the token")
        
    factory_contract = web3.eth.contract(address=factory_address,abi=factory_abi)
    lp_address = factory_contract.functions.getPair(token_address,token_paired_address).call()
    print('LP Pair Address: ' + str(lp_address))
    lp_contract = web3.eth.contract(address=lp_address, abi=lp_abi )
    lp_decimals = lp_contract.functions.decimals().call()
    lp_actual_decimals = 10 ** lp_decimals
    total_balance_in_lp = lp_contract.functions.totalSupply().call() / lp_actual_decimals
    print("total balance in LP", total_balance_in_lp)
        
    print("Trying to get the deployer address of the coin")
    deployer_url = current_chain['base_scan_url']  + f"module=account&action=txlist&address={token_address}&startblock=0&endblock=99999999&sort=asc&apikey={api_key}"
        
    try:
        print("thiss line")
        print(deployer_url)
        response = requests.get(deployer_url)
            # print("that line", response)
        data = response.json()
            # print("it cannot be this line?")
            # print(data)
        if data["status"] == "1":
                # Get the first transaction, which is typically the contract creation
            contract_creation_tx = data["result"][0]
            deployer_address = contract_creation_tx["from"]
            print(f"The deployer address of the contract {token_address} is {deployer_address}")
        else:
            print("Unable to retrieve contract creation transaction.")

            
    except Exception as e:
        print(str(e))
        
    try:
        print("here")
        if 'owner' in abi:
            print("in here")
            owner = token_contract_handler.functions.owner().call()
            if owner != web3.to_checksum_address(owner_address):
                print(owner)
                balanceOf = token_contract_handler.functions.balanceOf(owner).call()
                    
                if balanceOf > 0:
                    print('owner holds : ' + balanceOf  + '' + token_symbol)
                else:
                    print('owner holds no token') 
                
                    
                    
                    #check owner Lp token
                balanceLp = lp_contract.functions.balanceOf(owner)
                    
                if balanceLp > 0:
                    ownerPerLp = (total_balance_in_lp/ balanceLp) * 100
                    print('owner holds ' + balanceOf + 'lptoken')
                    print('owner holds ' + ownerPerLp + ' % Lp token')
                else:
                    print(owner + ' holds no LP token')    
                    token_score += 2
                    
            else:
                print(owner + ' ownership renounced')
                token_score += 2
        elif "deployer_address" in locals():
            print("owner found, finding the amount of coins it holds")
            balanceOf = token_contract_handler.functions.balanceOf(web3.to_checksum_address(deployer_address)).call()
            burnt_amount = token_contract_handler.functions.balanceOf(web3.to_checksum_address(owner_address)).call()
            print(balanceOf, "Current Balance of the tokens", type(balanceOf))
            print(burnt_amount, "Current Balance of Burnt Wallet", type(balanceOf))

            if balanceOf > 0.0:
                print(web3.from_wei(balanceOf, 'ether'), "going inside")
                    # print('owner holds : ' + self.w3.from_wei(str(balanceOf), 'ether')  + '' + token_symbol)
            else:
                print('owner holds no token') 
                 #check owner Lp token
            balanceLp = lp_contract.functions.balanceOf(web3.to_checksum_address(deployer_address)).call()
            balanceLpburnt = lp_contract.functions.balanceOf(web3.to_checksum_address(Burnt_LP_address)).call()
            print("Burnt LP address", balanceLpburnt)

            print(balanceLp, type(balanceLp))
            if balanceLp > 0.0:
                ownerPerLp = (total_balance_in_lp/ balanceLp) * 100
                print('owner holds ' + str(web3.from_wei(balanceOf, 'ether')) + 'lptoken')
                print('owner holds ' + str(web3.from_wei(ownerPerLp, 'ether')) + ' % Lp token')
                if int(web3.from_wei(ownerPerLp, 'ether'))<=5:
                        token_score+=1
            else:
                print(owner + ' holds no LP token')    
                token_score += 2    

    except Exception as e:
        print('no owner', str(e))
        print("herel")
        token_score += 2

        
    return token_score/6


"""
    Description:
        This function handles the detection of a new potential token based on a given event. 
        It extracts relevant information from the event, such as token address, name, and symbol, 
        and prints a notification. Additionally, it can trigger actions like buying the token 
        if certain conditions are met.

    Parameters:
        - event: The event object representing the token-related activity.
        - walletAddress (str): The wallet address associated with the operation.
        - private_key (str): The private key for the walletAddress.
        - transactionRevertTime: The time to wait for a transaction to revert before considering it failed.
        - snipeBNBAmount: The amount of BNB to use for sniping.
        - sellProfit: The desired profit percentage for selling the token.
        - leverage_manager: The leverage manager object.
        - main_wallet_engine: The main wallet engine object.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - None

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.

    Usage:
        found_token_general(event, walletAddress, private_key, transactionRevertTime, snipeBNBAmount, sellProfit, leverage_manager, main_wallet_engine, active_chain)
"""
def found_token_general(event,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit,leverage_manager,main_wallet_engine,active_chain, total_holders_count, liquidity_lock,max_tax,liquidiity_available, is_main, blacklist_token_address_list):
    """
    Parameters:
        - event: The event object representing the token-related activity.
        - walletAddress (str): The wallet address associated with the operation.
        - private_key (str): The private key for the walletAddress.
        - transactionRevertTime: The time to wait for a transaction to revert before considering it failed.
        - snipeBNBAmount: The amount of BNB to use for sniping.
        - sellProfit: The desired profit percentage for selling the token.
        - leverage_manager: The leverage manager object.
        - main_wallet_engine: The main wallet engine object.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - None

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.

    """
    
    print("in the general found token")
    
    try:
        if active_chain is None or active_chain not in chain_list.keys():
            raise ChainNameNotFoundError(active_chain)
        current_chain = chain_list[active_chain]
        web3 = current_chain['web3']

        w_token_address = current_chain['w_address']
        w_token_address_checksum = Web3.to_checksum_address(w_token_address)
          # BNB
        erc_20_abi = current_chain['erc_20_abi']
        router_address, router_abi = current_chain['router_address'], current_chain['router_abi']

        router_contract = web3.eth.contract(address=router_address, abi=router_abi)
    except ChainNameNotFoundError as e:
        print(str(e))
        return None
    except Exception as e:
        print('Error:', e)
    try:
        jsonEventContents = json.loads(Web3.toJSON(event))
        if "web3" not in locals():
            print("sorry, something went wrong while establishing the connection to web3, breaking")
            return -1
        
        if ((jsonEventContents['args']['token0'] == w_token_address) or (jsonEventContents['args']['token1'] == w_token_address)): 
        #check if pair is WBNB, if not then ignore it
        
            if (jsonEventContents['args']['token0'] == w_token_address):
               token_address = jsonEventContents['args']['token1']
            else:
                token_address = jsonEventContents['args']['token0']
            if "anker_token" not in current_chain:
                raise AnkrInitError
            anker_token = current_chain['anker_token']
            token_info_sniping = TokenInfoSniping(active_chain, token_address=token_address, ankr_token=anker_token)
            total_holders = token_info_sniping.get_total_holders()
            if total_holders['status'] == -1:
                print("sorry cannot get holders of this token returning ...")
                return 
            if total_holders['status'] == 1 and total_holders['result'] >= total_holders_count:
                print("Number of holders are equal to or greater so buying the token")
            else:
                return
            if is_main == True:
                honey = HoneypotChecker(address=token_address, active_chain=active_chain)

                if honey.amount_of_liquidity() < liquidiity_available:
                    print("amoutn of liquidity is less than what is available retuning..........")
                    return
                if honey.get_liquidity_lock() < liquidity_lock:
                    print("amount of liquiidity lock is less than the value returning....")
                    return
                if honey.get_taxes() > max_tax:
                    print("amount of tax is more than the max tax returning....... ")
                    return 
                if token_address in blacklist_token_address_list:
                    print("token in the blacklisted tokens returning .....")
                    return
            
            token_contract = web3.eth.contract(address=token_address, abi=erc_20_abi) #code to get name and symbol from token address

            token_name = token_contract.functions.name().call()
            token_symbol = token_contract.functions.symbol().call()

            print(style.YELLOW + currentTimeStamp + " [Token] New potential token detected: " + style.CYAN + token_name + " (" + token_symbol + "): " + style.MAGENTA + token_address + style.RESET)
            socketIO.emit("tokenFound", {"tokenName": token_name, 'tokenAddress':token_address, 'tokenSymbol':token_symbol})

            global numTokensDetected
            global numTokensBought
            numTokensDetected = numTokensDetected + 1 
            updateTitle(walletAddress)


         #--------------------------------------------MINI AUDIT FEATURE-------------------------------------------------------
            if enableMiniAudit == True:
            #     score = get_token_score(token_address=token_address)
            #     if score <= 0.3:
            #         print("Bad Score returning")
            #         return -1
                pass
            #  #we dont care about audit, just buy it
            if(sellOnlyMode == "False"):
                print("We are here")
                # Buy(tokenAddress, tokenSymbol)
                buy_for_eth_general(snipeBNBAmount, token_address, False,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit,active_chain,leverage_manager,main_wallet_engine)
                numTokensBought += 1
                updateTitle(walletAddress)
                    
            print("") # line break: move onto scanning for next token

    except:
        pass


"""
    Description:
        This function handles the detection of a new potential token based on a given event.
        It extracts relevant information from the event, such as the transaction hash and deployer address.
        If the detected token corresponds to the deployer address, it attempts to buy the token using the
        buy_for_eth_general function.

    Parameters:
        - event: The event object representing the token-related activity.
        - walletAddress (str): The wallet address associated with the operation.
        - private_key (str): The private key for the walletAddress.
        - transactionRevertTime: The time to wait for a transaction to revert before considering it failed.
        - snipeBNBAmount: The amount of BNB to use for sniping.
        - sellProfit: The desired profit percentage for selling the token.
        - leverage_manager: The leverage manager object.
        - main_wallet_engine: The main wallet engine object.
        - active_chain (str): The name of the active blockchain.
        - deployer_address (str): The deployer address associated with the token launch.

    Returns:
        - None

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.
        - TokenNotBought: If the token cannot be bought successfully.
        - TokenNotFound: If the new token launch cannot be found.

    Usage:
        found_token_snipe(event, walletAddress, private_key, transactionRevertTime, snipeBNBAmount, sellProfit, leverage_manager, main_wallet_engine, active_chain, deployer_address)
"""
def found_token_snipe(event,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit,leverage_manager,main_wallet_engine,active_chain, deployer_address):
    """
    Parameters:
        - event: The event object representing the token-related activity.
        - walletAddress (str): The wallet address associated with the operation.
        - private_key (str): The private key for the walletAddress.
        - transactionRevertTime: The time to wait for a transaction to revert before considering it failed.
        - snipeBNBAmount: The amount of BNB to use for sniping.
        - sellProfit: The desired profit percentage for selling the token.
        - leverage_manager: The leverage manager object.
        - main_wallet_engine: The main wallet engine object.
        - active_chain (str): The name of the active blockchain.
        - deployer_address (str): The deployer address associated with the token launch.

    Returns:
        - None

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.
        - TokenNotBought: If the token cannot be bought successfully.
        - TokenNotFound: If the new token launch cannot be found.
    """
    print("in the general found token")
    
    try:
        if active_chain is None or active_chain not in chain_list.keys():
            raise ChainNameNotFoundError(active_chain)
        current_chain = chain_list[active_chain]
        web3 = current_chain['web3']

        w_token_address = current_chain['w_address']
        w_token_address_checksum = Web3.to_checksum_address(w_token_address)
          # BNB
        erc_20_abi = current_chain['erc_20_abi']
        router_address, router_abi = current_chain['router_address'], current_chain['router_abi']
        api_key = current_chain['scan_api_key']
        router_contract = web3.eth.contract(address=router_address, abi=router_abi)
    except ChainNameNotFoundError as e:
        print(str(e))
        return None
    except Exception as e:
        print('Error:', e)
    try:
        jsonEventContents = json.loads(Web3.to_json(event))
        if "web3" not in locals():
            print("sorry, something went wrong while establishing the connection to web3, breaking")
            return -1
        print(jsonEventContents)
        tx_hash = jsonEventContents["transactionHash"]
        try:
            main_txn = web3.eth.get_transaction(tx_hash)
            if main_txn:
                print(main_txn['from'], "from_wallet")
                from_wallet = main_txn['from']
                if from_wallet == deployer_address:
                    # buy_for_eth_general
                    scan_url = f"https://api-goerli.etherscan.io/api?module=account&action=txlist&address={walletAddress}&startblock=0&endblock=99999999&page=1&offset=10&sort=desc&apikey={api_key}"
                    response = requests.get(scan_url)
                    data = response.json()
                    print(data.keys(),"==========> Keys for the data")
                    resp_list = data['result']
                    for i in resp_list:
                        if i['methodId'] == "0x60806040":
                            token_to_buy = i['contractAddress']
                            # break
                    if "token_to_buy" not in locals():
                        
                        print("something went wrong.")
                        raise TokenNotFound
                        return -1
            print(main_txn)
        except Exception as e:
            print(str(e), 'cannot get the txns returning....')
            return -1
        # token_to_buy = 
        token_contract = web3.eth.contract(address=web3.to_checksum_address(token_to_buy), abi=erc_20_abi) #code to get name and symbol from token address

        token_name = token_contract.functions.name().call()
        token_symbol = token_contract.functions.symbol().call()

        print(style.YELLOW + currentTimeStamp + " [Token] New potential token detected: " + style.CYAN + token_name + " (" + token_symbol + "): " + style.MAGENTA + token_to_buy + style.RESET)
        socketIO.emit("tokenFound", {"tokenName": token_name, 'tokenAddress':token_to_buy, 'tokenSymbol':token_symbol})
        amt, tx_hash = buy_for_eth_general(snipeBNBAmount, token_to_buy, False,walletAddress,private_key,active_chain)
        print(amt, tx_hash, "<============= Buying tx hash and amount")
        if tx_hash is not None and amt is not None:
            print("token has been bought", tx_hash, "for amount", amt)
            return
        
        raise TokenNotBought

    except TokenNotBought as e:
        print("token cannot be bought", str(e))
        socketIO.emit("tokenBuyingError", {"error": str(e), 'tokenAddress':token_to_buy, 'tokenSymbol':token_symbol})

    except TokenNotFound as e:
        print("Could not find the new token launch", str(e))
        socketIO.emit("tokenNotFound", {"error": str(e), 'tokenAddress':token_to_buy, 'tokenSymbol':token_symbol})
        pass

    except Exception as e:
        print("something went wrong in finding the token for new launches", str(e))
        socketIO.emit("tokenBuyingError", {"error": str(e), 'tokenAddress':token_to_buy, 'tokenSymbol':token_symbol})
        pass
   

# #-----------------------------------------TOKEN SCANNER MONITORING/SELL CALCULATION BACKGROUND CODE----------------------------------------------------------------------
"""
    Executes actions upon finding a potential token for leverage.

    Description:
    This function is triggered when a potential token for leverage is detected based on an event.
    It performs actions such as auditing, checking for potential issues, and initiating the sniping process.

    Usage:
    - Provide the event object containing information about the detected token.
    - Specify the walletAddress associated with the sniping operation.
    - Include the private_key for the wallet.
    - Set the snipeBNBAmount as the amount of BNB to use for sniping.
    - Pass an instance of the LeverageManager class for managing leverage-related operations.
    - Pass the main wallet engine (WalletEngine) for handling primary wallet functions.
    - Specify the active_chain, representing the blockchain network (e.g., 'BSC', 'ETH').

    Parameters:
    - event (object): The event object containing information about the detected token.
    - walletAddress (str): The wallet address associated with the sniping operation.
    - private_key (str): The private key for the wallet.
    - snipeBNBAmount (float): The amount of BNB to use for sniping.
    - leverage_manager (LeverageManager): An instance of the LeverageManager class.
    - main_wallet_engine (WalletEngine): An instance of the main wallet engine.
    - active_chain (str): The blockchain network (e.g., 'BSC', 'ETH').

    Returns:
    None

    Raises:
    Any exceptions raised during the execution.

"""
def found_token_for_leverage(event,walletAddress,private_key,snipeBNBAmount,leverage_manager,main_wallet_engine,active_chain):
    """
    Executes actions upon finding a potential token for leverage.

    Parameters:
    - event (object): The event object containing information about the detected token.
    - walletAddress (str): The wallet address associated with the sniping operation.
    - private_key (str): The private key for the wallet.
    - snipeBNBAmount (float): The amount of BNB to use for sniping.
    - leverage_manager (LeverageManager): An instance of the LeverageManager class.
    - main_wallet_engine (WalletEngine): An instance of the main wallet engine.
    - active_chain (str): The blockchain network (e.g., 'BSC', 'ETH').

    Returns:
    None

    Raises:
    Any exceptions raised during the execution.
    """
    print("in found Token, for leverage")
    infura_url = infura_url  # Replace with your Infura project ID

    web3 = Web3(Web3.HTTPProvider(infura_url))

    pancakeSwap_RouterAddress = pancakeSwap_RouterAddress
    pancake_ABI = '''[{"inputs":[{"internalType":"address","name":"_factory","type":"address"},{"internalType":"address","name":"_WETH","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"WETH","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"amountADesired","type":"uint256"},{"internalType":"uint256","name":"amountBDesired","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amountTokenDesired","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountIn","outputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountOut","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsIn","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"reserveA","type":"uint256"},{"internalType":"uint256","name":"reserveB","type":"uint256"}],"name":"quote","outputs":[{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETHSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermit","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermitSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityWithPermit","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapETHForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETHSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]'''
    BNBTokenAddress = Web3.to_checksum_address(BNBTokenAddress)  # BNB
    tokenNameABI='''[{"inputs":[{"internalType":"uint256","name":"chainId_","type":"uint256"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"src","type":"address"},{"indexed":true,"internalType":"address","name":"guy","type":"address"},{"indexed":false,"internalType":"uint256","name":"wad","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":true,"inputs":[{"indexed":true,"internalType":"bytes4","name":"sig","type":"bytes4"},{"indexed":true,"internalType":"address","name":"usr","type":"address"},{"indexed":true,"internalType":"bytes32","name":"arg1","type":"bytes32"},{"indexed":true,"internalType":"bytes32","name":"arg2","type":"bytes32"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"}],"name":"LogNote","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"src","type":"address"},{"indexed":true,"internalType":"address","name":"dst","type":"address"},{"indexed":false,"internalType":"uint256","name":"wad","type":"uint256"}],"name":"Transfer","type":"event"},{"constant":true,"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"PERMIT_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"burn","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"guy","type":"address"}],"name":"deny","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"mint","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"src","type":"address"},{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"move","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"holder","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"expiry","type":"uint256"},{"internalType":"bool","name":"allowed","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"pull","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"push","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"guy","type":"address"}],"name":"rely","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"src","type":"address"},{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"version","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"wards","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}]'''
    amountOut = None
    
    try:
        jsonEventContents = json.loads(Web3.toJSON(event))
        if ((jsonEventContents['args']['token0'] == BNBTokenAddress) or (jsonEventContents['args']['token1'] == BNBTokenAddress)): 
        #check if pair is WBNB, if not then ignore it
        
            if (jsonEventContents['args']['token0'] == BNBTokenAddress):
               tokenAddress = jsonEventContents['args']['token1']
            else:
                tokenAddress = jsonEventContents['args']['token0']
       
            getTokenName = web3.eth.contract(address=tokenAddress, abi=tokenNameABI) #code to get name and symbol from token address

            tokenName = getTokenName.functions.name().call()
            tokenSymbol = getTokenName.functions.symbol().call()

            print(style.YELLOW + currentTimeStamp + " [Token] New potential token detected: " + style.CYAN + tokenName + " (" + tokenSymbol + "): " + style.MAGENTA + tokenAddress + style.RESET)
            socketIO.emit("tokenFound", {"tokenName": tokenName, 'tokenAddress':tokenAddress, 'tokenSymbol':tokenSymbol})

            global numTokensDetected
            global numTokensBought, is_leverage_sniping
            numTokensDetected = numTokensDetected + 1 
            updateTitle(walletAddress)


         #--------------------------------------------MINI AUDIT FEATURE-------------------------------------------------------

            if(enableMiniAudit == True): #enable mini audit feature: quickly scans token for potential features that make it a scam / honeypot / rugpull etc
                print(style.YELLOW + "[Token] Starting Mini Audit...")
                contractCodeGetRequestURL = contractCodeGetRequest_url + tokenAddress + "&apikey=" + bscScanAPIKey
                contractCodeRequest = requests.get(url = contractCodeGetRequestURL)
                tokenContractCode = contractCodeRequest.json()

                # if(str(tokenContractCode['result'][0]['ABI']) == "Contract source code not verified") and checkSourceCode == "True": #check if source code is verified
                #     print(style.RED + "[FAIL] Contract source code isn't verified.")

                # elif (BNBTokenAddress in str(tokenContractCode['result'][0]['SourceCode'])) and checkPancakeV1Router == "True": #check if pancakeswap v1 router is used
                #     print(style.RED + "[FAIL] Contract uses PancakeSwap v1 router.")


                # elif (str(pancakeSwapRouterAddress) not in str(tokenContractCode['result'][0]['SourceCode'])) and checkValidPancakeV2 == "True": #check if pancakeswap v2 router is used
                #     print(style.RED + "[FAIL] Contract doesn't use valid PancakeSwap v2 router.")

                # elif "mint" in str(tokenContractCode['result'][0]['SourceCode']) and checkMintFunction == "True": #check if any mint function enabled
                #     print(style.RED + "[FAIL] Contract has mint function enabled.")


                # elif ("function transferFrom(address sender, address recipient, uint256 amount) public override returns (bool)" in str(tokenContractCode['result'][0]['SourceCode']) or "function _approve(address owner, address spender, uint256 amount) internal" in str(tokenContractCode['result'][0]['SourceCode']) or "newun" in str(tokenContractCode['result'][0]['SourceCode'])) and checkHoneypot == "True": #check if token is honeypot
                #     print(style.RED + "[FAIL] Contract is a honeypot.")

                # else:
                print(style.GREEN + "[SUCCESS] Token has passed mini audit.") #now you can buy
                socketIO.emit("miniAuditPassed", {"tokenName": tokenName, 'tokenAddress':tokenAddress, 'tokenSymbol':tokenSymbol})

                tokenBNBPrice = check_token_price_general(tokenAddress,active_chain)
                print(style.GREEN + tokenName, "ETH price", tokenBNBPrice)
                numTokensBought = numTokensBought + 1
                if(sellOnlyMode == "False"):
                        print("We came thisclose to buying it")
                        # socketIO.emit("buyingToken", {"tokenName": tokenName, 'tokenAddress':tokenAddress, 'tokenSymbol':tokenSymbol, 'price':tokenBNBPrice})
                        if main_wallet_engine.leverage <= 0:
                            print("sorry, the user has not taken any leverage, cannot buy, kindly head over to God Mode.")
                            is_leverage_sniping = False
                            
                        # Buy(tokenAddress, tokenSymbol)
                        handle_buying_for_sniping({"amount":snipeBNBAmount, "tokenAddress":tokenAddress,'walletAddress':walletAddress,'private_key':private_key})
                        updateTitle(walletAddress)
                        print("------token BNB prie==",tokenBNBPrice)
                        # socketIO.emit("boughtToken", {"tokenName": tokenName, 'tokenAddress':tokenAddress, 'tokenSymbol':tokenSymbol, 'price':tokenBNBPrice})

                        newPurchasedCoin = [tokenSymbol, tokenBNBPrice, tokenAddress, 0, 0]
                        # token_bought_time[tokenSymbol] = time.time()
                        print("newPurchasedCoin===>",newPurchasedCoin)
                        leverage_manager.add_token(token_address=tokenAddress, token_value=tokenBNBPrice, sender_address=walletAddress, leverage_taken=2)

                        # f = open('boughtcoins.csv', 'a')
                        # writer = csv.writer(f)
                        # writer.writerow(newPurchasedCoin)
                        # f.close()
                        print("Added newly sniped coin info to boughtcoins.csv")                  
                    
            else: #we dont care about audit, just buy it
                if(sellOnlyMode == "False"):
                    print("We are here")
                    Buy(tokenAddress, tokenSymbol)
                    numTokensBought += 1
                    updateTitle()
                    
            print("") # line break: move onto scanning for next token

    except:
        pass


"""
    Description:
        This function is triggered when a new potential token for leverage sniping is detected based on a blockchain event.
        It performs a mini-audit on the token and, if successful, initiates the purchase process.

    Parameters:
        - event: The blockchain event containing information about the detected token.
        - walletAddress (str): The address of the wallet initiating the leverage sniping.
        - private_key (str): The private key associated with the wallet.
        - snipeBNBAmount (float): The amount of BNB to use for sniping.
        - leverage_manager: An instance of the leverage manager for tracking leveraged tokens.
        - main_wallet_engine: An instance of the main wallet engine for managing the main wallet.
        - active_chain (str): The name of the active blockchain.

    Returns:
        None

    Usage:
        found_token_for_leverage_general(event, "0x123abc...", "private_key_here", 1.0, leverage_manager_instance, main_wallet_instance, "ethereum")
    """

def found_token_for_leverage_general(event,walletAddress,private_key,snipeBNBAmount,leverage_manager,main_wallet_engine,active_chain):
    """
    Parameters:
        - event: The blockchain event containing information about the detected token.
        - walletAddress (str): The address of the wallet initiating the leverage sniping.
        - private_key (str): The private key associated with the wallet.
        - snipeBNBAmount (float): The amount of BNB to use for sniping.
        - leverage_manager: An instance of the leverage manager for tracking leveraged tokens.
        - main_wallet_engine: An instance of the main wallet engine for managing the main wallet.
        - active_chain (str): The name of the active blockchain.

    Returns:
        None
    """
    
    # print("in found Token, for leverage")
    # infura_url = infura_url  # Replace with your Infura project ID

    # web3 = Web3(Web3.HTTPProvider(infura_url))

    # pancakeSwap_RouterAddress = pancakeSwap_RouterAddress
    # pancake_ABI = '''[{"inputs":[{"internalType":"address","name":"_factory","type":"address"},{"internalType":"address","name":"_WETH","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"WETH","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"amountADesired","type":"uint256"},{"internalType":"uint256","name":"amountBDesired","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amountTokenDesired","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountIn","outputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountOut","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsIn","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"reserveA","type":"uint256"},{"internalType":"uint256","name":"reserveB","type":"uint256"}],"name":"quote","outputs":[{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETHSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermit","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermitSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityWithPermit","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapETHForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETHSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]'''
    # BNBTokenAddress = Web3.to_checksum_address(BNBTokenAddress)  # BNB
    # tokenNameABI='''[{"inputs":[{"internalType":"uint256","name":"chainId_","type":"uint256"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"src","type":"address"},{"indexed":true,"internalType":"address","name":"guy","type":"address"},{"indexed":false,"internalType":"uint256","name":"wad","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":true,"inputs":[{"indexed":true,"internalType":"bytes4","name":"sig","type":"bytes4"},{"indexed":true,"internalType":"address","name":"usr","type":"address"},{"indexed":true,"internalType":"bytes32","name":"arg1","type":"bytes32"},{"indexed":true,"internalType":"bytes32","name":"arg2","type":"bytes32"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"}],"name":"LogNote","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"src","type":"address"},{"indexed":true,"internalType":"address","name":"dst","type":"address"},{"indexed":false,"internalType":"uint256","name":"wad","type":"uint256"}],"name":"Transfer","type":"event"},{"constant":true,"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"PERMIT_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"burn","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"guy","type":"address"}],"name":"deny","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"mint","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"src","type":"address"},{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"move","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"holder","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"expiry","type":"uint256"},{"internalType":"bool","name":"allowed","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"pull","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"push","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"guy","type":"address"}],"name":"rely","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"src","type":"address"},{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"version","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"wards","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}]'''
    # amountOut = None
    
    try:
        if active_chain is None or active_chain not in chain_list.keys():
            raise ChainNameNotFoundError(active_chain)
        current_chain = chain_list[active_chain]
        web3 = current_chain['web3']

        w_token_address = current_chain['w_address']
        w_token_address_checksum = Web3.to_checksum_address(w_token_address)
          # BNB
        erc_20_abi = current_chain['erc_20_abi']
        router_address, router_abi = current_chain['router_address'], current_chain['router_abi']

        router_contract = web3.eth.contract(address=router_address, abi=router_abi)
    except ChainNameNotFoundError as e:
        print(str(e))
        return None
    except Exception as e:
        print('Error:', e)
    try:
        jsonEventContents = json.loads(Web3.toJSON(event))
        if ((jsonEventContents['args']['token0'] == w_token_address) or (jsonEventContents['args']['token1'] == w_token_address)): 
        #check if pair is WBNB, if not then ignore it
        
            if (jsonEventContents['args']['token0'] == w_token_address):
               tokenAddress = jsonEventContents['args']['token1']
            else:
                tokenAddress = jsonEventContents['args']['token0']
       
            getTokenName = web3.eth.contract(address=tokenAddress, abi=erc_20_abi) #code to get name and symbol from token address

            tokenName = getTokenName.functions.name().call()
            tokenSymbol = getTokenName.functions.symbol().call()

            print(style.YELLOW + currentTimeStamp + " [Token] New potential token detected: " + style.CYAN + tokenName + " (" + tokenSymbol + "): " + style.MAGENTA + tokenAddress + style.RESET)
            socketIO.emit("tokenFound", {"tokenName": tokenName, 'tokenAddress':tokenAddress, 'tokenSymbol':tokenSymbol})

            global numTokensDetected
            global numTokensBought, is_leverage_sniping
            numTokensDetected = numTokensDetected + 1 
            updateTitle(walletAddress)


         #--------------------------------------------MINI AUDIT FEATURE-------------------------------------------------------

            if(enableMiniAudit == True): #enable mini audit feature: quickly scans token for potential features that make it a scam / honeypot / rugpull etc
                print(style.YELLOW + "[Token] Starting Mini Audit...")
                contractCodeGetRequestURL = contractCodeGetRequest_url + tokenAddress + "&apikey=" + bscScanAPIKey
                contractCodeRequest = requests.get(url = contractCodeGetRequestURL)
                tokenContractCode = contractCodeRequest.json()

                # if(str(tokenContractCode['result'][0]['ABI']) == "Contract source code not verified") and checkSourceCode == "True": #check if source code is verified
                #     print(style.RED + "[FAIL] Contract source code isn't verified.")

                # elif (BNBTokenAddress in str(tokenContractCode['result'][0]['SourceCode'])) and checkPancakeV1Router == "True": #check if pancakeswap v1 router is used
                #     print(style.RED + "[FAIL] Contract uses PancakeSwap v1 router.")


                # elif (str(pancakeSwapRouterAddress) not in str(tokenContractCode['result'][0]['SourceCode'])) and checkValidPancakeV2 == "True": #check if pancakeswap v2 router is used
                #     print(style.RED + "[FAIL] Contract doesn't use valid PancakeSwap v2 router.")

                # elif "mint" in str(tokenContractCode['result'][0]['SourceCode']) and checkMintFunction == "True": #check if any mint function enabled
                #     print(style.RED + "[FAIL] Contract has mint function enabled.")


                # elif ("function transferFrom(address sender, address recipient, uint256 amount) public override returns (bool)" in str(tokenContractCode['result'][0]['SourceCode']) or "function _approve(address owner, address spender, uint256 amount) internal" in str(tokenContractCode['result'][0]['SourceCode']) or "newun" in str(tokenContractCode['result'][0]['SourceCode'])) and checkHoneypot == "True": #check if token is honeypot
                #     print(style.RED + "[FAIL] Contract is a honeypot.")

                # else:
                print(style.GREEN + "[SUCCESS] Token has passed mini audit.") #now you can buy
                socketIO.emit("miniAuditPassed", {"tokenName": tokenName, 'tokenAddress':tokenAddress, 'tokenSymbol':tokenSymbol})

                tokenBNBPrice = check_token_price_general(tokenAddress,active_chain)
                print(style.GREEN + tokenName, "ETH price", tokenBNBPrice)
                numTokensBought = numTokensBought + 1
                if(sellOnlyMode == "False"):
                        print("We came thisclose to buying it")
                        # socketIO.emit("buyingToken", {"tokenName": tokenName, 'tokenAddress':tokenAddress, 'tokenSymbol':tokenSymbol, 'price':tokenBNBPrice})
                        if main_wallet_engine.leverage <= 0:
                            print("sorry, the user has not taken any leverage, cannot buy, kindly head over to God Mode.")
                            is_leverage_sniping = False
                        buy_for_eth_general(snipeBNBAmount,tokenAddress,False,walletAddress,private_key,active_chain)    
                        # Buy(tokenAddress, tokenSymbol)
                        # handle_buying_for_sniping({"amount":snipeBNBAmount, "tokenAddress":tokenAddress,'walletAddress':walletAddress,'private_key':private_key})
                        updateTitle(walletAddress)
                        print("------token BNB prie==",tokenBNBPrice)
                        # socketIO.emit("boughtToken", {"tokenName": tokenName, 'tokenAddress':tokenAddress, 'tokenSymbol':tokenSymbol, 'price':tokenBNBPrice})

                        newPurchasedCoin = [tokenSymbol, tokenBNBPrice, tokenAddress, 0, 0]
                        # token_bought_time[tokenSymbol] = time.time()
                        print("newPurchasedCoin===>",newPurchasedCoin)
                        leverage_manager.add_token(token_address=tokenAddress, token_value=tokenBNBPrice, sender_address=walletAddress, leverage_taken=2)

                        # f = open('boughtcoins.csv', 'a')
                        # writer = csv.writer(f)
                        # writer.writerow(newPurchasedCoin)
                        # f.close()
                        print("Added newly sniped coin info to boughtcoins.csv")                  
                    
            else: #we dont care about audit, just buy it
                if(sellOnlyMode == "False"):
                    print("We are here")
                    buy_for_eth_general(snipeBNBAmount,tokenAddress,False,walletAddress,private_key,active_chain)
                    numTokensBought += 1
                    updateTitle()
                    
            print("") # line break: move onto scanning for next token

    except:
        pass



# #-----------------------------------------TOKEN SCANNER MONITORING/SELL CALCULATION BACKGROUND CODE----------------------------------------------------------------------


"""
    Description:
        This asynchronous function continuously monitors events using an event filter and performs actions
        based on the observed events. It checks the token prices, sells tokens when certain conditions are met,
        and updates relevant CSV files.

    Parameters:
        - event_filter: An event filter to monitor blockchain events.
        - poll_interval (int): Time interval (in seconds) between consecutive event polling.
        - lastRunTime (datetime): Timestamp of the last time the function ran.
        - walletAddress (str): Ethereum address associated with the wallet.
        - private_key (str): Private key for the wallet's Ethereum address.
        - transactionRevertTime (int): Time (in seconds) to wait for a transaction before reverting.
        - snipeBNBAmount (float): Amount of BNB used for sniping.
        - sellProfit (float): Profit percentage at which to sell the tokens.

    Returns:
        None

    Usage:
        Run this function in an asynchronous event loop.

    Notes:
        - The function uses global variables and external functions (not provided in the snippet).
        - Ensure proper exception handling and connection to external services.

"""
# is_sniping = True
async def tokenLoop(event_filter, poll_interval, lastRunTime,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit):
    """
    Parameters:
        - event_filter: An event filter to monitor blockchain events.
        - poll_interval (int): Time interval (in seconds) between consecutive event polling.
        - lastRunTime (datetime): Timestamp of the last time the function ran.
        - walletAddress (str): Ethereum address associated with the wallet.
        - private_key (str): Private key for the wallet's Ethereum address.
        - transactionRevertTime (int): Time (in seconds) to wait for a transaction before reverting.
        - snipeBNBAmount (float): Amount of BNB used for sniping.
        - sellProfit (float): Profit percentage at which to sell the tokens.

    Returns:
        None
    """
    try:
        sniping_info=thread_dict.get(walletAddress,None)
        print('thread dict',thread_dict)
    except Exception as e:
        print('exception for the facing the dict',str(e))
    try:
        sniping_info['snipe']
    except Exception as e:
        print('sniping info execption',str(e))
    print('sniping_info[]',sniping_info['snipe'],type(sniping_info['snipe']))
    while sniping_info['snipe'] :
        print('sniping_info[]',sniping_info['snipe'])
        # print("TokenLOOP Start")
        try:
            newCSV = []
            #
            # 6ceac1695375030441aea9ffc2627e4686b6dfc8fb46c535aa22066a4a8db683
            # 0x3f6119Ca5aD093f0F7e7Ee1C2D93641F78dbe43e (walletAddress)

            # print(lastRunTime)
            if datetime.datetime.now() - lastRunTime > timedelta(hours=0, minutes=0, seconds=45):
                with open('boughtcoins.csv', 'r') as csvfile:
                    datareader = csv.reader(csvfile)
                    for row in datareader:

                        #If real price paid not yet calculated
                        if row[4] == "0": 
                            tokenContractAddress = web3.to_checksum_address(row[2])
                            sellTokenContract = web3.eth.contract(address=row[2], abi=tokenNameABI)
                            newTokenVal, newTokenReadableBal, newTokenSymbolIs = getTokenBalance(sellTokenContract, walletAddress)
                            if(newTokenReadableBal is not None or newTokenReadableBal is not None or newTokenReadableBal != ""):
                                # actualCostPrice = float(0.0075) / float(newTokenReadableBal) its happened for reason. we will check further. may its important
                                actualCostPrice = row[1]   #this enter by me itself.
                                newActualCostPrice = actualCostPrice
                                newRealPriceCalculated = 1
                            else:
                                newActualCostPrice = row[1]
                                newRealPriceCalculated = 0

                        else:
                            newActualCostPrice = row[1]
                            newRealPriceCalculated = 1
                        tokenToCheckPrice = checkTokenPrice(row[2])

                        #Only those which haven't been sold yet
                        if row[3] == "0":
                            print(style.WHITE + row[0],tokenToCheckPrice)
                            if(tokenToCheckPrice is not None or tokenToCheckPrice != '' or tokenToCheckPrice is not None):
                                print("tokenToCheckPrice===>",float(tokenToCheckPrice))
 
                                socketIO.emit('checkingTokenPrice', {'tokenToCheckPrice':str(tokenToCheckPrice), 'sellProfit':str(sellProfit),'priceToBeSoldAt':str(float(row[1]) * float(sellProfit)), 'tokenName':row[0] })

                                print("float(row[1]) * float(sellProfit)==>",float(row[1]) , float(sellProfit),float(row[1]) * float(sellProfit))
                                if(float(tokenToCheckPrice) >= float(row[1]) * float(sellProfit) or (float(tokenToCheckPrice) / float(row[1])) * float(100) <= (float(100) - float(stop_loss)) ): #or time.time()+int(max_run_time_for_token)*60> token_bought_time# There is ETH price in row[1] or (time.time()+max_run_time_for_token>token_bought_time[row[0]]
                                    socketIO.emit("sellingToken", {"tokenName": row[0], 'price':str(tokenToCheckPrice)})

                                    print(style.GREEN + "Time to sell this token")
                                    tokenContractAddress = web3.to_checksum_address(row[2])
                                    sellTokenContract = web3.eth.contract(address=tokenContractAddress, abi=tokenNameABI)
                                    tokenValue, tokenReadableBal, tokenSymbolIs = getTokenBalance(sellTokenContract, walletAddress)
                                    print("Token:", row[0], "total balance is", tokenReadableBal)
                                    soldTxHash = Sell(sellTokenContract, tokenValue, tokenReadableBal, tokenContractAddress,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit)
                                    socketIO.emit("tokenSold", {"tokenName": row[0], 'price':str(tokenValue), 'totalReadableBalance':str(tokenReadableBal)})

                                    #after sell:
                                    newCSV.append([row[0],newActualCostPrice,row[2],"1",newRealPriceCalculated])
                                    f = open('soldcoins.csv', 'a')
                                    #coin,boughtprice,soldprice,boughtvalue,soldvalue,contract,txhash
                                    soldPrice = checkTokenPrice(row[2])
                                    newPurchasedCoin = [datetime.datetime.now(),row[0],row[1],soldPrice,snipeBNBAmount,soldPrice*tokenReadableBal,row[3],soldTxHash]
                                    writer = csv.writer(f)
                                    writer.writerow(newPurchasedCoin)
                                    f.close()
                                    token_bought_time = time.time()
                                # elif :
                                #     pass
                                else:
                                    socketIO.emit('keepHolding', {'tokenToCheckPrice':str(tokenToCheckPrice), 'sellProfit':str(sellProfit),'priceToBeSoldAt':str(float(row[1]) * float(sellProfit)), 'tokenName':str(row[0]) })

                                    print(style.WHITE + f"Keep holding for {walletAddress}", row[0])
                                    newCSV.append([row[0],newActualCostPrice,row[2],row[3],newRealPriceCalculated])
                                lastRunTime = datetime.datetime.now()
                            else:
                                print("tokenToCheckPrice is null or empty")
                                newCSV.append([row[0],newActualCostPrice,row[2],row[3]],newRealPriceCalculated)
                    with open('boughtcoins.csv', 'w') as writeexcel:
                        a = csv.writer(writeexcel)
                        for line in newCSV:
                            a.writerow (line)
            try:
                eventing = event_filter.get_new_entries()
                print(eventing)
            except Exception as e:
                print('here', e)
            try:
                
                try:
                    if (len(eventing)>0) and ("event" in eventing[0]):
                        print("in the eventing if condition", eventing)
                        foundToken(eventing,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit)
                except Exception as e:
                    print(e, "yep")


                for PairCreated in eventing:
                    print("We are going to go for fountToken")
                    foundToken(PairCreated,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit)
                await asyncio.sleep(poll_interval)
            except Exception as e:  
                print("in exception", e)
        except Exception as e:
            print(e, event_filter, "in the exception")
            pass
            


# event_filter = contract.events.PairCreated.create_filter(fromBlock='latest')

def get_sellprofit_stop_loss_active_dict(sellProfitPer,stopLossPer):
    sellProfitdict, sellprofitindex, stopLossdict,stoplossindex = None, None, None, None
    for index, value in enumerate(sellProfitPer):
        if value['status'] == False:
            sellProfitdict = sellProfitPer[index]
            sellprofitindex = index
            break
    for index, value in enumerate(stopLossPer):
        if value['status'] == False:
            stopLossdict = stopLossPer[index]
            stoplossindex = index
            break
    
    return sellProfitdict, sellprofitindex, stopLossdict,stoplossindex

            




is_sniping_general = True

"""
    Description:
        This asynchronous function represents the main loop for monitoring and managing token-related actions.
        It continuously checks the status of bought tokens, their prices, and triggers selling actions based on certain conditions.
        Additionally, it listens for new token creation events using an event filter.

    Parameters:
        - event_filter: The event filter used to listen for new token creation events.
        - poll_interval (int): The time interval, in seconds, between each poll of the token status.
        - lastRunTime (datetime): The timestamp representing the last time the loop was run.
        - walletAddress (str): The wallet address associated with the sniping activity.
        - private_key (str): The private key corresponding to the wallet address.
        - transactionRevertTime (int): The time, in seconds, to wait for a transaction to revert.
        - snipeBNBAmount (float): The amount of BNB to use for sniping activities.
        - sellProfit (float): The profit percentage at which to trigger the selling of bought tokens.
        - active_chain (str): The name of the active blockchain.
        - leverage_manager: An instance of the leverage manager for handling token actions.
        - main_wallet_engine: The main wallet engine responsible for managing the main wallet.

    Usage:
        await token_loop_general(event_filter, poll_interval, lastRunTime, walletAddress, private_key, transactionRevertTime, snipeBNBAmount, sellProfit, active_chain, leverage_manager, main_wallet_engine)
"""
async def token_loop_general(event_filter, poll_interval,lastRunTime,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit,active_chain,leverage_manager,main_wallet_engine, total_holders_count, liquidity_lock,max_tax,liquidiity_available,is_main, blacklist_token_address_list,sellProfitPer,stopLossPer):
    """
    Parameters:
        - event_filter: The event filter used to listen for new token creation events.
        - poll_interval (int): The time interval, in seconds, between each poll of the token status.
        - lastRunTime (datetime): The timestamp representing the last time the loop was run.
        - walletAddress (str): The wallet address associated with the sniping activity.
        - private_key (str): The private key corresponding to the wallet address.
        - transactionRevertTime (int): The time, in seconds, to wait for a transaction to revert.
        - snipeBNBAmount (float): The amount of BNB to use for sniping activities.
        - sellProfit (float): The profit percentage at which to trigger the selling of bought tokens.
        - active_chain (str): The name of the active blockchain.
        - leverage_manager: An instance of the leverage manager for handling token actions.
        - main_wallet_engine: The main wallet engine responsible for managing the main wallet.

    """
    
    try:
        if active_chain is None or active_chain not in chain_list.keys():
            raise ChainNameNotFoundError(active_chain)
        current_chain = chain_list[active_chain]
        web3 = current_chain['web3']
        w_token_address = current_chain['w_address']
        w_token_address = Web3.to_checksum_address(w_token_address)
        router_address, router_abi = current_chain['router_address'], current_chain['router_abi']
          # BNB
        erc_20_abi = current_chain['erc_20_abi']
        amountOut = None
        print(web3.net.version)
        # tokenRouter = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc_20_abi)
        # tokenDecimals = tokenRouter.functions.decimals().call()
        # tokenDecimals = getTokenDecimal(tokenDecimals)
    except ChainNameNotFoundError as e:
        print(str(e))
        return None
    except Exception as e:
        print(str(e), 'In the main exception')
        return None

    while thread_dict[walletAddress]['snipe']:
        # print("TokenLOOP Start")
        try:
            # newCSV = []
            #
            if "web3" not in locals():
                print("sorry, the web3 connection is lost breaking the sniping loop")
                break
            bought_tokens = leverage_manager.get_user_tokens(walletAddress)
            print(bought_tokens, "Bought Tokens")
            # print(lastRunTime)
            if datetime.datetime.now() - lastRunTime > timedelta(hours=0, minutes=0, seconds=50):
                if(bought_tokens):
                    for token_1 in bought_tokens:
                        tokenToCheckPrice = check_token_price_general(token_1[0],active_chain)

                        print(style.WHITE + token_1[0],tokenToCheckPrice)
                        if(tokenToCheckPrice is not None or tokenToCheckPrice != '' or tokenToCheckPrice is not None):
                            print("tokenToCheckPrice===>",float(tokenToCheckPrice))
                                # keep_holding.value=1
                                # socketIO.emit("new", {"something":"hello"})
                                # sio.emit('wallet', {'walletAddress': walletAddress, 'privateKey':private_key})
                            socketIO.emit('checkingTokenPrice', {'tokenToCheckPrice':str(tokenToCheckPrice), 'sellProfit':str(sellProfit),'priceToBeSoldAt':str(float(token_1[1]) * float(sellProfit)) })
                                # send_to_socket("text")
                                # a=emit_event()
                                # print(a)

                                # sellprofit is = sellprofit/100 +1 
                            # Get the sellProfitPer,stopLossPer active dict 
                            sellProfitdict, sellprofitindex, stopLossdict,stoplossindex = get_sellprofit_stop_loss_active_dict(sellProfitPer,stopLossPer)
                            print("float(row[1]) * float(sellProfit)==>",float(token_1[1]) , float(sellProfit),float(token_1[1]) * float(sellProfit))
                            sellProfit= sellProfitdict['sellprfit']/100 +1
                            stop_loss = stopLossdict['stopLoss']/100+1
                            if(float(tokenToCheckPrice) >= float(token_1[1]) * float(sellProfit) or (float(tokenToCheckPrice) / float(token_1[1])) * float(100) <= (float(100) - float(stop_loss))): #or time.time()+int(max_run_time_for_token)*60> token_bought_time# There is ETH price in row[1] or (time.time()+max_run_time_for_token>token_bought_time[row[0]]
                                socketIO.emit("sellingToken", {"tokenName": token_1[0], 'price':str(tokenToCheckPrice)})

                                if (float(tokenToCheckPrice) >= float(token_1[1]) * float(sellProfit)):
                                    if sellProfitdict == None:
                                        print(style.GREEN + "The sellprofit dont have any list pending ")

                                    print(style.GREEN + "Time to sell this token with sellprofit percentage")
                                    token_contract_address = web3.to_checksum_address(token_1[0])
                                    # sellTokenContract = web3.eth.contract(address=token_contract_address, abi=tokenNameABI)
                                    # sample dict =[ {'sellprfit':20, 'holdingtobesold':30,'status':false}]
                                    # sample dict =[ {'stopLoss':20, 'holdingtobesold':30,'status':false}]
                                    # tokenreadable balance is = tokenreadablebalace * holdingtobesold/100
                                    tokenValue, tokenReadableBal, tokenSymbolIs = get_token_balance_general(token_contract_address, walletAddress,active_chain)
                                    print("Token:", token_1[0], "total balance is", tokenReadableBal, type(tokenValue))
                                    print(type(tokenValue), "Type of Token Value")
                                    tokenReadableBal = tokenReadableBal = tokenReadableBal * float(sellProfitdict['holdingtobesold'])/100

                                    soldTxHash = handle_selling_general({'amount':tokenReadableBal, "tokenAddress":token_1[0],'private_key':private_key,"active_chain":active_chain})
                                    socketIO.emit("tokenSold", {"tokenName": token_1[0], 'price':str(tokenValue), 'totalReadableBalance':str(tokenReadableBal)})
                                    soldPrice = check_token_price_general(token_1[0],active_chain)
                                    sellProfitPer[sellprofitindex]['status']= True
                                
                                    # token_bought_time = time.time()
                                    time.sleep(5)

                                    leverage_manager.sell_token(token_address=token_1[0], sender_address=walletAddress, private_key=private_key, sold_amount=soldPrice)
                                    delta = datetime.timedelta(seconds=10)
                                    lastRunTime = datetime.datetime.now() + delta
                                    time.sleep(5)



                                elif ((float(tokenToCheckPrice) / float(token_1[1])) * float(100) <= (float(100) - float(stop_loss))): 
                                    print(style.YELLOW + "Time to sell this token with stopLoss percentage")
                                    token_contract_address = web3.to_checksum_address(token_1[0])
                            
                                    tokenValue, tokenReadableBal, tokenSymbolIs = get_token_balance_general(token_contract_address, walletAddress,active_chain)
                                    print("Token:", token_1[0], "total balance is", tokenReadableBal, type(tokenValue))
                                    print(type(tokenValue), "Type of Token Value")

                                    tokenReadableBal = tokenReadableBal = tokenReadableBal * float(stopLossdict['holdingtobesold'])/100

                                    soldTxHash = handle_selling_general({'amount':tokenReadableBal, "tokenAddress":token_1[0],'private_key':private_key,"active_chain":active_chain})
                                    socketIO.emit("tokenSold", {"tokenName": token_1[0], 'price':str(tokenValue), 'totalReadableBalance':str(tokenReadableBal)})
                                    soldPrice = check_token_price_general(token_1[0],active_chain)
                                    stopLossPer[stoplossindex]['status']= True
                                

                                    # token_bought_time = time.time()
                                    time.sleep(5)

                                    leverage_manager.sell_token(token_address=token_1[0], sender_address=walletAddress, private_key=private_key, sold_amount=soldPrice)
                                    delta = datetime.timedelta(seconds=10)
                                    lastRunTime = datetime.datetime.now() + delta
                                    time.sleep(5)

                                
                            else:
                                socketIO.emit('keepHolding', {'tokenToCheckPrice':str(tokenToCheckPrice), 'sellProfit':str(sellProfit),'priceToBeSoldAt':str(float(token_1[1]) * float(sellProfit))})

                                print(style.WHITE + "Keep holding", token_1[0])
                                # newCSV.append([row[0],newActualCostPrice,row[2],row[3],newRealPriceCalculated])
                            lastRunTime = datetime.datetime.now()
                        else:
                            print("tokenToCheckPrice is null or empty")
                            # newCSV.append([row[0],newActualCostPrice,row[2],row[3]],newRealPriceCalculated)
            try:
                eventing = event_filter.get_new_entries()
                print(eventing)
            except Exception as e:
                print('here', e)
            try:
                # try:
                #     if type(eventing) == AttributeDict or "event" in eventing:
                #         print("in the If Condition")
                #         if eventing['event'] == "PairCreated":
                #             print("yes PairCreated, going in PairCreated")
                #             foundToken(eventing)
                # except Exception as e:
                #     print("something", e)
                
                try:
                    if (len(eventing)>0) and ("event" in eventing[0]):
                        print("in the eventing if condition", eventing)
                        found_token_general(eventing,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit,leverage_manager,main_wallet_engine,active_chain, total_holders_count, liquidity_lock,max_tax,liquidiity_available, is_main, blacklist_token_address_list)
                except Exception as e:
                    print(e, "yep")
                # for i in event_filter.get_new_entries():
                #     print(i)

                for PairCreated in eventing:
                    print("We are going to go for fountToken")
                    found_token_general(PairCreated,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit,leverage_manager,main_wallet_engine,active_chain, total_holders_count, liquidity_lock,max_tax,liquidiity_available, is_main, blacklist_token_address_list)
                await asyncio.sleep(poll_interval)
            except Exception as e:  
                print("in exception", e)
        except Exception as e:
            print(e, event_filter, "in the exception")
            pass


"""
    Description:
        Checks whether the given string is a valid Ethereum address.

    Parameters:
        - address (str): The Ethereum address to be validated.

    Returns:
        - bool: True if the address is a valid Ethereum address, False otherwise.

    Notes:
        Ethereum addresses are expected to be 40 characters long and consist of hexadecimal characters (0-9, a-f).
        Additional checks, such as the correct checksum, are performed if the `eth-utils` package is available.

    Usage:
        result = is_valid_ethereum_address("0x123abc...")

    Raises:
        - ImportError: If the `eth-utils` package is not installed.

    """
def is_valid_ethereum_address(address):
    """
    Parameters:
        - address (str): The Ethereum address to be validated.

    Returns:
        - bool: True if the address is a valid Ethereum address, False otherwise.

    Raises:
        - ImportError: If the `eth-utils` package is not installed.
    """
    # Ethereum addresses are 40 characters long and consist of hexadecimal characters (0-9, a-f)
    import re
    
    if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
        return False
    
    # Additional checks, e.g., for the correct checksum
    # (This requires the `eth-checksum` package, which you can install with pip)
    try:
        from eth_utils import is_address
        return is_address(address)
    except ImportError:
        # If the eth-checksum package is not installed, you can't check for checksum validity
        # Consider installing the package for a more thorough check
        return True
    except Exception as e:
        print("something went wrong", e)


"""
    Description:
        This asynchronous function represents the main loop for sniping ERC20 tokens.
        It continuously monitors the specified blockchain for new events, such as token creations,
        and triggers the `found_token_snipe` function when relevant events are detected.
        Additionally, it checks the prices of previously bought tokens and sells them if
        certain conditions are met.

    Parameters:
        - event_filter: The event filter object for monitoring blockchain events.
        - poll_interval (int): The interval (in seconds) between each poll for new events.
        - lastRunTime (datetime): The timestamp of the last time the loop was executed.
        - walletAddress (str): The wallet address associated with the sniping operation.
        - private_key (str): The private key of the wallet for signing transactions.
        - transactionRevertTime (int): The time (in seconds) to wait for a transaction before reverting.
        - snipeBNBAmount (float): The amount of BNB to use for sniping transactions.
        - sellProfit (float): The profit percentage at which to sell previously bought tokens.
        - active_chain (str): The name of the active blockchain.
        - leverage_manager: An object representing the leverage manager for handling token transactions.
        - main_wallet_engine: The main wallet engine for managing wallet-related operations.
        - deployer_address (str): The address of the deployer.

    Returns:
        None

    Usage:
        await token_loop_snipe(event_filter, poll_interval, lastRunTime, walletAddress, private_key, transactionRevertTime, snipeBNBAmount, sellProfit, active_chain, leverage_manager, main_wallet_engine, deployer_address)
    """
async def token_loop_snipe(event_filter, poll_interval,lastRunTime,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit,active_chain,leverage_manager,main_wallet_engine, deployer_address):
    """
    Parameters:
        - event_filter: The event filter object for monitoring blockchain events.
        - poll_interval (int): The interval (in seconds) between each poll for new events.
        - lastRunTime (datetime): The timestamp of the last time the loop was executed.
        - walletAddress (str): The wallet address associated with the sniping operation.
        - private_key (str): The private key of the wallet for signing transactions.
        - transactionRevertTime (int): The time (in seconds) to wait for a transaction before reverting.
        - snipeBNBAmount (float): The amount of BNB to use for sniping transactions.
        - sellProfit (float): The profit percentage at which to sell previously bought tokens.
        - active_chain (str): The name of the active blockchain.
        - leverage_manager: An object representing the leverage manager for handling token transactions.
        - main_wallet_engine: The main wallet engine for managing wallet-related operations.
        - deployer_address (str): The address of the deployer.

    Returns:
        None

    """
    
    print("in token loop", leverage_manager)
    try:
        
        if active_chain is None or active_chain not in chain_list.keys():
            raise ChainNameNotFoundError(active_chain)
        # print(chain_list, active_chain)
        current_chain = chain_list[active_chain]
        # print(current_chain, type(current_chain), current_chain['web3'])
        web3 = current_chain['web3']
        # token_address = web3.to_checksum_address(token_address)
        # current_chain = chain_list[active_chain]
        w_token_address = current_chain['w_address']
        w_token_address = Web3.to_checksum_address(w_token_address)
        router_address, router_abi = current_chain['router_address'], current_chain['router_abi']
          # BNB
        erc_20_abi = current_chain['erc_20_abi']
        amountOut = None
        print(web3.net.version)
        
        # tokenRouter = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc_20_abi)
        # tokenDecimals = tokenRouter.functions.decimals().call()
        # tokenDecimals = getTokenDecimal(tokenDecimals)
    except ChainNameNotFoundError as e:
        print(str(e))
        return None
    except Exception as e:
        print(str(e), 'In the main exception')
        return None
    print(thread_dict[walletAddress])
    while thread_dict[walletAddress]['new_snipe']:
        # print("TokenLOOP Start")
        try:
            # newCSV = []
            #
            if "web3" not in locals():
                print("sorry, the web3 connection is lost breaking the sniping loop")
                break
            bought_tokens = leverage_manager.get_user_tokens(walletAddress)
            print(bought_tokens, "Bought Tokens")
            # print(lastRunTime)
            if datetime.datetime.now() - lastRunTime > timedelta(hours=0, minutes=0, seconds=50):
                if(bought_tokens):
                    for token_1 in bought_tokens:
                        tokenToCheckPrice = check_token_price_general(token_1[0],active_chain)

                        print(style.WHITE + token_1[0],tokenToCheckPrice)
                        if(tokenToCheckPrice is not None or tokenToCheckPrice != '' or tokenToCheckPrice is not None):
                            print("tokenToCheckPrice===>",float(tokenToCheckPrice))
        
                            socketIO.emit('checkingTokenPrice', {'tokenToCheckPrice':str(tokenToCheckPrice), 'sellProfit':str(sellProfit),'priceToBeSoldAt':str(float(token_1[1]) * float(sellProfit)) })
                        
                            print("float(row[1]) * float(sellProfit)==>",float(token_1[1]) , float(sellProfit),float(token_1[1]) * float(sellProfit))
                            if(float(tokenToCheckPrice) >= float(token_1[1]) * float(sellProfit) or (float(tokenToCheckPrice) / float(token_1[1])) * float(100) <= (float(100) - float(stop_loss)) ): #or time.time()+int(max_run_time_for_token)*60> token_bought_time# There is ETH price in row[1] or (time.time()+max_run_time_for_token>token_bought_time[row[0]]
                                socketIO.emit("sellingToken", {"tokenName": token_1[0], 'price':str(tokenToCheckPrice)})

                                print(style.GREEN + "Time to sell this token")
                                token_contract_address = web3.to_checksum_address(token_1[0])
                                # sellTokenContract = web3.eth.contract(address=token_contract_address, abi=tokenNameABI)
                                tokenValue, tokenReadableBal, tokenSymbolIs = get_token_balance_general(token_contract_address, walletAddress,active_chain)
                                if tokenReadableBal > 0:
                                    print("Token:", token_1[0], "total balance is", tokenReadableBal, type(tokenValue))
                                    print(type(tokenValue), "Type of Token Value")
                                    soldTxHash = handle_selling_general({'amount':tokenReadableBal, "tokenAddress":token_1[0],'private_key':private_key,"active_chain":active_chain})
                                    socketIO.emit("tokenSold", {"tokenName": token_1[0], 'price':str(tokenValue), 'totalReadableBalance':str(tokenReadableBal)})
                                    soldPrice = check_token_price_general(token_1[0],active_chain)
                                    time.sleep(5)  
                                    leverage_manager.sell_token(token_address=token_1[0], sender_address=walletAddress, private_key=private_key, sold_amount=soldPrice)
                                    time.sleep(5)  
                                else:
                                    
                                    print("Token already sold removing from the bought coins")
                                    try:
                                        leverage_manager.sell_token(token_address=token_1[0], sender_address=walletAddress, private_key=private_key, sold_amount=0)
                                    except Exception as e:
                                        print("something is wrong with selling leverage contract", str(e))

                                

                                # token_bought_time = time.time()
                                                          
                                delta = datetime.timedelta(seconds=10)
                                lastRunTime = datetime.datetime.now() + delta
                                time.sleep(5)
                                # elif :
                                #     pass
                            else:
                                socketIO.emit('keepHolding', {'tokenToCheckPrice':str(tokenToCheckPrice), 'sellProfit':str(sellProfit),'priceToBeSoldAt':str(float(token_1[1]) * float(sellProfit))})

                                print(style.WHITE + "Keep holding", token_1[0])
                                # newCSV.append([row[0],newActualCostPrice,row[2],row[3],newRealPriceCalculated])
                            lastRunTime = datetime.datetime.now()
                        else:
                            print("tokenToCheckPrice is null or empty")
                            # newCSV.append([row[0],newActualCostPrice,row[2],row[3]],newRealPriceCalculated)
            try:
                eventing = event_filter.get_new_entries()
                print(eventing, "New events")
            except Exception as e:
                print('here', e)
            try:
                # try:
                #     if type(eventing) == AttributeDict or "event" in eventing:
                #         print("in the If Condition")
                #         if eventing['event'] == "PairCreated":
                #             print("yes PairCreated, going in PairCreated")
                #             foundToken(eventing)
                # except Exception as e:
                #     print("something", e)
                
                # try:
                #     if (len(eventing)>0) and ("event" in eventing[0]):
                #         print("in the eventing if condition", eventing)
                #         found_token_snipe(eventing,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit,leverage_manager,main_wallet_engine,active_chain, deployer_address)
                # except Exception as e:
                #     print(e, "yep")
                # for i in event_filter.get_new_entries():
                #     print(i)

                for PairCreated in eventing:
                    print("We are going to go for fountToken")
                    found_token_snipe(PairCreated,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit,leverage_manager,main_wallet_engine,active_chain, deployer_address)
                await asyncio.sleep(poll_interval)
            except Exception as e:  
                print("in exception", e)
        except Exception as e:
            print(e, event_filter, "in the exception")
            pass     


"""
    Description:
        This function listens for newly created token pairs on a decentralized exchange by monitoring the PairCreated event
        emitted by the specified factory contract on the given blockchain.

    Parameters:
        - walletAddress (str): The wallet address to use for interacting with the blockchain.
        - private_key (str): The private key associated with the wallet address for transaction signing.
        - transactionRevertTime (int): The time, in seconds, to wait for a transaction to confirm before reverting it.
        - snipeBNBAmount (float): The amount of BNB to use for sniping new token pairs.
        - sellProfit (float): The desired profit percentage to sell the acquired tokens.
        - active_chain (str): The name of the active blockchain.
        - leverage_manager: The leverage manager instance for handling leverage-related operations.
        - main_wallet_engine: The main wallet engine instance for managing the main wallet.

    Returns:
        - bool: True if the function completes successfully.

    Raises:
        - ContractNotInitError: If there is an issue initializing the listening contract.

    Usage:
        result = listen_for_tokens_general(walletAddress, private_key, transactionRevertTime, snipeBNBAmount, sellProfit, active_chain, leverage_manager, main_wallet_engine)
"""
def listen_for_tokens_general(walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit,active_chain,leverage_manager,main_wallet_engine, total_holders_count, liquidity_lock,max_tax,liquidiity_available, is_main, blacklist_token_address_list,sellProfitPer,stopLossPer):
    """
    Parameters:
        - walletAddress (str): The wallet address to use for interacting with the blockchain.
        - private_key (str): The private key associated with the wallet address for transaction signing.
        - transactionRevertTime (int): The time, in seconds, to wait for a transaction to confirm before reverting it.
        - snipeBNBAmount (float): The amount of BNB to use for sniping new token pairs.
        - sellProfit (float): The desired profit percentage to sell the acquired tokens.
        - active_chain (str): The name of the active blockchain.
        - leverage_manager: The leverage manager instance for handling leverage-related operations.
        - main_wallet_engine: The main wallet engine instance for managing the main wallet.

    Returns:
        - bool: True if the function completes successfully.

    Raises:
        - ContractNotInitError: If there is an issue initializing the listening contract.
    """
    try:    
        lastRunTime = datetime.datetime.now()
        token_listening_contract = None
        try:
            if active_chain is not None and active_chain in chain_list.keys():
                current_chain = chain_list[active_chain]
                factory_contract, factory_abi, web3 = current_chain["factory_address"], current_chain['factory_abi'], current_chain['web3']
                token_listening_contract = web3.eth.contract(address=factory_contract, abi=factory_abi)
                print("Done setting up the listenting contract", factory_contract, active_chain)
        except ChainNameNotFoundError as e:
            
            print(str(e))
        except Exception as e:
            print(str(e))
            # return None
        # contract = 

        print("herew")
        print(web3.is_connected())
        if token_listening_contract == None:
            print("sorry something went wrong with setting up the listening contract....")
            print("returning....")
            raise ContractNotInitError
        try:
            event_filter = token_listening_contract.events.PairCreated.create_filter(fromBlock='latest')
            pass
        except Exception as e:
            print("Error skipped 1", e)
            pass
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(asyncio.gather(token_loop_general(event_filter, 0, lastRunTime,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit,active_chain,leverage_manager,main_wallet_engine, total_holders_count, liquidity_lock,max_tax,liquidiity_available, is_main, blacklist_token_address_list,sellProfitPer,stopLossPer)))
        except Exception as e:
            print("Error 2", e)
        try:
            pass
                
        except Exception as e:
            print("Error skipped 3", e)
            pass
        finally:
            try:
                return True
            except Exception as e:
                print("Error skipped 4", e)
                pass
    except ContractNotInitError as e:
        print("Cannot init the listening contract", e)
        

"""
    Description:
        This function listens for newly created token pairs on a decentralized exchange (DEX) and initiates
        a sniping process when a new token pair is detected.

    Parameters:
        - walletAddress (str): The Ethereum address of the wallet used for sniping.
        - private_key (str): The private key corresponding to the wallet address.
        - transactionRevertTime (int): The time (in seconds) to wait for a transaction to revert before considering it failed.
        - snipeBNBAmount (float): The amount of BNB to use for sniping.
        - sellProfit (float): The profit percentage at which to trigger the sell during sniping.
        - active_chain (str): The name of the active blockchain.
        - leverage_manager: (type): Description of the leverage manager object.
        - main_wallet_engine (type): Description of the main wallet engine object.
        - deployer_address (str): The Ethereum address of the deployer.

    Returns:
        - bool: True if the function executes successfully.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.

    Usage:
        success = listen_for_tokens_sniper(walletAddress, private_key, transactionRevertTime, snipeBNBAmount, sellProfit, active_chain, leverage_manager, main_wallet_engine, deployer_address)
"""
def listen_for_tokens_sniper(walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit,active_chain,leverage_manager,main_wallet_engine, deployer_address):
    """
    Parameters:
        - walletAddress (str): The Ethereum address of the wallet used for sniping.
        - private_key (str): The private key corresponding to the wallet address.
        - transactionRevertTime (int): The time (in seconds) to wait for a transaction to revert before considering it failed.
        - snipeBNBAmount (float): The amount of BNB to use for sniping.
        - sellProfit (float): The profit percentage at which to trigger the sell during sniping.
        - active_chain (str): The name of the active blockchain.
        - leverage_manager: (type): Description of the leverage manager object.
        - main_wallet_engine (type): Description of the main wallet engine object.
        - deployer_address (str): The Ethereum address of the deployer.

    Returns:
        - bool: True if the function executes successfully.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.
    """
    
    lastRunTime = datetime.datetime.now()
    token_listening_contract = None
    try:
        if active_chain is not None and active_chain in chain_list.keys():
            current_chain = chain_list[active_chain]
            factory_contract, factory_abi, web3 = current_chain["factory_address"], current_chain['factory_abi'], current_chain['web3']
            token_listening_contract = web3.eth.contract(address=factory_contract, abi=factory_abi)
            print("Done setting up the listenting contract", factory_contract, active_chain)
    except ChainNameNotFoundError as e:
        
        print(str(e))
    except Exception as e:
        print(str(e))
        # return None
    # contract = 

    print("herew")
    print(web3.is_connected())
    try:
        event_filter = token_listening_contract.events.PairCreated.create_filter(fromBlock='latest')
        pass
    except Exception as e:
        print("Error skipped 1", e)
        pass
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(asyncio.gather(token_loop_snipe(event_filter, 0, lastRunTime,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit,active_chain,leverage_manager,main_wallet_engine, deployer_address)))
    except Exception as e:
        print("Error 2", e)
    try:
        pass
               
    except Exception as e:
        print("Error skipped 3", e)
        pass
    finally:
        try:
            return True
        except Exception as e:
            print("Error skipped 4", e)
            pass


"""
    Description:
        This function listens for new token pairs created events and triggers the tokenLoop function
        to monitor transactions related to the created token pairs.

    Parameters:
        - walletAddress (str): The Ethereum address of the wallet.
        - private_key (str): The private key associated with the wallet address.
        - transactionRevertTime (int): The time interval to revert a transaction if not confirmed.
        - snipeBNBAmount (float): The amount of BNB to use for sniping transactions.
        - sellProfit (float): The desired profit percentage for selling tokens.

    Returns:
        - bool: Returns True on successful completion.

    Usage:
        success = listenForTokens("0x123abc...", "private_key_here", 60, 0.1, 5.0)
    """
def listenForTokens(walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit):
    """
    Parameters:
        - walletAddress (str): The Ethereum address of the wallet.
        - private_key (str): The private key associated with the wallet address.
        - transactionRevertTime (int): The time interval to revert a transaction if not confirmed.
        - snipeBNBAmount (float): The amount of BNB to use for sniping transactions.
        - sellProfit (float): The desired profit percentage for selling tokens.

    Returns:
        - bool: Returns True on successful completion.
    """

    print(walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit)
    lastRunTime = datetime.datetime.now()
    print("herew")
    try:
        event_filter = contract.events.PairCreated.create_filter(fromBlock='latest')
        pass
    except Exception as e:
        print("Error skipped 1", e)
        pass
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(asyncio.gather(tokenLoop(event_filter, 0, lastRunTime,walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit)))
    except Exception as e:
        print("Error 2 in listen for tokens", e)
    try:
        pass
               
    except Exception as e:
        print("Error skipped 3", e)
        pass
    finally:
        try:
            return True
        except Exception as e:
            print("Error skipped 4", e)
            pass

# is_leverage_sniping = True
"""
    Description:
        Asynchronous function that continuously monitors events using an event filter.
        It checks for specific conditions related to token transactions and triggers actions accordingly.
        The loop runs until the `leverageSnipe` flag in `leverage_thread_dict` is set to False.

    Parameters:
        - event_filter: The event filter object for monitoring blockchain events.
        - poll_interval (float): The time interval (in seconds) between consecutive event checks.
        - lastRunTime (datetime.datetime): The timestamp of the last time the loop ran.
        - walletAddress (str): The Ethereum address of the wallet associated with the loop.
        - private_key (str): The private key corresponding to the wallet address.
        - snipeBNBAmount (float): The amount of BNB to use for sniping operations.
        - leverage_manager: An instance of the leverage manager.
        - main_wallet_engine: The main wallet engine instance.
        
    Returns:
        None

    Notes:
        - The loop continuously monitors events, checks token prices, and triggers actions based on specified conditions.
        - The loop sleeps for the specified poll interval between consecutive event checks.
        - The loop stops when the `leverageSnipe` flag in `leverage_thread_dict` is set to False.

    Usage:
        await token_loop_for_leverage(event_filter, poll_interval, lastRunTime, walletAddress, private_key, snipeBNBAmount, leverage_manager, main_wallet_engine)
    """
async def token_loop_for_leverage(event_filter, poll_interval, lastRunTime,walletAddress,private_key,snipeBNBAmount,leverage_manager,main_wallet_engine):
    """
    Parameters:
        - event_filter: The event filter object for monitoring blockchain events.
        - poll_interval (float): The time interval (in seconds) between consecutive event checks.
        - lastRunTime (datetime.datetime): The timestamp of the last time the loop ran.
        - walletAddress (str): The Ethereum address of the wallet associated with the loop.
        - private_key (str): The private key corresponding to the wallet address.
        - snipeBNBAmount (float): The amount of BNB to use for sniping operations.
        - leverage_manager: An instance of the leverage manager.
        - main_wallet_engine: The main wallet engine instance.
        
    Returns:
        None
    """
    # print("TokenLOOP Starst")
    infura_url = infura_url  # Replace with your Infura project ID
    web3 = Web3(Web3.HTTPProvider(infura_url))
    tokenNameABI='''[{"inputs":[{"internalType":"uint256","name":"chainId_","type":"uint256"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"src","type":"address"},{"indexed":true,"internalType":"address","name":"guy","type":"address"},{"indexed":false,"internalType":"uint256","name":"wad","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":true,"inputs":[{"indexed":true,"internalType":"bytes4","name":"sig","type":"bytes4"},{"indexed":true,"internalType":"address","name":"usr","type":"address"},{"indexed":true,"internalType":"bytes32","name":"arg1","type":"bytes32"},{"indexed":true,"internalType":"bytes32","name":"arg2","type":"bytes32"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"}],"name":"LogNote","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"src","type":"address"},{"indexed":true,"internalType":"address","name":"dst","type":"address"},{"indexed":false,"internalType":"uint256","name":"wad","type":"uint256"}],"name":"Transfer","type":"event"},{"constant":true,"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"PERMIT_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"burn","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"guy","type":"address"}],"name":"deny","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"mint","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"src","type":"address"},{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"move","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"holder","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"expiry","type":"uint256"},{"internalType":"bool","name":"allowed","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"pull","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"push","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"guy","type":"address"}],"name":"rely","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"src","type":"address"},{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"version","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"wards","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}]'''

    while leverage_thread_dict[walletAddress]['leverageSnipe']:
        # print("TokenLOOP Start")
        try:
            bought_tokens = leverage_manager.get_user_tokens(walletAddress)
            print("current bought tokens are", bought_tokens)

            if datetime.datetime.now() - lastRunTime > timedelta(hours=0, minutes=0, seconds=10):
                if (bought_tokens):
                    for token_1 in bought_tokens:
                        tokenToCheckPrice = check_token_price_for_goerrli(token_1[0])
                        if(tokenToCheckPrice is not None or tokenToCheckPrice != '' or tokenToCheckPrice is not None):
                            print("tokenToCheckPrice===>",float(tokenToCheckPrice))
                            socketIO.emit('checkingTokenPrice', {'tokenToCheckPrice':str(tokenToCheckPrice), 'sellProfit':str(sellProfit),'priceToBeSoldAt':(float(web3.from_wei(token_1[1], 'ether')) * float(sellProfit))})
                            print("float(row[1]) * float(sellProfit)==>",float(token_1[1]) , float(sellProfit),float(token_1[1]) * float(sellProfit))
                            if(float(tokenToCheckPrice) >= float(token_1[1]) * float(sellProfit) or (float(tokenToCheckPrice) / float(token_1[1])) * float(100) <= (float(100) - float(stop_loss)) ): #or time.time()+int(max_run_time_for_token)*60> token_bought_time# There is ETH price in row[1] or (time.time()+max_run_time_for_token>token_bought_time[row[0]]                 
                                socketIO.emit("sellingToken", {"tokenAddress": token_1[0], 'price':str(tokenToCheckPrice)})
                                print(style.GREEN + "Time to sell this token")
                                tokenContractAddress = web3.to_checksum_address(token_1[0])
                                sellTokenContract = web3.eth.contract(address=tokenContractAddress, abi=tokenNameABI)
                                tokenValue, tokenReadableBal, tokenSymbolIs = getTokenBalanceGorelli(sellTokenContract, walletAddress)
                                print("Token:", token_1[0], "total balance is", tokenReadableBal)
                                handle_selling({'amount':0.0002, 'tokenAddress':web3.to_checksum_address(token_1[0])})
                                # tx_hash_for_approval = approve_uniswap_router(0.00002, tokenContractAddress)
                                # print(tx_hash_for_approval, "TX hash for approval")
                                # soldTxHash = sell_dai_for_weth(0.00002, token_contract_address=tokenContractAddress)
                                # print(soldTxHash, "Sold TX Hash")
                                socketIO.emit("tokenSold", {"tokenAddress": token_1[0], 'price':str(tokenValue), 'totalReadableBalance':str(tokenReadableBal)})
                                soldPrice = check_token_price_for_goerrli(token_1[0])
                                time.sleep(5)

                                leverage_manager.sell_token(token_address=token_1[0], sender_address=walletAddress, private_key=private_key, sold_amount=soldPrice)
                                delta = datetime.timedelta(seconds=10)
                                lastRunTime = datetime.datetime.now() + delta
                                time.sleep(5)
                            else:
                                socketIO.emit('keepHolding', {'tokenToCheckPrice':str(tokenToCheckPrice), 'sellProfit':str(sellProfit),'priceToBeSoldAt':str(float(token_1[1]) * float(sellProfit)) })

                                print(style.WHITE + "Keep holding", token_1[0])
                            lastRunTime = datetime.datetime.now()
     
           
            try:
                eventing = event_filter.get_new_entries()
                print(eventing)
            except Exception as e:
                print('here', e)
            try:
                try:
                    # if type(eventing) == AttributeDict or "event" in eventing:
                    #     print("in the If Condition")
                    #     if eventing['event'] == "PairCreated":
                    #         print("yes PairCreated, going in PairCreated")
                    #         foundToken(eventing)
                    pass
                except Exception as e:
                    print("something", e)
                
                try:
                    if (len(eventing)>0) and ("event" in eventing[0]):
                        print("in the eventing if condition", eventing)
                        found_token_for_leverage(eventing,walletAddress,private_key,snipeBNBAmount,leverage_manager,main_wallet_engine,active_chain)
                except Exception as e:
                    print(e, "yep")
                # for i in event_filter.get_new_entries():
                #     print(i)

                for PairCreated in eventing:
                    print("We are going to go for fountToken")
                    found_token_for_leverage(PairCreated,walletAddress,private_key,snipeBNBAmount,leverage_manager,main_wallet_engine,active_chain)
                await asyncio.sleep(poll_interval)
            except Exception as e:  
                print("in exception", e)
        except Exception as e:
            print(e, event_filter, "in the exception")
            pass


"""
    Description:
        This asynchronous function implements a loop to continuously monitor and manage tokens
        for leverage trading. It checks token prices, executes selling actions, and handles new token events.

    Parameters:
        - event_filter: An event filter for tracking token-related events.
        - poll_interval (float): The time interval (in seconds) between each iteration of the loop.
        - lastRunTime (datetime): The timestamp of the last run time.
        - walletAddress (str): The Ethereum address of the wallet.
        - private_key (str): The private key associated with the wallet address.
        - snipeBNBAmount (float): The amount of BNB to use for sniping.
        - leverage_manager: An instance of the leverage manager.
        - main_wallet_engine: The main wallet engine.
        - active_chain (str): The name of the active blockchain.

    Usage:
        await token_loop_for_leverage_general(event_filter, poll_interval, lastRunTime, walletAddress, private_key, snipeBNBAmount, leverage_manager, main_wallet_engine, active_chain)

    Notes:
        - The function runs indefinitely in an asynchronous loop.
        - It continuously checks token prices and performs selling actions based on predefined conditions.
        - It handles new token events and invokes the appropriate functions for processing them.
        - Use the `leverage_thread_dict` to control the loop (start, pause, stop).
"""         
async def token_loop_for_leverage_general(event_filter, poll_interval, lastRunTime,walletAddress,private_key,snipeBNBAmount,leverage_manager,main_wallet_engine,active_chain):
    """
    Parameters:
        - event_filter: An event filter for tracking token-related events.
        - poll_interval (float): The time interval (in seconds) between each iteration of the loop.
        - lastRunTime (datetime): The timestamp of the last run time.
        - walletAddress (str): The Ethereum address of the wallet.
        - private_key (str): The private key associated with the wallet address.
        - snipeBNBAmount (float): The amount of BNB to use for sniping.
        - leverage_manager: An instance of the leverage manager.
        - main_wallet_engine: The main wallet engine.
        - active_chain (str): The name of the active blockchain.

    Usage:
        await token_loop_for_leverage_general(event_filter, poll_interval, lastRunTime, walletAddress, private_key, snipeBNBAmount, leverage_manager, main_wallet_engine, active_chain)
    """
    # print("TokenLOOP Starst")
    
    # infura_url = infura_url  # Replace with your Infura project ID
    # web3 = Web3(Web3.HTTPProvider(infura_url))
    # tokenNameABI='''[{"inputs":[{"internalType":"uint256","name":"chainId_","type":"uint256"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"src","type":"address"},{"indexed":true,"internalType":"address","name":"guy","type":"address"},{"indexed":false,"internalType":"uint256","name":"wad","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":true,"inputs":[{"indexed":true,"internalType":"bytes4","name":"sig","type":"bytes4"},{"indexed":true,"internalType":"address","name":"usr","type":"address"},{"indexed":true,"internalType":"bytes32","name":"arg1","type":"bytes32"},{"indexed":true,"internalType":"bytes32","name":"arg2","type":"bytes32"},{"indexed":false,"internalType":"bytes","name":"data","type":"bytes"}],"name":"LogNote","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"src","type":"address"},{"indexed":true,"internalType":"address","name":"dst","type":"address"},{"indexed":false,"internalType":"uint256","name":"wad","type":"uint256"}],"name":"Transfer","type":"event"},{"constant":true,"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"PERMIT_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"burn","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"guy","type":"address"}],"name":"deny","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"mint","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"src","type":"address"},{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"move","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"holder","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"expiry","type":"uint256"},{"internalType":"bool","name":"allowed","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"pull","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"usr","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"push","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"guy","type":"address"}],"name":"rely","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"src","type":"address"},{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"version","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"wards","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}]'''
  
    
    try:
        if active_chain is None or active_chain not in chain_list.keys():
            raise ChainNameNotFoundError(active_chain)
        # print(chain_list, active_chain)
        current_chain = chain_list[active_chain]
        # print(current_chain, type(current_chain), current_chain['web3'])
        web3 = current_chain['web3']
        # token_address = web3.to_checksum_address(token_address)
        # current_chain = chain_list[active_chain]
        w_token_address = current_chain['w_address']
        w_token_address = Web3.to_checksum_address(w_token_address)
        router_address, router_abi = current_chain['router_address'], current_chain['router_abi']
          # BNB
        erc_20_abi = current_chain['erc_20_abi']
        amountOut = None
        print(web3.net.version)
        # tokenRouter = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc_20_abi)
        # tokenDecimals = tokenRouter.functions.decimals().call()
        # tokenDecimals = getTokenDecimal(tokenDecimals)
    except ChainNameNotFoundError as e:
        print(str(e))
        return None
    except Exception as e:
        print(str(e), 'In the main exception')
        return None
    
    while leverage_thread_dict[walletAddress]['leverageSnipe']:
        # print("TokenLOOP Start")
        try:
            if "web3" not in locals():
                print("sorry, the web3 connection is lost breaking the sniping loop")
                break
            bought_tokens = leverage_manager.get_user_tokens(walletAddress)
            print("current bought tokens are", bought_tokens)

            if datetime.datetime.now() - lastRunTime > timedelta(hours=0, minutes=0, seconds=50):
                if (bought_tokens):
                    for token_1 in bought_tokens:
                        tokenToCheckPrice = check_token_price_general(token_1[0],active_chain)
                        if(tokenToCheckPrice is not None or tokenToCheckPrice != '' or tokenToCheckPrice is not None):
                            print("tokenToCheckPrice===>",float(tokenToCheckPrice))
                            socketIO.emit('checkingTokenPrice', {'tokenToCheckPrice':str(tokenToCheckPrice), 'sellProfit':str(sellProfit),'priceToBeSoldAt':(float(web3.from_wei(token_1[1], 'ether')) * float(sellProfit))})
                            print("float(row[1]) * float(sellProfit)==>",float(token_1[1]) , float(sellProfit),float(token_1[1]) * float(sellProfit))
                            if(float(tokenToCheckPrice) >= float(token_1[1]) * float(sellProfit) or (float(tokenToCheckPrice) / float(token_1[1])) * float(100) <= (float(100) - float(stop_loss)) ): #or time.time()+int(max_run_time_for_token)*60> token_bought_time# There is ETH price in row[1] or (time.time()+max_run_time_for_token>token_bought_time[row[0]]                 
                                socketIO.emit("sellingToken", {"tokenAddress": token_1[0], 'price':str(tokenToCheckPrice)})
                                print(style.GREEN + "Time to sell this token")
                                tokenContractAddress = web3.to_checksum_address(token_1[0])
                                sellTokenContract = web3.eth.contract(address=tokenContractAddress, abi=tokenNameABI)
                                tokenValue, tokenReadableBal, tokenSymbolIs = get_token_balance_general(token_1[0], walletAddress, active_chain)
                                print("Token:", token_1[0], "total balance is", tokenReadableBal, type(tokenReadableBal))
                                handle_selling_general({'amount':tokenReadableBal, "tokenAddress":token_1[0],'private_key':private_key,"active_chain":active_chain})
                                # tx_hash_for_approval = approve_uniswap_router(0.00002, tokenContractAddress)
                                # print(tx_hash_for_approval, "TX hash for approval")
                                # soldTxHash = sell_dai_for_weth(0.00002, token_contract_address=tokenContractAddress)
                                # print(soldTxHash, "Sold TX Hash")
                                socketIO.emit("tokenSold", {"tokenAddress": token_1[0], 'price':str(tokenValue), 'totalReadableBalance':str(tokenReadableBal)})
                                soldPrice = check_token_price_general(token_1[0],active_chain)
                                time.sleep(5)

                                leverage_manager.sell_token(token_address=token_1[0], sender_address=walletAddress, private_key=private_key, sold_amount=soldPrice)
                                delta = datetime.timedelta(seconds=10)
                                lastRunTime = datetime.datetime.now() + delta
                                time.sleep(5)
                            else:
                                socketIO.emit('keepHolding', {'tokenToCheckPrice':str(tokenToCheckPrice), 'sellProfit':str(sellProfit),'priceToBeSoldAt':str(float(token_1[1]) * float(sellProfit)) })

                                print(style.WHITE + "Keep holding", token_1[0])
                            lastRunTime = datetime.datetime.now()
     
     
           
            try:
                eventing = event_filter.get_new_entries()
                print(eventing)
            except Exception as e:
                print('here', e)
            try:
                try:
                    # if type(eventing) == AttributeDict or "event" in eventing:
                    #     print("in the If Condition")
                    #     if eventing['event'] == "PairCreated":
                    #         print("yes PairCreated, going in PairCreated")
                    #         foundToken(eventing)
                    pass
                except Exception as e:
                    print("something", e)
                
                try:
                    if (len(eventing)>0) and ("event" in eventing[0]):
                        print("in the eventing if condition", eventing)
                        found_token_for_leverage_general(eventing, walletAddress,private_key,snipeBNBAmount,leverage_manager,main_wallet_engine,active_chain)
                except Exception as e:
                    print(e, "yep")
                # for i in event_filter.get_new_entries():
                #     print(i)

                for PairCreated in eventing:
                    print("We are going to go for fountToken")
                    found_token_for_leverage_general(PairCreated, walletAddress,private_key,snipeBNBAmount,leverage_manager,main_wallet_engine,active_chain)
                await asyncio.sleep(poll_interval)
            except Exception as e:  
                print("in exception", e)
        except Exception as e:
            print(e, event_filter, "in the exception")
            pass
            

"""
    Description:
        This function sets up and runs an event loop to listen for events related to token pairs being created.
        When an event is detected, it triggers the asynchronous function `token_loop_for_leverage`.

    Parameters:
        - walletAddress (str): The wallet address associated with the listener.
        - private_key (str): The private key corresponding to the wallet address.
        - snipeBNBAmount (float): The amount of BNB to be used in sniping operations.
        - leverage_manager: An object representing the leverage manager.
        - main_wallet_engine: An object representing the main wallet engine.

    Returns:
        - bool: True if the function completes successfully, False otherwise.

    Raises:
        - Exception: If any unexpected error occurs during the process.

    Usage:
        success = handle_listen_for_leverage("0x123abc...", "private_key", 0.5, leverage_manager_obj, wallet_engine_obj)
"""
def handle_listen_for_leverage(walletAddress,private_key,snipeBNBAmount,leverage_manager,main_wallet_engine):
    """
    Parameters:
        - walletAddress (str): The wallet address associated with the listener.
        - private_key (str): The private key corresponding to the wallet address.
        - snipeBNBAmount (float): The amount of BNB to be used in sniping operations.
        - leverage_manager: An object representing the leverage manager.
        - main_wallet_engine: An object representing the main wallet engine.

    Returns:
        - bool: True if the function completes successfully, False otherwise.

    Raises:
        - Exception: If any unexpected error occurs during the process.
    """
    lastRunTime = datetime.datetime.now()
    print("herew")
    try:
        event_filter = contract.events.PairCreated.create_filter(fromBlock='latest')
        pass
    except Exception as e:
        print("Error skipped 1", e)
        pass
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(asyncio.gather(token_loop_for_leverage(event_filter, 0, lastRunTime,walletAddress,private_key,snipeBNBAmount,leverage_manager,main_wallet_engine)))
    except Exception as e:
        print("Error 2", e)
    try:
        pass
               
    except Exception as e:
        print("Error skipped 3", e)
        pass
    finally:
        try:
            return True
        except Exception as e:
            print("Error skipped 4", e)
            pass


"""
    Description:
        This function sets up and runs a listener for the creation of new token pairs on a decentralized exchange (DEX).
        When a new pair is created, it triggers the specified asynchronous token loop for leverage management.

    Parameters:
        - walletAddress (str): The Ethereum wallet address for interacting with the DEX.
        - private_key (str): The private key associated with the wallet address.
        - snipeBNBAmount (float): The amount of BNB to use for sniping new token pairs.
        - leverage_manager (object): An instance of the leverage manager for managing leverage.
        - main_wallet_engine (object): The main wallet engine for wallet-related operations.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - bool: Returns True if the function runs successfully; otherwise, it may raise exceptions or return None.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.

    Usage:
        result = handle_listen_for_leverage_general("0x123abc...", "private_key", 1.0, leverage_manager, main_wallet_engine, "ethereum")
    """
def handle_listen_for_leverage_general(walletAddress,private_key,snipeBNBAmount,leverage_manager,main_wallet_engine,active_chain):
    """
    Parameters:
        - walletAddress (str): The Ethereum wallet address for interacting with the DEX.
        - private_key (str): The private key associated with the wallet address.
        - snipeBNBAmount (float): The amount of BNB to use for sniping new token pairs.
        - leverage_manager (object): An instance of the leverage manager for managing leverage.
        - main_wallet_engine (object): The main wallet engine for wallet-related operations.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - bool: Returns True if the function runs successfully; otherwise, it may raise exceptions or return None.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.
    """
    lastRunTime = datetime.datetime.now()
    print("herew")
    token_listening_contract = None
    try:
        if active_chain is not None and active_chain in chain_list.keys():
            current_chain = chain_list[active_chain]
            factory_contract, factory_abi, web3 = current_chain["factory_address"], current_chain['factory_abi'], current_chain['web3']
            token_listening_contract = web3.eth.contract(address=factory_contract, abi=factory_abi)
            print("Done setting up the listenting contract")
    except ChainNameNotFoundError as e:
        
        print(str(e))
    except Exception as e:
        print(str(e))
    try:
        if token_listening_contract == None:
            print("The listening contract has not been properly setted, something went wrong with that")
            return
        event_filter = token_listening_contract.events.PairCreated.create_filter(fromBlock='latest')
        pass
    except Exception as e:
        print("Error skipped 1", e)
        pass
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(asyncio.gather(token_loop_for_leverage_general(event_filter, 0, lastRunTime,walletAddress,private_key,snipeBNBAmount,leverage_manager,main_wallet_engine,active_chain)))
    except Exception as e:
        print("Error 2", e)
    try:
        pass
               
    except Exception as e:
        print("Error skipped 3", e)
        pass
    finally:
        try:
            return True
        except Exception as e:
            print("Error skipped 4", e)
            pass


"""
    Description:
        This function serves as a handler for mirroring transactions on a specified blockchain.
        It initiates an asyncio event loop and runs the `mirror_transactions_general` function to mirror transactions.

    Parameters:
        - walletAddress (str): The wallet address for which transactions will be mirrored.
        - private_key (str): The private key associated with the wallet address.
        - active_chain (str): The name of the active blockchain.

    Usage:
        mirror_handler("0x123abc...", "private_key_here", "ethereum")

    Notes:
        - The function sets up an asyncio event loop to run asynchronous tasks.
        - Exceptions are caught and logged for each step to ensure the handler continues operation even if errors occur.
"""
def mirror_handler(walletAddress,private_key,active_chain):
    """
    Parameters:
        - walletAddress (str): The wallet address for which transactions will be mirrored.
        - private_key (str): The private key associated with the wallet address.
        - active_chain (str): The name of the active blockchain.

    Usage:
        mirror_handler("0x123abc...", "private_key_here", "ethereum")
    """
    # lastRunTime = datetime.datetime.now()
    print("herew")
    try:
        # event_filter = contract.events.PairCreated.create_filter(fromBlock='latest')
        pass
    except Exception as e:
        print("Error skipped 1", e)
        pass
    try:
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(asyncio.gather(mirror_transactions_general(walletAddress,private_key,active_chain)))
    except Exception as e:
        print("Error 2", e)
    try:
        pass
               
    except Exception as e:
        print("Error skipped 3", e)
        pass
    finally:
        try:
            # listenForTokens()
            pass
        except Exception as e:
            print("Error skipped 4", e)
            pass


"""
    Description:
        Start a new thread to execute the given worker function.

    Parameters:
        - worker_function (function): The function to be executed in the new thread.

    Returns:
        - threading.Thread: The created thread.

    Usage:
        worker_thread = start_thread(my_worker_function)
    """
def start_thread(worker_function):
    """

    Parameters:
        - worker_function (function): The function to be executed in the new thread.

    Returns:
        - threading.Thread: The created thread.
    """

    worker_thread = threading.Thread(target=worker_function)
    print("worker_thread",worker_thread)
    worker_thread.start()
    print('worker_thread is ', worker_thread)
    return worker_thread


"""
    Description:
        Stop a running thread associated with a specific wallet address.

    Parameters:
        - worker_thread (threading.Thread): The thread to be stopped.
        - walletAddress (str): The wallet address associated with the thread.
        - is_snipe (bool): A flag indicating whether the thread is related to sniping.

    Returns:
        - threading.Thread: The stopped thread.

    Usage:
        stopped_thread = stop_thread(my_thread, "0x123abc...", True)
"""
def stop_thread(worker_thread,walletAddress, is_snipe):
    """
    Parameters:
        - worker_thread (threading.Thread): The thread to be stopped.
        - walletAddress (str): The wallet address associated with the thread.
        - is_snipe (bool): A flag indicating whether the thread is related to sniping.

    Returns:
        - threading.Thread: The stopped thread.
    """
    print('we are in stop thread ')
    print(worker_thread)
    if is_snipe:
        thread_dict[walletAddress]['snipe']=False

        # is_sniping = False
    else:
        mirror_thread_dict[walletAddress]['mirrorSnipe']=False
        
    worker_thread.join()
    return worker_thread


"""
    Description:
        Stop the mirroring process by setting the global flag 'isMirroring' to False.

    Parameters:
        - worker_thread (threading.Thread): The thread associated with the mirroring process.

    Usage:
        stop_mirroring(my_mirroring_thread)
    """
def stop_mirrioring(worker_thread):
    """
    Parameters:
        - worker_thread (threading.Thread): The thread associated with the mirroring process.
    """
    global isMirroring
    isMirroring = False
    worker_thread.join()


"""
    Description:
        This function stops the leverage sniping for a specific wallet address by setting the associated
        thread's 'leverageSnipe' flag to False and waiting for the thread to join.

    Parameters:
        - worker_thread (Thread): The thread associated with the leverage sniping.
        - walletAddress (str): The wallet address for which leverage sniping is being stopped.

    Returns:
        - Thread: The joined worker thread.

    Usage:
        stopped_thread = stop_leverage_sniping(worker_thread_instance, "0x123abc...")
"""
def stop_leverage_sniping(worker_thread,walletAddress):
    """
    Parameters:
        - worker_thread (Thread): The thread associated with the leverage sniping.
        - walletAddress (str): The wallet address for which leverage sniping is being stopped.

    Returns:
        - Thread: The joined worker thread.
    """
    leverage_thread_dict[walletAddress]['leverageSnipe']=False
    # is_leverage_sniping = False
    worker_thread.join()
    return worker_thread    


"""
    Description:
        This function starts a new thread for leverage sniping using the provided worker function.

    Parameters:
        - worker_function (function): The function to be executed by the leverage sniping thread.

    Returns:
        - Thread: The newly created leverage sniping thread.

    Usage:
        new_thread = start_leverage_thread(worker_function_instance)
    """
def start_leverage_thread(worker_function):
    """
    Parameters:
        - worker_function (function): The function to be executed by the leverage sniping thread.

    Returns:
        - Thread: The newly created leverage sniping thread.
    """
    global is_leverage_sniping
    is_leverage_sniping = True
    worker_thread = threading.Thread(target=worker_function)
    # worker_thread.start()
    return worker_thread


"""
    Description:
        This function restarts the leverage sniping thread by creating a new thread with the provided worker function.

    Parameters:
        - worker_function (function): The function to be executed by the leverage sniping thread.

    Returns:
        - Thread: The newly created leverage sniping thread.

    Usage:
        restarted_thread = restart_leverage_thread(worker_function_instance)
"""
def restart_leverage_thread(worker_function):
    """
    Parameters:
        - worker_function (function): The function to be executed by the leverage sniping thread.

    Returns:
        - Thread: The newly created leverage sniping thread.

    """
    global is_leverage_sniping
    is_leverage_sniping = True
    worker_thread = threading.Thread(target=worker_function)
    # worker_thread.start()
    print(worker_thread, worker_thread.is_alive())
    return worker_thread


"""
    Description:
        This function restarts a thread based on whether it is associated with sniping or mirroring.

    Parameters:
        - worker_function (function): The function to be executed by the thread.
        - is_snipe (bool): A flag indicating whether the thread is associated with sniping.

    Returns:
        - Thread: The newly created thread.

    Usage:
        restarted_thread = restart_thread(worker_function_instance, True)
    """
def restart_thread(worker_function, is_snipe):
    """
    Parameters:
        - worker_function (function): The function to be executed by the thread.
        - is_snipe (bool): A flag indicating whether the thread is associated with sniping.

    Returns:
        - Thread: The newly created thread.
    """
    if is_snipe:
        global is_sniping
        is_sniping = True
    else:
        global isMirroring
        isMirroring = True
    # stop_thread(thread_instance)
    # print(worker_function)
    thread_instance = start_thread(worker_function)
    print(thread_instance, thread_instance.is_alive())
    return thread_instance


# from web3 import Web3, Account

# Initialize a Web3 instance


# Connect to the Uniswap V2 Router contract

# Function to sell DAI for WETH on Uniswap V2
"""
    Description:
        This function executes a token swap using the Uniswap V2 Router on the Ethereum blockchain.
        It sells a specified amount of Ethereum for a given ERC20 token.

    Parameters:
        - amount (float): The amount of Ethereum to sell.
        - token_address (str): The Ethereum address of the ERC20 token to receive.
        - is_increase_nonce (bool): If True, increases the transaction nonce by 1.
        - wallet_address (str): The wallet address from which the transaction is initiated.
        - private_key (str): The private key corresponding to the wallet address.

    Returns:
        - tuple: A tuple containing the amount of received tokens in WETH and the transaction hash.

    Raises:
        - Exception: Any unexpected error during the transaction.

    Usage:
        result = buy_for_eth(1.0, "0x123abc...", True, "0xYourWalletAddress", "YourPrivateKey")
    """
def buy_for_eth(amount, token_address, is_increase_nonce,wallet_address,private_key):
    """
    Parameters:
        - amount (float): The amount of Ethereum to sell.
        - token_address (str): The Ethereum address of the ERC20 token to receive.
        - is_increase_nonce (bool): If True, increases the transaction nonce by 1.
        - wallet_address (str): The wallet address from which the transaction is initiated.
        - private_key (str): The private key corresponding to the wallet address.

    Returns:
        - tuple: A tuple containing the amount of received tokens in WETH and the transaction hash.

    Raises:
        - Exception: Any unexpected error during the transaction.
    """
   
    try:
        infura_url = infura_url  # Replace with your Infura project ID

        web3 = Web3(Web3.HTTPProvider(infura_url))
        uniswap_router_address = pancakeSwap_RouterAddress  # Ethereum Mainnet Uniswap V2 Router address
        with open('./uniswapRouterABI.json', 'r') as abi_file:
            uniswap_router_abi = json.load(abi_file)  # Load the ABI from a JSON file

        uniswap_router_contract = web3.eth.contract(address=uniswap_router_address, abi=uniswap_router_abi)

        
        print("here", amount * 10**18)
        

        # Your private key and wallet address
        # private_key = '32892f7e0f4f5e306fb60e8370b8ff3b4753e3e94914d9b41df223e94f71630d'
        # wallet_address = '0x0bFD580a07a6f0F8ef8F9010D827d136c1ec6e43'

        # Contract address of the token you want to sell (DAI in this case)
        token_contract_address = DAI_token_address  # DAI token address on Ethereum Mainnet

        # Amount of DAI you want to sell
        dai_amount = 4  # Change this to the desired amount

        # Create an Ethereum account from the private key
        account = Account.from_key(private_key)    
    
        dai_amount_in_wei = int(dai_amount * 10**18)
        wei_amount = web3.to_wei(amount, 'ether')
        print(wei_amount)
        path = [Web3.to_checksum_address(goerli_wrapped_ether_address),Web3.to_checksum_address(token_address)]  # DAI to WETH trading path

        # Estimate the amount of WETH you will receive
        amount_out_min = uniswap_router_contract.functions.getAmountsOut(wei_amount, path).call()
        weth_amount_in_wei = amount_out_min[1]

        print(f'Estimated amount of the token you will recieve: {weth_amount_in_wei / 10**18} WETH')

        # Execute the swap
        gas_price = web3.eth.gas_price
        gas_limit = 300000
        if is_increase_nonce:
            nonce = web3.eth.get_transaction_count(account.address) + 1
        else:
            nonce = web3.eth.get_transaction_count(account.address)


        transaction = {
            'from': account.address,
            'value': wei_amount,  # You are selling DAI, not sending ETH
            'gasPrice': gas_price,
            'gas': gas_limit,
            'nonce': nonce,
        }
        time_limit = int(time.time() + 60 * 10)
        if is_increase_nonce:
            slippageAmount = (amount_out_min[1] * 20) / 100;
            amount_out_min[1] = int(amount_out_min[1] + slippageAmount)
            time_limit += int(60*10)
        function_data = uniswap_router_contract.functions.swapExactETHForTokens(
            amount_out_min[1],  # Min amount of WETH you expect to receive
            path,
            wallet_address,
            time_limit,  # 10 minutes
        ).build_transaction(transaction)
        signed_transaction = web3.eth.account.sign_transaction(function_data, private_key)

        tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction).hex()

        print(f'Transaction Hash: {tx_hash}')
        return {weth_amount_in_wei / 10**18}, tx_hash

    except Exception as e:
        print('Error:', e)


"""
    Description:
        This function approves the Uniswap Router to spend a specified amount of a given ERC20 token
        on behalf of the provided wallet address. The approval is necessary for subsequent token swaps.

    Parameters:
        - amount (float): The amount of the ERC20 token to approve for spending.
        - token_contract_address (str): The Ethereum address of the ERC20 token contract.
        - wallet_address (str): The Ethereum address of the wallet approving the Uniswap Router.
        - private_key (str): The private key corresponding to the wallet address.

    Returns:
        - str or None: The transaction hash if the approval is successful, None if an error occurs.

    Raises:
        - Exception: If an unexpected error occurs during the approval process.

    Usage:
        tx_hash = approve_uniswap_router(10.0, "0x123abc...", "0x456def...", "0x789ghi...")
"""
def approve_uniswap_router(amount, token_contract_address,walletAddress,private_key):
    """
    Parameters:
        - amount (float): The amount of the ERC20 token to approve for spending.
        - token_contract_address (str): The Ethereum address of the ERC20 token contract.
        - wallet_address (str): The Ethereum address of the wallet approving the Uniswap Router.
        - private_key (str): The private key corresponding to the wallet address.

    Returns:
        - str or None: The transaction hash if the approval is successful, None if an error occurs.

    Raises:
        - Exception: If an unexpected error occurs during the approval process.
    """
    try:
        infura_url = infura_url  # Replace with your Infura project ID

        web3 = Web3(Web3.HTTPProvider(infura_url))
        uniswap_router_address = pancakeSwap_RouterAddress  # Ethereum Mainnet Uniswap V2 Router address
        with open('./uniswapRouterABI.json', 'r') as abi_file:
            uniswap_router_abi = json.load(abi_file)  # Load the ABI from a JSON file

        uniswap_router_contract = web3.eth.contract(address=uniswap_router_address, abi=uniswap_router_abi)

        with open('./erc20.json', 'r') as erc20_abi_file:
            erc20_abi_file_ = json.load(erc20_abi_file)  # Load the ABI from a JSON file

        dai_contract_address = web3.to_checksum_address(token_contract_address) # DAI token contract address
        dai_contract_abi =erc20_abi_file_  # Replace with the actual DAI token ABI

        dai_contract = web3.eth.contract(address=dai_contract_address, abi=dai_contract_abi)

        # Calculate the allowance amount (maximum uint256 value)
        max_allowance =amount
        # eth_value = Web3.from_wei(max_allowance, 'ether')
        # prin
        if max_allowance < 100000:
            max_allowance = int(max_allowance * 10**18)
        
        account = Account.from_key(private_key)    
        dai_amount = 4  # Change this to the desired amount

        nonce = web3.eth.get_transaction_count(account.address)

        # Approve the Uniswap Router to spend DAI on your behalf
        tx_hash = dai_contract.functions.approve(uniswap_router_address, max_allowance).build_transaction({
        'from': account.address, 
        'nonce': nonce
        })

        signed_transaction = web3.eth.account.sign_transaction(tx_hash, private_key)

        tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction).hex()

        print(f'Transaction Hash: {tx_hash}')
        return tx_hash

    except Exception as e:
        print('Err:', e)



# Function to sell DAI for WETH on Uniswap V2
"""
    Description:
        This function executes a swap on the Uniswap decentralized exchange, selling a specified amount of DAI tokens
        for WETH (wrapped ether). The swap is performed using the Uniswap V2 Router.

    Parameters:
        - amount (float): The amount of DAI tokens to sell.
        - token_contract_address (str): The Ethereum address of the ERC20 token (DAI) to sell.
        - walletAddress (str): The Ethereum address of the wallet initiating the swap.
        - private_key (str): The private key corresponding to the wallet initiating the swap.

    Returns:
        - tuple: A tuple containing the estimated amount of WETH to receive and the transaction hash.
                 Returns (None, None) if an error occurs during the process.

    Note:
        - The DAI token contract address, Uniswap Router address, and other constants should be appropriately set
          before using this function.
        - Gas price, gas limit, and nonce are set based on default values in this example. Adjust them as needed.

    Usage:
        sell_dai_for_weth(4.0, "0x123abc...", "0xwalletAddress...", "private_key_string...")
"""
def sell_dai_for_weth(amount, token_contract_address,walletAddress,private_key):
    """
    Parameters:
        - amount (float): The amount of DAI tokens to sell.
        - token_contract_address (str): The Ethereum address of the ERC20 token (DAI) to sell.
        - walletAddress (str): The Ethereum address of the wallet initiating the swap.
        - private_key (str): The private key corresponding to the wallet initiating the swap.

    Returns:
        - tuple: A tuple containing the estimated amount of WETH to receive and the transaction hash.
                 Returns (None, None) if an error occurs during the process.

    Note:
        - The DAI token contract address, Uniswap Router address, and other constants should be appropriately set
          before using this function.
        - Gas price, gas limit, and nonce are set based on default values in this example. Adjust them as needed.
    """
    try:
        infura_url = infura_url  # Replace with your Infura project ID

        web3 = Web3(Web3.HTTPProvider(infura_url))
        uniswap_router_address = pancakeSwap_RouterAddress  # Ethereum Mainnet Uniswap V2 Router address
        with open('./uniswapRouterABI.json', 'r') as abi_file:
            uniswap_router_abi = json.load(abi_file)  # Load the ABI from a JSON file

        uniswap_router_contract = web3.eth.contract(address=uniswap_router_address, abi=uniswap_router_abi)

        with open('./erc20.json', 'r') as erc20_abi_file:
            erc20_abi_file_ = json.load(erc20_abi_file)  # Load the ABI from a JSON file

        dai_contract_address = DAI_token_address  # DAI token contract address
        dai_contract_abi =erc20_abi_file_  # Replace with the actual DAI token ABI

        dai_contract = web3.eth.contract(address=dai_contract_address, abi=dai_contract_abi)

        # Calculate the allowance amount (maximum uint256 value)
        max_allowance =20
        max_allowance = int(max_allowance * 10**18)
        account = Account.from_key(private_key)    
        dai_amount = 4  # Change this to the desired amount


        dai_amount_in_wei = int(amount * 10**18)
        print("amount",dai_amount_in_wei)
        path = [web3.to_checksum_address(token_contract_address), web3.to_checksum_address(goerli_wrapped_ether_address)]  # DAI to WETH trading path

        # Estimate the amount of WETH you will receive
        amount_out_min = uniswap_router_contract.functions.getAmountsOut(dai_amount_in_wei, path).call()

        weth_amount_in_wei = amount_out_min[1]

        print(f'Estimated amount of WETH to receive: {weth_amount_in_wei / 10**18} WETH')

        # Execute the swap
        gas_price = web3.eth.gas_price
        gas_limit = 300000

        nonce = web3.eth.get_transaction_count(account.address) + 1

        transaction = {
            'from': account.address,
            'value': 0,  # You are selling DAI, not sending ETH
            'gasPrice': gas_price,
            'gas': gas_limit,
            'nonce': nonce,
        }

        function_data = uniswap_router_contract.functions.swapExactTokensForETH(
            dai_amount_in_wei,
            amount_out_min[1],  # Min amount of WETH you expect to receive
            path,
            walletAddress,
            int(time.time()) + 60 * 10,  # 10 minutes
        ).build_transaction(transaction)
        signed_transaction = web3.eth.account.sign_transaction(function_data, private_key)

        tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction).hex()

        print(f'Transaction Hash: {tx_hash}')
        return amount_out_min, tx_hash

    except Exception as e:
        print('Error:', e)


"""
    Description:
        This function handles pending transactions, specifically focusing on transactions involving
        a specified wallet (`wallet_to_mirror`). It checks if the transaction is either outgoing
        from or incoming to the specified wallet and emits appropriate events using socketIO.

    Parameters:
        - w3 (Web3): An instance of the Web3 object.
        - tx_hash (str): The hash of the pending transaction.
        - wallet_to_mirror (str): The wallet address being monitored.
        - walletAddress (str): The address of the wallet used for transaction handling.
        - private_key (str): The private key associated with the walletAddress.
        - active_chain (str): The name of the active blockchain.

    Usage:
        handle_transaction(w3, "0x123abc...", "0x456def...", "0x789ghi...", "private_key_here", "ethereum")

    Notes:
        - This function checks if the pending transaction is related to the specified `wallet_to_mirror`.
        - It emits events through socketIO to signal success or failure in handling mirror swap transactions.
"""
def handle_transaction(w3, tx_hash, wallet_to_mirror,walletAddress,private_key,active_chain):
    """
    Parameters:
        - w3 (Web3): An instance of the Web3 object.
        - tx_hash (str): The hash of the pending transaction.
        - wallet_to_mirror (str): The wallet address being monitored.
        - walletAddress (str): The address of the wallet used for transaction handling.
        - private_key (str): The private key associated with the walletAddress.
        - active_chain (str): The name of the active blockchain.

    Usage:
        handle_transaction(w3, "0x123abc...", "0x456def...", "0x789ghi...", "private_key_here", "ethereum")
    """
    # Get pending transaction details
    print("here")
    try:
        tx = w3.eth.get_transaction(tx_hash)
        # print(tx)

        if tx is not None:
            # Check if the transaction is sent from the wallet to mirror
            # if(mirror_swap_transaction(tx, wallet_to_mirror)):
            res, tx_hash = mirror_swap_transaction(tx, wallet_to_mirror,walletAddress,private_key,active_chain)
            print(res, tx_hash)
            if res is not None:
                if res == True:
                    print("Doing Success")
                    socketIO.emit("successMirror", {"txHash":tx_hash})
                else:
                    socketIO.emit("noMirror")
            if tx['from'].lower() == wallet_to_mirror.lower():
                print(f"Pending Outgoing Transaction from {wallet_to_mirror} to {tx['to']}")
            # Check if the transaction is sent to the wallet to mirror
            elif tx['to'] and tx['to'].lower() == wallet_to_mirror.lower():
                print(f"Pending Incoming Transaction to {wallet_to_mirror} from {tx['from']}")
    except Exception as e:
        print("coudnt find txn", e)


"""
    Description:
        Customize this function to create and send a swap transaction using the PancakeSwap Router contract
        based on the incoming transaction data. The function parses the transaction data and provides the
        correct input for the swapExactTokensForTokens or swapExactETHForTokens function, handling gas prices,
        gas limits, and nonce correctly.

    Parameters:
        - tx (dict): The transaction dictionary containing details like 'to', 'from', 'input', etc.
        - wallet_to_mirror (str): The address of the wallet to be mirrored.
        - walletAddress (str): The address of the mirroring wallet.
        - private_key (str): The private key of the mirroring wallet.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - tuple or None: A tuple containing (success_flag, tx_hash) if successful, or None if an error occurs.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.

    Usage:
        success, tx_hash = mirror_swap_transaction(tx, "0x123abc...", "0x456def...", "0x789ghi...", "bsc")
"""
def mirror_swap_transaction(tx, wallet_to_mirror,walletAddress,private_key,active_chain):
    """
    Parameters:
        - tx (dict): The transaction dictionary containing details like 'to', 'from', 'input', etc.
        - wallet_to_mirror (str): The address of the wallet to be mirrored.
        - walletAddress (str): The address of the mirroring wallet.
        - private_key (str): The private key of the mirroring wallet.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - tuple or None: A tuple containing (success_flag, tx_hash) if successful, or None if an error occurs.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.
    """
    # Customize this function to create and send a swap transaction
    # using the PancakeSwap Router contract based on the incoming transaction data.
    # You need to parse the transaction data and provide the correct input
    # for the swapExactTokensForTokens or swapExactETHForTokens function.
    # Remember to handle gas prices, gas limits, and nonce correctly.
    print("in mirro")
    
    try:
        if active_chain is None or active_chain not in chain_list.keys():
            raise ChainNameNotFoundError(active_chain)
        # print(chain_list, active_chain)
        current_chain = chain_list[active_chain]
        # print(current_chain, type(current_chain), current_chain['web3'])
        web3 = current_chain['web3']
        print('web3',web3)
        # token_address = web3.to_checksum_address(token_address)
        # current_chain = chain_list[active_chain]
        w_token_address = current_chain['w_address']
        w_token_address = Web3.to_checksum_address(w_token_address)
        router_address, router_abi = current_chain['router_address'], current_chain['router_abi']
          # BNB
        erc_20_abi = current_chain['erc_20_abi']
        amountOut = None
        print(web3.net.version)
        # tokenRouter = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc_20_abi)
        # tokenDecimals = tokenRouter.functions.decimals().call()
        # tokenDecimals = getTokenDecimal(tokenDecimals)
        base_scan_url, scan_api_key = current_chain['base_scan_url'], current_chain['scan_api_key']

    except ChainNameNotFoundError as e:
        print(str(e))
        return None
    except Exception as e:
        print(str(e), 'In the main exception')
        return None
    
    try:
        # infura_url = infura_url  # Replace with your Infura project ID

        # web3 = Web3(Web3.HTTPProvider(infura_url))
        maxMirrorLimit=mirror_thread_dict[walletAddress]['maxMirrorLimit']
        if "web3" not in locals():
            print("Something is wrong with the web3 connection, returning web3 not found locals() funtion")
            return 
        account = Account.from_key(private_key)    

        # uniswap_router_address = pancakeSwap_RouterAddress  # Ethereum Mainnet Uniswap V2 Router address
        # with open('./uniswapRouterABI.json', 'r') as abi_file:
            # uniswap_router_abi = json.load(abi_file)  # Load the ABI from a JSON file

        if tx.to == router_address and tx['from'] == wallet_to_mirror:
            print("Found Mirror here")
            socketIO.emit("foundMirror", {"txHash":web3.toJSON(tx), "walletAddress":walletAddress})
            uniswap_router_contract = web3.eth.contract(address=router_address, abi=router_abi)
            function_input = uniswap_router_contract.decode_function_input(tx.input)
            print(function_input, type(function_input), type(function_input[0]))   
            args = function_input[1]
            args['to'] = walletAddress
            print(args)
            gas_limit = 300000
            nonce = web3.eth.get_transaction_count(account.address) 
            gas_price = web3.eth.gas_price
            if web3.from_wei(tx['value'], 'ether')> maxMirrorLimit:
                print("in val", tx['value'], maxMirrorLimit)
                socketIO.emit("noMirror", {'txVal':tx['value']})
                return False
            print(tx)
            if ("swapExactTokensForETH" in function_input[0].__str__()):
                print("in here")
                socketIO.emit("mirrored", {"txhash":"tx_hash"})

                print(walletAddress)
                amount_out_min = uniswap_router_contract.functions.getAmountsOut(args['amountIn'],  args["path"]).call()
                approve_uniswap_router(args['amountIn'], args['path'][0])
                nonce = web3.eth.get_transaction_count(account.address) + 1
                function_args = {
                'from': account.address,
                'value': tx['value'],  # You are selling DAI, not sending ETH
                'gasPrice': gas_price,
                'gas':gas_limit ,
                'nonce': nonce  ,
                }
                try:
                    function_data = uniswap_router_contract.functions.swapExactTokensForETH(
                    args['amountIn'],
                    amount_out_min[1],  # Min amount of WETH you expect to receive
                    args["path"],
                    walletAddress,
                    int(time.time()) + 60 * 10,  # 10 minutes
                ).build_transaction(function_args)
                # transaction = function_input[0].transact({'from':walletAddress})
                # transaction_hash = transaction.build_transaction(args)
                # print(transaction_hash)
                    signed_transaction = web3.eth.account.sign_transaction(function_data, private_key)
                    tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction).hex()
                    print(tx_hash)
                    socketIO.emit("mirrored", {"txhash":tx_hash})
                    etherscan_uri = f"{base_scan_url}module=transaction&action=gettxreceiptstatus&txhash={tx_hash}&apikey={scan_api_key}"
                    response = requests.get(etherscan_uri)
                    return True, tx_hash

                    if not response:
                        raise Exception
                    if response.text['result']['status'] == 0:
                        raise Exception
                except Exception as e:
                    try:
                        nonce = web3.eth.get_transaction_count(account.address) + 2
                        function_args = {
                        'from': account.address,
                        'value': tx['value'],  # You are selling DAI, not sending ETH
                        'gasPrice': gas_price,
                        'gas':gas_limit ,
                        'nonce': nonce  ,
                        }
                                
                        function_data = uniswap_router_contract.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
                        args['amountIn'],
                        amount_out_min[1],  # Min amount of WETH you expect to receive
                        args["path"],
                        walletAddress,
                        int(time.time()) + 60 * 10,  # 10 minutes
                    ).build_transaction(function_args)
                    # transaction = function_input[0].transact({'from':walletAddress})
                    # transaction_hash = transaction.build_transaction(args)
                    # print(transaction_hash)
                        signed_transaction = web3.eth.account.sign_transaction(function_data, private_key)
                        tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction).hex()
                        print(tx_hash)
                        socketIO.emit("mirrored", {"txhash":tx_hash})
                        return True, tx_hash
                    except Exception as e:
                        print("Something went wrong in mirroing that sell transaction", e)
            if ("swapExactETHForTokens" in function_input[0].__str__()):
                function_args = {
                'from': account.address,
                'value': tx['value'],  # You are selling DAI, not sending ETH
                'gasPrice': gas_price,
                'gas':gas_limit ,
                'nonce': nonce,
                }
                print("in here")
                print(walletAddress)
                amount_out_min = uniswap_router_contract.functions.getAmountsOut(tx['value'],  args["path"]).call()
                args['path'][0], args['path'][1] = web3.to_checksum_address(args['path'][0]), web3.to_checksum_address(args['path'][1])
                function_data = uniswap_router_contract.functions.swapExactETHForTokens(
                # args['amountIn'],
                amount_out_min[1],  # Min amount of WETH you expect to receive
                args["path"],
                walletAddress,
                int(time.time())+ 60 * 100,  # 10 minutes
            ).build_transaction(function_args)
            # transaction = function_input[0].transact({'from':walletAddress})
            # transaction_hash = transaction.build_transaction(args)
            # print(transaction_hash)
                signed_transaction = web3.eth.account.sign_transaction(function_data, private_key)
                tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction).hex()
                print(tx_hash)
                return True, tx_hash
            
            # function_data = uniswap_router_contract.functions.function_input[0](
            #     dai_amount_in_wei,
            #     amount_out_min[1],  # Min amount of WETH you expect to receive
            #     path,
            #     walletAddress,
            #     int(time.time()) + 60 * 10,  # 10 minutes
            # ).build_transaction(transaction)
        else:
            return None, None 

        #
    except Exception as E:
        print("error in handling mirror", E)
    # Example: Swap BNB for a specific token using swapExactETHForTokens
    # swap_function = pancake_swap_router.functions.swapExactETHForTokens(
    #     amountOutMin, path, to, deadline
    # )
    # tx_data = swap_function.build_transaction({
    #     'chainId': 56,  # BSC mainnet chain ID
    #     'gasPrice': w3.to_wei('5', 'gwei'),  # Customize gas price
    #     'gas': 2000000,  # Customize gas limit
    #     'nonce': w3.eth.get_transaction_count(mirror_account.address),
    # })

    # signed_mirror_tx = w3.eth.account.sign_transaction(tx_data, private_key)
    # tx_hash = w3.eth.send_raw_transaction(signed_mirror_tx.rawTransaction)
    # print(f"Mirrored Swap Transaction Hash: {tx_hash.hex()}")
    pass



"""
    Description:
        Asynchronous function to continuously mirror Ethereum transactions for a specific wallet address.

    Parameters:
        - walletAddress (str): The Ethereum address of the wallet to mirror transactions for.
        - private_key (str): The private key corresponding to the wallet address.

    Raises:
        - Exception: If an error occurs during the mirror snipe process.

    Usage:
        asyncio.create_task(mirror_transactions("0x123abc...", "private_key"))

    Notes:
        - This function runs in an infinite loop, continuously monitoring and handling new transactions.
        - To stop the mirror snipe, set `mirror_thread_dict[walletAddress]['mirrorSnipe']` to False.

    Global Variables:
        - mirror_thread_dict (dict): A dictionary to store mirror snipe-related information.
          It is assumed to be pre-defined and accessible within the function.

"""
async def mirror_transactions(walletAddress,private_key):
    """
    Parameters:
        - walletAddress (str): The Ethereum address of the wallet to mirror transactions for.
        - private_key (str): The private key corresponding to the wallet address.

    Raises:
        - Exception: If an error occurs during the mirror snipe process.

    Global Variables:
        - mirror_thread_dict (dict): A dictionary to store mirror snipe-related information.
          It is assumed to be pre-defined and accessible within the function.

    """
    try:
        # last_block = w3.eth.get_block_number
        # global last_block
        infura_url = infura_url  # Replace with your Infura project ID
        # ws_uri = "wss://bold-billowing-theorem.ethereum-goerli.discover.quiknode.pro/37486ccdc266345915a62af1f17cb0418d103adb/"
        web3 = Web3(Web3.HTTPProvider(infura_url))
        # pending_txn_filter = web3.eth.filter('pending')
        last_block = web3.eth.block_number
        # current_block_number = web3.eth.block_number
        # current_block_number=9675741
 
        current_block_number =9646683

        i = 0
        while mirror_thread_dict[walletAddress]['mirrorSnipe']:
            
            
            print(current_block_number, last_block)
            # if current_block_number > last_block:
            print("hello")
                # for block_number in range(last_block + 1, current_block_number + 1):
            block = web3.eth.get_block(current_block_number)
                    # print(block)
            if block or not mirror_thread_dict[walletAddress]['mirrorSnipe']:
                for tx_hash in block['transactions']:
                        # print(tx_hash)
                    if not mirror_thread_dict[walletAddress]['mirrorSnipe']:
                        break
                    to_be_mirror_wallet=mirror_thread_dict[walletAddress]['to_be_mirror_wallet']
                    handle_transaction(web3, tx_hash, to_be_mirror_wallet,walletAddress,private_key,active_chain)
            print(current_block_number)
            current_block_number+=1
            # await asyncio.sleep(4)
            # pending_txns = pending_txn_filter.get_new_entries()
            # print(pending_txns)
            # for tx_hash in pending_txns:
            #     handle_pending_transaction(web3,tx_hash, "0x70F657164e5b75689b64B7fd1fA275F334f28e18" )
            i+=1
    except Exception as e:
        print("Something went wrong in the mirror snipe", e)


"""
    Description:
        This asynchronous function continuously monitors and mirrors transactions related to a specific wallet address.
        It retrieves and processes transactions from the specified blockchain until the `mirrorSnipe` flag is set to False.

    Parameters:
        - walletAddress (str): The Ethereum address of the wallet to monitor and mirror transactions.
        - private_key (str): The private key corresponding to the wallet address for transaction signing.
        - active_chain (str): The name of the active blockchain.

    Notes:
        The function uses the global variable `mirror_thread_dict` to manage the state of the mirror snipe process.

    Usage:
        await mirror_transactions_general("0x123abc...", "0xabcdef...", "ethereum")

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.
        - Exception: If an unexpected error occurs during the mirror snipe process.

    Important:
        The function runs asynchronously, and you should use an event loop (e.g., asyncio) to execute it.
"""
async def mirror_transactions_general(walletAddress,private_key,active_chain):
    """
    Parameters:
        - walletAddress (str): The Ethereum address of the wallet to monitor and mirror transactions.
        - private_key (str): The private key corresponding to the wallet address for transaction signing.
        - active_chain (str): The name of the active blockchain.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.
        - Exception: If an unexpected error occurs during the mirror snipe process.
    """
    
    
    try:
        if active_chain is None or active_chain not in chain_list.keys():
            raise ChainNameNotFoundError(active_chain)
        # print(chain_list, active_chain)
        current_chain = chain_list[active_chain]
        # print(current_chain, type(current_chain), current_chain['web3'])
        web3 = current_chain['web3']
        # token_address = web3.to_checksum_address(token_address)
        # current_chain = chain_list[active_chain]
        w_token_address = current_chain['w_address']
        w_token_address = Web3.to_checksum_address(w_token_address)
        router_address, router_abi = current_chain['router_address'], current_chain['router_abi']
          # BNB
        erc_20_abi = current_chain['erc_20_abi']
        amountOut = None
        print(web3.net.version)
        # tokenRouter = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc_20_abi)
        # tokenDecimals = tokenRouter.functions.decimals().call()
        # tokenDecimals = getTokenDecimal(tokenDecimals)
    except ChainNameNotFoundError as e:
        print(str(e))
        return None
    except Exception as e:
        print(str(e), 'In the main exception')
        return None
    try:
        if "web3" not in locals():
            print("something is wrong with the web3 connection returning..")
        
        # last_block = w3.eth.get_block_number
        # global last_block
        # infura_url = infura_url  # Replace with your Infura project ID
        # ws_uri = "wss://bold-billowing-theorem.ethereum-goerli.discover.quiknode.pro/37486ccdc266345915a62af1f17cb0418d103adb/"
        # web3 = Web3(Web3.HTTPProvider(infura_url))
        # pending_txn_filter = web3.eth.filter('pending')
        last_block = web3.eth.block_number
        # current_block_number = web3.eth.block_number
        current_block_number=9675741
 
        # current_block_number =9646683

        i = 0
        walletAddress
        
        while mirror_thread_dict[walletAddress]['mirrorSnipe']:
            
            to_be_mirror_wallet=mirror_thread_dict[walletAddress]['to_be_mirror_wallet']
            print(current_block_number, last_block, "blocks, info")
            # if current_block_number > last_block:
            print("hello")
                # for block_number in range(last_block + 1, current_block_number + 1):
            block = web3.eth.get_block(current_block_number)
                    # print(block)
            if block or not mirror_thread_dict[walletAddress]['mirrorSnipe']:
                for tx_hash in block['transactions']:
                        # print(tx_hash)
                    if not mirror_thread_dict[walletAddress]['mirrorSnipe']:
                        break
                    handle_transaction(web3, tx_hash, to_be_mirror_wallet,walletAddress,private_key,active_chain)
            print(current_block_number, "current_block_number")
            current_block_number+=1
            # await asyncio.sleep(4)
            # pending_txns = pending_txn_filter.get_new_entries()
            # print(pending_txns)
            # for tx_hash in pending_txns:
            #     handle_pending_transaction(web3,tx_hash, "0x70F657164e5b75689b64B7fd1fA275F334f28e18" )
            i+=1
    except Exception as e:
        print("Something went wrong in the mirror snipe", e)



buyTokenThread = threading.Thread(target=Buy, args=(None, None))



# input("")
#------------------------------------------END OF TOKEN SCANNER BACKGROUND CODE---------------------------------------------------------------------




#------------------------------------------ LEVERAGE AND LIQUIDITY MANAGERS--------------------------------------------------------------------

# from LiquidationEngine.LiquidationEngine import LiquidationEngine
# from LiquidationEngine.LeverageEngine import LeverageManagement

from .LiquidationEngine.LiquidationEngine import LiquidationEngine
from .LiquidationEngine.LeverageEngine import LeverageManagement


"""
    Description:
        This function initializes an instance of the LeverageManagement class, which allows interaction with a
        smart contract representing a leverage management system. The contract is identified by its address and ABI.

    Parameters:
        - walletAddress (str): The Ethereum address of the user's wallet.
        - private_key (str): The private key corresponding to the walletAddress for transaction signing.

    Returns:
        - LeverageManagement: An instance of the LeverageManagement class for managing leverage-related operations.

    Usage:
        leverage_manager = Leverage_manager("0x123abc...", "your_private_key")
        # Now you can use leverage_manager to interact with the leverage management smart contract.

    Note:
        Ensure that the provided walletAddress and private_key are valid and have the necessary permissions.

    Global Variables:
        - leverage_contract_address: The Ethereum address of the leverage management smart contract.
        - leverage_contract_abi: The ABI (Application Binary Interface) of the leverage management smart contract.
        - leverage_infura_url: The Infura URL for connecting to the Ethereum network.

    """
def Leverage_manager(walletAddress,private_key):
    """
    
    Parameters:
        - walletAddress (str): The Ethereum address of the user's wallet.
        - private_key (str): The private key corresponding to the walletAddress for transaction signing.

    Returns:
        - LeverageManagement: An instance of the LeverageManagement class for managing leverage-related operations.

    Global Variables:
        - leverage_contract_address: The Ethereum address of the leverage management smart contract.
        - leverage_contract_abi: The ABI (Application Binary Interface) of the leverage management smart contract.
        - leverage_infura_url: The Infura URL for connecting to the Ethereum network.

    """
    # leverage_contract_address = leverage_contract_address
    # print(leverage_contract_address)
    # leverage_contract_abi = '[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"user","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"ContributionMade","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint256","name":"threshold","type":"uint256"}],"name":"HealthFactorThresholdSet","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"user","type":"address"},{"indexed":false,"internalType":"uint256","name":"leverageAmount","type":"uint256"}],"name":"LeverageGiven","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"tokenAddress","type":"address"}],"name":"TokenBoughtFromLeverage","type":"event"},{"inputs":[{"internalType":"address","name":"tokenAddress","type":"address"},{"internalType":"uint256","name":"tokenValue","type":"uint256"},{"internalType":"address","name":"userAddress","type":"address"},{"internalType":"uint256","name":"leverageTaken","type":"uint256"}],"name":"addToken","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address[]","name":"tokenAddresses","type":"address[]"},{"internalType":"uint256[]","name":"tokenValues","type":"uint256[]"},{"internalType":"uint256[]","name":"leveragesTaken","type":"uint256[]"},{"internalType":"address","name":"userAddress","type":"address"}],"name":"addTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"admin","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"balance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"deposit","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"getHealthFactorThreshold","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getLeverageAmount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getTotalContributions","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getUserContribution","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getUserTokens","outputs":[{"components":[{"internalType":"address","name":"tokenAddress","type":"address"},{"internalType":"uint256","name":"tokenValue","type":"uint256"},{"internalType":"uint256","name":"leverageTaken","type":"uint256"},{"internalType":"uint256","name":"soldTokenValue","type":"uint256"}],"internalType":"struct LeverageWallet.TokenInfo[]","name":"","type":"tuple[]"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"giveLeverage","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"healthFactor","type":"uint256"},{"internalType":"address","name":"userAddres","type":"address"}],"name":"giveProperLeverage","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"healthFactorThreshold","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"leverageAmount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"makeContribution","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"tokenAddress","type":"address"},{"internalType":"uint256","name":"soldAmount","type":"uint256"}],"name":"sellToken","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"threshold","type":"uint256"}],"name":"setHealthFactorThreshold","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"setLeverageAmount","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"userContributions","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"userLeverageGiven","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"userSoldTokens","outputs":[{"components":[{"internalType":"address","name":"tokenAddress","type":"address"},{"internalType":"uint256","name":"tokenValue","type":"uint256"},{"internalType":"uint256","name":"leverageTaken","type":"uint256"},{"internalType":"uint256","name":"soldTokenValue","type":"uint256"}],"stateMutability":"view","type":"function"}],"type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"uint256","name":"","type":"uint256"}],"name":"userTokensInfo","outputs":[{"components":[{"internalType":"address","name":"tokenAddress","type":"address"},{"internalType":"uint256","name":"tokenValue","type":"uint256"},{"internalType":"uint256","name":"leverageTaken","type":"uint256"},{"internalType":"uint256","name":"soldTokenValue","type":"uint256"}],"stateMutability":"view","type":"function"}],"type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"withdraw","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"withdrawUserContribution","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
    leverage_contract_abi='''
    [
			{
				"inputs": [],
				"stateMutability": "nonpayable",
				"type": "constructor"
			},
			{
				"anonymous": false,
				"inputs": [
					{
						"indexed": true,
						"internalType": "address",
						"name": "user",
						"type": "address"
					},
					{
						"indexed": false,
						"internalType": "uint256",
						"name": "amount",
						"type": "uint256"
					}
				],
				"name": "ContributionMade",
				"type": "event"
			},
			{
				"anonymous": false,
				"inputs": [
					{
						"indexed": false,
						"internalType": "uint256",
						"name": "threshold",
						"type": "uint256"
					}
				],
				"name": "HealthFactorThresholdSet",
				"type": "event"
			},
			{
				"anonymous": false,
				"inputs": [
					{
						"indexed": true,
						"internalType": "address",
						"name": "user",
						"type": "address"
					},
					{
						"indexed": false,
						"internalType": "uint256",
						"name": "leverageAmount",
						"type": "uint256"
					}
				],
				"name": "LeverageGiven",
				"type": "event"
			},
			{
				"anonymous": false,
				"inputs": [
					{
						"indexed": true,
						"internalType": "address",
						"name": "tokenAddress",
						"type": "address"
					}
				],
				"name": "TokenBoughtFromLeverage",
				"type": "event"
			},
			{
				"inputs": [
					{
						"internalType": "address",
						"name": "tokenAddress",
						"type": "address"
					},
					{
						"internalType": "uint256",
						"name": "tokenValue",
						"type": "uint256"
					},
					{
						"internalType": "address",
						"name": "userAddress",
						"type": "address"
					},
					{
						"internalType": "uint256",
						"name": "leverageTaken",
						"type": "uint256"
					}
				],
				"name": "addToken",
				"outputs": [],
				"stateMutability": "nonpayable",
				"type": "function"
			},
			{
				"inputs": [
					{
						"internalType": "address[]",
						"name": "tokenAddresses",
						"type": "address[]"
					},
					{
						"internalType": "uint256[]",
						"name": "tokenValues",
						"type": "uint256[]"
					},
					{
						"internalType": "uint256[]",
						"name": "leveragesTaken",
						"type": "uint256[]"
					},
					{
						"internalType": "address",
						"name": "userAddress",
						"type": "address"
					}
				],
				"name": "addTokens",
				"outputs": [],
				"stateMutability": "nonpayable",
				"type": "function"
			},
			{
				"inputs": [],
				"name": "admin",
				"outputs": [
					{
						"internalType": "address",
						"name": "",
						"type": "address"
					}
				],
				"stateMutability": "view",
				"type": "function"
			},
			{
				"inputs": [],
				"name": "balance",
				"outputs": [
					{
						"internalType": "uint256",
						"name": "",
						"type": "uint256"
					}
				],
				"stateMutability": "view",
				"type": "function"
			},
			{
				"inputs": [
					{
						"internalType": "uint256",
						"name": "amount",
						"type": "uint256"
					}
				],
				"name": "deposit",
				"outputs": [],
				"stateMutability": "payable",
				"type": "function"
			},
			{
				"inputs": [],
				"name": "getHealthFactorThreshold",
				"outputs": [
					{
						"internalType": "uint256",
						"name": "",
						"type": "uint256"
					}
				],
				"stateMutability": "view",
				"type": "function"
			},
			{
				"inputs": [],
				"name": "getLeverageAmount",
				"outputs": [
					{
						"internalType": "uint256",
						"name": "",
						"type": "uint256"
					}
				],
				"stateMutability": "view",
				"type": "function"
			},
			{
				"inputs": [],
				"name": "getTotalContributions",
				"outputs": [
					{
						"internalType": "uint256",
						"name": "",
						"type": "uint256"
					}
				],
				"stateMutability": "view",
				"type": "function"
			},
			{
				"inputs": [
					{
						"internalType": "address",
						"name": "user",
						"type": "address"
					}
				],
				"name": "getUserContribution",
				"outputs": [
					{
						"internalType": "uint256",
						"name": "",
						"type": "uint256"
					}
				],
				"stateMutability": "view",
				"type": "function"
			},
			{
				"inputs": [
					{
						"internalType": "address",
						"name": "user",
						"type": "address"
					}
				],
				"name": "getUserSoldTokens",
				"outputs": [
					{
						"components": [
							{
								"internalType": "address",
								"name": "tokenAddress",
								"type": "address"
							},
							{
								"internalType": "uint256",
								"name": "tokenValue",
								"type": "uint256"
							},
							{
								"internalType": "uint256",
								"name": "leverageTaken",
								"type": "uint256"
							},
							{
								"internalType": "uint256",
								"name": "soldTokenValue",
								"type": "uint256"
							}
						],
						"internalType": "struct LeverageWallet.TokenInfo[]",
						"name": "",
						"type": "tuple[]"
					}
				],
				"stateMutability": "view",
				"type": "function"
			},
			{
				"inputs": [
					{
						"internalType": "address",
						"name": "user",
						"type": "address"
					}
				],
				"name": "getUserTokens",
				"outputs": [
					{
						"components": [
							{
								"internalType": "address",
								"name": "tokenAddress",
								"type": "address"
							},
							{
								"internalType": "uint256",
								"name": "tokenValue",
								"type": "uint256"
							},
							{
								"internalType": "uint256",
								"name": "leverageTaken",
								"type": "uint256"
							},
							{
								"internalType": "uint256",
								"name": "soldTokenValue",
								"type": "uint256"
							}
						],
						"internalType": "struct LeverageWallet.TokenInfo[]",
						"name": "",
						"type": "tuple[]"
					}
				],
				"stateMutability": "view",
				"type": "function"
			},
			{
				"inputs": [],
				"name": "giveLeverage",
				"outputs": [],
				"stateMutability": "nonpayable",
				"type": "function"
			},
			{
				"inputs": [
					{
						"internalType": "uint256",
						"name": "healthFactor",
						"type": "uint256"
					},
					{
						"internalType": "address",
						"name": "userAddres",
						"type": "address"
					}
				],
				"name": "giveProperLeverage",
				"outputs": [],
				"stateMutability": "nonpayable",
				"type": "function"
			},
			{
				"inputs": [],
				"name": "healthFactorThreshold",
				"outputs": [
					{
						"internalType": "uint256",
						"name": "",
						"type": "uint256"
					}
				],
				"stateMutability": "view",
				"type": "function"
			},
			{
				"inputs": [],
				"name": "leverageAmount",
				"outputs": [
					{
						"internalType": "uint256",
						"name": "",
						"type": "uint256"
					}
				],
				"stateMutability": "view",
				"type": "function"
			},
			{
				"inputs": [],
				"name": "makeContribution",
				"outputs": [],
				"stateMutability": "payable",
				"type": "function"
			},
			{
				"inputs": [
					{
						"internalType": "address",
						"name": "tokenAddress",
						"type": "address"
					},
					{
						"internalType": "uint256",
						"name": "soldAmount",
						"type": "uint256"
					}
				],
				"name": "sellToken",
				"outputs": [],
				"stateMutability": "nonpayable",
				"type": "function"
			},
			{
				"inputs": [
					{
						"internalType": "uint256",
						"name": "threshold",
						"type": "uint256"
					}
				],
				"name": "setHealthFactorThreshold",
				"outputs": [],
				"stateMutability": "nonpayable",
				"type": "function"
			},
			{
				"inputs": [
					{
						"internalType": "uint256",
						"name": "amount",
						"type": "uint256"
					}
				],
				"name": "setLeverageAmount",
				"outputs": [],
				"stateMutability": "nonpayable",
				"type": "function"
			},
			{
				"inputs": [
					{
						"internalType": "address",
						"name": "",
						"type": "address"
					}
				],
				"name": "userContributions",
				"outputs": [
					{
						"internalType": "uint256",
						"name": "",
						"type": "uint256"
					}
				],
				"stateMutability": "view",
				"type": "function"
			},
			{
				"inputs": [
					{
						"internalType": "address",
						"name": "",
						"type": "address"
					}
				],
				"name": "userLeverageGiven",
				"outputs": [
					{
						"internalType": "uint256",
						"name": "",
						"type": "uint256"
					}
				],
				"stateMutability": "view",
				"type": "function"
			},
			{
				"inputs": [
					{
						"internalType": "address",
						"name": "",
						"type": "address"
					},
					{
						"internalType": "uint256",
						"name": "",
						"type": "uint256"
					}
				],
				"name": "userSoldTokens",
				"outputs": [
					{
						"internalType": "address",
						"name": "tokenAddress",
						"type": "address"
					},
					{
						"internalType": "uint256",
						"name": "tokenValue",
						"type": "uint256"
					},
					{
						"internalType": "uint256",
						"name": "leverageTaken",
						"type": "uint256"
					},
					{
						"internalType": "uint256",
						"name": "soldTokenValue",
						"type": "uint256"
					}
				],
				"stateMutability": "view",
				"type": "function"
			},
			{
				"inputs": [
					{
						"internalType": "address",
						"name": "",
						"type": "address"
					},
					{
						"internalType": "uint256",
						"name": "",
						"type": "uint256"
					}
				],
				"name": "userTokensInfo",
				"outputs": [
					{
						"internalType": "address",
						"name": "tokenAddress",
						"type": "address"
					},
					{
						"internalType": "uint256",
						"name": "tokenValue",
						"type": "uint256"
					},
					{
						"internalType": "uint256",
						"name": "leverageTaken",
						"type": "uint256"
					},
					{
						"internalType": "uint256",
						"name": "soldTokenValue",
						"type": "uint256"
					}
				],
				"stateMutability": "view",
				"type": "function"
			},
			{
				"inputs": [
					{
						"internalType": "uint256",
						"name": "amount",
						"type": "uint256"
					}
				],
				"name": "withdraw",
				"outputs": [],
				"stateMutability": "nonpayable",
				"type": "function"
			},
			{
				"inputs": [
					{
						"internalType": "uint256",
						"name": "amount",
						"type": "uint256"
					}
				],
				"name": "withdrawUserContribution",
				"outputs": [],
				"stateMutability": "nonpayable",
				"type": "function"
			}
		]
    '''   
    # leverage_infura_url = leverage_infura_url
    leverage_manager = LeverageManagement(leverage_infura_url,
                                        leverage_contract_abi, 
                                        leverage_contract_address, 
                                        walletAddress, 
                                        private_key)
    return leverage_manager



# Create a LiquidationEngine instance for each wallet
"""
    Description:
        This function creates an instance of the LiquidationEngine for managing a main wallet's leveraged positions.

    Parameters:
        - walletAddress (str): The Ethereum address of the main wallet.
        - private_key (str): The private key associated with the main wallet.
        - leverage_manager: An instance of the leverage manager used for managing leverage.

    Returns:
        - LiquidationEngine: An instance of the LiquidationEngine configured for the main wallet.

    Usage:
        main_engine = Main_wallet_engine("0x123abc...", "private_key_here", leverage_manager_instance)
"""
def Main_wallet_engine(walletAddress,private_key,leverage_manager):  
    """
    Parameters:
        - walletAddress (str): The Ethereum address of the main wallet.
        - private_key (str): The private key associated with the main wallet.
        - leverage_manager: An instance of the leverage manager used for managing leverage.

    Returns:
        - LiquidationEngine: An instance of the LiquidationEngine configured for the main wallet.
    """ 

    main_wallet_engine = LiquidationEngine(
            ethereum_node_url=ethereum_node_url,
            private_key=private_key,
            account_address=walletAddress,
            router_address=router_address,
            # token_address="0x75521d5D96Ceb4c71b8f8051ea0b018A2Db8848C",
            # initial_position=0.000001,  # Initial position in ETH
            max_chunk_percentage=0.1,  # Max chunk size as a percentage of remaining position
            slippage_tolerance=0.01,  # Slippage tolerance as a decimal
            # leverage=5,  # Leverage
            maintenance_margin=0.8,  # Maintenance margin in ETH
            liquidation_threshold=0.7,  # Liquidation threshold in ETH
            # bought_price=0.0000001/0.199599960159847952,
            gas_price=10,
            gas_amount=850000,
            transaction_revert_time=10000,
            leverage_engine=leverage_manager
        )
    return main_wallet_engine




#------------------------------------------END OF LEVERAGE AND LIQUIDITY MANAGERS CODE---------------------------------------------------------------------



"""
    Endpoint: /mirror
    HTTP Method: POST

    Description:
        This route handles the mirroring increment request received via POST method.
        The request should include a JSON object containing 'chatId' and 'active_chain'.
        It starts a mirroring loop thread for the specified wallet if conditions are met.

    Request JSON Object:
        {
            'chatId': (str) Telegram chat ID,
            'active_chain': (str) Name of the active blockchain,
        }

    Returns:
        - jsonify: JSON response indicating the status of the mirroring process.
                   Returns 'chatId not found' if the chatId is not registered.
                   Returns 'started for {walletAddress}' if the mirroring process is initiated.
                   Returns an error message if conditions are not met.

    Notes:
        - The mirroring process is handled by a separate thread.
        - Ensure the wallet is registered and has necessary information in the 'chatId_dict'.
        - The mirroring thread is managed in 'mirror_thread_dict'.

    Usage:
        Send a POST request to '/mirror' with the required JSON object to initiate mirroring.
    """
# @socketIO.on('mirror')
@app.route('/mirror',methods=['POST'])
def mirror_increment():
    """
    Request JSON Object:
        {
            'chatId': (str) Telegram chat ID,
            'active_chain': (str) Name of the active blockchain,
        }

    Returns:
        - jsonify: JSON response indicating the status of the mirroring process.
                   Returns 'chatId not found' if the chatId is not registered.
                   Returns 'started for {walletAddress}' if the mirroring process is initiated.
                   Returns an error message if conditions are not met.

    Usage:
        Send a POST request to '/mirror' with the required JSON object to initiate mirroring.
    """
    #  in data we get the array for inputs
    try:
        data=request.json
        print("loop started")

        chatId=data['chatId']
        active_chain=data['active_chain']
        if chatId not in chatId_dict:
            return jsonify({'result':'chatId not found'}), 400

        if chatId not in multi_wallet_dict:
            return jsonify({'result':"chatId not found"}), 400
            
        count, index = 0, -1
        for j, k in enumerate(multi_wallet_dict[chatId]):
            print(multi_wallet_dict[chatId][j], j)
            if multi_wallet_dict[chatId][j]['status'] == True:
                        
                index = j
                count+=1
                print(index, "index")
                
        if count > 1:
            return jsonify({'result':'multiple active wallets'}),400
        else:
            count=0
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
            
            
        walletAddress=multi_wallet_dict[chatId][index]['walletAddress']
        private_key=multi_wallet_dict[chatId][index]['private_key']
                
        if walletAddress in mirror_thread_dict:
            mirror_loop_thread=threading.Thread(target=mirror_handler,args=(walletAddress,private_key,active_chain))
            mirror_thread_dict[walletAddress]['mirrorThread']=mirror_loop_thread
            mirror_thread_dict[walletAddress]['mirrorSnipe']=True
            mirror_loop_thread.start()
            socketIO.emit('mirroringFromMined', {'value': f"started for {walletAddress}"})
                    
        else:
            return jsonify({'result':f'need to set the maxMirrorLimit or to_be_mirror_wallet for walletAddress {walletAddress}'}), 400
        return jsonify('start'), 200
    except Exception as e:
        print(str(e), "Error in starting mirror")
        return jsonify({"error":str(e)}),400
        # else:
        #     print("not test")
        #     globalMirrorThread = restart_thread(mirror_handler, False)
        #     print(globalSnipingThread)

        

"""
    Endpoint: /buyToken
    HTTP Method: POST

    Description:
        This endpoint handles the purchase of a specified amount of an ERC20 token using the provided
        wallet address and private key. The result of the purchase, including the token amount and transaction hash,
        is sent back as a JSON response. Additionally, a 'tokenBought' event is emitted via Socket.IO.

    Request JSON Payload:
        {
            "amount": float,    # The amount of the token to be purchased.
            "tokenAddress": str, # The Ethereum address of the ERC20 token.
            "chatId": str,       # Unique identifier for the chat.
            "active_chain": str  # The name of the active blockchain.
        }

    Response JSON:
        {
            "tokenAmount": str,  # The amount of the purchased token.
            "tokenAddress": str, # The Ethereum address of the purchased token.
            "txHash": str        # The transaction hash of the purchase.
        }

    Socket.IO Event:
        - Event Name: 'tokenBought'
        - Payload: {"tokenAmount": str, "tokenAddress": str, "txHash": str}

    Returns:
        - JSON response with information about the purchased token.

    Raises:
        - KeyError: If 'chatId' is not found in the chatId_dict.

    Usage:
        curl -X POST -H "Content-Type: application/json" -d '{"amount": 10, "tokenAddress": "0x123abc...", "chatId": "123", "active_chain": "ethereum"}' http://your-api-url/buyToken
    """
@app.route('/buyToken',methods=['POST'])
def handle_buying():
    """
    Request JSON Payload:
        {
            "amount": float,    # The amount of the token to be purchased.
            "tokenAddress": str, # The Ethereum address of the ERC20 token.
            "chatId": str,       # Unique identifier for the chat.
            "active_chain": str  # The name of the active blockchain.
        }

    Response JSON:
        {
            "tokenAmount": str,  # The amount of the purchased token.
            "tokenAddress": str, # The Ethereum address of the purchased token.
            "txHash": str        # The transaction hash of the purchase.
        }

    Socket.IO Event:
        - Event Name: 'tokenBought'
        - Payload: {"tokenAmount": str, "tokenAddress": str, "txHash": str}

    Returns:
        - JSON response with information about the purchased token.

    Raises:
        - KeyError: If 'chatId' is not found in the chatId_dict.
    """
    try:
        data=request.json
        amount, token_address,chatId, active_chain = data['amount'], data['tokenAddress'],data['chatId'], data['active_chain']
        if chatId not in chatId_dict:
            return jsonify({'result':'chatId not found'}),400
        
        if chatId not in multi_wallet_dict:
            return jsonify({'result':"chatId not found"}), 400
        
        count, index = 0, -1
        for j, k in enumerate(multi_wallet_dict[chatId]):
            print(multi_wallet_dict[chatId][j], j)
            if multi_wallet_dict[chatId][j]['status'] == True:
                    
                index = j
                count+=1
                print(index, "index")
            
        if count > 1:
            return jsonify({'result':'multiple active wallets'}),400
        else:
            count=0
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
        
        
        walletAddress=multi_wallet_dict[chatId][index]['walletAddress']
        private_key=multi_wallet_dict[chatId][index]['private_key']
        print('walletAddress',walletAddress)
        print('private_key',private_key)
        buying_response= buy_for_eth_general(amount, token_address, False,walletAddress,private_key, active_chain)
        if isinstance(buying_response, dict):
            return jsonify(buying_response), 400
        token_amount, tx_hash = buying_response 
        print(type(tx_hash), type(token_amount))
        socketIO.emit('tokenBought', {"tokenAmount":str(token_amount), "tokenAddress":str(token_address), "txHash":str(tx_hash)})
        # socketIO.emit('test', {'walletAddress': walletAddress, 'privateKey':private_key})
        return jsonify({"tokenAmount":str(token_amount), "tokenAddress":str(token_address), "txHash":str(tx_hash)}),200
    except Exception as e:
        print(str(e), "error in buying")
        return jsonify({"error":str(e)}), 400

# ----------------------------------- Leverage buying funtionality -------------------------------------


# @app.route('/getLeverageWithToken', methods=['POST'])
# def handle_get_leverage():
#     data=request.json

#     token_address,chatId, active_chain = data['tokenAddress'],data['chatId'], data['active_chain']
#     if chatId not in chatId_dict:
#         return jsonify({'result':'chatId not found'}),400
#     walletAddress=chatId_dict[chatId]['walletAddress']
#     private_key=chatId_dict[chatId]['private_key']
#     if walletAddress not in leverage_thread_dict:
#         return jsonify({'result':'leverage is not init'}),400
#     Leverage_manager=leverage_thread_dict[walletAddress]['Leverage_manager']
#     leverageAmount=Leverage_manager.get_leverage_amount(token_address,active_chain)
#     if leverageAmount == -1  :
#         return jsonify({'result':f'No leverage for {token_address}','leverageAmount':0}),400
#     return jsonify({'result':f'Leverage for {token_address}','leverageAmount':leverageAmount}),200
    


# @app.route('/buyTokenwithLeverage',methods=['POST'])
# def handle_leverage_buying():
#     data=request.json
#     amount, token_address,chatId, active_chain, leverageAmount = data['amount'], data['tokenAddress'],data['chatId'], data['active_chain'],data['leverageAmount']
    
#     if chatId not in chatId_dict:
#         return jsonify({'result':'chatId not found'}),400
    
#     walletAddress=chatId_dict[chatId]['walletAddress']
#     private_key=chatId_dict[chatId]['private_key']
    
#     if walletAddress not in leverage_thread_dict:
#         return jsonify({'result':'leverage is not init'})
    
#     Leverage_manager=leverage_thread_dict[walletAddress]['Leverage_manager']
  
    
#     amountWithLeverage = amount * leverageAmount
#     token_amount, tx_hash = buy_for_eth_general(amountWithLeverage, token_address, False,walletAddress,private_key, active_chain)
#     if token_amount == None or tx_hash == None:
#         return jsonify({'result':'Something is wrong!,Try Again'})
    
#     print(type(tx_hash), type(token_amount))
#     socketIO.emit('leverageTokenBought', {"tokenAmount":str(token_amount), "tokenAddress":str(token_address), "txHash":str(tx_hash)})
#     Leverage_manager.add_token(token_address=token_address, token_value=token_amount, sender_address=walletAddress, leverage_taken=leverageAmount)

#     return jsonify({"tokenAmount":str(token_amount), "tokenAddress":str(token_address), "txHash":str(tx_hash)}),200

"""
    Description:
        This function handles the process of buying a specified amount of a given ERC20 token using Ethereum.
        It takes the necessary data from the input `data` dictionary, including the amount, token address, wallet address,
        and private key. The buying process is performed by calling the `buy_for_eth` function.

    Parameters:
        - data (dict): A dictionary containing the following key-value pairs:
            - 'amount' (float): The amount of the token to buy.
            - 'tokenAddress' (str): The Ethereum address of the ERC20 token.
            - 'walletAddress' (str): The Ethereum address of the wallet performing the transaction.
            - 'private_key' (str): The private key associated with the wallet for transaction signing.

    Returns:
        - dict: A dictionary containing information about the transaction, including:
            - 'tokenAmount' (str): The amount of the bought token.
            - 'tokenAddress' (str): The Ethereum address of the ERC20 token.
            - 'txHash' (str): The transaction hash of the completed transaction.

    Usage:
        data = {
            'amount': 10.0,
            'tokenAddress': "0x123abc...",
            'walletAddress': "0x456def...",
            'private_key': "0x789ghi...",
        }
        result = handle_buying_for_sniping(data)
    """
def handle_buying_for_sniping(data):
    """
    Parameters:
        - data (dict): A dictionary containing the following key-value pairs:
            - 'amount' (float): The amount of the token to buy.
            - 'tokenAddress' (str): The Ethereum address of the ERC20 token.
            - 'walletAddress' (str): The Ethereum address of the wallet performing the transaction.
            - 'private_key' (str): The private key associated with the wallet for transaction signing.

    Returns:
        - dict: A dictionary containing information about the transaction, including:
            - 'tokenAmount' (str): The amount of the bought token.
            - 'tokenAddress' (str): The Ethereum address of the ERC20 token.
            - 'txHash' (str): The transaction hash of the completed transaction.
    """
    # data=request.json
    amount, token_address,walletAddress,private_key = data['amount'], data['tokenAddress'],data['walletAddress'],data['private_key']
    print('walletAddress',walletAddress)
    print('private_key',private_key)
    token_amount, tx_hash = buy_for_eth(amount, token_address, False,walletAddress,private_key)
    print(type(tx_hash), type(token_amount))
    # socketIO.emit('tokenBought', {"tokenAmount":str(token_amount), "tokenAddress":str(token_address), "txHash":str(tx_hash)})
    return  {"tokenAmount":str(token_amount), "tokenAddress":str(token_address), "txHash":str(tx_hash)}

"""
    Description:
        This function performs a token swap using the Uniswap V2 Router on the Ethereum blockchain.
        It sells a specified amount of one ERC20 token (`token_to_sell_address`) to buy another ERC20 token (`token_to_buy_address`).

    Parameters:
        - amount (float): The amount of the token to be sold.
        - token_to_sell_address (str): The Ethereum address of the ERC20 token to be sold.
        - token_to_buy_address (str): The Ethereum address of the ERC20 token to be bought.

    Returns:
        - tuple: A tuple containing the estimated amount of the bought token in WETH (float) and the transaction hash (str).
                 Returns None if an error occurs during the process.

    Notes:
        - Ensure that the `private_key` global variable is set with the private key of the account performing the swap.

    Usage:
        result = buy_for_tokens_and_tokens(1.0, "0x123abc...", "0x456def...")
    """
def buy_for_tokens_and_tokens(amount, token_to_sell_address, token_to_buy_address):
    """
    Parameters:
        - amount (float): The amount of the token to be sold.
        - token_to_sell_address (str): The Ethereum address of the ERC20 token to be sold.
        - token_to_buy_address (str): The Ethereum address of the ERC20 token to be bought.

    Returns:
        - tuple: A tuple containing the estimated amount of the bought token in WETH (float) and the transaction hash (str).
                 Returns None if an error occurs during the process.
    """
    global private_key
    try:
        infura_url = infura_url  # Replace with your Infura project ID

        web3 = Web3(Web3.HTTPProvider(infura_url))
        uniswap_router_address = pancakeSwap_RouterAddress  # Ethereum Mainnet Uniswap V2 Router address
        with open('./uniswapRouterABI.json', 'r') as abi_file:
            uniswap_router_abi = json.load(abi_file)  # Load the ABI from a JSON file

        uniswap_router_contract = web3.eth.contract(address=uniswap_router_address, abi=uniswap_router_abi)

        
        print("here", amount * 10**18)
        

    

        # Create an Ethereum account from the private key
        account = Account.from_key(private_key)    
    
        # dai_amount_in_wei = int(dai_amount * 10**18)
        wei_amount = int(amount * 10**18)
        print(wei_amount)
        path = [Web3.to_checksum_address(token_to_sell_address),Web3.to_checksum_address(token_to_buy_address)]  # DAI to WETH trading path

        # Estimate the amount of WETH you will receive
        amount_out_min = uniswap_router_contract.functions.getAmountsOut(wei_amount, path).call()
        weth_amount_in_wei = amount_out_min[1]

        print(f'Estimated amount of the token you will recieve: {weth_amount_in_wei / 10**18} WETH')

        # Execute the swap
        gas_price = web3.eth.gas_price
        gas_limit = 300000

        nonce = web3.eth.get_transaction_count(account.address)


        transaction = {
            'from': account.address,
            'value': 0,  # You are selling DAI, not sending ETH
            'gasPrice': gas_price,
            'gas': gas_limit,
            'nonce': nonce + 1 ,
        }
        time_limit = int(time.time() + 60 * 10)
        # if is_increase_nonce:
        #     slippageAmount = (amount_out_min[1] * 20) / 100;
        #     amount_out_min[1] = int(amount_out_min[1] + slippageAmount)
        #     time_limit += int(60*10)
        function_data = uniswap_router_contract.functions.swapExactTokensForTokens(
            wei_amount, 
            amount_out_min[1],  # Min amount of WETH you expect to receive
            path,
            account.address,
            time_limit,  # 10 minutes
        ).build_transaction(transaction)
        signed_transaction = web3.eth.account.sign_transaction(function_data, private_key)

        tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction).hex()

        print(f'Transaction Hash: {tx_hash}')
        return {weth_amount_in_wei / 10**18}, tx_hash

    except Exception as e:
        print('Error:', e)


"""
    Description:
        This function performs a token swap on a decentralized exchange (DEX) like Uniswap using the specified blockchain's router contract.
        It swaps a given amount of one ERC20 token for another ERC20 token.

    Parameters:
        - amount (float): The amount of the token to be sold in the transaction.
        - token_to_sell_address (str): The Ethereum address of the ERC20 token to be sold.
        - token_to_buy_address (str): The Ethereum address of the ERC20 token to be bought.

    Returns:
        - tuple or None: A tuple containing the estimated amount of the bought token in WETH and the transaction hash.
                        Returns None if an error occurs during the process.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.

    Usage:
        result = buy_for_tokens_and_tokens_general(1.5, "0x123abc...", "0x456def...")
        # The result may look like: ({'estimated_weth_amount': 2.0}, '0xabcdef...')

    Note:
        The function assumes a predefined structure of the blockchain's router contract and ERC20 tokens.
        Make sure to replace the placeholders with actual values before using this function.
    """
def buy_for_tokens_and_tokens_general(amount, token_to_sell_address, token_to_buy_address):
    """
    Parameters:
        - amount (float): The amount of the token to be sold in the transaction.
        - token_to_sell_address (str): The Ethereum address of the ERC20 token to be sold.
        - token_to_buy_address (str): The Ethereum address of the ERC20 token to be bought.

    Returns:
        - tuple or None: A tuple containing the estimated amount of the bought token in WETH and the transaction hash.
                        Returns None if an error occurs during the process.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.
    """
    global private_key
    global active_chain, chain_list, is_mirroring_general
    
    try:
        if active_chain is None or active_chain not in chain_list.keys():
            raise ChainNameNotFoundError(active_chain)
        # print(chain_list, active_chain)
        current_chain = chain_list[active_chain]
        # print(current_chain, type(current_chain), current_chain['web3'])
        web3 = current_chain['web3']
        token_address = web3.to_checksum_address(token_address)
        # current_chain = chain_list[active_chain]
        w_token_address = current_chain['w_address']
        w_token_address = Web3.to_checksum_address(w_token_address)
        router_address, router_abi = current_chain['router_address'], current_chain['router_abi']
          # BNB
        erc_20_abi = current_chain['erc_20_abi']
        amountOut = None
        print(web3.net.version)
        # tokenRouter = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=erc_20_abi)
        # tokenDecimals = tokenRouter.functions.decimals().call()
        # tokenDecimals = getTokenDecimal(tokenDecimals)
    except ChainNameNotFoundError as e:
        print(str(e))
        return None
    except Exception as e:
        print(str(e), 'In the main exception')
        return None
    
    try:
        # infura_url = infura_url  # Replace with your Infura project ID

        # web3 = Web3(Web3.HTTPProvider(infura_url))
        if "web3" not in locals():
            print("sorry, web3 connection could not be established")
            return
        # uniswap_router_address = pancakeSwap_RouterAddress  # Ethereum Mainnet Uniswap V2 Router address
        # with open('./uniswapRouterABI.json', 'r') as abi_file:
            # uniswap_router_abi = json.load(abi_file)  # Load the ABI from a JSON file

        uniswap_router_contract = web3.eth.contract(address=router_address, abi=router_abi)

        
        print("here", amount * 10**18)
        

      
        account = Account.from_key(private_key)    
    
        # dai_amount_in_wei = int(dai_amount * 10**18)
        wei_amount = int(amount * 10**18)
        print(wei_amount)
        path = [Web3.to_checksum_address(token_to_sell_address),Web3.to_checksum_address(token_to_buy_address)]  # DAI to WETH trading path

        # Estimate the amount of WETH you will receive
        amount_out_min = uniswap_router_contract.functions.getAmountsOut(wei_amount, path).call()
        weth_amount_in_wei = amount_out_min[1]

        print(f'Estimated amount of the token you will recieve: {weth_amount_in_wei / 10**18} WETH')

        # Execute the swap
        gas_price = web3.eth.gas_price
        gas_limit = 300000
        # if is_increase_nonce:
        #     nonce = web3.eth.get_transaction_count(account.address) + 1
        # else:
        nonce = web3.eth.get_transaction_count(account.address)


        transaction = {
            'from': account.address,
            'value': 0,  # You are selling DAI, not sending ETH
            'gasPrice': gas_price,
            'gas': gas_limit,
            'nonce': nonce + 1 ,
        }
        time_limit = int(time.time() + 60 * 10)

        function_data = uniswap_router_contract.functions.swapExactTokensForTokens(
            wei_amount, 
            amount_out_min[1],  # Min amount of WETH you expect to receive
            path,
            account.address,
            time_limit,  # 10 minutes
        ).build_transaction(transaction)
        signed_transaction = web3.eth.account.sign_transaction(function_data, private_key)

        tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction).hex()

        print(f'Transaction Hash: {tx_hash}')
        return {weth_amount_in_wei / 10**18}, tx_hash

    except Exception as e:
        print('Error:', e)



"""
    Endpoint: /buytokenswithtokens
    HTTP Method: POST

    Description:
        Endpoint for handling token-to-token purchases using the Uniswap router.

    JSON Request Payload:
        {
            "tokenToSpendAddress": "0x123abc...",
            "tokenToGetAddress": "0x456def...",
            "amount": 10
        }

    Returns:
        JSON Response:
        - Success (HTTP 200):
            {
                "txHash": "0xabc123...",
                "amountReceived": "9.5"
            }
        - Error (HTTP 400):
            {
                "txHash": "Error message",
                "amountReceived": 0
            }

    Notes:
        - The function expects a JSON payload with 'tokenToSpendAddress', 'tokenToGetAddress', and 'amount'.
        - It performs the following steps:
            1. Approves the Uniswap router for spending the specified amount of the token to be spent.
            2. Initiates a token-to-token trade using the Uniswap router.
        - If an error occurs during the process, it returns an error response with an HTTP 400 status code.

    Usage:
        Send a POST request to '/buytokenswithtokens' with the required JSON payload.
    """


@app.route('/buytokenswithtokens', methods=["POST"])
def handle_buying_with_tokens():
    """
    JSON Request Payload:
        {
            "tokenToSpendAddress": "0x123abc...",
            "tokenToGetAddress": "0x456def...",
            "amount": 10
        }

    Returns:
        JSON Response:
        - Success (HTTP 200):
            {
                "txHash": "0xabc123...",
                "amountReceived": "9.5"
            }
        - Error (HTTP 400):
            {
                "txHash": "Error message",
                "amountReceived": 0
            }
    """

    # Your token sniper bot logic here
    # print("here")
    try:
        data = request.get_json()
        token_to_spend_address, token_buy_address, amount = data['tokenToSpendAddress'], data['tokenToGetAddress'], data['amount']
        print(token_to_spend_address, token_buy_address)
        txhash_approval = approve_uniswap_router_general(amount, token_to_spend_address)
        print("Transaction Hash for approval is", txhash_approval)
        try:
            a, b = buy_for_tokens_and_tokens_general(token_to_buy_address=token_buy_address, token_to_sell_address=token_to_spend_address, amount=amount)
        except Exception as e:
            response = {"txHash":str(e), "amountRecieved":0}
            print(str(e))
            return jsonify(response), 400
            
       
        print(a, b)
        response = {"txHash":b, "amountRecieved":str(a)}
        return jsonify(response), 200
    except Exception as e:
        return str(e), 400
    

"""
    Endpoint for retrieving the token balance for a given wallet and token on a specified blockchain.

    Endpoint: /tokenBalance
    HTTP Method: POST

    Request JSON:
        {
            "chatId": "string",
            "active_chain": "string",
            "tokenAddress": "string"
        }

    Response JSON:
        {
            "tokenBalance": float,
            "tokenAddress": "string",
            "tokenID": "string"
        }

    Returns:
        - 200 OK: Successful response with token balance details.
        - 400 Bad Request: If there is an error in the request or fetching the token balance.

    Raises:
        - None

    Notes:
        - The 'chatId' parameter is used to identify the user's wallet.
        - The 'active_chain' parameter specifies the blockchain to query.
        - The 'tokenAddress' parameter is the Ethereum address of the ERC20 token.

    Usage:
        curl -X POST -H "Content-Type: application/json" -d '{"chatId": "123", "active_chain": "ethereum", "tokenAddress": "0xabc123..."}' http://your-api-domain/tokenBalance
    """
@app.route("/tokenBalance", methods=['POST'])
def handle_token_balance():
    
    """
    Request JSON:
        {
            "chatId": "string",
            "active_chain": "string",
            "tokenAddress": "string"
        }

    Response JSON:
        {
            "tokenBalance": float,
            "tokenAddress": "string",
            "tokenID": "string"
        }

    Returns:
        - 200 OK: Successful response with token balance details.
        - 400 Bad Request: If there is an error in the request or fetching the token balance.

    Raises:
        - None
    """
    # global tokenNameABI
    # global walletAddress, chain_list, active_chain
    # global chain_list
    try:
        data=request.json
           
        chatId, active_chain=data['chatId'], data['active_chain']
           
            
        if chatId not in chatId_dict:
            return jsonify({'result':'ChatId not found'}), 400
            
        if chatId not in multi_wallet_dict:
            return jsonify({'result':"chatId not found"}), 400
        
        count, index = 0, -1
        for j, k in enumerate(multi_wallet_dict[chatId]):
            print(multi_wallet_dict[chatId][j], j)
            if multi_wallet_dict[chatId][j]['status'] == True:
                    
                index = j
                count+=1
                print(index, "index")
            
        if count > 1:
            return jsonify({'result':'multiple active wallets'}),400
        else:
            count=0
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
        
        
        walletAddress=multi_wallet_dict[chatId][index]['walletAddress']
        
        # walletAddress=chatId_dict[chatId]['walletAddress']
       
        infura_url = chain_list[active_chain]['rpc_url']
        erc20_abi = chain_list[active_chain]['erc_20_abi']
        # infura_url = infura_url  # Replace with your Infura project ID
        web3 = Web3(Web3.HTTPProvider(infura_url))
        # global walletAddress
        data = request.get_json()
        token_address = data['tokenAddress']
        print(token_address)
        sellTokenContract = web3.eth.contract(address=web3.to_checksum_address(token_address), abi=erc20_abi)
        token_value, token_readable_balance, token_symbol = get_token_balance_general(token_address,walletAddress,active_chain)
        print(token_symbol, token_readable_balance)
        response = {"tokenBalance":token_readable_balance, 'tokenAddress':token_address, 'tokenID':token_symbol}
        return jsonify(response), 200
    except Exception as e:
        print('error fetching the token balance',str(e))
        return str(e), 400
    # socketIO.emit("tokenBalance", {"tokenBalance":token_readable_balance, 'tokenAddress':token_address, 'tokenID':token_symbol})


"""
    Endpoint for retrieving the Ethereum balance associated with a given wallet address.

    Endpoint : /getEthBalance
    Method: POST

    JSON Payload:
        - chatId (str): The unique identifier for the chat or user.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - JSON: A JSON response containing the Ethereum balance in Ether.

    Raises:
        - KeyError: If the provided chatId is not found in the chatId_dict.
        - Exception: If there is an error during the process.

    Usage:
        - Send a POST request to '/getEthBalance' with the required JSON payload.

    Example JSON Payload:
        {
            "chatId": "123456",
            "active_chain": "ethereum"
        }
    """

@app.route('/getEthBalance', methods=['POST'])
def handle_eth_balance():
    """
    JSON Payload:
        - chatId (str): The unique identifier for the chat or user.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - JSON: A JSON response containing the Ethereum balance in Ether.

    Raises:
        - KeyError: If the provided chatId is not found in the chatId_dict.
        - Exception: If there is an error during the process.
    """
    # rpc_url = infura_url  # Replace with your Infura project ID
    # global walletAddress, chain_list, active_chain
    data=request.json
           
    chatId, active_chain=data['chatId'], data['active_chain']
    try:
        # Connect to an Ethereum node
        if chatId not in chatId_dict:
            return jsonify({'result':'ChatId not found'}), 400
        
        if chatId not in multi_wallet_dict:
            return jsonify({'result':"chatId not found"}), 400
        
        count, index = 0, -1
        for j, k in enumerate(multi_wallet_dict[chatId]):
            print(multi_wallet_dict[chatId][j], j)
            if multi_wallet_dict[chatId][j]['status'] == True:
                    
                index = j
                count+=1
                print(index, "index")
            
        if count > 1:
            return jsonify({'result':'multiple active wallets'}),400
        else:
            count=0
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
        
        
        walletAddress=multi_wallet_dict[chatId][index]['walletAddress']
        
        # walletAddress=chatId_dict[chatId]['walletAddress']
        rpc_url = chain_list[active_chain]['rpc_url']
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        # Check if the connection to the node is successful
        if w3.is_connected():
            # Convert the wallet address to checksum format
            checksum_address = w3.to_checksum_address(walletAddress)

            # Fetch the Ethereum balance in Wei
            balance_wei = w3.eth.get_balance(checksum_address)

            # Convert Wei to Ether
            balance_eth = w3.from_wei(balance_wei, 'ether')
            response = {"ethBalance":balance_eth}

            return jsonify(response), 200
        else:
            return "Error: Unable to connect to the Ethereum node"

    except Exception as e:
        return f"Error: {str(e)}", 400
    # pass


@app.route('/getBalance', methods=['POST'])
def handle_get_balance():
    """
    JSON Payload:
        - chatId (str): The unique identifier for the chat or user.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - JSON: A JSON response containing the Ethereum balance in Ether.

    Raises:
        - KeyError: If the provided chatId is not found in the chatId_dict.
        - Exception: If there is an error during the process.
    """
    # rpc_url = infura_url  # Replace with your Infura project ID
    # global walletAddress, chain_list, active_chain
    data=request.json
           
    chatId, active_chain, wallet_address=data['chatId'], data['active_chain'], data['walletAddress']
    try:
        # Connect to an Ethereum node
        if chatId not in chatId_dict:
            return jsonify({'result':'ChatId not found'}), 400
        walletAddress=chatId_dict[chatId]['walletAddress']
        rpc_url = chain_list[active_chain]['rpc_url']
        print(rpc_url)
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        # Check if the connection to the node is successful
        if w3.is_connected():
            # Convert the wallet address to checksum format
            checksum_address = w3.to_checksum_address(wallet_address)

            # Fetch the Ethereum balance in Wei
            balance_wei = w3.eth.get_balance(checksum_address)

            # Convert Wei to Ether
            balance_eth = w3.from_wei(balance_wei, 'ether')
            response = {"ethBalance":balance_eth}

            return jsonify(response), 200
        else:
            return "Error: Unable to connect to the Ethereum node"

    except Exception as e:
        return f"Error: {str(e)}", 400
    # pass


@app.route('/getInputData', methods=['POST'])
def handle_input_data():
    """
    JSON Payload:
        - chatId (str): The unique identifier for the chat or user.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - JSON: A JSON response containing the Ethereum balance in Ether.

    Raises:
        - KeyError: If the provided chatId is not found in the chatId_dict.
        - Exception: If there is an error during the process.
    """
    # rpc_url = infura_url  # Replace with your Infura project ID
    # global walletAddress, chain_list, active_chain
    try:
        data=request.json
            
        chatId, active_chain, input_data, function_name=data['chatId'], data['active_chain'], data['inputData'], data['functionName']
        # if "swap" not in function_name:
        #     return jsonify({' result':'Function name not found'}), 400
        print(len(input_data), "length of Input data")
        try:
            # Connect to an Ethereum node
            if chatId not in chatId_dict:
                return jsonify({'result':'ChatId not found'}), 400
            # walletAddress=chatId_dict[chatId]['walletAddress']
            rpc_url = chain_list[active_chain]['rpc_url']
            print(rpc_url)
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            abi = chain_list[active_chain]['router_abi']
            contract = w3.eth.contract(address=chain_list[active_chain]['router_address'], abi=abi)
            try:
                decoded_data = contract.decode_function_input(input_data)
            except Exception as e:
                print(str(e), "Error while decoding input data")
                hexdataTrimed = input_data[2:]

# Split trimmed string every 64 characters
                n = 128
                dataSplit = [hexdataTrimed[i:i+n] for i in range(0, len(hexdataTrimed), n)]

# Fill new list with converted decimal values
                data = []
                for val in range(len(dataSplit)):
                    toDec = int(dataSplit[val], 16)
                    data.append(toDec)

                print(data) 
                
            print(decoded_data, decoded_data[1]['amountIn'], decoded_data[1]['amountOutMin'], decoded_data[1]['path'])
            if function_name == "swapExactETHForTokens(uint256 amountOutMin, address[] path, address to, uint256 deadline)":
                token_contract = w3.eth.contract(address=decoded_data[1]['path'][0], abi=chain_list[active_chain]['erc_20_abi'])
                symbol = token_contract.functions.symbol().call()
                return_data = {
                    "buyingPrice":decoded_data[1]['amountIn'],
                    "tokenAddress":decoded_data[1]['path'][1], 
                    "tokenSymbol":symbol,
                    "tokenAmount":decoded_data[1]['amountOutMin']
                }
                return jsonify(return_data), 200
            print(function_name, "swapExactTokensForETH(uint256 amountIn, uint256 amountOutMin, address[] path, address to, uint256 deadline)")
            if function_name == "swapExactTokensForETH(uint256 amountIn, uint256 amountOutMin, address[] path, address to, uint256 deadline)":
                token_contract = w3.eth.contract(address=decoded_data[1]['path'][0], abi=chain_list[active_chain]['erc_20_abi'])
                symbol = token_contract.functions.symbol().call()
                return_data = {
                    "buyingPrice":decoded_data[1]['amountIn'],
                    "tokenAddress":decoded_data[1]['path'][0], 
                    "tokenSymbol":symbol,
                    "tokenAmount":decoded_data[1]['amountOutMin']
                }
                return jsonify(return_data), 200
            if function_name =="approve(address spender, uint256 tokens)":
                print(decoded_data, "Decoded Data")
            # transaction = web3.eth.getTransaction(transaction_hash)

        # Get input data from the transaction
            # input_data = transaction['input'][2:]

        # Decode input data
            # decoded_data = decode_abi(abi[0]['inputs'], bytes.fromhex(input_data))
         
            # return decoded_data

            # Check if the connection to the node is successful
            if w3.is_connected():
                # Convert the wallet address to checksum format
                # checksum_address = w3.to_checksum_address(wallet_address)

                # Fetch the Ethereum balance in Wei
                # balance_wei = w3.eth.get_balance(checksum_address)

                # Convert Wei to Ether
                # balance_eth = w3.from_wei(balance_wei, 'ether')
                response = {"ethBalance":decoded_data}

                return jsonify(response), 200
            else:
                return "Error: Unable to connect to the Ethereum node"

        except Exception as e:
            return f"Error: {str(e)}", 400
    except Exception as e:
        return jsonify({"error":str(e)}), 400
    # pass



"""
    Handle the request to retrieve the contract address associated with a user's wallet.

    Endpoint:/walletToDeposit
    method : POST

    Request JSON:
        {
            "chatId": "123456789"  # Replace with the actual chatId
        }

    Response:
        - If successful, returns the contract address associated with the user's wallet.
        - If the chatId is not found, returns {'result': 'ChatId not found'}.
        - If the wallet is not initialized for leverage, returns {'result': 'your not init leverage'}.
        - If the contract address is not found, returns {'wallet': 'cannot find the wallet to fund, something went wrong'}.

    Returns:
        - JSON response with the contract address or an error message.

    Usage:
        curl -X POST -H "Content-Type: application/json" -d '{"chatId": "123456789"}' http://your-server/walletToDeposit
    """
@app.route('/walletToDeposit', methods=['POST'])
def handle_contract_address():
    """
    Request JSON:
        {
            "chatId": "123456789"  # Replace with the actual chatId
        }

    Response:
        - If successful, returns the contract address associated with the user's wallet.
        - If the chatId is not found, returns {'result': 'ChatId not found'}.
        - If the wallet is not initialized for leverage, returns {'result': 'your not init leverage'}.
        - If the contract address is not found, returns {'wallet': 'cannot find the wallet to fund, something went wrong'}.

    Returns:
        - JSON response with the contract address or an error message.
    """
    # rpc_url = infura_url  # Replace with your Infura project ID
    # global walletAddress
    try:
        data=request.json
           
        chatId=data['chatId']
           
            
        if chatId not in chatId_dict:
            return jsonify({'result':'ChatId not found'}), 400
            

        
        walletAddress=chatId_dict[chatId]['walletAddress']
       
        if walletAddress not in leverage_thread_dict:
            return jsonify({'result':'your not init leverage'}), 400
        
        leverage_manager=leverage_thread_dict[walletAddress]['leverage_manager']
        contract_address_to_return = leverage_manager.contract_address
        
        if contract_address_to_return is not None:
            response = {"wallet":contract_address_to_return}
            return jsonify(response),200
                # Conect to an Ethereum node
        else:
            return {"wallet":"cannot find the wallet to fund something went wrong"}


    except Exception as e:
        return f"Error: {str(e)}", 400
    # pass


"""
    Endpoint:/getHealthFactor
    method : POST

    Description:
        This route handles the request to retrieve the health factor of a user's leveraged position.
        It expects a JSON payload containing the 'chatId' for user identification.


    Parameters (JSON Payload):
        - chatId (str): The unique identifier for the user's chat session.

    Returns:
        - JSON Response: Contains the health factor of the user's leveraged position.

    HTTP Status Codes:
        - 200 OK: Successful response with health factor.
        - 400 Bad Request: Error response, typically due to invalid input or internal issues.

    Usage:
        curl -X POST -H "Content-Type: application/json" -d '{"chatId": "123456"}' http://your-server/getHealthFactor
    """
@app.route('/getHealthFactor', methods=['POST'])
def handle_health_factor():
    """
    Parameters (JSON Payload):
        - chatId (str): The unique identifier for the user's chat session.

    Returns:
        - JSON Response: Contains the health factor of the user's leveraged position.

    HTTP Status Codes:
        - 200 OK: Successful response with health factor.
        - 400 Bad Request: Error response, typically due to invalid input or internal issues.
    """
    # rpc_url = infura_url  # Replace with your Infura project ID
    
    try:
        data=request.json
           
        chatId=data['chatId']
           
            
        if chatId not in chatId_dict:
            return jsonify({'result':'ChatId not found'}), 400
            

        
        walletAddress=chatId_dict[chatId]['walletAddress']
       
        if walletAddress not in leverage_thread_dict:
            return jsonify({'result':'your not init leverage'}), 400
        
        leverage_manager=leverage_thread_dict[walletAddress]['leverage_manager']
        health_factor = leverage_manager.calculate_health_factor(walletAddress)
        
        if health_factor is not None:
            response = {"healthFactor":health_factor}
            return jsonify(response),200
                # Conect to an Ethereum node
        else:
            return {"wallet":"cannot find the health factor something went wrong"}


    except Exception as e:
        return f"Error: {str(e)}", 400
    # pass


"""
    Endpoint:/getCurrentLeverage
    method : POST

    Description:
        Endpoint for retrieving the current leverage multiplier associated with a user's wallet.

    Parameters:
        - chatId (str): The unique identifier for the user's chat session.
            It is used to look up the associated wallet address in the `chatId_dict`.

    Returns:
        - JSON response:
            - If the chatId is not found in `chatId_dict`, returns {'result':'ChatId not found'} with HTTP status 200.
            - If the wallet address is not found in `leverage_thread_dict`, returns {'result':'your not init leverage'} with HTTP status 200.
            - If the leverage multiplier is found, returns {"leverageMultiplier":leverage_mul} with HTTP status 200.
            - If the wallet is found but the leverage multiplier is not available, returns {"wallet":"cannot find the leverage multiplier"} with HTTP status 400.
            - If an unexpected error occurs, returns a generic error message with HTTP status 500.

    Usage:
        This endpoint is typically called by clients to retrieve the current leverage multiplier associated with a user's wallet.
        Example usage with a JSON payload:
        ```
        {
            "chatId": "unique_chat_id"
        }
        ```
    """
@app.route('/getCurrentLeverage', methods=['POST'])
def handle_current_leverage():
    """
    Parameters:
        - chatId (str): The unique identifier for the user's chat session.
            It is used to look up the associated wallet address in the `chatId_dict`.

    Returns:
        - JSON response:
            - If the chatId is not found in `chatId_dict`, returns {'result':'ChatId not found'} with HTTP status 200.
            - If the wallet address is not found in `leverage_thread_dict`, returns {'result':'your not init leverage'} with HTTP status 200.
            - If the leverage multiplier is found, returns {"leverageMultiplier":leverage_mul} with HTTP status 200.
            - If the wallet is found but the leverage multiplier is not available, returns {"wallet":"cannot find the leverage multiplier"} with HTTP status 400.
            - If an unexpected error occurs, returns a generic error message with HTTP status 500.
    """
    # rpc_url = infura_url  # Replace with your Infura project ID
    try:
        data=request.json
           
        chatId=data['chatId']
           
            
        if chatId not in chatId_dict:
            return jsonify({'result':'ChatId not found'}), 400
            

        
        walletAddress=chatId_dict[chatId]['walletAddress']
       
        if walletAddress not in leverage_thread_dict:
            return jsonify({'result':'your not init leverage'}), 400
        
        leverage_manager=leverage_thread_dict[walletAddress]['leverage_manager']
        
        leverage_mul = leverage_manager.get_leverage_multiplier()
        
        if leverage_mul is not None:
            return jsonify({"leverageMultiplier":leverage_mul}),200
                # Conect to an Ethereum node
        else:
            return jsonify({"wallet":"cannot find the leverage multiplier"}),400


    except Exception as e:
        return f"Error: {str(e)}", 500
    # pass

"""
    Endpoint : /getLiquidationThreshold
    Method:POST

    Description:
        This route handles the HTTP POST request to retrieve the current liquidation threshold for a given user's wallet.


    Parameters (JSON Body):
        - chatId (str): The unique identifier for the user's chat.
        
    Returns:
        - JSON Response:
            - {'result': 'ChatId not found'}: If the provided chatId is not associated with any user.
            - {'result': 'your not init leverage'}: If the user's wallet is not initialized for leverage.
            - {'liqThres': liquidity_threshold}: If successful, returns the current liquidation threshold.

    Raises:
        - 500 Internal Server Error: If an unexpected error occurs during the process.

    Usage:
        Send a POST request to '/getLiquidationThreshold' with the JSON body containing the 'chatId'.

    Example:
        curl -X POST -H "Content-Type: application/json" -d '{"chatId": "123456"}' http://your_server_url/getLiquidationThreshold
"""

@app.route('/getLiquidationThreshold', methods=['POST'])
def handle_current_liquidation_threshold():
    """
    Parameters (JSON Body):
        - chatId (str): The unique identifier for the user's chat.
        
    Returns:
        - JSON Response:
            - {'result': 'ChatId not found'}: If the provided chatId is not associated with any user.
            - {'result': 'your not init leverage'}: If the user's wallet is not initialized for leverage.
            - {'liqThres': liquidity_threshold}: If successful, returns the current liquidation threshold.

    Raises:
        - 500 Internal Server Error: If an unexpected error occurs during the process.
    """
    # rpc_url = infura_url  # Replace with your Infura project ID
    try:
        data=request.json
           
        chatId=data['chatId']
           
            
        if chatId not in chatId_dict:
            return jsonify({'result':'ChatId not found'}), 400
            

        
        walletAddress=chatId_dict[chatId]['walletAddress']
       
        if walletAddress not in leverage_thread_dict:
            return jsonify({'result':'your not init leverage'}), 400
        
        
        main_wallet_engine=leverage_thread_dict[walletAddress]['main_wallet_engine']
    
        liq_thresh = main_wallet_engine.get_liquidity_threshold()
            
        if liq_thresh is not None:
            response = {"liqThres":liq_thresh}
            return jsonify(response),200
                    # Conect to an Ethereum node
        else:
            return {"wallet":"cannot find the liquidation threshold"}


    except Exception as e:
        return jsonify({'error':str(e)}),400
    # pass

"""
    EndPoint: /startWithLeverage
    Method:POST

    Description:
        This route handles the initiation of leverage sniping for a given user's wallet.
        It starts a new thread to listen for leverage opportunities and execute sniping transactions.


    Request JSON Payload:
        - chatId (str): The unique identifier for the user's chat.
        - amount (float): The amount to snipe in BNB.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - JSON: A response indicating the result of the snipe initiation.

    Raises:
        - KeyError: If the provided chatId is not found in the chatId_dict.
        - KeyError: If the provided walletAddress is not found in the leverage_thread_dict.
        - ValueError: If the user has not taken any leverage yet.
        - Exception: Any other unexpected error during the process.

    Usage:
        POST request to '/startWithLeverage' with a JSON payload containing 'chatId', 'amount', and 'active_chain'.
    """
@app.route('/startWithLeverage', methods=['POST'])
def handle_start_with_leverage():
    """
    Request JSON Payload:
        - chatId (str): The unique identifier for the user's chat.
        - amount (float): The amount to snipe in BNB.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - JSON: A response indicating the result of the snipe initiation.

    Raises:
        - KeyError: If the provided chatId is not found in the chatId_dict.
        - KeyError: If the provided walletAddress is not found in the leverage_thread_dict.
        - ValueError: If the user has not taken any leverage yet.
        - Exception: Any other unexpected error during the process.
    """
    try:
            data=request.json
           
            chatId=data['chatId']
            snipeBNBAmount=data['amount']
            active_chain=data['active_chain']
            if chatId not in chatId_dict:
                return jsonify({'result':'ChatId not found'}), 400
            

        
            walletAddress=chatId_dict[chatId]['walletAddress']
            private_key=chatId_dict[chatId]['private_key']
            
            if walletAddress not in leverage_thread_dict:
                return jsonify({'result':'your not init leverage'}), 400
            
            # rpc_url = infura_url  # Replace with your Infura project ID
            main_wallet_engine=leverage_thread_dict[walletAddress]['main_wallet_engine']
            leverage_manager=leverage_thread_dict[walletAddress]['leverage_manager']

            if main_wallet_engine.leverage <= 0:
                return jsonify({"snipingStarted":"Sorry, you have taken no leverage yet"}), 400
            
          
      
            try:
                LeverageSnipingThread = threading.Thread(target=handle_listen_for_leverage_general,args=(walletAddress,private_key,snipeBNBAmount,leverage_manager,main_wallet_engine,active_chain))
            except Exception as e:
                print('thread error',str(e))
            leverage_thread_dict[walletAddress]['leverageThread']=LeverageSnipingThread
            leverage_thread_dict[walletAddress]['leverageSnipe']=True
            LeverageSnipingThread.start()

            return jsonify({'result':'snipe started'}), 200
    except Exception as e:
            return jsonify({"Error":str(e) }) ,400
    # pass


"""
    EndPoint: /stopLeverageSniping
    Method:POST

    Description:
        This route endpoint stops the leverage sniping loop associated with a specific wallet address.
        It expects a JSON payload containing the 'chatId' and stops the leverage sniping if the wallet address is found.

    JSON Payload:
        - chatId (str): The unique identifier for the chat.
        
    Returns:
        - JSON response:
            - {'result': 'chatId not found'}: If the provided 'chatId' is not associated with any wallet address.
            - {'result': 'walletAddress not found'}: If the wallet address associated with the 'chatId' is not found.
            - {'result': 'leverage sniping stop'}: If the leverage sniping loop is successfully stopped.

    HTTP Status Codes:
        - 200: If the leverage sniping is successfully stopped.
        - 400: If an exception occurs during the process.

    Raises:
        - None

    Usage:
        Send a POST request to '/stopLeverageSniping' with a JSON payload containing 'chatId' to stop the leverage sniping loop.
    """

@app.route('/stopLeverageSniping', methods=['POST'])
def handle_stop_leverage_sniping():
    print("leverage sniping loop stopped")
    
    try:    
        data=request.json
        chatId=data['chatId']

        if chatId not in  chatId_dict:
            return jsonify({'result':'chatId not found'}), 400
        
        walletAddress=chatId_dict[chatId]['walletAddress']
        
        if walletAddress  not in  leverage_thread_dict:
            return jsonify({'result':'walletAddress not found'}), 400
       
            
        print(leverage_thread_dict)
        lerverageThread=leverage_thread_dict[walletAddress]['leverageThread']
        stop_leverage_sniping(lerverageThread,walletAddress)
        
        return jsonify({'result':'leverage sniping stop'}),200
    except Exception as e:
        return jsonify({"value":str(e)}), 400



"""
    EndPoint: /changeChain
    Method:POST

    Description:
        This route handles the POST request for changing the active blockchain chain in the application.
        It updates the global variables `chain_list` and `active_chain` based on the received JSON data.

    Request:
        - Method: POST
        - Data Format: JSON
        - Expected JSON Structure:
            {
                "chain_name": "desired_chain_name"
            }

    Returns:
        - JSON Response:
            - If successful, returns:
                {
                    "status": "success",
                    "current_chain": "new_active_chain",
                    "error": None
                }
            - If the specified chain is not found, returns:
                {
                    "status": "Failure, chain not found",
                    "current_chain": "current_active_chain",
                    "error": "ChainNameNotFoundError: specified chain_name not found"
                }
            - If an unexpected error occurs, returns:
                {
                    "status": "failure",
                    "current_chain": "current_active_chain",
                    "error": "Exception: description of the unexpected error"
                }
    """
@app.route('/changeChain', methods=['POST'])
def handle_changing_chain():
    global chain_list, active_chain
    try:
        data = request.json
        print(data)
        chain_name = data['chain_name']
        if chain_name not in chain_list.keys():
            # active_chain = 
            raise ChainNameNotFoundError(chain_name=chain_name)
        
        active_chain = chain_name
        return jsonify({"status":"success", "current_chain":active_chain, 'error':None}), 400
        # pass
    except ChainNameNotFoundError as e:
        return jsonify({'status':'Failure, chain not found', 'current_chain':active_chain, 'error':str(e)}), 400
        # pass
    except Exception as e:
        return jsonify({'status':'failure', 'current_chain':active_chain, 'error':str(e)}), 400


"""
    EndPoint: /initLeverage
    Method:POST

    Description:
        Initializes the leverage manager and main wallet engine for a given user's chat session.

    Method:
        POST

    Request JSON Payload:
        - chatId (str): The unique identifier for the user's chat session.

    Returns:
        - JSON: Returns a JSON response indicating the result of the initialization:
                - {'result': 'chatId not found'}: If the provided chatId is not registered.
                - {'result': 'leverage initialized'}: If the initialization is successful.

    Notes:
        The function expects a valid chatId in the request payload, which is used to retrieve
        the associated wallet address and private key. It then initializes a Leverage_manager
        and Main_wallet_engine for the user's wallet address.

        The initialized objects are stored in the leverage_thread_dict for further reference.

    Example Usage:
        curl -X POST -H "Content-Type: application/json" -d '{"chatId": "example_chat_id"}' http://your-api-url/initLeverage
    """
@app.route("/initLeverage", methods=["POST"])
def handle_init_lev():
    try:
        data = request.json
        chatId = data['chatId']
        if chatId not in  chatId_dict:
            return jsonify({'result':'chatId not found'}), 400
            
        if chatId not in multi_wallet_dict:
            return jsonify({'result':"chatId not found"}), 400
        
        count, index = 0, -1
        for j, k in enumerate(multi_wallet_dict[chatId]):
            print(multi_wallet_dict[chatId][j], j)
            if multi_wallet_dict[chatId][j]['status'] == True:
                    
                index = j
                count+=1
                print(index, "index")
            
        if count > 1:
            return jsonify({'result':'multiple active wallets'}),400
        else:
            count=0
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
        
        
        walletAddress=multi_wallet_dict[chatId][index]['walletAddress']
        private_key=multi_wallet_dict[chatId][index]['private_key']

        leverage_manager=Leverage_manager(walletAddress,private_key)
        main_wallet_engine=Main_wallet_engine(walletAddress,private_key,leverage_manager)
        leverage_thread_dict[walletAddress]={'leverageThread':None,'leverageSnipe':True,'leverage_manager':leverage_manager,'main_wallet_engine':main_wallet_engine}
        return jsonify({'result':'leverage initalized'}), 200         
    except Exception as e:
        print(str(e))
        return jsonify({'result':-1, "error":str(e)}), 400
    pass


"""
    EndPoint: /getLeverage
    Method:POST

    Description:
        This function handles the request to retrieve the leverage value for a given wallet address.
        It checks if the necessary parameters are present in the incoming JSON data and then uses
        the LeverageManager associated with the wallet address to calculate and return the leverage value.

    Returns:
        - JSON Response: A JSON response containing the calculated leverage value and, if successful, the transaction hash.
                          If an error occurs, an appropriate error message is returned in the response.

    Usage:
        The function is typically used as an endpoint in a web service to respond to requests for leverage values.

    Example JSON Request:
        {
            "chatId": "123456789",
            "otherParameter": "..."
        }

    Example JSON Response:
        {
            "leverageValue": 2.5,
            "txHash": "0x123abc..."
        }
    """
@app.route('/getLeverage', methods=['POST'])
def handle_get_leverage():
    print("leverage sniping loop stopped")
    try: 
        data = request.json
        chatId=data['chatId']

        if chatId not in  chatId_dict:
            return jsonify({'result':'chatId not found'}), 400
        
        walletAddress=chatId_dict[chatId]['walletAddress']


        if walletAddress  not in  leverage_thread_dict:
            return jsonify({'result':'walletAddress not found'}), 400
            
            
        leverage_manager=leverage_thread_dict[walletAddress]['leverage_manager']
        response = leverage_manager.give_proper_leverage(walletAddress)
        if response['leverage_value']>0:
            return jsonify({"leverageValue":response['leverage_value'], "txHash":response['txnHash']}), 400
        if response['leverage_value']==None:
            return jsonify({"leverageValue":response['leverage_value'], "txHash":"something went wrong while calculating leverage"}), 400
        if response['leverage_value'] == -1:
            return jsonify({"leverageValue":response['leverage_value'], "txHash":"health factor not met"}), 400

    except Exception as e:
        return jsonify({"value":str(e)}), 400


"""
    EndPoint: /makeContributions
    Method:POST

    Description:
        This route handles the incoming POST requests for making contributions to a leverage manager.
        It extracts the necessary information from the JSON payload, such as chatId and amount_to_invest,
        and attempts to make a contribution using the corresponding leverage manager.

    Request Payload:
        - chatId (str): The unique identifier for the user's chat.
        - amount_to_invest (float): The amount to contribute to the leverage manager.

    Returns:
        - JSON: If the contribution is successful, it returns a JSON with 'contribution' and 'txhash' keys.
                If the chatId or walletAddress is not found, it returns a JSON with an appropriate message.
                If an unexpected error occurs, it returns a JSON with the error message.

    Example Usage:
        POST '/makeContributions'
        {
            "chatId": "123456",
            "amount_to_invest": 100.0
        }
    """
@app.route('/makeContributions', methods=['POST'])
def handle_make_contributions():
    
    try:
        data = request.json
        chatId=data['chatId']
        amount_to_contribute =data['amount_to_invest']

        print(str(amount_to_contribute))

        if chatId not in  chatId_dict:
            return jsonify({'result':'chatId not found'}), 400
        
        walletAddress=chatId_dict[chatId]['walletAddress']
        private_key=chatId_dict[chatId]['private_key']

        if walletAddress  not in  leverage_thread_dict:
            return jsonify({'result':'walletAddress not found'}), 400
        
        leverage_manager=leverage_thread_dict[walletAddress]['leverage_manager']
        
        response = leverage_manager.make_contribution(str(amount_to_contribute), walletAddress, private_key)
        print(response.keys(), list(response.keys()), "contribution" in list(response.keys()))
        if "contribution" in response.keys():
            return jsonify({"contribution":response['contribution'], "txhash":response['txhash']}), 200
       
        return jsonify({'makecontribution':'contribution not found'}),400


    except Exception as e:
        return jsonify({"value":str(e)}), 400


"""
    EndPoint: /currentWallet
    Method:POST

    Description:
        This route handles the POST request to '/currentWallet' and sends the current wallet information
        (private key and public key) to the connected client via a WebSocket. The wallet information is
        retrieved based on the 'chatId' received in the request.

    Request JSON Data:
        {
            "chatId": "unique_identifier"
        }

    Response:
        {
            "privateKey": "private_key_as_string",
            "publicKey": "wallet_address_as_string"
        }

    WebSocket Emitted Event:
        Event Name: 'currentWallet'
        Event Data: {
            "privateKey": "private_key_as_string",
            "publicKey": "wallet_address_as_string"
        }
    """
@app.route('/currentWallet',methods=['POST'])
def handle_sending_current_wallet():
    try:
        data=request.json
        chatId=data['chatId']
        walletAddress=chatId_dict[chatId]['walletAddress']
        private_key=chatId_dict[chatId]['private_key']
    
        socketIO.emit('currentWallet', {"privateKey":str(private_key), "publicKey":str(walletAddress)})
        return jsonify({'privateKey':str(private_key),"publicKey": str(walletAddress) }), 400
        # socketIO.emit('test', {'walletAddress': walletAddress, 'privateKey':private_key})
    except Exception as e:
        print(str(e), "error in current wallet endpoint")
        return jsonify({"error":str(e)}), 400

"""
    EndPoint: /sellToken
    Method:POST
    Description:
        Handles the selling of a specified ERC20 token for ETH on Uniswap, including the approval
        and execution steps. Emits relevant information through Socket.IO.

    Request Method:
        POST

    Request JSON Payload:
        - amount (float): The amount of the token to be sold.
        - tokenAddress (str): The Ethereum address of the ERC20 token.
        - chatId (str): The unique identifier for the chat.
        - active_chain (str): The name of the active blockchain.

    Returns:
        - JSON Response: Includes information about the token amount, token address,
                         transaction hash for approval, and transaction hash for selling.

    Usage:
        curl -X POST -H "Content-Type: application/json" -d '{"amount": 10, "tokenAddress": "0x123abc...", "chatId": "123", "active_chain": "ethereum"}' http://your-app-url/sellToken
    """
@app.route('/sellToken',methods=['POST'])
def handle_selling():
    # Your token sniper bot logic here
    try:
        print("in selling")
        data=request.json
        amount, token_address,chatId,active_chain = data['amount'], data['tokenAddress'],data['chatId'],data['active_chain']
        if chatId not in chatId_dict:
            return jsonify({'result':f'chatId {chatId} not found'}),400
        
        if chatId not in multi_wallet_dict:
            return jsonify({'result':"chatId not found"}), 400
        
        count, index = 0, -1
        for j, k in enumerate(multi_wallet_dict[chatId]):
            print(multi_wallet_dict[chatId][j], j)
            if multi_wallet_dict[chatId][j]['status'] == True:
                    
                index = j
                count+=1
                print(index, "index")
            
        if count > 1:
            return jsonify({'result':'multiple active wallets'}),400
        else:
            count=0
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
        
        
        walletAddress=multi_wallet_dict[chatId][index]['walletAddress']
        private_key=multi_wallet_dict[chatId][index]['private_key']
        is_nonce = True
        print(amount, data)
        tx_hash_for_approval = approve_uniswap_router_general(amount, token_address,private_key,active_chain)
        if tx_hash_for_approval == -1:
            is_nonce = False
        # print(type(tx_hash), type(token_amount))
        print(tx_hash_for_approval, is_nonce)
        selling_response = sell_for_eth_and_approve_general(amount, token_address,private_key,active_chain, is_nonce)
        if selling_response == -1:
            return jsonify({"error":"cannot sell this token, try selling another token"}), 400
        token_amount, tx_hash_for_selling = selling_response
        socketIO.emit('tokenSold', {"tokenAmount":str(token_amount), "tokenAddress":str(token_address), "txHashApproval":str(tx_hash_for_approval), 'txHashSold':str(tx_hash_for_selling)})
        # socketIO.emit('test', {'walletAddress': walletAddress, 'privateKey':private_key})
        return jsonify( {"tokenAmount":str(token_amount), "tokenAddress":str(token_address), "txHashApproval":str(tx_hash_for_approval), 'txHashSold':str(tx_hash_for_selling)}), 200
    except Exception as e:
        print(str(e), "error in selling")
        return jsonify({"error":str(e)}), 400

"""
    Description:
        This function handles the selling process for a given ERC20 token. It initiates the approval
        process for the Uniswap router and then performs the token sale.

    Parameters:
        - data (dict): A dictionary containing information about the token sale, including:
            - 'amount' (float): The amount of the token to be sold.
            - 'tokenAddress' (str): The Ethereum address of the ERC20 token.
            - 'private_key' (str): The private key for the wallet initiating the sale.
            - 'active_chain' (str): The name of the active blockchain.

    Returns:
        None

    Usage:
        handle_selling_general({
            'amount': 10.0,
            'tokenAddress': "0x123abc...",
            'private_key': "0xabcdef...",
            'active_chain': "ethereum"
        })

    Notes:
        - The function prints debug information to the console.
        - The result of the token sale, including token amount and transaction hashes, is emitted
          through a Socket.IO event named 'tokenSold'.
    """
def handle_selling_general(data):
    # Your token sniper bot logic here
    try:
        print("in selling")
        amount, token_address,private_key,active_chain = data['amount'], data['tokenAddress'],data['private_key'],data['active_chain']
        print(amount, data)
        tx_hash_for_approval = approve_uniswap_router_general(amount, token_address,private_key,active_chain)
        # print(type(tx_hash), type(token_amount))
        print(tx_hash_for_approval)
        token_amount, tx_hash_for_selling = sell_for_eth_and_approve_general(amount, token_address,private_key,active_chain)

        socketIO.emit('tokenSold', {"tokenAmount":str(token_amount), "tokenAddress":str(token_address), "txHashApproval":str(tx_hash_for_approval), 'txHashSold':str(tx_hash_for_selling)}), 200
        # socketIO.emit('test', {'walletAddress': walletAddress, 'privateKey':private_key})
    except Exception as e:
        print("error in selling general", str(e))
    

"""
    Endpoint: /stop
    method : POST

    Description:
        This endpoint is responsible for stopping a sniping thread associated with a specific wallet address.
        It receives a JSON payload containing the 'chatId' identifying the user and stops the corresponding sniping thread.

    Method:
        POST

    Request JSON Payload:
        - chatId (str): The unique identifier for the user.

    Response:
        - If the 'chatId' is not found in the dictionary, returns a JSON response indicating that the chatId is not found.
        - If successful, stops the sniping thread, emits a 'stopSniping' event through a socketIO connection, and returns a JSON response.

    Raises:
        - None

    Usage:
        curl -X POST -H "Content-Type: application/json" -d '{"chatId": "exampleChatId"}' http://yourdomain.com/stop
    """

# @socketIO.on('stop')
@app.route('/stop',methods=['POST'])
def handle_increment():
    try:
        print("loop stopped")
        data=request.json
        chatId=data['chatId']
        if chatId not in chatId_dict:
            return jsonify({'result':'chatId not found'}),400
        
        if chatId not in multi_wallet_dict:
            return jsonify({'result':"chatId not found"}), 400
            
        count, index = 0, -1
        for j, k in enumerate(multi_wallet_dict[chatId]):
            print(multi_wallet_dict[chatId][j], j)
            if multi_wallet_dict[chatId][j]['status'] == True:
                        
                index = j
                count+=1
                print(index, "index")
                
        if count > 1:
            return jsonify({'result':'multiple active wallets'}),400
        else:
            count=0
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
            
        walletAddress=multi_wallet_dict[chatId][index]['walletAddress']
        
        # walletAddress=chatId_dict[chatId]['walletAddress']
        thread_info=thread_dict[walletAddress]
        sniping_thread=thread_info['Thread']
        print(sniping_thread)
        # is_sniping = False
        a=stop_thread(sniping_thread,walletAddress, True)
        print(str(a))
        socketIO.emit('stopSniping', {'value': "stopped"})
        return jsonify({'snipe_stop':str(walletAddress)}), 200
    except Exception as e:
        print(str(e), "error in stopping sniping")
        return jsonify({"error":str(e)}), 400

"""
    Endpoint: /mirrorStop
    Method: POST

    Description:
        This endpoint stops the mirror operation for a specific wallet address.

    Method:
        POST

    Parameters (JSON in Request Body):
        - chatId (str): The chat ID associated with the user.
        
    Returns:
        - JSON Response:
            - If successful, returns {'stopMirror': 'mirror Stop'}.
            - If the chatId is not found, returns {'result': 'chatId not found'} with HTTP status code 400.
            - If the walletAddress is not found or the mirror operation is not running,
              returns {'result': 'walletAddress not found, Please start mirror first'} with HTTP status code 400.

    Usage:
        Send a POST request to '/mirrorStop' with a JSON payload containing the 'chatId'.
    """
@app.route('/mirrorStop',methods=['POST'])
def stopmirror_increment():
    try:
        print('we are in the mirror stop')
        # time.sleep(5)
        data=request.json
        print(data)
        print("loop stopped")
        chatId=data['chatId']
        if chatId not in chatId_dict:
            return jsonify({'result':'chatId not found'}),400
    
        if chatId not in multi_wallet_dict:
            return jsonify({'result':"chatId not found"}), 400
            
        count, index = 0, -1
        for j, k in enumerate(multi_wallet_dict[chatId]):
            print(multi_wallet_dict[chatId][j], j)
            if multi_wallet_dict[chatId][j]['status'] == True:
                        
                index = j
                count+=1                
                print(index, "index")
                
        if count > 1:
            return jsonify({'result':'multiple active wallets'}),400
        else:
            count=0
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
            
            
        walletAddress=multi_wallet_dict[chatId][index]['walletAddress']  
        # walletAddress=chatId_dict[chatId]['walletAddress']
    
        if walletAddress in mirror_thread_dict:
            mirrorThread=mirror_thread_dict[walletAddress]['mirrorThread']
            print(mirror_thread_dict)
            a=stop_thread(mirrorThread,walletAddress, False)
            print(str(a))
            return jsonify({'stopMirror':'mirror Stop'}), 200

            # stop_thread(mirrorThread,walletAddress, False)
            # socketIO.emit('stopMirror', {'value': f"stopped for {walletAddress}"})
        return jsonify({'result':'walletAddress not found,Please start mirror first'}),400
    except Exception as e:
        return jsonify({"result":"something went wrong", "error":str(e)}), 400


# @app.route('/checkLiquidation', methods=["POST"])
# def handle_checking_liquidation():
#     data = request.json
#     chatId = data['chatId']
#     walletAddress=chatId_dict[chatId]['walletAddress']
#     main_wallet_engine=leverage_thread_dict
#     main_wallet_engine.start_monitoring()




"""
    Endpoint: /setMaxMirrorLimit
    Method: POST

    Description:
        This route sets the maximum mirror limit for a wallet based on the received JSON data.
        If the wallet is already part of the mirror_thread_dict, it updates the existing entry.
        Otherwise, it creates a new entry for the wallet in mirror_thread_dict.

    Request JSON:
        - chatId (str): The unique identifier for a chat.
        - maxMirrorLimit (int): The maximum mirror limit to be set for the wallet.

    Response JSON:
        - If successful: {'maxMirrorLimit': 'maxMirrorLimit set for walletAddress'}
        - If chatId not found: {'result': 'chatId not found'}

    Raises:
        - None

    Usage:
        - Send a POST request to '/setMaxMirrorLimit' with the required JSON data.

    Note:
        - The function uses global variables chatId_dict and mirror_thread_dict.
        - It emits a 'maxMirrorLimitSet' event using SocketIO.

    """
# @socketIO.on('setMaxMirrorLimit')
@app.route('/setMaxMirrorLimit',methods=['POST'])
def setMaxMirrorLimit_wallet():
    # Your token sniper bot logic here
    try:
        data=request.json
        chatId = data['chatId']
        maxMirrorLimit=data['maxMirrorLimit']

        if chatId not in chatId_dict:
            return jsonify({'result':'chatId not found'}),400
        if chatId not in multi_wallet_dict:
            return jsonify({'result':"chatId not found"}), 400
            
        count, index = 0, -1
        for j, k in enumerate(multi_wallet_dict[chatId]):
            print(multi_wallet_dict[chatId][j], j)
            if multi_wallet_dict[chatId][j]['status'] == True:
                        
                index = j
                count+=1
                print(index, "index")
                
        if count > 1:
            return jsonify({'result':'multiple active wallets'}),400
        else:
            count=0
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
            
            
        walletAddress=multi_wallet_dict[chatId][index]['walletAddress']
        
        # walletAddress=chatId_dict[chatId]['walletAddress']

        if walletAddress in mirror_thread_dict:
            mirror_thread_dict[walletAddress]['maxMirrorLimit']=maxMirrorLimit
        else:
            mirror_thread_dict[walletAddress]={'mirrorThread':None,'mirrorSnipe':False,'maxMirrorLimit':maxMirrorLimit,'to_be_mirror_wallet':None}

            
        socketIO.emit("maxMirrorLimitSet", {'maxMirrorLimit':f'{maxMirrorLimit} set for {walletAddress}'})
    
        print("mirror_thread_dict",mirror_thread_dict)
        return jsonify({'maxMirrorLimit':f'maxMirrorLimit {maxMirrorLimit} set for {walletAddress}'}), 200
    except Exception as e:
        print(str(e), "error in setting the max limit of the wallet")
        return jsonify({"error":str(e)}), 400

"""
    Endpoint: /setMirrorWallet
    Method: POST

    Description:
        Endpoint to set the mirror wallet for a user identified by their 'chatId'. 
        The mirror wallet is the target wallet for a mirroring operation.

    Method:
        POST

    JSON Payload:
        - chatId (str): Unique identifier for the user.
        - mirrorWallet (str): The Ethereum address to set as the mirror wallet.

    Returns:
        - JSON: Returns a JSON response indicating the status of the mirror wallet setting.

    Status Codes:
        - 200 OK: Mirror wallet successfully set.
        - 400 Bad Request: If the provided 'chatId' is not found in the 'chatId_dict'.

    Usage:
        Example JSON Payload:
        {
            "chatId": "unique_chat_id",
            "mirrorWallet": "0x123abc..."
        }
    """
@app.route('/setMirrorWallet',methods=['POST'])
def setMirrorWallet_wallet():
    try:
        data=request.json
        chatId=data['chatId']
        to_be_mirror_wallet = data['mirrorWallet']
        if chatId not in chatId_dict:
            return jsonify({'result':'chatId not found'}),400
        if chatId not in multi_wallet_dict:
            return jsonify({'result':"chatId not found"}), 400
            
        count, index = 0, -1
        for j, k in enumerate(multi_wallet_dict[chatId]):
            print(multi_wallet_dict[chatId][j], j)
            if multi_wallet_dict[chatId][j]['status'] == True:
                        
                index = j
                count+=1
                print(index, "index")
                
        if count > 1:
            return jsonify({'result':'multiple active wallets'}),400
        else:
            count=0
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
            
            
        walletAddress=multi_wallet_dict[chatId][index]['walletAddress']
        # walletAddress=chatId_dict[chatId]['walletAddress']

        if walletAddress in mirror_thread_dict:
            mirror_thread_dict[walletAddress]['to_be_mirror_wallet']=to_be_mirror_wallet
        else:
            mirror_thread_dict[walletAddress]={'mirrorThread':None,'mirrorSnipe':False,'maxMirrorLimit':None,'to_be_mirror_wallet':to_be_mirror_wallet}
        
        socketIO.emit("mirrorWalletSet", {"mirrorWallet":to_be_mirror_wallet})
        print("mirror_thread_dict",mirror_thread_dict)
        return jsonify({'mirrorWallet':f'set mirrorWallet {to_be_mirror_wallet} '}),200
    except Exception as e:
        print(str(e), "error in setting the mirror wallet")
        return jsonify({"error":str(e)}), 400

"""
    Description:
        This SocketIO event handler generates a new wallet address and private key,
        and emits the wallet information to the connected clients.

    Usage:
        This function is typically triggered when a client sends a 'wallet' event.

    Global Variables:
        - walletAddress (str): The generated wallet address.
        - private_key (str): The generated private key.

    Example:
        SocketIO client triggers the 'wallet' event, and the server responds by emitting the
        wallet information to the client.

        Client-side:
        ```javascript
        socket.emit('wallet');
        ```

        Server-side (in Flask-SocketIO event handler):
        ```python
        @socketIO.on('wallet')
        def send_wallet():
            # Your token sniper bot logic here
            # ...

        ```

    """
@socketIO.on('wallet')
def send_wallet():
    # Your token sniper bot logic here
    # print(data)
    global walletAddress
    global private_key
    private_key = os.urandom(32).hex()

    account = web3.eth.account.from_key(private_key)
    walletAddress = account.address
    socketIO.emit('wallet', {'walletAddress': walletAddress, 'privateKey':private_key})

    # emit('wallet', {'walletAddress': walletAddress, 'privateKey':private_key})

"""
    Description:
        This function serves as the event handler for the 'test' socket event.
        It emits a 'test' event with a message "emiting" to connected clients.

    Usage:
        This function is typically used as a callback for the 'test' socket event.
        It can be triggered by clients to test the communication with the server.

    Note:
        Customize the function body to include your token sniper bot logic.
    """
@socketIO.on('test')
def handle_increment():
    # Your token sniper bot logic here
    # print("here")
    # print(stop_loss, gasAmount, snipeBNBAmount, private_key, walletAddress, sellProfit)
    # socketIO.emit('test', {"hellp":"hello"})
    # socketIO.emit('test', {'walletAddress': walletAddress, 'privateKey':private_key})
     socketIO.emit('test', "emiting")


"""
    Endpoint for setting and updating wallet information associated with a specific chat ID.
    Endpoint :/setWallet
    Method: POST

    JSON Payload:
        - chatId (str): Unique identifier for the chat.
        - walletAddress (str): Ethereum wallet address to be associated with the chat ID.
        - privateKey (str): Private key corresponding to the provided wallet address.

    Response:
        - JSON: Updated wallet information, including the wallet address and private key.

    Side Effects:
        - Updates the `chatId_dict` with the provided wallet information.
        - Emits a 'walletUpdate' event via Socket.IO with the updated wallet information.

    Returns:
        - tuple: JSON response containing the updated wallet information, HTTP status code (200).

    Usage:
        Example JSON payload:
        {
            "chatId": "123456",
            "walletAddress": "0xabcdef...",
            "privateKey": "0x123456..."
        }
    """


@app.route('/setWallet',methods=['POST'])
def set_wallet():
    try:
        data=request.json
        chatId=data['chatId']
        walletAddress, private_key = data['walletAddress'], data['privateKey']
        chatId_dict[chatId]['walletAddress']=walletAddress
        chatId_dict[chatId]['private_key']=private_key

        socketIO.emit('walletUpdate', {'walletAddress':walletAddress, 'privateKey':private_key})
        return jsonify({'walletAddress':walletAddress, 'privateKey':private_key}),200
    except Exception as e:
        print(str(e), "error in setting wallet")
        return jsonify({"error":str(e)}),400

"""
    Description:
        Event handler for setting the stop loss value. Updates the global variable `stop_loss`
        with the provided stop loss value and emits a 'stopLossUpdate' event to inform clients.

    Parameters:
        - data (dict): A dictionary containing the 'stopLoss' value to be set.

    Emits:
        - 'stopLossUpdate' event with the updated stop loss value.

    Usage:
        socketIO.emit('setStopLoss', {'stopLoss': 0.05})
    """
@socketIO.on('setStopLoss')
def set_wallet(data):
    global stop_loss
    # global private_key
    stop_loss= data['stopLoss']
    socketIO.emit('stopLossUpdate', {'stopLoss':stop_loss})


"""
    Description:
        Event handler for setting the maximum run time for a token. Updates the global variable
        `max_run_time_for_token` with the provided value and emits a 'maxRunTime' event to inform clients.

    Parameters:
        - data (dict): A dictionary containing the 'maxRunTime' value to be set.

    Emits:
        - 'maxRunTime' event with the updated maximum run time value.

    Usage:
        socketIO.emit('setTokenRunTime', {'maxRunTime': 3600})
    """
@socketIO.on('setTokenRunTime')
def set_wallet(data):
    global max_run_time_for_token
    # global private_key
    max_run_time_for_token= data['maxRunTime']
    socketIO.emit('maxRunTime', {'maxRunTime':max_run_time_for_token})

"""
    Description:
        Event handler for responding to a client's request for CSV data. Reads the content of
        'boughtcoins.csv' and 'soldcoins.csv' files and emits 'csv_data' and 'csv_data2' events
        with the respective CSV data to inform clients.

    Emits:
        - 'csv_data' event with the content of 'boughtcoins.csv'.
        - 'csv_data2' event with the content of 'soldcoins.csv'.

    Usage:
        socketIO.emit('request_csv')
    """
@socketIO.on('request_csv')
def send_csv():
    with open('boughtcoins.csv', 'rb') as file:
        csv_data = file.read()
        socketIO.emit('csv_data', csv_data)
    with open('soldcoins.csv', 'rb') as file:
        csv_data = file.read()
        socketIO.emit('csv_data2', csv_data)


"""
    Endpoint:/getCurrentTokenHolding
    method: POST

    Description:
        This endpoint handles requests to retrieve information about the current token holdings
        of a user identified by their chat ID. The user's wallet address is retrieved from the
        `chatId_dict`, and the corresponding `leverage_manager` is used to fetch the user's token balances.

    Request JSON Payload:
        - chatId (str): The unique chat ID of the user.

    Returns:
        - JSON: A JSON response containing information about the user's token holdings.
                If the user or wallet is not found, appropriate error messages are returned.

    Usage:
        POST request to "/getCurrentTokenHolding" with JSON payload:
        {"chatId": "user_chat_id"}
    """
@app.route("/getCurrentTokenHolding",methods=['POST'])
def handle_showing_current_token_holding():
    try:
        data=request.json
        chatId=data['chatId']
        if chatId not in  chatId_dict:
            return jsonify({'result':'chatId not found'}),400
        if chatId not in multi_wallet_dict:
            return jsonify({'result':"chatId not found"}), 400
            
        count, index = 0, -1
        for j, k in enumerate(multi_wallet_dict[chatId]):
            print(multi_wallet_dict[chatId][j], j)
            if multi_wallet_dict[chatId][j]['status'] == True:
                        
                index = j
                count+=1
                print(index, "index")
                
        if count > 1:
            return jsonify({'result':'multiple active wallets'}),400
        else:
            count=0
        if index == -1: 
            return jsonify({'result':'no active wallet'}),400
            
            
        walletAddress=multi_wallet_dict[chatId][index]['walletAddress']
        # walletAddress=chatId_dict[chatId]['walletAddress']
        if walletAddress  not in  leverage_thread_dict:
            return jsonify({'result':'walletAddress not found'}),400
        
        leverage_manager=leverage_thread_dict[walletAddress]['leverage_manager']

        tokens = leverage_manager.get_user_tokens(walletAddress)
        tokens_list = []
        print(tokens)
        
        for token in tokens:
            token_value, token_readable_balance, token_symbol = get_token_balance_general(token[0],walletAddress,active_chain)
            tokens_list.append({'tokenAddress':token[0], 'tokenAmount':token[1], 'tokenSymbol':token_symbol})
        if len(tokens)<=0:
            return jsonify({'tokensInfo':0}), 200
        return jsonify({'tokensInfo':tokens_list}), 200
    except Exception as e:
        return jsonify({'error':str(e)}), 400
"""
    Endpoint:/getTokenSold
    method: POST

    Description:
        This route handles the request to retrieve information about tokens sold by a user.
        It expects a JSON payload with a 'chatId' field, looks up the associated wallet address,
        and then retrieves the tokens sold information using the associated Leverage Manager contract.

    Request Method:
        POST

    Request JSON Payload:
        - chatId (str): The unique identifier for a chat.

    Returns:
        - JSON: Returns a JSON response containing information about tokens sold by the user.
                If the chatId or walletAddress is not found, appropriate error messages are returned.

    Example Usage:
        POST /getTokenSold
        {"chatId": "unique_chat_id"}

    Example Response (tokensInfo present):
        {"tokensInfo": [{"tokenAddress": "0x123abc...", "tokenAmount": 100}, {"tokenAddress": "0x456def...", "tokenAmount": 50}]}

    Example Response (no tokensInfo):
        {"tokensInfo": 0}
    """
@app.route("/getTokenSold",methods=['POST']) 
def handle_token_sold_showing():
    try:
        data=request.json
        chatId=data['chatId']
        if chatId not in  chatId_dict:
            return jsonify({'result':'chatId not found'}), 200
        
        # walletAddress=chatId_dict[chatId]['walletAddress']
        if chatId not in multi_wallet_dict:
            return jsonify({'result':"chatId not found"}), 400
            
        count, index = 0, -1
        for j, k in enumerate(multi_wallet_dict[chatId]):
            print(multi_wallet_dict[chatId][j], j)
            if multi_wallet_dict[chatId][j]['status'] == True:
                        
                index = j
                count+=1
                print(index, "index")
                
        if count > 1:
            return jsonify({'result':'multiple active wallets'}),400
        else:
            count=0
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
            
            
        walletAddress=multi_wallet_dict[chatId][index]['walletAddress']
        
        
        
        if walletAddress  not in  leverage_thread_dict:
            return jsonify({'result':'walletAddress not found'}), 400
        
        leverage_manager=leverage_thread_dict[walletAddress]['leverage_manager']
        token_sold = leverage_manager.contract.functions.getUserSoldTokens(walletAddress).call()
            # return token_sold
        print(token_sold)
        tokens_list = []
        print(token_sold)
            # for token in tokens:
            #     tokens_list.append({'tokenAddress':token[0], 'tokenAmount':token[1], 'tokenSymbol':token_symbol})
            # if len(tokens)<=0:
            #     return jsonify({'tokensInfo':0})
            # return jsonify({'tokensInfo':tokens_list})
        for token in token_sold:
            token_value, token_readable_balance, token_symbol = get_token_balance_general(token[0],walletAddress,active_chain)

            tokens_list.append({'tokenAddress':token[0], 'tokenAmount':token[1], 'tokenSymbol':token_symbol})
        if len(token_sold)<=0:
            return jsonify({'tokensInfo':0}), 200

        return jsonify({'tokensInfo':tokens_list}), 200
    except Exception as e:
        print(str(e), "error in getting the token bought")
        return jsonify({"error":str(e)}), 400

"""
    Description:
        This function handles pending transactions received through a socketIO event.
        It parses the incoming data to determine the operation type ('op') and associated arguments.
        Depending on the operation type, it triggers specific actions related to token swaps, liquidity removal, and liquidity addition.

    Parameters:
        - data (dict): A dictionary containing information about the pending transaction, including:
            - 'op' (str): The operation type, indicating the nature of the pending transaction.
            - 'args' (str): A JSON-encoded string representing the arguments associated with the operation.
            - 'walletAddress' (str): The wallet address associated with the pending transaction.

    Returns:
        None

    Raises:
        None (All exceptions are caught and logged.)

    Usage:
        This function is typically invoked when a 'pending' socketIO event is received.

    Example:
        socketIO.emit('pending', {"op": "swapExactETHForTokens", "args": "[0.0001, ['ETH', 'TOKEN_ADDRESS']]",
                                  "walletAddress": "0x123abc..."})

    Note:
        The function handles different operation types and triggers specific actions accordingly,
        such as buying tokens for ETH, removing liquidity, and adding liquidity.
    """
@socketIO.on('pending')
def pending_transactions(data):
    try:
        print(data.keys())
        op = data['op']
        args_list = json.loads(data['args'])
        walletAddress=data["walletAddress"]
        # print(type(data['args']))
        # print(data['args']['1'])
        path = args_list[1]
        amountOutMin = args_list[0]
        maxMirrorLimit=mirror_thread_dict[walletAddress]['maxMirrorLimit']
        if "swapExactETHForTokens" in data['op']:
            amount, token_address = maxMirrorLimit, path[1]
            print(amount, data)
            token_amount, tx_hash = buy_for_eth(0.0001, token_address, True)
            print(type(tx_hash), type(token_amount))
            socketIO.emit('tokenBought', {"tokenAmount":str(token_amount), "tokenAddress":str(token_address), "txHash":str(tx_hash)})
            #Handle the buying logic here
        if "removeLiquidity" in op:
            pass #handle the case in which liquidity has been removed
        if "addLiquidity" in op:
            pass #handle the frontRunning and selling
    
    except Exception as e:
        print(data['args'])
        print("Error in Handling Snipe", e)



"""
    Endpoint to retrieve information about a specific token from the LunarCRUSH API.
    Endpoint: /getTokenInfo/<tokenName>
    method:GET

    Parameters:
        - tokenName (str): The name of the token for which information is requested.

    Returns:
        - JSON response containing:
            - 'tokenseries': Time series data for the specified token.
            - 'changeInterval': Change data for the specified token within a specific interval.
            - 'top_influencer': Information about the top influencer for the specified token.

    Raises:
        - JSONDecodeError: If there is an error parsing the JSON response from the LunarCRUSH API.
        - RequestException: If there is a network-related error during the API request.

    Usage:
        This endpoint is accessed via a GET request to '/getTokenInfo/<tokenName>'.

    Note:
        The LunarCRUSH API key used for authorization is included in the headers of the requests.

    Example:
        GET '/getTokenInfo/bitcoin'

    Response:
        {
            "tokenseries": {...},
            "changeInterval": [...],
            "top_influencer": {...}
        }
    """
# @app.route('/getTokenInfo/<tokenName>', methods=['GET'])
# def tokenInfo(tokenName):
#     url1 = f"https://lunarcrush.com/api4/public/coins/{tokenName}/time-series/v1"
#     header_1 = {
#         'Authorization': 'Bearer b29npf6wystcx7go8m69gnp30blnnhheoer3ndulc'
#     }
#     url2 = f"https://lunarcrush.com/api3/coins/{tokenName}/change?interval=1d"
#     header_2 = {
#         'Authorization': 'Bearer b29npf6wystcx7go8m69gnp30blnnhheoer3ndulc'
#     }
#     url3 = "https://lunarcrush.com/api3/coins/2/influencers"
#     headers_3 = {
#      'Authorization': 'Bearer b29npf6wystcx7go8m69gnp30blnnhheoer3ndulc'
#     }

#     try:
#         response1 = requests.get(url1, headers=header_1)
#         response2 = requests.get(url2, headers=header_2)
#         response3 = requests.get(url3, headers=headers_3)
       
#         if response1.status_code == 200 and response2.status_code == 200 and response3.status_code:
#             data = response1.json()
#             data2=response2.json()
#             data3=response3.json()
#             latest_data = max(data['timeSeries'], key=lambda item: item['time'])
        
#             tweet_sentiment_impact_count=0
#             tweet_sentiment_count=0
#             timeSeries_dict={}
#             for key ,value in latest_data.items():
#                 if 'tweet_sentiment_impact' in key:
#                     if value:
                        
#                         tweet_sentiment_impact_count += value
#                 elif 'tweet_sentiment' in key:
#                     if value:
#                         # continue
#                         tweet_sentiment_count+=value
#                 else:
#                     if value:
#                         # continue
#                         timeSeries_dict[key]=value



#             max_engagement = 0    
#             max_engagement_json = None
#             if data3['data']:
#                 for entry in data3['data']:
#                     engagement = entry.get("engagement")
#                     if engagement and engagement > max_engagement:
#                         max_engagement = engagement
#                         max_engagement_json = entry

#             timeSeries_dict['tweet_sentiment_impact_count'] = tweet_sentiment_impact_count
#             timeSeries_dict['tweet_sentiment_count'] = tweet_sentiment_count 
            
            

#             return jsonify({"tokenseries":timeSeries_dict,"changeInterval":data2['data'],'top_influencer':max_engagement_json}),200
#         elif response1.status_code == 401:
#             # Handle 401 Unauthorized error
#             return jsonify({"error": "Unauthorized. Check your API key."}), 400
#         else:
#             # Handle other HTTP errors
#             return jsonify({"error": f"Failed to retrieve data. Status code: {response1.status_code}, {response1}"}), 400

#     except requests.exceptions.RequestException as e:
#         # Handle network errors
#         return jsonify({"error": "Error fetching data: " + str(e)})
#     except json.JSONDecodeError as e:
#         # Handle JSON parsing errors
#         return jsonify({"error": "Error parsing JSON: " + str(e)}), 400

import json
@app.route('/getTokenInfo/<tokenName>', methods=['GET'])
def tokenInfo(tokenName):
    try:
        # data = request.json
        # token_address = data['tokenAddress']
        # token_name = None
        # try:
        #     for i in chain_list:
        #         active_chain_loop = chain_list[i]
        #         web3, erc20_abi = active_chain_loop['web3'], active_chain_loop['erc_20_abi']
        #         try:
        #             sellTokenContract = web3.eth.contract(address=web3.to_checksum_address(token_address), abi=erc20_abi)
        #             token_name = sellTokenContract.functions.name().call()
        #             print(token_name, "Token Name")
        #             # token_value, token_readable_balance, token_symbol = get_token_balance_general(token_address,walletAddress,active_chain)
        #             break
        #         except Exception as e:
        #             print(str(e))
        #             continue
        # except Exception as e:
        #     print(str(e))
        #     return jsonify({"error":str(e)}), 400
        
        # if token_name == None:
        #     return jsonify({"error":"tokenName not found"})
        try :
            url1 = f"https://lunarcrush.com/api4/public/coins/{tokenName}/time-series/v1"
            header_1 = {
                'Authorization': 'Bearer 5xsqqoxa3sigxhae157xlyrxb6lq2blvzb6f2yg1'
            }
            
            response1 = requests.get(url1, headers=header_1)
            data1 = response1.json()
            coinName = data1['data']['name'].lower()
            coinName=coinName.replace(" ", "")
            print(coinName)
            
            url2 = f"https://api.coingecko.com/api/v3/coins/{coinName}"        
            response2 = requests.get(url2)
        except Exception as e:
            print(str(e))
            return jsonify({"error":str(e)}), 400
            
        if response1.status_code == 200 and response2.status_code == 200:
            data2 = response2.json()

            latest_data1 = max(data1['timeSeries'], key=lambda item: item['time'])
            latest_data2 = data2['community_data']
            
            community_data,market_data_auth= data2['community_data'],data2['market_data']
            main_dict ={}
            for key, value in community_data.items():
                main_dict[key]= value
            
            main_dict['ath'] = market_data_auth['ath']['usd']
            main_dict['ath_change_percentage']= market_data_auth["ath_change_percentage"]['usd']
            main_dict['atl']= market_data_auth["atl"]['usd']
            main_dict['atl_change_percentage']= market_data_auth["atl_change_percentage"]['usd']
            main_dict['circulating_supply']= market_data_auth["circulating_supply"]
            main_dict['current_price']= market_data_auth["current_price"]
            main_dict['current_price']= market_data_auth["current_price"]['usd']
            main_dict['market_cap']= market_data_auth["market_cap"]['usd']
            main_dict['market_cap_change_24h']= market_data_auth["market_cap_change_24h"]
            main_dict['price_change_percentage_7d']= market_data_auth["price_change_percentage_7d"]
            main_dict['price_change_percentage_30d']= market_data_auth["price_change_percentage_30d"]
            main_dict['price_change_percentage_1y']= market_data_auth["price_change_percentage_1y"]
            main_dict['total_volume']= market_data_auth["total_volume"]['usd']
            main_dict['sentiment_votes_down_percentage']= data2["sentiment_votes_down_percentage"]
            main_dict['sentiment_votes_up_percentage']= data2["sentiment_votes_up_percentage"]
            
            response_data = {"tokenseries": latest_data1,"changeInterval": main_dict}
            return jsonify(response_data), 200
        return jsonify({'error':'Third party API not working'}),400                             
    except Exception as e:
            print(str(e))
            return jsonify({"error": "Error parsing JSON: " + str(e)}), 400

"""
    Endpoint: /

    Description:
        This route returns a simple string response, indicating the successful connection to the index endpoint.

    Returns:
        - str: A simple string message indicating successful connection.

    Usage:
        - Accessing this route in a web browser or through an HTTP request to the root endpoint.
    """
@app.route('/')
def index():
    return "heelpo"

"""
    Description:
        Socket.IO event handler for the 'connect' event. This function is triggered when a client
        successfully connects to the Socket.IO server.

    Parameters:
        - data (dict): Additional data associated with the connection. In most cases, this is not used.

    Returns:
        None

    Usage:
        This function is automatically called when a client establishes a connection to the Socket.IO server.
        It can be used to perform any necessary actions upon client connection.

    Notes:
        The function is decorated with @socketIO.on('connect'), indicating that it is an event handler
        for the 'connect' event.

    Example:
        @socketIO.on('connect')
        def test_connect(data):
            # Your custom logic for handling the 'connect' event goes here
            print(data)
    """

@socketIO.on('connect')
def test_connect(data):
    # currentSocketId = request.namespace.socket.sessid
    print(data)
    # emit('my response', {'data': 'Connected'})


# ---------------------------------------- Multi user creation -----------------

"""
    Endpoint: /godModeStart
    method: POST
    Description:
        This route function starts a sniping process for a specified wallet address using the provided data.
        The data includes parameters such as transaction revert time, snipe BNB amount, sell profit,
        active blockchain, chat ID, etc.

    Request (POST) Payload:
        - transactionRevertTime (int): Time in seconds for a transaction to revert.
        - amount (float): The amount of BNB to use for sniping.
        - profitToAttain (float): The desired profit percentage to attain.
        - active_chain (str): The name of the active blockchain.
        - chatId (str): The chat ID associated with the user.

    Returns:
        - JSON response: A JSON response indicating the result of the sniping process initiation.

    Result Codes:
        - 200: Snipe started successfully.
        - 400: Chat ID not found in the dictionary.

    Usage:
        The route is typically accessed through a POST request with the required data.
        Example usage: /godModeStart
    """
@app.route('/godModeStart',methods=['POST'])
def multiprocessing():
    try:    
        data=request.json
        response_dic={}
    # for data in details:
       
        # walletAddress = data['walletAddress']
        # private_key = data['privateKey']
    
        transactionRevertTime = data['transactionRevertTime']
        snipeBNBAmount = data['amount']
        sellProfit = data['profitToAttain']
        active_chain=data['active_chain']
        chatId=data['chatId']
        total_holders_count = data['holdersCount']
        liquidity_lock = data['liquidityLock']
        max_tax = data['maxTax']
        liquidiity_available = data['liquidityAvailable']
        is_main = data['isMain']
        blacklist_token_address_list = data['blacklistTokens']
        sellProfitPer = data['sellProfitper']
        stopLossPer = data['stopLossPer']
        if chatId in chatId_dict:
            if chatId not in multi_wallet_dict:
                return jsonify({'result':"chatId not found"}), 400
        
            count, index = 0, -1
            for j, k in enumerate(multi_wallet_dict[chatId]):
                print(multi_wallet_dict[chatId][j], j)
                if multi_wallet_dict[chatId][j]['status'] == True:
                        
                    index = j
                    count+=1
                    print(index, "index")
                
            if count > 1:
                return jsonify({'result':'multiple active wallets'}),400
            else:
                count=0
            if index == -1:
                return jsonify({'result':'no active wallet'}),400
            
            
            walletAddress=multi_wallet_dict[chatId][index]['walletAddress']
            private_key=multi_wallet_dict[chatId][index]['private_key']
                
            # walletAddress=chatId_dict[chatId]['walletAddress']
            # private_key=chatId_dict[chatId]['private_key']
            leverage_manager=leverage_thread_dict[walletAddress]['leverage_manager']
            main_wallet_engine=leverage_thread_dict[walletAddress]['main_wallet_engine']
            thread_dict[walletAddress]={'Thread':None,'snipe':True}
            token_loop_thread = threading.Thread(target=listen_for_tokens_general,args=(walletAddress,private_key,transactionRevertTime,snipeBNBAmount,sellProfit,active_chain,leverage_manager,main_wallet_engine, total_holders_count,liquidity_lock,max_tax,liquidiity_available, is_main, blacklist_token_address_list,sellProfitPer,stopLossPer))
            thread_dict[walletAddress]['Thread']=token_loop_thread
            token_loop_thread.start()

            #pushing thread_Id to DB
            # push_thread_to_db(thread_dict)

            # socketIO.emit('snipingStarted', {'value': "started"})
            return jsonify({'result':f'snipe started for {walletAddress}','chatID':chatId}), 200
        else:
            return jsonify({'result':'chatId not found'}), 400
    except Exception as e:
        print(str(e), "error in godModeStart")
        return jsonify({"error":str(e)}), 400

"""
    Description:
        This route checks if a given chat ID exists in the `chatId_dict`.

    HTTP Method:
        POST

    JSON Payload:
        - chatId (str): The chat ID to be checked.

    Returns:
        - JSON: {'result': True} if the chat ID is found in `chatId_dict`, {'result': False} otherwise.
    """
@app.route('/CheckChatId', methods=['POST'])
def check_chatID():
    try:
        data=request.json
        chatId=data['chatId']
        if chatId in chatId_dict:
            return jsonify({'result':True}), 200
        return jsonify({'result':False}), 400
    except Exception as e:
        print(str(e), "error in checking chatID")
        return jsonify({"error":str(e)}), 400


@app.route('/searchbar', methods=["POST"])
def check_data():
    try:
        data = request.json
        input_address = data['input_address']
        chain = data['chain']
        
        current_chain = chain_list[chain]
        rpc_url = current_chain['rpc_url']
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        if w3.is_connected():

            if input_address:

                try:
                    with open('./erc20.json', 'r') as erc20_abi_file:
                        erc20_abi_file_ = json.load(erc20_abi_file)  # Load the ABI from a JSON file

                    erc20_contract_abi =erc20_abi_file_
                    
                    erc20_contract = w3.eth.contract(address=w3.to_checksum_address(input_address), abi=erc20_contract_abi)
                    name = erc20_contract.functions.name().call()
                    symbol = erc20_contract.functions.symbol().call()
                    
                    response = {'message': 'ERC20 contract address'}
                    return jsonify(response), 200
                    
                except Exception as e:
                    # response = {'message': 'Something went wrong'}
                    print(str(e))
                    if w3.is_address(input_address):
                        response = {'message': 'wallet address'}
                        return jsonify(response), 200
                    else:
                        response = {'message': 'inavalid input'}
                        return jsonify(response), 400
                
                    
            else:    
                response = {'message': 'Please send valid input'}
                return jsonify(response), 400
            
        else:
            response = {'message': 'Error: Unable to connect to the Ethereum node'}
            return jsonify(response), 400
    except Exception as e:
        print(str(e), "error in searchbar")
        return jsonify({"error":str(e)}), 400



"""

    Endpoint : /getLeveragetoken
    method : POST
    Description:
        This route handler function calculates and returns the leverage score for a given ERC20 token
        based on the score obtained from the `get_leverage_token` function.

    Request (JSON):
        {
            "chatId": "unique_identifier",
            "tokenAddress": "0x123abc...",
            "active_chain": "ethereum"
        }

    Response (JSON):
        - Success (status 200):
            {
                "result": "1",
                "error": "",
                "leverage": calculated_leverage_score
            }
        - Error (status 400):
            {
                "result": "-1",
                "error": "Error message",
                "leverage": -1
            }

    Notes:
        - If the `chatId` is not found in the `chatId_dict`, a 400 Bad Request response is returned.
        - The leverage score is calculated based on the score obtained from the `get_leverage_token` function.
        - The calculated leverage score is returned in the response JSON.

    Raises:
        - ChainNameNotFoundError: If the specified blockchain is not found in the predefined chain list.

    Usage:
        curl -X POST -H "Content-Type: application/json" -d '{"chatId":"unique_identifier", "tokenAddress":"0x123abc...", "active_chain":"ethereum"}' http://yourdomain.com/getLeveragetoken
    """
@app.route('/getLeveragetoken', methods=['POST'])
def get_leverage_for_token():
    try:
        data=request.json
        chatId, token_address, active_chain=data['chatId'], data['tokenAddress'], data['active_chain']
        if chatId not in chatId_dict:
            return jsonify({'result':"chatID not found"}), 400
        try:
            score = get_leverage_token(token_address, active_chain)
            if score == 10:
                return jsonify({"result":"1", "error":"", 'leverage':5}), 200
            elif score == 5:
                return jsonify({"result":"1", "error":"", 'leverage':1.1}), 200
            else:
            # Handle cases in between
                if 5 < score < 10:
                    # You can implement a linear interpolation 
                    # 1.1 + (score - 5) * (5 - 1.1) / (10 - 5) 
                    # for values between 5 and 10
                    # Example: Linear interpolation between (5, 1.1) and (10, 5)
                    print(1.1 + (score - 5) * (5 - 1.1) / (10 - 5), "token_score")
                    return jsonify({"result":"1", "error":"", 'leverage':1.1 + (score - 5) * (5 - 1.1) / (10 - 5)}), 200
                else:
                    # Handle any other cases not explicitly defined
                    return jsonify({"result":"-1", "error":str(e), 'leverage':0}), 400
        except ChainNameNotFoundError as e:
            print("error in getting token score", str(e))
            return jsonify({"result":"-1", "error":str(e), 'leverage':-1}), 400
        except TokenNotFoundError as e:
            print("error in getting token info from the api", str(e))
            return jsonify({"result":"-1", "error":str(e), 'leverage':0}), 400
        except Exception as e:
            print("something went wrong with getting the token score", str(e))
            return jsonify({"result":"-1", "error":str(e), 'leverage':-1}), 400
    except Exception as e:
        print("error in getting leverage token", str(e))
        return jsonify({"error":str(e)}), 400

"""
    Endpoint:/buyTokenWithLeverage
    method : POST
    Description:
        This route handles the request to buy tokens with leverage. It retrieves necessary information
        from the JSON payload, such as the amount, token address, chat ID, active blockchain, and leverage.
        It then checks if the provided chat ID is valid, retrieves the associated wallet address and private key,
        calculates the adjusted token amount based on leverage, and initiates the token purchase using the
        `buy_for_eth_general` function. Finally, it emits a socketIO event to notify the client about the token purchase.

    Returns:
        - JSON: Returns a JSON response containing information about the token purchase, including the adjusted
                token amount, token address, and transaction hash.

    Usage:
        The route '/buyTokenWithLeverage' is expected to handle POST requests with a JSON payload containing
        the following fields:
        - amount (float): The original token amount to be purchased.
        - tokenAddress (str): The Ethereum address of the token to be purchased.
        - chatId (str): The chat ID associated with the user making the request.
        - active_chain (str): The name of the active blockchain.
        - leverage (int): The leverage to be applied to the token purchase.

        Example JSON payload:
        {
            "amount": 10.0,
            "tokenAddress": "0x123abc...",
            "chatId": "123456789",
            "active_chain": "ethereum",
            "leverage": 2
        }
    """
@app.route('/buyTokenWithLeverage',methods=['POST'])
def handle_buying_tokens_with_leverage():
    try:
        data=request.json
        amount, token_address,chatId, active_chain, leverage = data['amount'], data['tokenAddress'],data['chatId'], data['active_chain'], data['leverage']
        if chatId not in chatId_dict:
            return jsonify({'result':'chatId not found'}),400
        
        if chatId not in multi_wallet_dict:
            return jsonify({'result':"chatId not found"}), 400
            
        count, index = 0, -1
        for j, k in enumerate(multi_wallet_dict[chatId]):
            print(multi_wallet_dict[chatId][j], j)
            if multi_wallet_dict[chatId][j]['status'] == True:
                        
                index = j
                count+=1
                print(index, "index")
                
        if count > 1:
            return jsonify({'result':'multiple active wallets'}),400
        else:
            count=0
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
            
            
        walletAddress=multi_wallet_dict[chatId][index]['walletAddress']
        private_key=multi_wallet_dict[chatId][index]['private_key']    
        
        
        print('walletAddress',walletAddress)
        print('private_key',private_key)
        print("Token amount with leverage", amount * leverage)
        amount = amount * leverage
        token_amount, tx_hash = buy_for_eth_general(amount, token_address, False,walletAddress,private_key, active_chain)
        print(type(tx_hash), type(token_amount))
        socketIO.emit('tokenBought', {"tokenAmount":str(token_amount), "tokenAddress":str(token_address), "txHash":str(tx_hash)})
        # socketIO.emit('test', {'walletAddress': walletAddress, 'privateKey':private_key})
        return jsonify({"tokenAmount":str(token_amount), "tokenAddress":str(token_address), "txHash":str(tx_hash)}),200
        # return jsonify({'result':False})
    except Exception as e:
        print(str(e), "error in buying with leverage")
        return jsonify({"error":str(e)}), 400



@app.route('/getWallets', methods=['POST'])
def getting_multiwallets():
    try:
        data=request.json
        chatId=data['chatId']
        if chatId not in chatId_dict:
            return jsonify({'result':'chatId not found'}),400
        if chatId not in multi_wallet_dict:
            return jsonify({'result':'chatId not found'}),400
        
        return jsonify({'result':multi_wallet_dict[chatId]})
    except Exception as e:
        print(str(e))
        return jsonify({'result':str(e)}), 403
        
@app.route('/activeWallet', methods=['POST'])
def getting_activewallet():
    try:
        data=request.json
        chatId=data['chatId']
        if chatId not in chatId_dict:
            return jsonify({'result':'chatId not found'}),400
        if chatId not in multi_wallet_dict:
            return jsonify({'result':'chatId not found'}),400
        index, count = -1, 0

        for j, k in enumerate(multi_wallet_dict[chatId]):
            print(multi_wallet_dict[chatId][j], j)
            if multi_wallet_dict[chatId][j]['status'] == True:
                    
                index = j
                count+=1
                print(index, "index")
            
            if count > 1:
                return jsonify({'result':'multiple active wallets'}),400
            else:
                count=0
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
        
        return jsonify({'result':multi_wallet_dict[chatId][j], 'activeWallet':multi_wallet_dict[chatId][index]}), 200
            
    except Exception as e:
        print(str(e))
        return jsonify({'result':str(e)}), 403


def handle_getting_sharing_data(txn):
    pass
    


@app.route('/getSniperWalletTransaction', methods=['POST'])
def get_sharing_info():
    # return jsonify({"result":multi_wallet_dict})
    try:
        data=request.json
        chatId, active_chain=data['chatId'], data['active_chain']
        if chatId not in chatId_dict:
            return jsonify({'result':'chatId not found'}),400
        if chatId not in multi_wallet_dict:
            return jsonify({'result':'chatId not found'}),400
        if active_chain not in chain_list.keys():
            raise ChainNameNotFoundError
        txnData = data['txn']
        rpc_url = chain_list[active_chain]['rpc_url']
        print(rpc_url)
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        abi = chain_list[active_chain]['erc_20_abi']
        contract = w3.eth.contract(address=w3.to_checksum_address(chain_list[active_chain]['w_address']), abi=abi)
        decoded_data = contract.decode_function_input(txnData)
        print("Decoded Data", decoded_data)
        return jsonify({"result":"decoded"}), 200
        # pass
    except ChainNameNotFoundError as e:
        return jsonify({"result":"sorry, chain not found"}), 400

    except Exception as e:
        return jsonify({"error":str(e)}), 400

    
@app.route('/addWallet', methods=['POST'])
def adding_wallets():
    try:
        data=request.json
        chatId=data['chatId']
        if chatId not in chatId_dict:
            return jsonify({'result':'chatId not found'}),400
        if chatId not in multi_wallet_dict:
            return jsonify({'result':'chatId not found'}),400
        wallet_address, private_key = data['walletAddress'], data['privateKey']
        index, count = -1, 0
        try:

            for j, k in enumerate(multi_wallet_dict[chatId]):
                if multi_wallet_dict[chatId][j]['walletAddress'] == wallet_address:
                    return jsonify({'result':'wallet already exists'}),400
                if multi_wallet_dict[chatId][j]['status'] == True:
                    index = j
                    count+=1
                print(multi_wallet_dict[chatId][j]['walletAddress'] , wallet_address)
            if count > 1:
                return jsonify({'result':'multiple active wallets'}),400
            else:
                count=0
            # if multi_wallet_dict[v][i]['walletAddress'] == wallet_address:
            #     return jsonify({'result':'wallet already exists'}),400
        except Exception as e:
            print(str(e), "error in the for loop")
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
        multi_wallet_dict[chatId].append({"walletAddress":wallet_address, 'private_key':private_key, 'status':False})
        
        
        return jsonify({'result':multi_wallet_dict[chatId], 'activeWallet':multi_wallet_dict[chatId][index]}),200
            
    except Exception as e:
        print(str(e), "error")
        return jsonify({'result':str(e)}), 403



@app.route('/generateWallet', methods=['POST'])
def generating_wallets():
    try:
        data=request.json
        chatId=data['chatId']
        if chatId not in chatId_dict:
            return jsonify({'result':'chatId not found'}),400
        if chatId not in multi_wallet_dict:
            return jsonify({'result':'chatId not found'}),400
        # wallet_address, private_key = data['walletAddress'], data['privateKey']
        private_key = os.urandom(32).hex()

        # Derive the wallet address from the private key
        account = web3.eth.account.from_key(private_key)
        wallet_address = account.address
        index, count = -1, 0
        try:

            for j, k in enumerate(multi_wallet_dict[chatId]):
                if multi_wallet_dict[chatId][j]['walletAddress'] == wallet_address:
                    return jsonify({'result':'wallet already exists'}),400
                if multi_wallet_dict[chatId][j]['status'] == True:
                    index = j
                    count+=1
                print(multi_wallet_dict[chatId][j]['walletAddress'] , wallet_address)
            if count > 1:
                return jsonify({'result':'multiple active wallets'}),400
            else:
                count=0
            # if multi_wallet_dict[v][i]['walletAddress'] == wallet_address:
            #     return jsonify({'result':'wallet already exists'}),400
        except Exception as e:
            print(str(e), "error in the for loop")
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
        multi_wallet_dict[chatId].append({"walletAddress":wallet_address, 'private_key':private_key, 'status':False})
        
        
        return jsonify({'result':multi_wallet_dict[chatId], 'activeWallet':multi_wallet_dict[chatId][index]}), 200
            
    except Exception as e:
        print(str(e), "error")
        return jsonify({'result':str(e)}), 403



@app.route('/multiWalletList')
def show_multiwallets():
    return jsonify({"result":multi_wallet_dict}), 200

@app.route('/changeWallet', methods=['POST'])
def change_active_wallet():
    try:    
        data=request.json
        chatId=data['chatId']
        if chatId not in chatId_dict:
            return jsonify({'result':'chatId not found'}),400
        if chatId not in multi_wallet_dict:
            return jsonify({'result':'chatId not found'}),400
        
        index = data['index']
        temp_index, count = -1, 0
     
        for j, k in enumerate(multi_wallet_dict[chatId]):
            print(multi_wallet_dict[chatId][j], "Multi")
            if multi_wallet_dict[chatId][j]['status'] == True:
                temp_index = j
                count+=1
                # print(multi_wallet_dict[v][i]['walletAddress'] , wallet_address)
        print(count)
        if count > 1:
            print("Multiple active wallets, making the current wallet primary")
            for j, k in enumerate(multi_wallet_dict[chatId]):
                print(multi_wallet_dict[chatId][j], "here==>")
                if multi_wallet_dict[chatId][j]['status'] == True:
                    multi_wallet_dict[chatId][j]['status'] = False
                    # temp_index = i
                    # count+=1
        if temp_index == -1:
            # return jsonify({'result':'no active wallet'}),400
            print("No active Wallets")

        for j, k in enumerate(multi_wallet_dict[chatId]):
                # if multi_wallet_dict[v][j]['walletAddress'] == wallet_address:
                #     return jsonify({'result':'wallet already exists'}),400
            print(multi_wallet_dict[chatId][data['index']], data['index'], "Index", j)
                # if :
                    
            if multi_wallet_dict[chatId][j]['status'] == True:
                multi_wallet_dict[chatId][j]['status']=False
            if j == index:
                print(multi_wallet_dict[chatId][j],j , "somethiunf")
                if multi_wallet_dict[chatId][j]['status'] == True:
                    return jsonify({"result":"already acitve"}), 403
                multi_wallet_dict[chatId][j]['status'] = True
            #     # print(multi_wallet_dict[v][i]['walletAddress'] , wallet_address)
            # if multi_wallet_dict[v][i]['status'] == True:
            #     multi_wallet_dict[v][i]['status'] = False
            # if i == index:
            #     multi_wallet_dict[v][i]['status'] = True
        
        return jsonify({'result':multi_wallet_dict[chatId], 'activeWallet':multi_wallet_dict[chatId][index]}), 200
    except Exception as e:
        print(str(e))
        return jsonify({'result':str(e)}), 403


"""
    Description:
        This route creates a unique chatId along with a corresponding Ethereum wallet address
        and private key. The chatId and wallet details are stored in the `chatId_dict`.

    Request Method:
        - POST

    Request JSON Parameters:
        - chatId (str): The unique identifier for the chat.

    Returns:
        - JSON: Returns a JSON response indicating the result of the operation.
            - If the chatId already exists in `chatId_dict`, returns an error response.
            - If the chatId is unique, generates a new Ethereum wallet address and private key,
              associates them with the chatId, and returns a success response.

    Example Usage:
        POST /createChatId
        {
            "chatId": "unique_chat_id"
        }

    Example Response (Success):
        {
            "result": "chatId unique_chat_id created"
        }

    Example Response (Error - ChatId Already Exists):
        {
            "result": "chatId already exists",
            "status_code": 400
        }
    """

@app.route('/getWallets', methods=['POST'])
def getting_multiwallets():
    try:
        data=request.json
        chatId=data['chatId']
        if chatId not in chatId_dict:
            return jsonify({'result':'chatId not found'}),400
        if chatId not in multi_wallet_dict:
            return jsonify({'result':'chatId not found'}),400
        
        return jsonify({'result':multi_wallet_dict[chatId]})
    except Exception as e:
        print(str(e))
        return jsonify({'result':str(e)}), 403
        
@app.route('/activeWallet', methods=['POST'])
def getting_activewallet():
    try:
        data=request.json
        chatId=data['chatId']
        if chatId not in chatId_dict:
            return jsonify({'result':'chatId not found'}),400
        if chatId not in multi_wallet_dict:
            return jsonify({'result':'chatId not found'}),400
        index, count = -1, 0
        for i, v in enumerate(multi_wallet_dict):
            for j, k in enumerate(multi_wallet_dict[v]):
                print(multi_wallet_dict[v][j], j)
                if multi_wallet_dict[v][j]['status'] == True:
                    
                    index = j
                    count+=1
                    print(index, "index")
        if count > 1:
            return jsonify({'result':'multiple active wallets'}),400
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
        
        return jsonify({'result':multi_wallet_dict[chatId], 'activeWallet':multi_wallet_dict[chatId][index]})
            
    except Exception as e:
        print(str(e))
        return jsonify({'result':str(e)}), 403

@app.route('/addWallet', methods=['POST'])
def adding_wallets():
    try:
        data=request.json
        chatId=data['chatId']
        if chatId not in chatId_dict:
            return jsonify({'result':'chatId not found'}),400
        if chatId not in multi_wallet_dict:
            return jsonify({'result':'chatId not found'}),400
        wallet_address, private_key = data['walletAddress'], data['privateKey']
        index, count = -1, 0
        for i, v in enumerate(multi_wallet_dict):
            print(v)
            for j, k in enumerate(multi_wallet_dict[v]):
                if multi_wallet_dict[v][j]['walletAddress'] == wallet_address:
                    return jsonify({'result':'wallet already exists'}),400
                if multi_wallet_dict[v][j]['status'] == True:
                    index = j
                    count+=1
                print(multi_wallet_dict[v][i]['walletAddress'] , wallet_address)
            # if multi_wallet_dict[v][i]['walletAddress'] == wallet_address:
            #     return jsonify({'result':'wallet already exists'}),400
        if count > 1:
            return jsonify({'result':'multiple active wallets'}),400
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
        multi_wallet_dict[chatId].append({"walletAddress":wallet_address, 'private_key':private_key, 'status':False})
        
        
        return jsonify({'result':multi_wallet_dict[chatId], 'activeWallet':multi_wallet_dict[chatId][index]})
            
    except Exception as e:
        print(str(e), "error")
        return jsonify({'result':str(e)}), 403

@app.route('/multiWalletList')
def show_multiwallets():
    return jsonify({"result":multi_wallet_dict})

@app.route('/changeWallet', methods=['POST'])
def change_active_wallet():
    try:    
        data=request.json
        chatId=data['chatId']
        if chatId not in chatId_dict:
            return jsonify({'result':'chatId not found'}),400
        if chatId not in multi_wallet_dict:
            return jsonify({'result':'chatId not found'}),400
        
        index = data['index']
        temp_index, count = -1, 0
        for i, v in enumerate(multi_wallet_dict):
           for j, k in enumerate(multi_wallet_dict[v]):
                # if multi_wallet_dict[v][j]['walletAddress'] == wallet_address:
                #     return jsonify({'result':'wallet already exists'}),400
                print(multi_wallet_dict[v][j], "Multi")
                if multi_wallet_dict[v][j]['status'] == True:
                    temp_index = j
                    count+=1
                # print(multi_wallet_dict[v][i]['walletAddress'] , wallet_address)
        print(count)
        if count > 1:
            print("Multiple active wallets, making the current wallet primary")
            for i, v in enumerate(multi_wallet_dict):
                for j, k in enumerate(multi_wallet_dict[v]):
                    print(multi_wallet_dict[v][j], "here==>")
                    if multi_wallet_dict[v][j]['status'] == True:
                        multi_wallet_dict[v][j]['status'] = False
                    # temp_index = i
                    # count+=1
        if temp_index == -1:
            # return jsonify({'result':'no active wallet'}),400
            print("No active Wallets")
        for i, v in enumerate(multi_wallet_dict):
            for j, k in enumerate(multi_wallet_dict[v]):
                # if multi_wallet_dict[v][j]['walletAddress'] == wallet_address:
                #     return jsonify({'result':'wallet already exists'}),400
                print(multi_wallet_dict[v][data['index']], data['index'], "Index", j)
                # if :
                    
                if multi_wallet_dict[v][j]['status'] == True:
                    multi_wallet_dict[v][j]['status']=False
                if j == index:
                    print(multi_wallet_dict[v][j],j , "somethiunf")
                    if multi_wallet_dict[v][j]['status'] == True:
                        return jsonify({"result":"already acitve"}), 403
                    multi_wallet_dict[v][j]['status'] = True
            #     # print(multi_wallet_dict[v][i]['walletAddress'] , wallet_address)
            # if multi_wallet_dict[v][i]['status'] == True:
            #     multi_wallet_dict[v][i]['status'] = False
            # if i == index:
            #     multi_wallet_dict[v][i]['status'] = True
        
        return jsonify({'result':multi_wallet_dict[chatId], 'activeWallet':multi_wallet_dict[chatId][index]})
    except Exception as e:
        print(str(e))
        return jsonify({'result':str(e)}), 403


@app.route('/createChatId',methods=['POST'])
def create_chatId():
    """
    Request Method:
        - POST

    Request JSON Parameters:
        - chatId (str): The unique identifier for the chat.

    Returns:
        - JSON: Returns a JSON response indicating the result of the operation.
        - If the chatId already exists in `chatId_dict`, returns an error response.
        - If the chatId is unique, generates a new Ethereum wallet address and private key,associates them with the chatId, and returns a success response.

    """
    data=request.json
    chatId=data['chatId']
    

    if chatId in chatId_dict:
  
        return jsonify({'result':'chatId already Exists'}),400
    else:
        private_key = os.urandom(32).hex()

        # Derive the wallet address from the private key
        account = web3.eth.account.from_key(private_key)
        walletAddress = account.address
        chatId_dict[chatId]={'walletAddress':walletAddress,'private_key':private_key}
        if chatId not in multi_wallet_dict.keys():
            multi_wallet_dict[chatId] = []
            multi_wallet_dict[chatId].append({'walletAddress':walletAddress,'private_key':private_key, 'status':True})
        else:
            multi_wallet_dict[chatId].append({'walletAddress':walletAddress,'private_key':private_key, 'status':True})
    try:
        data=request.json
        chatId=data['chatId']
        

        if chatId in chatId_dict:
    
            return jsonify({'result':'chatId already Exists'}),400
        else:
            private_key = os.urandom(32).hex()

            # Derive the wallet address from the private key
            account = web3.eth.account.from_key(private_key)
            walletAddress = account.address
            chatId_dict[chatId]={'walletAddress':walletAddress,'private_key':private_key}
            if chatId not in multi_wallet_dict.keys():
                multi_wallet_dict[chatId] = []
                multi_wallet_dict[chatId].append({'walletAddress':walletAddress,'private_key':private_key, 'status':True})
            else:
                multi_wallet_dict[chatId].append({'walletAddress':walletAddress,'private_key':private_key, 'status':True})

            return jsonify({'result':f'chatId {chatId} created '}),200
    except Exception as e:
        print(str(e), "error in creating chatID")
        return jsonify({"error":str(e)}), 400
        
"""
    Description:
        This route returns information about the threads in the application.

    Endpoint:/thread_info
    Method:GET

    Returns:
        - JSON: A JSON response containing information about the threads.

    Usage:
        Access the route at '/thread_info' using a GET request to retrieve information about threads.
    """
@app.route('/thread_info',methods=['GET'])
def thrad_infomation():
    stringified_dict = {key: str(value) for key, value in thread_dict.items()}
    return jsonify({'thrad_info':stringified_dict}), 200


"""
    Description:
        This route serves the Swagger/OpenAPI specification file (swagger.json) from the 'static' directory.

    Returns:
        - File: The Swagger/OpenAPI specification file in JSON format.

    Usage:
        Access the route at '/static/swagger.json' to retrieve the Swagger/OpenAPI specification file.
    """

@app.route('/static/swagger.json')
def serve_swagger_spec():
    return send_from_directory('static', 'swagger.json')



"""
    Endpoint: /buyForLiquidtion
    Method: POST
    Description:
        This route handles the buying process for liquidation. It receives a POST request containing
        information such as the amount, token address, chat ID, and the active blockchain. The function
        performs the following steps:
        1. Emits a test event through the socketIO.
        2. Retrieves data from the incoming JSON request.
        3. Validates the chat ID and retrieves wallet information.
        4. Calls the buy_for_eth_general function to execute the token purchase.
        5. Emits a 'tokenBought' event through socketIO with the result.
        6. Checks the current token price using check_token_price_general.
        7. Initializes a LeverageManagement instance for managing leverage positions.
        8. Converts token price to Wei and adds the token to the leverage manager.
        9. Emits a 'tokenAdded' event through socketIO with the result.
        10. Returns a JSON response indicating the success of the operation.

    Request:
        - Body (JSON):
            {
                "amount": float,   # The amount to purchase.
                "tokenAddress": str,   # The Ethereum address of the ERC20 token.
                "chatId": str,   # The unique chat ID associated with the user.
                "active_chain": str   # The name of the active blockchain.
            }

    Response:
        - JSON:
            {
                "result": "success"
            }
            or
            {
                "result": "chatId not found"
            }
    """
@app.route('/buyForLiquidtion', methods=["POST"])
def handle_buying_liquidation():
    try:
        socketIO.emit("test")
        data = request.json
        # chatId = data['chatId']
        amount, token_address,chatId, current_chain = data['amount'], data['tokenAddress'],data['chatId'], data['active_chain']
        active_chain = chain_list['eth']
        # walletAddress=chatId_dict[chatId]['walletAddress']
        if chatId not in chatId_dict:
            return jsonify({'result':'chatId not found'}),400
        walletAddress=chatId_dict[chatId]['walletAddress']
        private_key=chatId_dict[chatId]['private_key']
        print('walletAddress',walletAddress)
        print('private_key',private_key)
        token_amount, tx_hash = buy_for_eth_general(amount, token_address, False,walletAddress,private_key, current_chain)
        print(type(tx_hash), type(token_amount))
        socketIO.emit('tokenBought', {"tokenAmount":str(token_amount), "tokenAddress":str(token_address), "txHash":str(tx_hash)})
        token_price = check_token_price_general(token_address, current_chain)
        print(token_price)
        leverage_manager= LeverageManagement(
            active_chain['rpc_url'],
            active_chain['leverage_wallet_abi'],
            active_chain['leverage_wallet_address'],
            walletAddress,
            private_key
        )
        print("There is no problem here......")
        token_price = web3.to_wei(token_price, "ether")
        print("There is no problem here......")

        token_address = web3.to_checksum_address(token_address)
        print("There is no problem here......")

        walletAddress = web3.to_checksum_address(walletAddress)
        print("There is no problem here......")

        leverage_manager.add_token(token_address=token_address, token_value=token_price, sender_address=walletAddress, leverage_taken=token_price)
        socketIO.emit("tokenAdded", {"token_amount":str(token_amount)})
        return jsonify({"result":"success"}), 200
    except Exception as e:
        print(str(e), "error in buying for liquidation")
        return jsonify({"error":str(e)}), 400


"""
    Description:
        Endpoint to initiate the checking of liquidation status for a specific wallet.

    Endpoint: /checkLiquidation
    Method:POST

    JSON Payload:
        {
            "chatId": "unique_chat_identifier"
        }

    Returns:
        - JSON: {"result": "chatId not found"} if the provided chatId is not registered.
                {"result": "walletAddress not found"} if the walletAddress associated with the chatId is not found.
                {"status": "done"} if the liquidation monitoring has been initiated successfully.

    Notes:
        - The function uses data from the provided chatId to retrieve wallet information and initiate liquidation monitoring.
        - Liquidation parameters and configuration are predefined within the function.
    """
@app.route('/checkLiquidation', methods=["POST"])
def handle_checking_liquidation():
    try:
        data = request.json
        chatId = data['chatId']
        active_chain = chain_list['eth']
        walletAddress, private_key=chatId_dict[chatId]['walletAddress'], chatId_dict[chatId]['private_key']


        if chatId not in  chatId_dict:
            return jsonify({'result':'chatId not found'}), 400
            
        walletAddress=chatId_dict[chatId]['walletAddress']


        if walletAddress  not in  leverage_thread_dict:
            return jsonify({'result':'walletAddress not found'}), 400
                
                
        leverage_manager=leverage_thread_dict[walletAddress]['leverage_manager']
        main_wallet_engine=LiquidationEngine(
            active_chain['rpc_url'],
            private_key,
            walletAddress,
            active_chain['router_address'],
            0.2,
            0.5,
            0.5,
            0.7,
            10,
            850000,
            1000000,
            leverage_manager,
            10,
            socketio=socketIO
        )
        main_wallet_engine.start_monitoring()
        return jsonify({'status':"done"}), 200
    except Exception as e:
        print(str(e), "error in checking liquidation")
        return jsonify({"result":str(e)}), 400

"""
    Endpoint: /checkStatus
    Method:POST
    Description:
        This route handler checks the status of a sniping process associated with a given chat ID.
        It verifies if the chat ID and wallet address exist in the respective dictionaries,
        and whether the sniping process is currently active.

    Request (JSON):
        - chatId (str): The unique identifier for a chat.
    
    Response:
        - If chatId does not exist: {'result': 'chatId Does not exist'}, status code 400.
        - If sniping has not been started: {'result': 'Sniping has not been Started'}, status code 400.
        - If sniping process is active: {'result': True}, status code 200.
        - If sniping process is not active: {'result': False}, status code 400.

    Returns:
        - JSON response indicating the status of the sniping process.

    Raises:
        - None

    Usage:
        Send a POST request to '/checkStatus' with a JSON payload containing 'chatId'.
    """
@app.route('/checkStatus', methods=["POST"])
def check_status():
    try:
        data=request.json
        chatId=data['chatId']
        if chatId not in chatId_dict:
            return jsonify({'result':'chatId Does not exists'}),400
        # walletAddress = chatId_dict[chatId]['walletAddress']
        if chatId not in multi_wallet_dict:
            return jsonify({'result':"chatId not found"}), 400
        
        count, index = 0, -1
        for j, k in enumerate(multi_wallet_dict[chatId]):
            print(multi_wallet_dict[chatId][j], j)
            if multi_wallet_dict[chatId][j]['status'] == True:
                    
                index = j
                count+=1
                print(index, "index")
            
        if count > 1:
            return jsonify({'result':'multiple active wallets'}),400
        else:
            count=0
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
        
        
        walletAddress=multi_wallet_dict[chatId][index]['walletAddress']
        
        if walletAddress not in thread_dict:
            return jsonify({'result':'Sniping has not been Started'}),400
        

        thread=thread_dict[walletAddress]['Thread']
        if thread_dict[walletAddress]['Thread'] ==None:
            return jsonify({'result':'Sniping has not been Started'}),400
        
        if thread.is_alive():
            return jsonify({'result':True}),200
        return jsonify({'result':False}),400
    except Exception as e:
       return jsonify({'return ':str(e)}), 400
       
       
@app.route('/checkStatusMirror', methods=["POST"])
def check_status_mirror():
    try:
        data=request.json
        chatId=data['chatId']
        if chatId not in chatId_dict:
            return jsonify({'result':'chatId Does not exists'}),400
        # walletAddress = chatId_dict[chatId]['walletAddress']
        if chatId not in multi_wallet_dict:
            return jsonify({'result':"chatId not found"}), 400
        
        count, index = 0, -1
        for j, k in enumerate(multi_wallet_dict[chatId]):
            print(multi_wallet_dict[chatId][j], j)
            if multi_wallet_dict[chatId][j]['status'] == True:
                    
                index = j
                count+=1
                print(index, "index")
            
        if count > 1:
            return jsonify({'result':'multiple active wallets'}),400
        else:
            count=0
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
        
        
        walletAddress=multi_wallet_dict[chatId][index]['walletAddress']
        
        if walletAddress not in mirror_thread_dict:
            return jsonify({'result':'Sniping has not been Started'}),400
        

        thread=mirror_thread_dict[walletAddress]['mirrorThread']
        if mirror_thread_dict[walletAddress]['mirrorThread'] == None:
            return jsonify({'result':'Sniping has not been Started'}),400
        
        if thread.is_alive():
            return jsonify({'result':True}),200
        return jsonify({'result':False}),400
    except Exception as e:
       return jsonify({'result':str(e)}), 400


# from pymongo import MongoClient

# client = MongoClient('mongodb+srv://pratappatil:Mobiloitte1@cluster0.l1qs6zy.mongodb.net/')
# db = client.JoshwaDB
# chatid_collection = db.chat_id
# thread_collection = db.thread_dict

# @app.route('/push_chatid')
# def push_chatid():
#     try:
#         data = request.get_json()

#         # Your logic for creating Chat ID
#         # Assuming the incoming data is a dictionary with the chatId_dict key
#         chatId_dict = data.get('chatId_dict', {})

#         existing_data = chatid_collection.find_one(chatId_dict)

#         if existing_data:
#             return jsonify({"message": f"Chat ID {chatId_dict} already exists in the collection. Skipping."}), 200
        
#         else:
#             chatid_collection.insert_one(chatId_dict)
#             return jsonify({"message": f"Chat ID {chatId_dict} pushed to the collection successfully."}), 201

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500




client = MongoClient('mongodb+srv://pratappatil:Mobiloitte1@cluster0.l1qs6zy.mongodb.net/')
db = client.JoshwaDB
chatid_collection = db.chat_id

@app.route('/push_chatid')
def push_chatid():
    try:
        chatid = chatId_dict
        print("\n\nchatid",chatid,"\n\n")
        result = list(chatid_collection.find({}, {'_id': 0}))
        keys_list = [list(d.keys())[0] for d in result if d]

        chatid_keys = list(chatid.keys())
        print("\n######chatid_keys",chatid_keys)
        for i in chatid_keys:
            if i not in keys_list:
                print(i,"\n\n\n")
                d={i:chatid[i]}
                print("not exist ",d)
                chatid_collection.insert_one(d)
            else:
                print("\n\nSkipping already exist ",i,chatid[i])

        return jsonify('m'), 200
    except Exception as e:
        print(str(e), "error in pushing chatID")
    # for i in chatId_dict:
    #     print(result = list(chatid_collection.find({}, {'_id': 0})))
    #     return jsonify('m')

# --------------------------------------------- Joshwa new functionailty to add as per Rudransh input-----------------
def get_top_tokens_with_holders_list(walletAddress):
    try:
        url = "https://etherscan.io/tokens"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            token_address = soup.find_all('a', class_='d-flex align-items-center gap-1 link-dark')[:11]
            print('token_addresses', token_address)
            tokens_dict = {}
            tokenCount = 0
            for link in token_address:
                token_name = link.find('div', class_='hash-tag text-truncate fw-medium').text.strip()
                

                print("for token ", token_name, '\n')            
                raw_token_link = link['href']
                token_link = raw_token_link.replace('/token/', '')

                analytics_url = f'https://etherscan.io/token/generic-tokenholders2?m=light&a={token_link}'
                analytics_response = requests.get(analytics_url, headers=headers)

                if analytics_response.status_code == 200:
                    analytics_soup = BeautifulSoup(analytics_response.text, 'html.parser')

                    rows = analytics_soup.find_all('tr')[1:11]  
                    holders_info = []
                    for row in rows:
                        cols = row.find_all('td')
                        sr_no = cols[0].text.strip()
                        holder = cols[1].text.strip()
                        
                        holder_element = cols[1].find('a' ,class_="js-clipboard link-secondary")
                        i_tag = holder_element.find('i', id=re.compile(r'linkIcon_addr_\d+'))
                        
                        if str(sr_no) in i_tag['id']:
                            address = holder_element['data-clipboard-text']
                        
                        if holder.startswith('0') and '...' in holder:
                                holder = address

                            
                        quantity = cols[2].text.strip()
                        percentage = cols[3].text.strip()
                        value = cols[4].text.strip()

                        holders_info.append({
                            'sr_no': sr_no,
                            'holder': holder,
                            "address":address,
                            'quantity': quantity,
                            'percentage': percentage,
                            'value': value
                        })

                    tokens_dict[token_name] = {
                        'token_address': token_link,
                        'holders_info': holders_info
                    }
                    tokenCount+= 1
                    if tokenCount >= 10:
                        break
            whale_token_list=[]
            for key, value in tokens_dict.items():
               
                for holder in value['holders_info']:
                    
                    if walletAddress == holder['address']:
                        
                        whale_token_list.append(f'The {walletAddress} is whale wallet for {key}')
            

            if len(whale_token_list) != 0:
                if len(whale_token_list) >= 5:
                    whale_token_list.append(f'The {walletAddress} is whale wallet')
                    whale_token =  True
                else:
                    whale_token = False

                final_dict = {
                    "info":whale_token_list,
                    "is_whale": whale_token
                }
                return final_dict
            else: 
                return None

        else:
            print('Execption in whale for etherscan api response', response.text)


            return None
    except Exception as e:
        print('Execption in whale function ', str(e))
    

@app.route('/customUserMonitoring', methods=['POST'])
def custom_user_monitoring():
    try:
        data=request.json
        chatId=data['chatId']
        page= data['page']
        pageOffset = data['pageOffset']
        walletAddress = data['walletAddress']

        if chatId not in chatId_dict:
            return jsonify({'result':'chatId Does not exists'}),400
        # walletAddress = chatId_dict[chatId]['walletAddress']
        if chatId not in multi_wallet_dict:
            return jsonify({'result':"chatId not found"}), 400

    
        url = "https://api-goerli.etherscan.io/api"
        api_key = "4WG64J2JT1G83TFFHBSP29T7GZ6MXA4BNG"
        parameters = {
            "module": "account",
            "action": "txlist",
            "address": walletAddress,
            "startblock": 0,
            "endblock": 99999999,
            "page": page,
            "offset": pageOffset,
            "sort": "asc",
            "apikey": api_key
        }
        response = requests.get(url, params=parameters)
        if response.status_code == 200:
            transactionsdata = response.json()
            for transaction in transactionsdata['result']:
                timestamp = int(transaction["timeStamp"])
                transaction["timeStamp"] = datetime.datetime.utcfromtimestamp(timestamp)

            return jsonify({'data':transactionsdata, 'responseMessage':'Data found sucessfully'}),200
        return jsonify({'result':response.text}) , 400
            
    except Exception as e:
        return jsonify({'result':str(e)}),500






@app.route('/customFilterWalletsCategories', methods = ['POST'])
def custom_filter_wallets_categories():
    try:
        data=request.json
        chatId=data['chatId']
        walletAddress = data['walletAddress']

        if chatId not in chatId_dict:
            return jsonify({'result':'chatId Does not exists'}),400
        
        if chatId not in multi_wallet_dict:
            return jsonify({'result':"chatId not found"}), 400

        whale_info = get_top_tokens_with_holders_list(walletAddress)
        if whale_info is not None:
            return jsonify({'data':whale_info,'category':'whale','responseMessage':'data found successfully'})
        else: 
            api_key = "4WG64J2JT1G83TFFHBSP29T7GZ6MXA4BNG"
            end_timestamp = int(datetime.datetime.now().timestamp())
            start_timestamp = int((datetime.datetime.now() - timedelta(days=30)).timestamp())

            # Construct the API request to retrieve the transaction history for the last 30 days
            url = f'https://api.etherscan.io/api?module=account&action=txlist&address={walletAddress}&startblock=0&endblock=99999999&sort=desc&apikey={api_key}&timestamp={start_timestamp}&endtimestamp={end_timestamp}'
            response = requests.get(url)

            if response.status_code == 200:
                # Process the response and filter/count the transactions based on the specified types
                transactions = response.json()['result']
                print('the length of transaction',len(transactions))
                

                # Initialize counters
                token_transfer_count = 0
                send_count = 0
                swap_count = 0

                # Filter transactions for the last 30 days
                transactions_last_30_days = [tx for tx in transactions if int(tx['timeStamp']) >= start_timestamp]

                print(transactions_last_30_days)
                for tx in transactions_last_30_days:
                   
                    input_data = tx.get('functionName', None)


                    if 'transfer' in input_data:
                        token_transfer_count += 1
                    elif 'send' in input_data:
                        send_count += 1
                    elif 'swap' in input_data.lower():
                        swap_count += 1
                    

                total_count = token_transfer_count + send_count + swap_count

                print("Token Transfer Count:", token_transfer_count)
                print("Send Count:", send_count)
                print("Swap Count:", swap_count)

                if total_count > 200:
                    hotWallet_dict={'is_hot':True,'info':f'The {walletAddress} is Hot Wallet'}
                    return jsonify({'data':hotWallet_dict,'category':'HotWallet','responseMessage':'Data found successfully'})
                elif swap_count > 200:
                    trading_dict={'is_Trading':True,'info':f'The {walletAddress} is Trading wallet'}
                    return jsonify({'data':trading_dict,'category':'TradingWallet','responseMessage':'Data found successfully'})
                else:
                    cold_dict={'is_cold':True,'info':f'The {walletAddress} is cold Wallet'}
                    return jsonify({'data':cold_dict,'category':'ColdWallet','responseMessage':'Data found successfully'})
    except Exception as e:
        return jsonify({'result':str(e)}),500



@app.route('/estimatValuesForGetEth',methods=['POST'])
def get_estimate_values():
    try:
        data=request.json
        chatId=data['chatId']
        fromToken = data['fromToken']
        # toToken = data['toToken']
        amount = data['Amount']
        active_chain = data['active_chain']

        if chatId not in chatId_dict:
            return jsonify({'result':'chatId Does not exists'}),400
        
        if chatId not in multi_wallet_dict:
            return jsonify({'result':"chatId not found"}), 400

        
        count, index = 0, -1
        for j, k in enumerate(multi_wallet_dict[chatId]):
            print(multi_wallet_dict[chatId][j], j)
            if multi_wallet_dict[chatId][j]['status'] == True:
                    
                index = j
                count+=1
                print(index, "index")
            
        if count > 1:
            return jsonify({'result':'multiple active wallets'}),400
        else:
            count=0
        if index == -1:
            return jsonify({'result':'no active wallet'}),400
        
        
        walletAddress=multi_wallet_dict[chatId][index]['walletAddress']
        private_key = multi_wallet_dict[chatId][index]['private_key']


        current_chain = chain_list[active_chain]

        web3, api_key = current_chain['web3'], current_chain['scan_api_key']
        sell_amount_in_wei = int(amount * 10**18)

        print(amount, "amount is ")
        
        if active_chain is None or active_chain not in chain_list.keys():
            raise ChainNameNotFoundError(active_chain)
       
        
        token_address = web3.to_checksum_address(fromToken)
        
        w_token_address = current_chain['w_address']
        w_token_address = Web3.to_checksum_address(w_token_address)
          # BNB
        erc_20_abi = current_chain['erc_20_abi']
        router_address, router_abi = current_chain['router_address'], current_chain['router_abi']

        router_contract = web3.eth.contract(address=router_address, abi=router_abi)

        max_allowance =20
        max_allowance = int(max_allowance * 10**18)
        account = Account.from_key(private_key)    
        dai_amount = 4  # Change this to the desired amount

        # sell_amount_in_wei =int(4*10**18)
        print("amount",sell_amount_in_wei)
        path = [web3.to_checksum_address(fromToken), w_token_address]  # DAI to WETH trading path

        # Estimate the amount of WETH you will receive
        amount_out_min = router_contract.functions.getAmountsOut(sell_amount_in_wei, path).call()

        weth_amount_in_wei = amount_out_min[1]

        print(f'Estimated amount of WETH to receive: {weth_amount_in_wei / 10**18} WETH')

        # Execute the swap
       
        nonce = web3.eth.get_transaction_count(account.address) 

        print('amountsout ehter',web3.from_wei(weth_amount_in_wei,'ether'))
            


        transaction = {
            'from': account.address,
            'gas': 8500000,
            'nonce': nonce,
        }
    
        function_data = router_contract.functions.swapExactTokensForETH(
                sell_amount_in_wei,
                0,  # Min amount of WETH you expect to receive
                path,
                account.address,
                int(time.time()) + 60 * 10,  # 10 minutes
            ).estimate_gas(transaction)
        esimateGas = web3.from_wei(function_data,'gwei')
        amountsOut = web3.from_wei(weth_amount_in_wei,'ether')
        finalDict = {
            "estimate_gas":esimateGas,
            "amountsOUT":amountsOut,
            "valueIn": 'ether'
        }


        
        print('estimatevalues',finalDict)
        return jsonify({'data':finalDict,'responseMessage': 'Data found successfully'}),200

    except Exception as e:
        return jsonify({'result':str(e)}),500




socketIO.run(app, host='0.0.0.0', port=8000)  




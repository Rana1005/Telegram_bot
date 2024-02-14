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
import sys
import ctypes
from requests import get
from decimalData import getTokenDecimal
import csv
# from attributedict.collections import AttributeDict
import traceback
import websockets
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
socketIO = SocketIO(app,async_mode='threading', cors_allowed_origins='*')
# print(socketIO.)
# socketio_thread_local = threading.local()
# import eventlet
# eventlet.monkey_patch()
# import socketio
# sio = socketio.Server(cors_allowed_origins="*")
# app = socketio.WSGIApp(sio)
maxMirrorLimit = 0.001
to_be_mirror_wallet = "0x0bFD580a07a6f0F8ef8F9010D827d136c1ec6e43"
stop_loss = 10
max_run_time_for_token= 0.5
token_bought_time = time.time()
isMirroring = True
# @socketIO.on("new")
def emit_event():
    try:
          # Emitting the "new" event
        # return emit("new", {"something":"hello"})
        pass
    except Exception as e:
        return "Error emitting event: " + str(e)



os.system("") #allows different colour text to be used


class style(): # Class of different text colours - default is white
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

print(style.MAGENTA) #change following text to magenta

# socketIO.emit()

print(style.WHITE)

currentTimeStamp = ""
def getTimestamp():
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

bscNode = obj['bscNode'] #set the BSC node to use. I highly recommend a private node such as QuickNode.
pancakeSwapRouterAddress = obj['pancakeSwapRouterAddress'] #load config data from JSON file into program
pancakeSwapFactoryAddress = '0x6725F303b657a9451d8BA641348b6761A6CC7a17' #read from JSON later
walletAddress = obj['walletAddress']
private_key = obj['walletPrivateKey'] #private key is kept safe and only used in the program

snipeBNBAmount = float(obj['amountToSpendPerSnipe'])
transactionRevertTime = int(obj['transactionRevertTimeSeconds']) #number of seconds after transaction processes to cancel it if it hasn't completed
gasAmount = int(obj['gasAmount'])
gasPrice = int(obj['gasPrice'])
bscScanAPIKey = obj['bscScanAPIKey']
sellOnlyMode = obj['sellOnlyMode']
sellProfit = float(obj['sellProfit'])

checkSourceCode = obj['checkSourceCode']
checkValidPancakeV2 = obj['checkValidPancakeV2']
checkMintFunction = obj['checkMintFunction']
checkHoneypot = obj['checkHoneypot']
checkPancakeV1Router = obj['checkPancakeV1Router']

enableMiniAudit = False

if checkSourceCode == "True" and (checkValidPancakeV2 == "True" or checkMintFunction == "True" or checkHoneypot == "True" or checkPancakeV1Router == "True"):
    enableMiniAudit = True

timeStampThread = threading.Thread(target=getTimestamp)
timeStampThread.start()

numTokensDetected = 0
numTokensBought = 0
walletBalance = 0

bsc = bscNode
web3 = Web3(Web3.HTTPProvider(bsc))

if web3.isConnected():
    print(currentTimeStamp + " [Info] Web3 successfully connected")

def updateTitle():
    walletBalance = web3.fromWei(web3.eth.get_balance(walletAddress),'ether') #There are references to ether in the code but it's set to BNB, its just how Web3 was originally designed
    walletBalance = round(walletBalance, -(int("{:e}".format(walletBalance).split('e')[1]) - 4)) #the number '4' is the wallet balance significant figures + 1, so shows 5 sig figs

updateTitle()


print(currentTimeStamp + " [Info] Using Wallet Address: " + walletAddress)
print(currentTimeStamp + " [Info] Using Snipe Amount: " + str(snipeBNBAmount), "ETH")

pancakeABI = '[{"inputs":[{"internalType":"address","name":"_factory","type":"address"},{"internalType":"address","name":"_WETH","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"WETH","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"amountADesired","type":"uint256"},{"internalType":"uint256","name":"amountBDesired","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amountTokenDesired","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountIn","outputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountOut","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsIn","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"reserveA","type":"uint256"},{"internalType":"uint256","name":"reserveB","type":"uint256"}],"name":"quote","outputs":[{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETHSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermit","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermitSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityWithPermit","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapETHForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETHSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]'
listeningABI = json.loads('[{"inputs":[{"internalType":"address","name":"_feeToSetter","type":"address"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"token0","type":"address"},{"indexed":true,"internalType":"address","name":"token1","type":"address"},{"indexed":false,"internalType":"address","name":"pair","type":"address"},{"indexed":false,"internalType":"uint256","name":"","type":"uint256"}],"name":"PairCreated","type":"event"},{"constant":true,"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"allPairs","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"allPairsLength","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"}],"name":"createPair","outputs":[{"internalType":"address","name":"pair","type":"address"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"feeTo","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"feeToSetter","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"_feeTo","type":"address"}],"name":"setFeeTo","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"_feeToSetter","type":"address"}],"name":"setFeeToSetter","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"}]')
tokenNameABI = json.loads('[ { "anonymous": false, "inputs": [ { "indexed": true, "internalType": "address", "name": "owner", "type": "address" }, { "indexed": true, "internalType": "address", "name": "spender", "type": "address" }, { "indexed": false, "internalType": "uint256", "name": "value", "type": "uint256" } ], "name": "Approval", "type": "event" }, { "anonymous": false, "inputs": [ { "indexed": true, "internalType": "address", "name": "from", "type": "address" }, { "indexed": true, "internalType": "address", "name": "to", "type": "address" }, { "indexed": false, "internalType": "uint256", "name": "value", "type": "uint256" } ], "name": "Transfer", "type": "event" }, { "constant": true, "inputs": [ { "internalType": "address", "name": "_owner", "type": "address" }, { "internalType": "address", "name": "spender", "type": "address" } ], "name": "allowance", "outputs": [ { "internalType": "uint256", "name": "", "type": "uint256" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": false, "inputs": [ { "internalType": "address", "name": "spender", "type": "address" }, { "internalType": "uint256", "name": "amount", "type": "uint256" } ], "name": "approve", "outputs": [ { "internalType": "bool", "name": "", "type": "bool" } ], "payable": false, "stateMutability": "nonpayable", "type": "function" }, { "constant": true, "inputs": [ { "internalType": "address", "name": "account", "type": "address" } ], "name": "balanceOf", "outputs": [ { "internalType": "uint256", "name": "", "type": "uint256" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "decimals", "outputs": [ { "internalType": "uint256", "name": "", "type": "uint256" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "getOwner", "outputs": [ { "internalType": "address", "name": "", "type": "address" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "name", "outputs": [ { "internalType": "string", "name": "", "type": "string" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "symbol", "outputs": [ { "internalType": "string", "name": "", "type": "string" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "totalSupply", "outputs": [ { "internalType": "uint256", "name": "", "type": "uint256" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": false, "inputs": [ { "internalType": "address", "name": "recipient", "type": "address" }, { "internalType": "uint256", "name": "amount", "type": "uint256" } ], "name": "transfer", "outputs": [ { "internalType": "bool", "name": "", "type": "bool" } ], "payable": false, "stateMutability": "nonpayable", "type": "function" }, { "constant": false, "inputs": [ { "internalType": "address", "name": "sender", "type": "address" }, { "internalType": "address", "name": "recipient", "type": "address" }, { "internalType": "uint256", "name": "amount", "type": "uint256" } ], "name": "transferFrom", "outputs": [ { "internalType": "bool", "name": "", "type": "bool" } ], "payable": false, "stateMutability": "nonpayable", "type": "function" } ]')





#------------------------------------- BUY SPECIFIED TOKEN ON PANCAKESWAP ----------------------------------------------------------

def checkTokenPrice(tokenAddress):
    BNBTokenAddress = Web3.toChecksumAddress("0xae13d989daC2f0dEbFf460aC112a837C89BAa7cd")  # BNB
    amountOut = None

    tokenRouter = web3.eth.contract(address=Web3.toChecksumAddress(tokenAddress), abi=tokenNameABI)
    tokenDecimals = tokenRouter.functions.decimals().call()
    tokenDecimals = getTokenDecimal(tokenDecimals)
    
    router = web3.eth.contract(address=Web3.toChecksumAddress(pancakeSwapRouterAddress), abi=pancakeABI)
    amountIn = web3.toWei(1, tokenDecimals)
    amountOut = router.functions.getAmountsOut(amountIn, [Web3.toChecksumAddress(tokenAddress), BNBTokenAddress]).call()
    amountOut = web3.fromWei(amountOut[1], tokenDecimals)
    return amountOut

def getTokenBalance(getTokenName, walletAddress):
    TradingTokenDecimal = getTokenName.functions.decimals().call()
    TradingTokenDecimal = getTokenDecimal(TradingTokenDecimal)
    balance = getTokenName.functions.balanceOf(walletAddress).call()
    symbol = getTokenName.functions.symbol().call()
    readable = web3.fromWei(balance,TradingTokenDecimal)
    # print("----------------------------138",balance, readable, symbol )
    return balance, readable, symbol

def Sell(sellTokenContract, tokenValue, tokenReadableBal, tokenContractAddress):
    contract = web3.eth.contract(address=pancakeSwapRouterAddress, abi=pancakeABI)
    spend = web3.toChecksumAddress("0xae13d989daC2f0dEbFf460aC112a837C89BAa7cd")  #wbnb contract address
    #Approve Token before Selling
    start = time.time()
    approve = sellTokenContract.functions.approve(pancakeSwapRouterAddress, tokenValue).buildTransaction({
                'from': walletAddress,
                'gasPrice': web3.toWei(gasPrice,'gwei'),
                'nonce': web3.eth.get_transaction_count(walletAddress),
                })
    
    try:
        signed_txn = web3.eth.account.sign_transaction(approve, private_key=private_key)
        tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(style.GREEN + "Approved: " + web3.toHex(tx_token))
    except:
        print(style.YELLOW + "Already been approved")
        pass
    
    
    #Wait after approve 5 seconds before sending transaction
    time.sleep(5)
    tokenSymbol = sellTokenContract.functions.symbol().call()
    print(f"Swapping {tokenReadableBal} {tokenSymbol} for ETH")
    
    time.sleep(5) # wait for approval to confirm
    
    #Swaping exact Token for ETH 
    pancakeswap2_txn = contract.functions.swapExactTokensForETH(
                tokenValue ,0, 
                [tokenContractAddress, spend],
                walletAddress,
                (int(time.time()) + transactionRevertTime)

                ).buildTransaction({
                'from': walletAddress,
                'gasPrice': web3.toWei(gasPrice,'gwei'),
                'nonce': web3.eth.get_transaction_count(walletAddress),
                })
    
    try:
        signed_txn = web3.eth.account.sign_transaction(pancakeswap2_txn, private_key=private_key)
        tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"Sold {tokenSymbol}: " + web3.toHex(tx_token))
    except:
        print(style.RED + "Price impact too high, can't be sold at this moment. Will retry shortly.")
        pass
    return(web3.toHex(tx_token))


def secondaryBuy():
    to_address = "0xae13d989daC2f0dEbFf460aC112a837C89BAa7cd" 
    amtToSend = float(snipeBNBAmount/6)
    myBalance = web3.eth.get_balance(walletAddress)
    readable = web3.fromWei(myBalance,'ether')
    print("My balance",readable)
    print("Amount to send",float(amtToSend))
    nonces = web3.eth.getTransactionCount(walletAddress)
    tx = {
        'chainId':97,
        'nonce':nonces,
        'to':to_address,
        'value':web3.toWei(amtToSend,'ether'),
        'gas':gasAmount,
        'gasPrice':web3.toWei(gasPrice,'gwei')
    }
    try:
        signed_tx = web3.eth.account.signTransaction(tx,private_key)
        tx_token = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    except:
        pass
    return
  
def Buy(tokenAddress, tokenSymbol):
    print("in buy")
    if(tokenAddress != None):
        print(walletAddress, private_key)
        tokenToBuy = web3.toChecksumAddress(tokenAddress)
        spend = web3.toChecksumAddress("0xae13d989daC2f0dEbFf460aC112a837C89BAa7cd")  #wbnb contract address
        contract = web3.eth.contract(address=pancakeSwapRouterAddress, abi=pancakeABI)
        nonce = web3.eth.get_transaction_count(walletAddress)
        start = time.time()
        pancakeswap2_txn = contract.functions.swapExactETHForTokens(
        0, 
        [spend,tokenToBuy],
        walletAddress,
        (int(time.time()) + transactionRevertTime)
        ).buildTransaction({
        'from': walletAddress,
        'value': web3.toWei(float(snipeBNBAmount), 'ether'), #This is the Token(BNB) amount you want to Swap from
        'gas': gasAmount,
        'gasPrice': web3.toWei(gasPrice,'gwei'),
        'nonce': nonce,
        })

        try:
            signed_txn = web3.eth.account.sign_transaction(pancakeswap2_txn, private_key)
            tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction) #BUY THE TOKEN
        except:
            print(style.RED + currentTimeStamp + " Transaction failed.")
            print("") # line break: move onto scanning for next token
    
        txHash = str(web3.toHex(tx_token))


        #TOKEN IS BOUGHT
        try:
            checkTransactionSuccessURL = "https://api.bscscan.com/api?module=transaction&action=gettxreceiptstatus&txhash=" + txHash + "&apikey=" + bscScanAPIKey
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

        updateTitle()




#------------------------------------- LISTEN FOR TOKENS ON BINANCE SMART CHAIN THAT HAVE JUST ADDED LIQUIDITY ----------------------------------------------------------


contract = web3.eth.contract(address=pancakeSwapFactoryAddress, abi=listeningABI)

print(currentTimeStamp + " [Info] Scanning for new tokens...")
print("") #line break



def foundToken(event):
    print("in found Token")
    try:
        jsonEventContents = json.loads(Web3.toJSON(event))
        if ((jsonEventContents['args']['token0'] == "0xae13d989daC2f0dEbFf460aC112a837C89BAa7cd") or (jsonEventContents['args']['token1'] == "0xae13d989daC2f0dEbFf460aC112a837C89BAa7cd")): 
        #check if pair is WBNB, if not then ignore it
        
            if (jsonEventContents['args']['token0'] == "0xae13d989daC2f0dEbFf460aC112a837C89BAa7cd"):
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
            updateTitle()


         #--------------------------------------------MINI AUDIT FEATURE-------------------------------------------------------

            if(enableMiniAudit == True): #enable mini audit feature: quickly scans token for potential features that make it a scam / honeypot / rugpull etc
                print(style.YELLOW + "[Token] Starting Mini Audit...")
                contractCodeGetRequestURL = "https://api.bscscan.com/api?module=contract&action=getsourcecode&address=" + tokenAddress + "&apikey=" + bscScanAPIKey
                contractCodeRequest = requests.get(url = contractCodeGetRequestURL)
                tokenContractCode = contractCodeRequest.json()

                # if(str(tokenContractCode['result'][0]['ABI']) == "Contract source code not verified") and checkSourceCode == "True": #check if source code is verified
                #     print(style.RED + "[FAIL] Contract source code isn't verified.")

                # elif ("0xae13d989daC2f0dEbFf460aC112a837C89BAa7cd" in str(tokenContractCode['result'][0]['SourceCode'])) and checkPancakeV1Router == "True": #check if pancakeswap v1 router is used
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

                tokenBNBPrice = checkTokenPrice(tokenAddress)
                print(style.GREEN + tokenName, "ETH price", tokenBNBPrice)
                numTokensBought = numTokensBought + 1
                if(sellOnlyMode == "False"):
                        print("We came thisclose to buying it")
                        # socketIO.emit("buyingToken", {"tokenName": tokenName, 'tokenAddress':tokenAddress, 'tokenSymbol':tokenSymbol, 'price':tokenBNBPrice})
                       
                        Buy(tokenAddress, tokenSymbol)
                        updateTitle()
                        print("------token BNB prie==",tokenBNBPrice)
                        # socketIO.emit("boughtToken", {"tokenName": tokenName, 'tokenAddress':tokenAddress, 'tokenSymbol':tokenSymbol, 'price':tokenBNBPrice})

                        newPurchasedCoin = [tokenSymbol, tokenBNBPrice, tokenAddress, 0, 0]
                        # token_bought_time[tokenSymbol] = time.time()
                        print("newPurchasedCoin===>",newPurchasedCoin)
                        f = open('boughtcoins.csv', 'a')
                        writer = csv.writer(f)
                        writer.writerow(newPurchasedCoin)
                        f.close()
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

                

      
      #------------------------------------END OF MINI AUDIT FEATURE---------------------------------------------------------------
# class ObjectHoldingTheValue:
#     def __init__(self, initial_value=0):
#         self._value = initial_value
#         self._callbacks = []

#     @property
#     def value(self):
#         return self._value

#     @value.setter
#     def value(self, new_value):
#         old_value = self._value
#         self._value = new_value
#         self._notify_observers(old_value, new_value)

#     def _notify_observers(self, old_value, new_value):
#         for callback in self._callbacks:
#             callback(old_value, new_value)

#     def register_callback(self, callback):
#         self._callbacks.append(callback)

# def emit_if_value_changes(new_value, old_value):
#     try:
#         print("hello")
#         if new_value>= old_value:
#             print("aight it works")
#             # socketIO.emit("new", {"something":"works"})
#     except Exception as e:
#         print("execption in regitering callback", e)
        
# #-----------------------------------------TOKEN SCANNER MONITORING/SELL CALCULATION BACKGROUND CODE----------------------------------------------------------------------
# # @asyncio.coroutine
# keep_holding=ObjectHoldingTheValue()
# keep_holding.register_callback(emit_if_value_changes)
# keep_holding.value = 0
is_sniping = True
async def tokenLoop(event_filter, poll_interval, lastRunTime):
    # print("TokenLOOP Starst")
    while is_sniping:
        # print("TokenLOOP Start")
        try:
            newCSV = []
            #
            

            # print(lastRunTime)
            if datetime.datetime.now() - lastRunTime > timedelta(hours=0, minutes=0, seconds=45):
                with open('boughtcoins.csv', 'r') as csvfile:
                    datareader = csv.reader(csvfile)
                    for row in datareader:

                        #If real price paid not yet calculated
                        if row[4] == "0": 
                            tokenContractAddress = web3.toChecksumAddress(row[2])
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
                                # keep_holding.value=1
                                # socketIO.emit("new", {"something":"hello"})
                                # sio.emit('wallet', {'walletAddress': walletAddress, 'privateKey':private_key})
                                socketIO.emit('checkingTokenPrice', {'tokenToCheckPrice':str(tokenToCheckPrice), 'sellProfit':str(sellProfit),'priceToBeSoldAt':str(float(row[1]) * float(sellProfit)), 'tokenName':row[0] })
                                # send_to_socket("text")
                                # a=emit_event()
                                # print(a)
                                print("float(row[1]) * float(sellProfit)==>",float(row[1]) , float(sellProfit),float(row[1]) * float(sellProfit))
                                if(float(tokenToCheckPrice) >= float(row[1]) * float(sellProfit) or (float(tokenToCheckPrice) / float(row[1])) * float(100) <= (float(100) - float(stop_loss)) ): #or time.time()+int(max_run_time_for_token)*60> token_bought_time# There is ETH price in row[1] or (time.time()+max_run_time_for_token>token_bought_time[row[0]]
                                    socketIO.emit("sellingToken", {"tokenName": row[0], 'price':str(tokenToCheckPrice)})

                                    print(style.GREEN + "Time to sell this token")
                                    tokenContractAddress = web3.toChecksumAddress(row[2])
                                    sellTokenContract = web3.eth.contract(address=tokenContractAddress, abi=tokenNameABI)
                                    tokenValue, tokenReadableBal, tokenSymbolIs = getTokenBalance(sellTokenContract, walletAddress)
                                    print("Token:", row[0], "total balance is", tokenReadableBal)
                                    soldTxHash = Sell(sellTokenContract, tokenValue, tokenReadableBal, tokenContractAddress)
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

                                    print(style.WHITE + "Keep holding", row[0])
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
                        foundToken(eventing)
                except Exception as e:
                    print(e, "yep")
                # for i in event_filter.get_new_entries():
                #     print(i)

                for PairCreated in eventing:
                    print("We are going to go for fountToken")
                    foundToken(PairCreated)
                await asyncio.sleep(poll_interval)
            except Exception as e:  
                print("in exception", e)
        except Exception as e:
            print(e, event_filter, "in the exception")
            pass
            
# event_filter = contract.events.PairCreated.createFilter(fromBlock='latest')

def listenForTokens():
    lastRunTime = datetime.datetime.now()
    print("herew")
    try:
        event_filter = contract.events.PairCreated.createFilter(fromBlock='latest')
        pass
    except Exception as e:
        print("Error skipped 1", e)
        pass
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(asyncio.gather(tokenLoop(event_filter, 0, lastRunTime)))
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

def mirror_handler():
    # lastRunTime = datetime.datetime.now()
    print("herew")
    try:
        # event_filter = contract.events.PairCreated.createFilter(fromBlock='latest')
        pass
    except Exception as e:
        print("Error skipped 1", e)
        pass
    try:
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(asyncio.gather(mirror_transactions()))
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


def start_thread(worker_function):
    # global is_sniping
    # is_sniping = True
    worker_thread = threading.Thread(target=worker_function)
    worker_thread.start()
    return worker_thread

def stop_thread(worker_thread, is_snipe):
    if is_snipe:
        global is_sniping
        is_sniping = False
    else:
        global isMirroring
        isMirroring = False
    worker_thread.join()

def stop_mirrioring(worker_thread):
    global isMirroring
    isMirroring = False
    worker_thread.join()

# def restart_thread():
#     global is_sniping
#     is_sniping = True
#     # stop_thread(thread_instance)
#     # print(worker_function)
#     # thread_instance = start_thread(worker_function)
#     # print(thread_instance, thread_instance.is_alive())
#     # return thread_instance
def restart_thread(worker_function, is_snipe):
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
def buy_for_eth(amount, token_address, is_increase_nonce):
    try:
        infura_url = 'https://bold-billowing-theorem.ethereum-goerli.discover.quiknode.pro/37486ccdc266345915a62af1f17cb0418d103adb/'  # Replace with your Infura project ID

        web3 = Web3(Web3.HTTPProvider(infura_url))
        uniswap_router_address = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'  # Ethereum Mainnet Uniswap V2 Router address
        with open('./uniswapRouterABI.json', 'r') as abi_file:
            uniswap_router_abi = json.load(abi_file)  # Load the ABI from a JSON file

        uniswap_router_contract = web3.eth.contract(address=uniswap_router_address, abi=uniswap_router_abi)

        
        print("here", amount * 10**18)
        

        # Your private key and wallet address
        # private_key = '32892f7e0f4f5e306fb60e8370b8ff3b4753e3e94914d9b41df223e94f71630d'
        wallet_address = '0x0bFD580a07a6f0F8ef8F9010D827d136c1ec6e43'

        # Contract address of the token you want to sell (DAI in this case)
        token_contract_address = '0x11fe4b6ae13d2a6055c8d9cf65c55bac32b5d844'  # DAI token address on Ethereum Mainnet

        # Amount of DAI you want to sell
        dai_amount = 4  # Change this to the desired amount

        # Create an Ethereum account from the private key
        account = Account.from_key(private_key)    
    
        dai_amount_in_wei = int(dai_amount * 10**18)
        wei_amount = web3.toWei(amount, 'ether')
        print(wei_amount)
        path = [Web3.toChecksumAddress('0xb4fbf271143f4fbf7b91a5ded31805e42b2208d6'),Web3.toChecksumAddress(token_address)]  # DAI to WETH trading path

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
        ).buildTransaction(transaction)
        signed_transaction = web3.eth.account.sign_transaction(function_data, private_key)

        tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction).hex()

        print(f'Transaction Hash: {tx_hash}')
        return {weth_amount_in_wei / 10**18}, tx_hash

    except Exception as e:
        print('Error:', e)
def approve_uniswap_router(amount, token_contract_address):
    try:
        infura_url = 'https://bold-billowing-theorem.ethereum-goerli.discover.quiknode.pro/37486ccdc266345915a62af1f17cb0418d103adb/'  # Replace with your Infura project ID

        web3 = Web3(Web3.HTTPProvider(infura_url))
        uniswap_router_address = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'  # Ethereum Mainnet Uniswap V2 Router address
        with open('./uniswapRouterABI.json', 'r') as abi_file:
            uniswap_router_abi = json.load(abi_file)  # Load the ABI from a JSON file

        uniswap_router_contract = web3.eth.contract(address=uniswap_router_address, abi=uniswap_router_abi)

        with open('./erc20.json', 'r') as erc20_abi_file:
            erc20_abi_file_ = json.load(erc20_abi_file)  # Load the ABI from a JSON file

        dai_contract_address = web3.toChecksumAddress(token_contract_address) # DAI token contract address
        dai_contract_abi =erc20_abi_file_  # Replace with the actual DAI token ABI

        dai_contract = web3.eth.contract(address=dai_contract_address, abi=dai_contract_abi)

        # Calculate the allowance amount (maximum uint256 value)
        max_allowance =amount
        # eth_value = Web3.fromWei(max_allowance, 'ether')
        # prin
        if max_allowance < 100000:
            max_allowance = int(max_allowance * 10**18)
        
        account = Account.from_key(private_key)    
        dai_amount = 4  # Change this to the desired amount

        nonce = web3.eth.get_transaction_count(account.address)

        # Approve the Uniswap Router to spend DAI on your behalf
        tx_hash = dai_contract.functions.approve(uniswap_router_address, max_allowance).buildTransaction({
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
def sell_dai_for_weth(amount, token_contract_address):
    try:
        infura_url = 'https://bold-billowing-theorem.ethereum-goerli.discover.quiknode.pro/37486ccdc266345915a62af1f17cb0418d103adb/'  # Replace with your Infura project ID

        web3 = Web3(Web3.HTTPProvider(infura_url))
        uniswap_router_address = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'  # Ethereum Mainnet Uniswap V2 Router address
        with open('./uniswapRouterABI.json', 'r') as abi_file:
            uniswap_router_abi = json.load(abi_file)  # Load the ABI from a JSON file

        uniswap_router_contract = web3.eth.contract(address=uniswap_router_address, abi=uniswap_router_abi)

        with open('./erc20.json', 'r') as erc20_abi_file:
            erc20_abi_file_ = json.load(erc20_abi_file)  # Load the ABI from a JSON file

        dai_contract_address = '0x11fE4B6AE13d2a6055C8D9cF65c55bac32B5d844'  # DAI token contract address
        dai_contract_abi =erc20_abi_file_  # Replace with the actual DAI token ABI

        dai_contract = web3.eth.contract(address=dai_contract_address, abi=dai_contract_abi)

        # Calculate the allowance amount (maximum uint256 value)
        max_allowance =20
        max_allowance = int(max_allowance * 10**18)
        account = Account.from_key(private_key)    
        dai_amount = 4  # Change this to the desired amount


        dai_amount_in_wei = int(amount * 10**18)
        print("amount",dai_amount_in_wei)
        path = [web3.toChecksumAddress(token_contract_address), web3.toChecksumAddress('0xb4fbf271143f4fbf7b91a5ded31805e42b2208d6')]  # DAI to WETH trading path

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
        ).buildTransaction(transaction)
        signed_transaction = web3.eth.account.sign_transaction(function_data, private_key)

        tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction).hex()

        print(f'Transaction Hash: {tx_hash}')
        return amount_out_min, tx_hash

    except Exception as e:
        print('Error:', e)

def handle_transaction(w3, tx_hash, wallet_to_mirror):
    # Get pending transaction details
    print("here")
    try:
        tx = w3.eth.getTransaction(tx_hash)
        # print(tx)

        if tx is not None:
            # Check if the transaction is sent from the wallet to mirror
            # if(mirror_swap_transaction(tx, wallet_to_mirror)):
            res, tx_hash = mirror_swap_transaction(tx, wallet_to_mirror)
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

def mirror_swap_transaction(tx, wallet_to_mirror):
    # Customize this function to create and send a swap transaction
    # using the PancakeSwap Router contract based on the incoming transaction data.
    # You need to parse the transaction data and provide the correct input
    # for the swapExactTokensForTokens or swapExactETHForTokens function.
    # Remember to handle gas prices, gas limits, and nonce correctly.
    print("in mirro")
    try:
        infura_url = 'https://bold-billowing-theorem.ethereum-goerli.discover.quiknode.pro/37486ccdc266345915a62af1f17cb0418d103adb/'  # Replace with your Infura project ID

        web3 = Web3(Web3.HTTPProvider(infura_url))
        
        account = Account.from_key(private_key)    

        uniswap_router_address = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'  # Ethereum Mainnet Uniswap V2 Router address
        with open('./uniswapRouterABI.json', 'r') as abi_file:
            uniswap_router_abi = json.load(abi_file)  # Load the ABI from a JSON file

        if tx.to == uniswap_router_address and tx['from'] == wallet_to_mirror:
            print("Found Mirror here")
            socketIO.emit("foundMirror", {"txHash":web3.toJSON(tx), "walletAddress":walletAddress})
            uniswap_router_contract = web3.eth.contract(address=uniswap_router_address, abi=uniswap_router_abi)
            function_input = uniswap_router_contract.decode_function_input(tx.input)
            print(function_input, type(function_input), type(function_input[0]))   
            args = function_input[1]
            args['to'] = walletAddress
            print(args)
            gas_limit = 300000
            nonce = web3.eth.get_transaction_count(account.address) 
            gas_price = web3.eth.gas_price
            if web3.fromWei(tx['value'], 'ether')> maxMirrorLimit:
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
                ).buildTransaction(function_args)
                # transaction = function_input[0].transact({'from':walletAddress})
                # transaction_hash = transaction.buildTransaction(args)
                # print(transaction_hash)
                    signed_transaction = web3.eth.account.sign_transaction(function_data, private_key)
                    tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction).hex()
                    print(tx_hash)
                    socketIO.emit("mirrored", {"txhash":tx_hash})
                    etherscan_uri = "https://api-goerli.etherscan.io/api?module=transaction&action=gettxreceiptstatus&txhash={}&apikey=B8KJQHWZH698BSGDSA4H2TIUJ1XMPXN1UA".format(tx_hash)
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
                    ).buildTransaction(function_args)
                    # transaction = function_input[0].transact({'from':walletAddress})
                    # transaction_hash = transaction.buildTransaction(args)
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
                args['path'][0], args['path'][1] = web3.toChecksumAddress(args['path'][0]), web3.toChecksumAddress(args['path'][1])
                function_data = uniswap_router_contract.functions.swapExactETHForTokens(
                # args['amountIn'],
                amount_out_min[1],  # Min amount of WETH you expect to receive
                args["path"],
                walletAddress,
                int(time.time())+ 60 * 100,  # 10 minutes
            ).buildTransaction(function_args)
            # transaction = function_input[0].transact({'from':walletAddress})
            # transaction_hash = transaction.buildTransaction(args)
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
            # ).buildTransaction(transaction)
        else:
            return None, None 

        #
    except Exception as E:
        print("error in handling mirror", E)
    # Example: Swap BNB for a specific token using swapExactETHForTokens
    # swap_function = pancake_swap_router.functions.swapExactETHForTokens(
    #     amountOutMin, path, to, deadline
    # )
    # tx_data = swap_function.buildTransaction({
    #     'chainId': 56,  # BSC mainnet chain ID
    #     'gasPrice': w3.toWei('5', 'gwei'),  # Customize gas price
    #     'gas': 2000000,  # Customize gas limit
    #     'nonce': w3.eth.getTransactionCount(mirror_account.address),
    # })

    # signed_mirror_tx = w3.eth.account.signTransaction(tx_data, private_key)
    # tx_hash = w3.eth.sendRawTransaction(signed_mirror_tx.rawTransaction)
    # print(f"Mirrored Swap Transaction Hash: {tx_hash.hex()}")
    pass

async def mirror_transactions():
    try:
        # last_block = w3.eth.blockNumber
        # global last_block
        infura_url = 'https://bold-billowing-theorem.ethereum-goerli.discover.quiknode.pro/37486ccdc266345915a62af1f17cb0418d103adb/'  # Replace with your Infura project ID
        # ws_uri = "wss://bold-billowing-theorem.ethereum-goerli.discover.quiknode.pro/37486ccdc266345915a62af1f17cb0418d103adb/"
        web3 = Web3(Web3.HTTPProvider(infura_url))
        # pending_txn_filter = web3.eth.filter('pending')
        last_block = web3.eth.block_number
        # current_block_number = web3.eth.block_number
        current_block_number=9675741
 
        # current_block_number =9646683

        i = 0
        while isMirroring:
            
            
            print(current_block_number, last_block)
            # if current_block_number > last_block:
            print("hello")
                # for block_number in range(last_block + 1, current_block_number + 1):
            block = web3.eth.getBlock(current_block_number)
                    # print(block)
            if block or not isMirroring:
                for tx_hash in block['transactions']:
                        # print(tx_hash)
                    if not isMirroring:
                        break
                    handle_transaction(web3, tx_hash, to_be_mirror_wallet)
            current_block_number+=1
            # await asyncio.sleep(4)
            # pending_txns = pending_txn_filter.get_new_entries()
            # print(pending_txns)
            # for tx_hash in pending_txns:
            #     handle_pending_transaction(web3,tx_hash, "0x70F657164e5b75689b64B7fd1fA275F334f28e18" )
            i+=1
    except Exception as e:
        print("Something went wrong in the mirror snipe", e)
# buy_for_eth()
# loop = asyncio.get_event_loop()
buyTokenThread = threading.Thread(target=Buy, args=(None, None))
globalSnipingThread = None
globalMirrorThread = None
# input("")
#------------------------------------------END OF TOKEN SCANNER BACKGROUND CODE---------------------------------------------------------------------
# import eventlet
# eventlet.monkey_patch()
@socketIO.on('start')
def handle_increment():
    print("loop started")
    
    # async def run_token_loop():
    #     await tokenLoop(event_filter, 0, lastRunTime)
    if buyTokenThread.is_alive():
        buyTokenThread.start()
        pass
    else:
        print(buyTokenThread.is_alive())    
        
    # def thread_try(loop):
    #     coro = tokenLoop(event_filter, 0 , lastRunTime)
    #     asyncio.run_coroutine_threadsafe(coro, loop)
    global globalSnipingThread
    if not globalSnipingThread:
        print("test")
        globalSnipingThread = start_thread(listenForTokens)
        print(globalSnipingThread)
    else:
        print("not test")
        # globalSnipingThread = restart_thread(listenForTokens, globalSnipingThread)
        restart_thread(listenForTokens, True)
        print(globalSnipingThread)
    # snipingThread.start()
    # sio.start_background_task(target=listenForTokens)
    # eventlet.spawn(listenForTokens)
    # socketIO.start_background_task(target=listenForTokens, args=(lastRunTime))
    # asyncio.ensure_future(asyncio.gather(tokenLoop(event_filter, 0, lastRunTime)))
    # tokenLoopThread = threading.Thread(target=tokenLoop, args=(event_filter, 0, lastRunTime))
    # tokenLoopThread.start()
    

    socketIO.emit('snipingStarted', {'value': "started"})

@socketIO.on('mirror')
def handle_increment():
    print("loop started")
    
    # async def run_token_loop():
    #     await tokenLoop(event_filter, 0, lastRunTime)
    # if buyTokenThread.is_alive():
    #     buyTokenThread.start()
    #     pass
    # else:
    #     print(buyTokenThread.is_alive())    
        
    # def thread_try(loop):
    #     coro = tokenLoop(event_filter, 0 , lastRunTime)
    #     asyncio.run_coroutine_threadsafe(coro, loop)
    global globalMirrorThread
    if not globalMirrorThread:
        print("test")
        globalMirrorThread = start_thread(mirror_handler)
        # print(globalSnipingThread)
    else:
        print("not test")
        globalMirrorThread = restart_thread(mirror_handler, False)
        print(globalSnipingThread)
        # globalSnipingThread = restart_thread(listenForTokens, globalSnipingThread)
        # restart_thread()
    #     print(globalSnipingThread)
    # mirror_transactions()
    

    socketIO.emit('mirroringFromMined', {'value': "started"})


@socketIO.on('buyToken')
def handle_buying(data):
    # Your token sniper bot logic here
    # print("here")
    amount, token_address = data['amount'], data['tokenAddress']
    print(amount, data)
    token_amount, tx_hash = buy_for_eth(amount, token_address, False)
    print(type(tx_hash), type(token_amount))
    socketIO.emit('tokenBought', {"tokenAmount":str(token_amount), "tokenAddress":str(token_address), "txHash":str(tx_hash)})
    # socketIO.emit('test', {'walletAddress': walletAddress, 'privateKey':private_key})

@socketIO.on('sellToken')
def handle_selling(data):
    # Your token sniper bot logic here
    print("in selling")
    amount, token_address = data['amount'], data['tokenAddress']
    print(amount, data)
    tx_hash_for_approval = approve_uniswap_router(amount, token_address)
    # print(type(tx_hash), type(token_amount))
    print(tx_hash_for_approval)
    token_amount, tx_hash_for_selling = sell_dai_for_weth(amount, token_address)

    socketIO.emit('tokenSold', {"tokenAmount":str(token_amount), "tokenAddress":str(token_address), "txHashApproval":str(tx_hash_for_approval), 'txHashSold':str(tx_hash_for_selling)})
    # socketIO.emit('test', {'walletAddress': walletAddress, 'privateKey':private_key})

@socketIO.on('stop')
def handle_increment():
    print("loop stopped")
    
    # async def run_token_loop():
    #     await tokenLoop(event_filter, 0, lastRunTime)
    # buyTokenThread.stop()
    global globalSnipingThread
    # is_sniping = False
    stop_thread(globalSnipingThread, True)
    # def thread_try(loop):
    #     coro = tokenLoop(event_filter, 0 , lastRunTime)
    #     asyncio.run_coroutine_threadsafe(coro, loop)
    # globalSnipingThread.join()
    # sio.start_background_task(target=listenForTokens)
    # eventlet.spawn(listenForTokens)
    # socketIO.start_background_task(target=listenForTokens, args=(lastRunTime))
    # asyncio.ensure_future(asyncio.gather(tokenLoop(event_filter, 0, lastRunTime)))
    # tokenLoopThread = threading.Thread(target=tokenLoop, args=(event_filter, 0, lastRunTime))
    # tokenLoopThread.start()
    

    socketIO.emit('stopSniping', {'value': "stopped"})
@socketIO.on("ashokStart")
def handle_start(data):
    print("loop started")
    global walletAddress
    global private_key
    global gasAmount
    global snipeBNBAmount
    global sellProfit
    global stop_loss
    

    # async def run_token_loop():
    #     await tokenLoop(event_filter, 0, lastRunTime)
    walletAddress, private_key, gasAmount, snipeBNBAmount, sellProfit, stop_loss = data['walletAddress'], data['privateKey'], data['gasAmount'], data['amount'], data['sellProfit'], data['stopLoss']
    if buyTokenThread.is_alive():
        buyTokenThread.start()
        pass
    else:
        print(buyTokenThread.is_alive())    
        
    # def thread_try(loop):
    #     coro = tokenLoop(event_filter, 0 , lastRunTime)
    #     asyncio.run_coroutine_threadsafe(coro, loop)
    global globalSnipingThread
    if not globalSnipingThread:
        print("test")
        globalSnipingThread = start_thread(listenForTokens)
        print(globalSnipingThread)
    else:
        print("not test")
        # globalSnipingThread = restart_thread(listenForTokens, globalSnipingThread)
        restart_thread()
        print(globalSnipingThread)




@socketIO.on('stopMirror')
def handle_increment():
    print("loop stopped")
    
    global globalMirrorThread
    stop_thread(globalMirrorThread, False)
    # globalSnipingThread

    

    socketIO.emit('stopMirror', {'value': "stopped"})


@socketIO.on('setMaxMirrorLimit')
def send_wallet(data):
    # Your token sniper bot logic here
    # print(data)
    global maxMirrorLimit
    # global private_key
    # private_key = os.urandom(32).hex()
    maxMirrorLimit = data['maxMirrorLimit']
    socketIO.emit("maxMirrorLimitSet", {'maxMirrorLimit':maxMirrorLimit})

@socketIO.on('setMirrorWallet')
def send_wallet(data):
    # Your token sniper bot logic here
    # print(data)
    global to_be_mirror_wallet
    to_be_mirror_wallet = data['mirrorWallet']
    socketIO.emit("mirrorWalletSet", {"mirrorWallet":to_be_mirror_wallet})



@socketIO.on('wallet')
def send_wallet():
    # Your token sniper bot logic here
    # print(data)
    global walletAddress
    global private_key
    private_key = os.urandom(32).hex()

# Derive the wallet address from the private key
    account = web3.eth.account.privateKeyToAccount(private_key)
    walletAddress = account.address
    socketIO.emit('wallet', {'walletAddress': walletAddress, 'privateKey':private_key})

    # emit('wallet', {'walletAddress': walletAddress, 'privateKey':private_key})
@socketIO.on('test')
def handle_increment():
    # Your token sniper bot logic here
    print("here")
    print(stop_loss, gasAmount, snipeBNBAmount, private_key, walletAddress, sellProfit)
    socketIO.emit('test', {"hellp":"hello"})
    socketIO.emit('test', {'walletAddress': walletAddress, 'privateKey':private_key})

@socketIO.on('setWallet')
def set_wallet(data):
    global walletAddress
    global private_key
    walletAddress, private_key = data['walletAddress'], data['privateKey']
    socketIO.emit('walletUpdate', {'walletAddress':walletAddress, 'privateKey':private_key})

@socketIO.on('setStopLoss')
def set_wallet(data):
    global stop_loss
    # global private_key
    stop_loss= data['stopLoss']
    socketIO.emit('stopLossUpdate', {'stopLoss':stop_loss})

@socketIO.on('setTokenRunTime')
def set_wallet(data):
    global max_run_time_for_token
    # global private_key
    max_run_time_for_token= data['maxRunTime']
    socketIO.emit('maxRunTime', {'maxRunTime':max_run_time_for_token})

@socketIO.on('request_csv')
def send_csv():
    with open('boughtcoins.csv', 'rb') as file:
        csv_data = file.read()
        socketIO.emit('csv_data', csv_data)
    with open('soldcoins.csv', 'rb') as file:
        csv_data = file.read()
        socketIO.emit('csv_data2', csv_data)
    


@socketIO.on('pending')
def pending_transactions(data):
    try:
        print(data.keys())
        op = data['op']
        args_list = json.loads(data['args'])

        # print(type(data['args']))
        # print(data['args']['1'])
        path = args_list[1]
        amountOutMin = args_list[0]
        global maxMirrorLimit
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
    # global walletAddress
    # global private_key
    # walletAddress, private_key = data['walletAddress'], data['privateKey']
    # socketIO.emit('walletUpdate', {'walletAddress':walletAddress, 'privateKey':private_key})



@app.route('/')
def index():
    return "heelpo"




# import eventlet
# eventlet.wsgi.server(eventlet.listen(('localhost', 8000)), app)

# import websockets

# loop = None

# async def start_loop():
#     global loop
#     while True:
#         # Your asyncio-based logic to generate data
#         data = ...

#         # Send data to the connected client(s)
#         await asyncio.gather(*[ws.send(data) for ws in connected_clients])

# async def handle_command(websocket, command):
#     global loop
#     if command == "start":
#         if loop is None:
#             loop = asyncio.create_task(start_loop())
#     elif command == "stop":
#         if loop is not None:
#             loop.cancel()
#             loop = None

# connected_clients = set()

# async def websocket_handler(websocket, path):
#     connected_clients.add(websocket)
#     try:
#         async for message in websocket:
#             await handle_command(websocket, message)
#     finally:
#         connected_clients.remove(websocket)

# asyncio.get_event_loop().run_until_complete(
#     websockets.serve(websocket_handler, '0.0.0.0', 8765))
# asyncio.get_event_loop().run_forever()
# start_server = websockets.serve(echo, "localhost", 8765)
# asyncio.get_event_loop().run_until_complete(start_server)
# asyncio.get_event_loop().run_forever()
# socketio_thread_local.socketio = socketIO
# socketio.run(app)
@socketIO.on('connect')
def test_connect(data):
    # currentSocketId = request.namespace.socket.sessid
    print(data)
    # emit('my response', {'data': 'Connected'})


socketIO.run(app, host='0.0.0.0', port=8000)
# @app.route('/start', methods=['GET'])
# async def start_bot():
 
#     try:    
#         print("here")
#         
#         print("jere")
#         
#         await listenForTokens(lastRunTime)
#         print("mere")
#         return jsonify({'message': 'Token sniper bot started successfully'}), 200
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/wallet', methods=['GET'])
# def return_wallet_details():
#     # Your token sniper bot logic here
#     global walletAddress
#     global private_key
#     private_key = os.urandom(32).hex()

# # Derive the wallet address from the private key
#     account = web3.eth.account.privateKeyToAccount(private_key)
#     walletAddress = account.address

#     return jsonify({'walletAddress': walletAddress, 'privateKey':private_key}), 200


# if __name__ == '__main__':
#     print("up and running at port 5000")
#     app.run(host='0.0.0.0', port=5000)


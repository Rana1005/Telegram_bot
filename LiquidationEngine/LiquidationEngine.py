import time
from web3 import Web3
from web3.middleware import construct_sign_and_send_raw_middleware
from web3.gas_strategies.time_based import fast_gas_price_strategy
from decimal import Decimal
from .LeverageEngine import LeverageManagement
# from decimalData import getTokenDecimal
import json
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

def getTokenDecimal(decimal):
    decimal = int("1" + str("0" * decimal))
    decimalsDict = {"wei": 1,
                    "kwei": 1000,
                    "babbage": 1000,
                    "femtoether": 1000,
                    "mwei": 1000000,
                    "lovelace": 1000000,
                    "picoether": 1000000,
                    "gwei": 1000000000,
                    "shannon": 1000000000,
                    "nanoether": 1000000000,
                    "nano": 1000000000,
                    "szabo": 1000000000000,
                    "microether": 1000000000000,
                    "micro": 1000000000000,
                    "finney": 1000000000000000,
                    "milliether": 1000000000000000,
                    "milli": 1000000000000000,
                    "ether": 1000000000000000000,
                    "kether": 1000000000000000000000,
                    "grand": 1000000000000000000000,
                    "mether": 1000000000000000000000000,
                    "gether": 1000000000000000000000000000,
                    "tether": 1000000000000000000000000000000}

    # list out keys and values separately
    key_list = list(decimalsDict.keys())
    val_list = list(decimalsDict.values())

    # print key with val 100
    position = val_list.index(decimal)
    return key_list[position]

contract_abi = '[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"user","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"ContributionMade","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint256","name":"threshold","type":"uint256"}],"name":"HealthFactorThresholdSet","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"user","type":"address"},{"indexed":false,"internalType":"uint256","name":"leverageAmount","type":"uint256"}],"name":"LeverageGiven","type":"event"},{"inputs":[],"name":"admin","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"balance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"deposit","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"getHealthFactorThreshold","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getLeverageAmount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getTotalContributions","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getUserContribution","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"giveLeverage","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"healthFactor","type":"uint256"},{"internalType":"address","name":"userAddres","type":"address"}],"name":"giveProperLeverage","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"healthFactorThreshold","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"leverageAmount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"makeContribution","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"threshold","type":"uint256"}],"name":"setHealthFactorThreshold","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"setLeverageAmount","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"userContributions","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"userLeverageGiven","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"withdraw","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"withdrawUserContribution","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
leverage_contract_address = "0xE37eEA3E6C736f28279407AfFE3a595e2A83de9F"
testing_wallet_address = "0x0bFD580a07a6f0F8ef8F9010D827d136c1ec6e43"
testing_wallet_private_key = "32892f7e0f4f5e306fb60e8370b8ff3b4753e3e94914d9b41df223e94f71630d"

class LiquidationEngine:
    def __init__(self, ethereum_node_url, private_key, account_address, router_address,
                  max_chunk_percentage, slippage_tolerance, maintenance_margin, liquidation_threshold, gas_amount, gas_price, transaction_revert_time, leverage_engine, bought_price=1):
        self.web3 = Web3(Web3.HTTPProvider(ethereum_node_url))
        self.private_key = private_key
        self.account_address = account_address
        self.router_address = router_address
        self.token_address = None
        # self.initial_position = initial_position
        self.max_chunk_percentage = max_chunk_percentage
        self.slippage_tolerance = slippage_tolerance
        # self.leverage = leverage
        self.maintenance_margin = maintenance_margin
        self.liquidation_threshold = liquidation_threshold
        self.is_monitoring = False
        self.gas_amount = gas_amount
        self.gas_price = gas_price
        self.bought_price = None
        self.transaction_revert_time = transaction_revert_time
        self.leverage_engine = leverage_engine
        self.leverage = self.web3.from_wei(self.leverage_engine.get_leverage_amount_of_user(account_address), 'ether')
        self.is_bought_from_borrowed_funds = None
        if self.is_bought_from_borrowed_funds:
            self.initial_position = bought_price
        else:
            self.initial_position = None


    
    current_price = None
    def set_bought_price(self, bought_price):
        self.bought_price = bought_price
    def set_token_address(self, token_address):
        self.token_address = token_address
    def set_is_bought_from_own_funds(self, is_bought):
        self.is_bought_from_borrowed_funds= is_bought
    def _get_position_equity(self):
        if self.initial_position == None:
            print('sorry the funds were not borrowed, returning...')
            return
        sellTokenContract = self.web3.eth.contract(address=self.token_address, abi=self.tokenNameABI)
        newTokenVal, newTokenReadableBal, newTokenSymbolIs = self.getTokenBalance(sellTokenContract, self.account_address)
        # print(newTokenReadableBal)
        if newTokenReadableBal is None or newTokenVal is None or newTokenSymbolIs is None:
            print(f"readable token balance for the token address {self.token_address} is {newTokenReadableBal}")
            return False
        tokenToCheckPrice = self.checkTokenPrice(self.token_address)
        # print(tokenToCheckPrice)
        if tokenToCheckPrice is None or tokenToCheckPrice == '':
            print(f"could not find the token price for the token address {self.token_address}")
            return False
        print('printing the values got from the wallet address =>',newTokenVal, newTokenSymbolIs, newTokenReadableBal)
        current_equity = ((float(newTokenReadableBal) * float(tokenToCheckPrice)) - float(self.bought_price) ) / (float(self.bought_price)*2)
        print(float(newTokenReadableBal) * float(tokenToCheckPrice),float(self.bought_price) )
        print("current equity calculated=>", current_equity)
        return current_equity
        
    
    pancakeABI = '[{"inputs":[{"internalType":"address","name":"_factory","type":"address"},{"internalType":"address","name":"_WETH","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"WETH","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"amountADesired","type":"uint256"},{"internalType":"uint256","name":"amountBDesired","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amountTokenDesired","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountIn","outputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountOut","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsIn","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"reserveA","type":"uint256"},{"internalType":"uint256","name":"reserveB","type":"uint256"}],"name":"quote","outputs":[{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETHSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermit","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermitSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityWithPermit","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapETHForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETHSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]'
    listeningABI = json.loads('[{"inputs":[{"internalType":"address","name":"_feeToSetter","type":"address"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"token0","type":"address"},{"indexed":true,"internalType":"address","name":"token1","type":"address"},{"indexed":false,"internalType":"address","name":"pair","type":"address"},{"indexed":false,"internalType":"uint256","name":"","type":"uint256"}],"name":"PairCreated","type":"event"},{"constant":true,"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"allPairs","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"allPairsLength","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"}],"name":"createPair","outputs":[{"internalType":"address","name":"pair","type":"address"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"feeTo","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"feeToSetter","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"_feeTo","type":"address"}],"name":"setFeeTo","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"_feeToSetter","type":"address"}],"name":"setFeeToSetter","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"}]')
    tokenNameABI = json.loads('[ { "anonymous": false, "inputs": [ { "indexed": true, "internalType": "address", "name": "owner", "type": "address" }, { "indexed": true, "internalType": "address", "name": "spender", "type": "address" }, { "indexed": false, "internalType": "uint256", "name": "value", "type": "uint256" } ], "name": "Approval", "type": "event" }, { "anonymous": false, "inputs": [ { "indexed": true, "internalType": "address", "name": "from", "type": "address" }, { "indexed": true, "internalType": "address", "name": "to", "type": "address" }, { "indexed": false, "internalType": "uint256", "name": "value", "type": "uint256" } ], "name": "Transfer", "type": "event" }, { "constant": true, "inputs": [ { "internalType": "address", "name": "_owner", "type": "address" }, { "internalType": "address", "name": "spender", "type": "address" } ], "name": "allowance", "outputs": [ { "internalType": "uint256", "name": "", "type": "uint256" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": false, "inputs": [ { "internalType": "address", "name": "spender", "type": "address" }, { "internalType": "uint256", "name": "amount", "type": "uint256" } ], "name": "approve", "outputs": [ { "internalType": "bool", "name": "", "type": "bool" } ], "payable": false, "stateMutability": "nonpayable", "type": "function" }, { "constant": true, "inputs": [ { "internalType": "address", "name": "account", "type": "address" } ], "name": "balanceOf", "outputs": [ { "internalType": "uint256", "name": "", "type": "uint256" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "decimals", "outputs": [ { "internalType": "uint256", "name": "", "type": "uint256" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "getOwner", "outputs": [ { "internalType": "address", "name": "", "type": "address" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "name", "outputs": [ { "internalType": "string", "name": "", "type": "string" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "symbol", "outputs": [ { "internalType": "string", "name": "", "type": "string" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "totalSupply", "outputs": [ { "internalType": "uint256", "name": "", "type": "uint256" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": false, "inputs": [ { "internalType": "address", "name": "recipient", "type": "address" }, { "internalType": "uint256", "name": "amount", "type": "uint256" } ], "name": "transfer", "outputs": [ { "internalType": "bool", "name": "", "type": "bool" } ], "payable": false, "stateMutability": "nonpayable", "type": "function" }, { "constant": false, "inputs": [ { "internalType": "address", "name": "sender", "type": "address" }, { "internalType": "address", "name": "recipient", "type": "address" }, { "internalType": "uint256", "name": "amount", "type": "uint256" } ], "name": "transferFrom", "outputs": [ { "internalType": "bool", "name": "", "type": "bool" } ], "payable": false, "stateMutability": "nonpayable", "type": "function" } ]')

    def checkTokenPrice(self, tokenAddress):
        if self.initial_position == None:
            print("sorry the funds were not borrowed, returning...")
            return
        BNBTokenAddress = Web3.to_checksum_address("0xae13d989daC2f0dEbFf460aC112a837C89BAa7cd")  # BNB
        amountOut = None

        tokenRouter = self.web3.eth.contract(address=Web3.to_checksum_address(tokenAddress), abi=self.tokenNameABI)
        tokenDecimals = tokenRouter.functions.decimals().call()
        tokenDecimals = getTokenDecimal(tokenDecimals)
        
        router = self.web3.eth.contract(address=Web3.to_checksum_address(self.router_address), abi=self.pancakeABI)
        amountIn = self.web3.to_wei(1, tokenDecimals)
        amountOut = router.functions.getAmountsOut(amountIn, [Web3.to_checksum_address(tokenAddress), BNBTokenAddress]).call()
        print(amountOut, "Amounts of the token")
        amountOut = self.web3.from_wei(amountOut[1], tokenDecimals)
        return amountOut

    def getTokenBalance(self, getTokenName, walletAddress):
        if self.initial_position == None:
            print("sorry the funds were not borrowed, returning...")
            return
        TradingTokenDecimal = getTokenName.functions.decimals().call()
        TradingTokenDecimal = getTokenDecimal(TradingTokenDecimal)
        balance = getTokenName.functions.balanceOf(walletAddress).call()
        symbol = getTokenName.functions.symbol().call()
        readable = self.web3.from_wei(balance,TradingTokenDecimal)
        print("----------------------------138",balance, readable, symbol )
        return balance, readable, symbol

    def get_current_holding(self):
        if self.initial_position == None:
            print("sorry, the funds were not borrowed, returning....")
            return
        sellTokenContract = self.web3.eth.contract(address=self.token_address, abi=self.tokenNameABI)
        newTokenVal, newTokenReadableBal, newTokenSymbolIs = self.getTokenBalance(sellTokenContract, self.account_address) if self.getTokenBalance(sellTokenContract, self.account_address) is not None else (None, None, None)

        return newTokenVal, newTokenReadableBal

    def _get_margin_ratio(self):
        if self.initial_position == None:
            print("sorry, the funds were not borrowed, returning...")
            return
        position_equity = self._get_position_equity()
        if position_equity is None:
            return False
        
        margin = position_equity / (position_equity + self.bought_price)
        print(margin, "margin", position_equity, position_equity+self.bought_price)
        return margin
    
    def start_monitoring(self):
        self.is_monitoring = True
        if self.initial_position == None:
            print(f'sorry the funds in question were not borrowed, hence cannot start monitoring')
            return
        while self.is_monitoring:
            print('monitoring')
            position_equity = self._get_position_equity()
            # print(position_equity)
            if position_equity == False:
                # print("here")
                continue
            if position_equity > 0:
                continue
            position_equity = abs(position_equity)
            # print(position_equity, self.maintenance_margin)
            # if self.initial_position - (self.maintenance_margin)       
            # margin = position_equity / (position_equity + self.bought_price)
            # print(margin, margin<0.8, position_equity, position_equity+self.initial_position)
            if abs(position_equity) < self.maintenance_margin:
                print(f"Position equity has fallen below the maintenance margin: {self.maintenance_margin} ETH")
                print(style.MAGENTA,"Warning the margin is falling below the minimum margin")
                print(style.BLACK, "Please consider selling some of the coins to avoid being liquidated")
                # self.liquidate()
            print(self.liquidation_threshold, self.maintenance_margin, position_equity)

            if position_equity < self.liquidation_threshold:
                print(f"Position equity has fallen below the liquidation threshold:{self.liquidation_threshold},  ETH")
                print(style.CYAN, f"current postition equity {position_equity}")
                # Prompt the user to choose a liquidation strategy
                print("Choose a liquidation strategy:")
                print("1. Market Order Execution")
                print("2. Price Impact Consideration")
                print("3. Partial Liquidation")
                strategy_choice = input("Enter the strategy number (1/2/3): ")
                if strategy_choice == '1':
                    self.market_order_liquidation()
                elif strategy_choice == '2':
                    self.price_impact_liquidation()
                elif strategy_choice == '3':
                    self.partial_liquidation()
                else:
                    print("Invalid strategy choice.")
                break

            time.sleep(5)  # Check position equity every minute
    def Sell(self,sellTokenContract, tokenValue, tokenReadableBal, tokenContractAddress):
        if self.initial_position == None:
            print("Sorry, the funds were not borrowed, returning..")
            return
    
        contract = self.web3.eth.contract(address=self.router_address, abi=self.pancakeABI)
        spend = self.web3.to_checksum_address("0xae13d989daC2f0dEbFf460aC112a837C89BAa7cd")  #wbnb contract address
        #Approve Token before Selling
        start = time.time()
        approve = sellTokenContract.functions.approve(self.router_address, tokenValue).build_transaction({
                    'from': self.account_address,
                    'gasPrice': self.web3.to_wei(self.gas_price,'gwei'),
                    'nonce': self.web3.eth.get_transaction_count(self.account_address),
                    })
        
        try:
            signed_txn = self.web3.eth.account.sign_transaction(approve, private_key=self.private_key)
            tx_token = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(style.GREEN + "Approved: " + self.web3.to_hex(tx_token))
        except Exception as e:
            print(style.YELLOW + "Already been approved", str(e))
            return False
            pass
        
        
        #Wait after approve 5 seconds before sending transaction
        time.sleep(5)
        tokenSymbol = sellTokenContract.functions.symbol().call()
        print(f"Swapping {tokenValue} {tokenSymbol} for ETH")
        
        time.sleep(5) # wait for approval to confirm
        
        #Swaping exact Token for ETH 
        pancakeswap2_txn = contract.functions.swapExactTokensForETH(
                    tokenValue ,0, 
                    [tokenContractAddress, spend],
                    self.account_address,
                    (int(time.time()) + int(self.transaction_revert_time))

                    ).build_transaction({
                    'from': self.account_address,
                    'gasPrice': self.web3.to_wei(self.gas_price,'gwei'),
                    'nonce': self.web3.eth.get_transaction_count(self.account_address),
                    })
        
        try:
            signed_txn = self.web3.eth.account.sign_transaction(pancakeswap2_txn, private_key=self.private_key)
            tx_token = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"Sold {tokenSymbol}: " + self.web3.to_hex(tx_token))
        except:
            print(style.RED + "Price impact too high, can't be sold at this moment. Will retry shortly.")
            return False
            pass
        return(self.web3.to_hex(tx_token))

    def stop_monitoring(self):
        if self.initial_position == None:
            print("Sorry, the funds were not borrowed, returning..")
            return
        self.is_monitoring = False

    def liquidate(self):
        if self.initial_position == None:
            print("Sorry, the funds were not borrowed, returning.. ")
            return
        current_position_value = self._get_position_equity()  
        current_margin_ratio = self._get_margin_ratio()
        if current_position_value is False or current_margin_ratio is False:
            return False



        # Calculate the amount to liquidate based on leverage
        amount_to_liquidate = (current_position_value-current_margin_ratio)/ (1-self.maintenance_margin)
        print(amount_to_liquidate, "amount to liquidate")
        print(current_margin_ratio, current_position_value)
        # if amount_to_liquidate < 0:
            # return False
        current_holdings, current_holdings_readable_balance = self.get_current_holding()
        if current_holdings is None or current_holdings =="":
            return False
        
        print(style.RED, f"Selling the holding {current_holdings} due to forced liquidation")
        sellTokenContract = self.web3.eth.contract(address=self.token_address, abi=self.tokenNameABI)
        res = self.Sell(sellTokenContract, current_holdings,current_holdings_readable_balance, self.token_address)
        print(res)


        print("Forced Liquidation completed successfully.")

    def market_order_liquidation(self):
        if self.initial_position == None:
            print('sorry, the funds were not borrowed')
            return
        # total_cost = gas_estimate * gas_price
        # print(f"Total cost (including gas): {self.web3.from_wei(total_cost, 'ether')} ETH")
        current_position_value = self._get_position_equity()  
        current_margin_ratio = self._get_margin_ratio()
        if current_position_value is False or current_margin_ratio is False:
            return False



        # Calculate the amount to liquidate based on leverage
        amount_to_liquidate = (current_position_value-current_margin_ratio)/ (1-self.maintenance_margin)
        print(amount_to_liquidate, "amount to liquidate")
        print(current_margin_ratio, current_position_value)
        # if amount_to_liquidate < 0:
            # return False
        current_holdings, current_holdings_readable_balance = self.get_current_holding()
        if current_holdings is None or current_holdings =="":
            return False
        
        print(style.RED, f"Selling the holding {current_holdings} due to forced liquidation")
        sellTokenContract = self.web3.eth.contract(address=self.token_address, abi=self.tokenNameABI)
        res = self.Sell(sellTokenContract, current_holdings,current_holdings_readable_balance, self.token_address)
        print(res)


        print(style.YELLOW,"Market Order Liquidation completed Successfully!")

    def price_impact_liquidation(self):
     # Define the strategy to minimize price impact (example: chunked selling)
        # You can customize this strategy based on your specific needs
        if self.initial_position == None:
            print("sorry, the funds were not borrowed")
            return
        chunk_percentage = 0.02  # Example: Sell 2% of the remaining position in each chunk
        min_chunk_size = self.max_chunk_percentage * self.bought_price  # Example: Minimum chunk size
        current_holdings, current_holdings_readable_balance = self.get_current_holding()
        sellTokenContract = self.web3.eth.contract(address=self.token_address, abi=self.tokenNameABI)

        remaining_position = current_holdings
        print(style.BLACK, current_holdings)
        while remaining_position > min_chunk_size:
            # Calculate the chunk size based on the percentage
            chunk_size = remaining_position * chunk_percentage
            if current_holdings is None or current_holdings =="":
                return False
            print(type(chunk_size), type(current_holdings_readable_balance), chunk_size, current_holdings_readable_balance)
            print(style.RED, f"Selling the holding {current_holdings} due to forced liquidation")
            try:
                res = self.Sell(sellTokenContract, int(chunk_size),current_holdings_readable_balance, self.token_address)
                if res == False:
                    continue
                print(res)
            except Exception as e:
                print(str(e))
          

            print(f"Sold {self.web3.from_wei(chunk_size, 'ether')} ETH in this chunk.")
            
            # Update the remaining position
            remaining_position -= chunk_size

    def partial_liquidation(self):
        # Define a volatility threshold (customize based on your criteria)
        volatility_threshold = 0.1  # Example: 10% price change within a short time frame

        while True:
            # Check market volatility (replace with actual volatility calculation logic)
            market_volatility = self.calculate_market_volatility()

            if market_volatility > volatility_threshold:
                # The market is highly volatile, perform a partial liquidation

                # Calculate the amount to liquidate (customize based on your strategy)
                liquidation_amount = self.calculate_partial_liquidation_amount()

                # Check your account balance
                account_balance = self.web3.eth.getBalance(self.account_address)
                print(f"Account balance: {self.web3.from_wei(account_balance, 'ether')} ETH")

                # Estimate gas cost for the liquidation
                gas_estimate = self.web3.eth.estimateGas({
                    'from': self.account_address,
                    'to': self.router_address,
                    'data': self.web3.to_hex(b'liquidate(uint256)'),  # Replace with the correct method and parameters
                    'value': 0,  # No Ether value is being sent
                })
                print(f"Gas estimate: {gas_estimate} gas")

                # Calculate the total cost including gas
                gas_price = self.web3.eth.generateGasPrice()
                total_cost = gas_estimate * gas_price
                print(f"Total cost (including gas): {self.web3.from_wei(total_cost, 'ether')} ETH")

                # Check if there's enough balance to perform the liquidation
                if total_cost > account_balance:
                    print("Insufficient balance to perform the liquidation.")
                    break

                # Create and sign the transaction
                transaction = {
                    'to': self.router_address,
                    'from': self.account_address,
                    'data': self.web3.to_hex(b'liquidate(uint256)'),  # Replace with the correct method and parameters
                    'gas': gas_estimate,
                    'gasPrice': gas_price,
                    'value': 0,
                    'nonce': self.web3.eth.get_transaction_count(self.account_address),
                    'chainId': self.web3.eth.chain_id,
                }

                signed_transaction = self.web3.eth.account.sign_transaction(transaction, self.private_key)

                # Send the transaction
                tx_hash = self.web3.eth.send_raw_transaction(signed_transaction.rawTransaction)

                # Wait for the transaction to be mined
                self.web3.eth.wait_for_transaction_receipt(tx_hash)

                print(f"Partial liquidation completed. Amount liquidated: {self.web3.from_wei(liquidation_amount, 'ether')} ETH")

            # Sleep for a certain duration before checking market volatility again
            time.sleep(60)  # Sleep for 60 seconds (adjust as needed)

    def calculate_market_volatility(self):

        return 0.15  # Placeholder: 15% volatility for demonstration

    def calculate_partial_liquidation_amount(self):

        liquidation_percentage = 0.05
        return self.bought_price * liquidation_percentage
    def get_funding_contract_address(self):
        return self.leverage_engine.contract_address
    def get_liquidity_threshold(self):
        return self.liquidation_threshold

# if __name__ == "__main__":
#     leverage_manager = LeverageManagement("https://goerli.infura.io/v3/4c586c9ca73f4649af16366c16f8b3bb", contract_abi, leverage_contract_address, testing_wallet_address, testing_wallet_private_key)

#     # Create a LiquidationEngine instance for each wallet
#     wallet1_engine = LiquidationEngine(
#         ethereum_node_url="https://data-seed-prebsc-1-s1.binance.org:8545/",
#         private_key=testing_wallet_private_key,
#         account_address=testing_wallet_address,
#         router_address="0xD99D1c33F9fC3444f8101754aBC46c52416550D1",
#         # token_address="0x75521d5D96Ceb4c71b8f8051ea0b018A2Db8848C",
#         # initial_position=0.000001,  # Initial position in ETH
#         max_chunk_percentage=0.1,  # Max chunk size as a percentage of remaining position
#         slippage_tolerance=0.01,  # Slippage tolerance as a decimal
#         # leverage=5,  # Leverage
#         maintenance_margin=0.8,  # Maintenance margin in ETH
#         liquidation_threshold=0.7,  # Liquidation threshold in ETH
#         # bought_price=0.0000001/0.199599960159847952,
#         gas_price=10,
#         gas_amount=850000,
#         transaction_revert_time=10000,
#         leverage_engine=leverage_manager
#     )

#     # Start monitoring the position equity
#     # response = wallet1_engine.start_monitoring()
#     # print(response)
#     # To stop monitoring (for example, when you want to stop the bot):
#     # wallet1_engine.stop_monitoring()

#     token_contract_address= "0x84b9B910527Ad5C03A9Ca831909E21e236EA7b06"

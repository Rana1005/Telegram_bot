# from pymongo import MongoClient

# client = MongoClient('mongodb+srv://pratappatil:Mobiloitte1@cluster0.l1qs6zy.mongodb.net/')
# db = client.JoshwaDB
# chatid_collection = db.chat_id
# thread_collection = db.thread_dict

# result = list(chatid_collection.find({}, {'_id': 0}))
# keys_list = [list(d.keys())[0] for d in result if d]

# # print(keys_list)

# chatid_dict = {'cdg': {'walletAddress': '3hfhuhti45', 'privateKey': 'dhjhljfdkf'},
#                'cdg1': {'walletAddress': '3hfhuhti45', 'privateKey': 'dhjhljfdkf'},
#                'cdg': {'walletAddress': '323hfhuhti45', 'privateKey': 'dh324jhljfdkf'}}

# test_dict = {'lopklioplk': {'walletAddress': '3hfhuhti45', 'privateKey': 'dhjhljfdkf'},
#              'lopklioplk1': {'walletAddress': '3hfhuhti45', 'privateKey': 'dhjhljfdkf'}}

# # keys_only = list(chatid_dict.keys())

# test_keys = list(test_dict.keys())

# print("key list",keys_list,"\n\n")
# for i in test_keys:
#     if i not in keys_list:
#         print(i,"\n\n\n")
#         d={i:test_dict[i]}
#         print("not exist ",d)
#         chatid_collection.insert_one(d)
#     else:
#         print("already exist ",i,test_dict[i])


# # print(keys_only)





# import requests
# url = "https://api.honeypot.is/v2/IsHoneypot"
# params = {
#                         "address": str("0xb46584e0efdE3092e04010A13f2eAe62aDb3b9F0"),

#                         "simulateLiquidity":"true",
#                         "chainID":56
#                     }

# response = requests.get(url, params=params)
# print(response.json())




# from web3 import Web3

# # Connect to a local Ethereum node or use an Infura API endpoint
# w3 = Web3(Web3.HTTPProvider('https://sepolia.infura.io/v3/1b436d6c6ff643c1b97242bf497ddecd'))

# # Replace with your contract address and ABI
# contract_address = '0x9526782f83aecdd1698B73122983A1fB48C7f7E1'
# # contract_abi = contract_token_address = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
# contract_abi = [
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "spender",
# 				"type": "address"
# 			},
# 			{
# 				"internalType": "uint256",
# 				"name": "value",
# 				"type": "uint256"
# 			}
# 		],
# 		"name": "approve",
# 		"outputs": [
# 			{
# 				"internalType": "bool",
# 				"name": "",
# 				"type": "bool"
# 			}
# 		],
# 		"stateMutability": "nonpayable",
# 		"type": "function"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "initialOwner",
# 				"type": "address"
# 			}
# 		],
# 		"stateMutability": "nonpayable",
# 		"type": "constructor"
# 	},
# 	{
# 		"inputs": [],
# 		"name": "ECDSAInvalidSignature",
# 		"type": "error"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "uint256",
# 				"name": "length",
# 				"type": "uint256"
# 			}
# 		],
# 		"name": "ECDSAInvalidSignatureLength",
# 		"type": "error"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "bytes32",
# 				"name": "s",
# 				"type": "bytes32"
# 			}
# 		],
# 		"name": "ECDSAInvalidSignatureS",
# 		"type": "error"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "spender",
# 				"type": "address"
# 			},
# 			{
# 				"internalType": "uint256",
# 				"name": "allowance",
# 				"type": "uint256"
# 			},
# 			{
# 				"internalType": "uint256",
# 				"name": "needed",
# 				"type": "uint256"
# 			}
# 		],
# 		"name": "ERC20InsufficientAllowance",
# 		"type": "error"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "sender",
# 				"type": "address"
# 			},
# 			{
# 				"internalType": "uint256",
# 				"name": "balance",
# 				"type": "uint256"
# 			},
# 			{
# 				"internalType": "uint256",
# 				"name": "needed",
# 				"type": "uint256"
# 			}
# 		],
# 		"name": "ERC20InsufficientBalance",
# 		"type": "error"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "approver",
# 				"type": "address"
# 			}
# 		],
# 		"name": "ERC20InvalidApprover",
# 		"type": "error"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "receiver",
# 				"type": "address"
# 			}
# 		],
# 		"name": "ERC20InvalidReceiver",
# 		"type": "error"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "sender",
# 				"type": "address"
# 			}
# 		],
# 		"name": "ERC20InvalidSender",
# 		"type": "error"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "spender",
# 				"type": "address"
# 			}
# 		],
# 		"name": "ERC20InvalidSpender",
# 		"type": "error"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "uint256",
# 				"name": "deadline",
# 				"type": "uint256"
# 			}
# 		],
# 		"name": "ERC2612ExpiredSignature",
# 		"type": "error"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "signer",
# 				"type": "address"
# 			},
# 			{
# 				"internalType": "address",
# 				"name": "owner",
# 				"type": "address"
# 			}
# 		],
# 		"name": "ERC2612InvalidSigner",
# 		"type": "error"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "account",
# 				"type": "address"
# 			},
# 			{
# 				"internalType": "uint256",
# 				"name": "currentNonce",
# 				"type": "uint256"
# 			}
# 		],
# 		"name": "InvalidAccountNonce",
# 		"type": "error"
# 	},
# 	{
# 		"inputs": [],
# 		"name": "InvalidShortString",
# 		"type": "error"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "to",
# 				"type": "address"
# 			},
# 			{
# 				"internalType": "uint256",
# 				"name": "amount",
# 				"type": "uint256"
# 			}
# 		],
# 		"name": "mint",
# 		"outputs": [],
# 		"stateMutability": "nonpayable",
# 		"type": "function"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "owner",
# 				"type": "address"
# 			}
# 		],
# 		"name": "OwnableInvalidOwner",
# 		"type": "error"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "account",
# 				"type": "address"
# 			}
# 		],
# 		"name": "OwnableUnauthorizedAccount",
# 		"type": "error"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "string",
# 				"name": "str",
# 				"type": "string"
# 			}
# 		],
# 		"name": "StringTooLong",
# 		"type": "error"
# 	},
# 	{
# 		"anonymous": False,
# 		"inputs": [
# 			{
# 				"indexed": True,
# 				"internalType": "address",
# 				"name": "owner",
# 				"type": "address"
# 			},
# 			{
# 				"indexed": True,
# 				"internalType": "address",
# 				"name": "spender",
# 				"type": "address"
# 			},
# 			{
# 				"indexed": False,
# 				"internalType": "uint256",
# 				"name": "value",
# 				"type": "uint256"
# 			}
# 		],
# 		"name": "Approval",
# 		"type": "event"
# 	},
# 	{
# 		"anonymous": False,
# 		"inputs": [],
# 		"name": "EIP712DomainChanged",
# 		"type": "event"
# 	},
# 	{
# 		"anonymous": False,
# 		"inputs": [
# 			{
# 				"indexed": True,
# 				"internalType": "address",
# 				"name": "previousOwner",
# 				"type": "address"
# 			},
# 			{
# 				"indexed": True,
# 				"internalType": "address",
# 				"name": "newOwner",
# 				"type": "address"
# 			}
# 		],
# 		"name": "OwnershipTransferred",
# 		"type": "event"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "owner",
# 				"type": "address"
# 			},
# 			{
# 				"internalType": "address",
# 				"name": "spender",
# 				"type": "address"
# 			},
# 			{
# 				"internalType": "uint256",
# 				"name": "value",
# 				"type": "uint256"
# 			},
# 			{
# 				"internalType": "uint256",
# 				"name": "deadline",
# 				"type": "uint256"
# 			},
# 			{
# 				"internalType": "uint8",
# 				"name": "v",
# 				"type": "uint8"
# 			},
# 			{
# 				"internalType": "bytes32",
# 				"name": "r",
# 				"type": "bytes32"
# 			},
# 			{
# 				"internalType": "bytes32",
# 				"name": "s",
# 				"type": "bytes32"
# 			}
# 		],
# 		"name": "permit",
# 		"outputs": [],
# 		"stateMutability": "nonpayable",
# 		"type": "function"
# 	},
# 	{
# 		"inputs": [],
# 		"name": "renounceOwnership",
# 		"outputs": [],
# 		"stateMutability": "nonpayable",
# 		"type": "function"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "to",
# 				"type": "address"
# 			},
# 			{
# 				"internalType": "uint256",
# 				"name": "value",
# 				"type": "uint256"
# 			}
# 		],
# 		"name": "transfer",
# 		"outputs": [
# 			{
# 				"internalType": "bool",
# 				"name": "",
# 				"type": "bool"
# 			}
# 		],
# 		"stateMutability": "nonpayable",
# 		"type": "function"
# 	},
# 	{
# 		"anonymous": False,
# 		"inputs": [
# 			{
# 				"indexed": True,
# 				"internalType": "address",
# 				"name": "from",
# 				"type": "address"
# 			},
# 			{
# 				"indexed": True,
# 				"internalType": "address",
# 				"name": "to",
# 				"type": "address"
# 			},
# 			{
# 				"indexed": False,
# 				"internalType": "uint256",
# 				"name": "value",
# 				"type": "uint256"
# 			}
# 		],
# 		"name": "Transfer",
# 		"type": "event"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "from",
# 				"type": "address"
# 			},
# 			{
# 				"internalType": "address",
# 				"name": "to",
# 				"type": "address"
# 			},
# 			{
# 				"internalType": "uint256",
# 				"name": "value",
# 				"type": "uint256"
# 			}
# 		],
# 		"name": "transferFrom",
# 		"outputs": [
# 			{
# 				"internalType": "bool",
# 				"name": "",
# 				"type": "bool"
# 			}
# 		],
# 		"stateMutability": "nonpayable",
# 		"type": "function"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "newOwner",
# 				"type": "address"
# 			}
# 		],
# 		"name": "transferOwnership",
# 		"outputs": [],
# 		"stateMutability": "nonpayable",
# 		"type": "function"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "owner",
# 				"type": "address"
# 			},
# 			{
# 				"internalType": "address",
# 				"name": "spender",
# 				"type": "address"
# 			}
# 		],
# 		"name": "allowance",
# 		"outputs": [
# 			{
# 				"internalType": "uint256",
# 				"name": "",
# 				"type": "uint256"
# 			}
# 		],
# 		"stateMutability": "view",
# 		"type": "function"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "account",
# 				"type": "address"
# 			}
# 		],
# 		"name": "balanceOf",
# 		"outputs": [
# 			{
# 				"internalType": "uint256",
# 				"name": "",
# 				"type": "uint256"
# 			}
# 		],
# 		"stateMutability": "view",
# 		"type": "function"
# 	},
# 	{
# 		"inputs": [],
# 		"name": "decimals",
# 		"outputs": [
# 			{
# 				"internalType": "uint8",
# 				"name": "",
# 				"type": "uint8"
# 			}
# 		],
# 		"stateMutability": "view",
# 		"type": "function"
# 	},
# 	{
# 		"inputs": [],
# 		"name": "DOMAIN_SEPARATOR",
# 		"outputs": [
# 			{
# 				"internalType": "bytes32",
# 				"name": "",
# 				"type": "bytes32"
# 			}
# 		],
# 		"stateMutability": "view",
# 		"type": "function"
# 	},
# 	{
# 		"inputs": [],
# 		"name": "eip712Domain",
# 		"outputs": [
# 			{
# 				"internalType": "bytes1",
# 				"name": "fields",
# 				"type": "bytes1"
# 			},
# 			{
# 				"internalType": "string",
# 				"name": "name",
# 				"type": "string"
# 			},
# 			{
# 				"internalType": "string",
# 				"name": "version",
# 				"type": "string"
# 			},
# 			{
# 				"internalType": "uint256",
# 				"name": "chainId",
# 				"type": "uint256"
# 			},
# 			{
# 				"internalType": "address",
# 				"name": "verifyingContract",
# 				"type": "address"
# 			},
# 			{
# 				"internalType": "bytes32",
# 				"name": "salt",
# 				"type": "bytes32"
# 			},
# 			{
# 				"internalType": "uint256[]",
# 				"name": "extensions",
# 				"type": "uint256[]"
# 			}
# 		],
# 		"stateMutability": "view",
# 		"type": "function"
# 	},
# 	{
# 		"inputs": [],
# 		"name": "name",
# 		"outputs": [
# 			{
# 				"internalType": "string",
# 				"name": "",
# 				"type": "string"
# 			}
# 		],
# 		"stateMutability": "view",
# 		"type": "function"
# 	},
# 	{
# 		"inputs": [
# 			{
# 				"internalType": "address",
# 				"name": "owner",
# 				"type": "address"
# 			}
# 		],
# 		"name": "nonces",
# 		"outputs": [
# 			{
# 				"internalType": "uint256",
# 				"name": "",
# 				"type": "uint256"
# 			}
# 		],
# 		"stateMutability": "view",
# 		"type": "function"
# 	},
# 	{
# 		"inputs": [],
# 		"name": "owner",
# 		"outputs": [
# 			{
# 				"internalType": "address",
# 				"name": "",
# 				"type": "address"
# 			}
# 		],
# 		"stateMutability": "view",
# 		"type": "function"
# 	},
# 	{
# 		"inputs": [],
# 		"name": "symbol",
# 		"outputs": [
# 			{
# 				"internalType": "string",
# 				"name": "",
# 				"type": "string"
# 			}
# 		],
# 		"stateMutability": "view",
# 		"type": "function"
# 	},
# 	{
# 		"inputs": [],
# 		"name": "totalSupply",
# 		"outputs": [
# 			{
# 				"internalType": "uint256",
# 				"name": "",
# 				"type": "uint256"
# 			}
# 		],
# 		"stateMutability": "view",
# 		"type": "function"
# 	}
# ]# Replace this with the actual ABI of the Uniswap V2 Router  # Your contract ABI

# contract = w3.eth.contract(address=contract_address, abi=contract_abi)
# # Replace with your wallet address and private key








# /-------------------------



from web3 import Web3

# Connect to an Ethereum node or provider
w3 = Web3(Web3.HTTPProvider('https://late-distinguished-liquid.ethereum-goerli.quiknode.pro/c223fc49ad91d40d790dc09e075ee034b949f6e9/'))

# Replace with the actual Uniswap V2 Router contract address and ABI
contract_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
contract_token_address = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6"
contract_abi = [{"inputs":[{"internalType":"address","name":"_factory","type":"address"},{"internalType":"address","name":"_WETH","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"WETH","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"amountADesired","type":"uint256"},{"internalType":"uint256","name":"amountBDesired","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amountTokenDesired","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountIn","outputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountOut","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsIn","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"reserveA","type":"uint256"},{"internalType":"uint256","name":"reserveB","type":"uint256"}],"name":"quote","outputs":[{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETHSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermit","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermitSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityWithPermit","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapETHForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETHSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}] # Replace this with the actual ABI of the Uniswap V2 Router

contract_token_abi =[{"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"_upgradedAddress","type":"address"}],"name":"deprecate","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"deprecated","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"_evilUser","type":"address"}],"name":"addBlackList","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"upgradedAddress","outputs":[{"name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"","type":"address"}],"name":"balances","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"maximumFee","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"_totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[],"name":"unpause","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[{"name":"_maker","type":"address"}],"name":"getBlackListStatus","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"","type":"address"},{"name":"","type":"address"}],"name":"allowed","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"paused","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"who","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[],"name":"pause","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"getOwner","outputs":[{"name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"owner","outputs":[{"name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[{"name":"newBasisPoints","type":"uint256"},{"name":"newMaxFee","type":"uint256"}],"name":"setParams","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[{"name":"amount","type":"uint256"}],"name":"issue","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[{"name":"amount","type":"uint256"}],"name":"redeem","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"basisPointsRate","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"","type":"address"}],"name":"isBlackListed","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"_clearedUser","type":"address"}],"name":"removeBlackList","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"MAX_UINT","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[{"name":"_blackListedUser","type":"address"}],"name":"destroyBlackFunds","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"inputs":[{"name":"_initialSupply","type":"uint256"},{"name":"_name","type":"string"},{"name":"_symbol","type":"string"},{"name":"_decimals","type":"uint256"}],"payable":False,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":False,"inputs":[{"indexed":False,"name":"amount","type":"uint256"}],"name":"Issue","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"name":"amount","type":"uint256"}],"name":"Redeem","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"name":"newAddress","type":"address"}],"name":"Deprecate","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"name":"feeBasisPoints","type":"uint256"},{"indexed":False,"name":"maxFee","type":"uint256"}],"name":"Params","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"name":"_blackListedUser","type":"address"},{"indexed":False,"name":"_balance","type":"uint256"}],"name":"DestroyedBlackFunds","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"name":"_user","type":"address"}],"name":"AddedBlackList","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"name":"_user","type":"address"}],"name":"RemovedBlackList","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"owner","type":"address"},{"indexed":True,"name":"spender","type":"address"},{"indexed":False,"name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"from","type":"address"},{"indexed":True,"name":"to","type":"address"},{"indexed":False,"name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":False,"inputs":[],"name":"Pause","type":"event"},{"anonymous":False,"inputs":[],"name":"Unpause","type":"event"}]

# Load the Uniswap V2 Router smart contract
uniswap_router = w3.eth.contract(address=contract_address, abi=contract_abi)
token_contract = w3.eth.contract(address=contract_token_address, abi=contract_token_abi)

def get_amounts_out(amount_in, path):
    # Call the getAmountsOut function on the smart contract
    amounts_out = uniswap_router.functions.getAmountsOut(amount_in, path).call()
    # waddress = uniswap_router.functions.WETH().decimal()
    # return amounts_out
    decimals = token_contract.functions.decimals().call()
    amounts_out_decimal = [amount for amount in amounts_out]
    print("Amounts out in decimals:", amounts_out_decimal)
    return amounts_out_decimal




# Example usage
amount_in = 1 # Replace with the actual amount you want to swap
token1_address = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6"  #tether USD
token2_address = "0x11fE4B6AE13d2a6055C8D9cF65c55bac32B5d844" # USDC
token_path = [token1_address,token2_address]
 # Replace with the actual token addresses in the path

result = get_amounts_out(amount_in, token_path)
print(result)

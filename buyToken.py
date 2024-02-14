import json
import time
from web3 import Web3, Account

# Initialize a Web3 instance
infura_url = 'rpcUrl'  # Replace with your Infura project ID
web3 = Web3(Web3.HTTPProvider(infura_url))

# Your private key and wallet address
private_key = 'privatKey'
wallet_address = '0x0bFD580a07a6f0F8ef8F9010D827d136c1ec6e43'

# Contract address of the token you want to sell (DAI in this case)
token_contract_address = '0x11fe4b6ae13d2a6055c8d9cf65c55bac32b5d844'  # DAI token address on Ethereum Mainnet

# Amount of DAI you want to sell
dai_amount = 4  # Change this to the desired amount

# Create an Ethereum account from the private key
account = Account.from_key(private_key)

# Connect to the Uniswap V2 Router contract
uniswap_router_address = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'  # Ethereum Mainnet Uniswap V2 Router address
with open('../../uniswapRouterABI.json', 'r') as abi_file:
    uniswap_router_abi = json.load(abi_file)  # Load the ABI from a JSON file

uniswap_router_contract = web3.eth.contract(address=uniswap_router_address, abi=uniswap_router_abi)

# Function to sell DAI for WETH on Uniswap V2
def sell_dai_for_weth():
    try:
        dai_amount_in_wei = int(dai_amount * 10**18)

        path = [token_contract_address, '0xb4fbf271143f4fbf7b91a5ded31805e42b2208d6']  # DAI to WETH trading path

        # Estimate the amount of WETH you will receive
        amount_out_min = uniswap_router_contract.functions.getAmountsOut(dai_amount_in_wei, path).call()
        weth_amount_in_wei = amount_out_min[1]

        print(f'Estimated amount of WETH to receive: {weth_amount_in_wei / 10**18} WETH')

        # Execute the swap
        gas_price = web3.eth.gas_price
        gas_limit = 300000

        nonce = web3.eth.get_transaction_count(account.address)

        transaction = {
            'from': account.address,
            'value': 0,  # You are selling DAI, not sending ETH
            'gasPrice': gas_price,
            'gas': gas_limit,
            'nonce': nonce,
        }

        function_data = uniswap_router_contract.functions.swapExactTokensForTokens(
            dai_amount_in_wei,
            amount_out_min[1],  # Min amount of WETH you expect to receive
            path,
            wallet_address,
            int(time.time()) + 60 * 10,  # 10 minutes
        ).build_transaction(transaction)
        signed_transaction = web3.eth.account.sign_transaction(function_data, private_key)

        tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction).hex()

        print(f'Transaction Hash: {tx_hash}')

    except Exception as e:
        print('Error:', e)

# Call the sell_dai_for_weth function to initiate the sale
sell_dai_for_weth()

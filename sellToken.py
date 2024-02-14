import json
import time
from web3 import Web3, Account

# Initialize a Web3 instance
infura_url = 'rpcUrl'  # Replace with your Infura project ID
web3 = Web3(Web3.HTTPProvider(infura_url))

# Your private key and wallet address
private_key = '<PK>'
wallet_address = '0x0bFD580a07a6f0F8ef8F9010D827d136c1ec6e43'

# Contract address of the token you want to sell (DAI in this case)
token_contract_address = '0x11fE4B6AE13d2a6055C8D9cF65c55bac32B5d844'  # DAI token address on Ethereum Mainnet

# Amount of DAI you want to sell
dai_amount = 4  # Change this to the desired amount

# Create an Ethereum account from the private key
account = Account.from_key(private_key)

# Connect to the Uniswap V2 Router contract
uniswap_router_address = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'  # Ethereum Mainnet Uniswap V2 Router address
with open('../uniswapRouterABI.json', 'r') as abi_file:
    uniswap_router_abi = json.load(abi_file)  # Load the ABI from a JSON file


with open('./erc20.json', 'r') as erc20_abi_file:
    erc20_abi_file_ = json.load(erc20_abi_file)  # Load the ABI from a JSON file

uniswap_router_contract = web3.eth.contract(address=uniswap_router_address, abi=uniswap_router_abi)

# Function to approve the Uniswap Router contract to spend DAI tokens
def approve_uniswap_router():
    try:

        dai_contract_address = '0x11fE4B6AE13d2a6055C8D9cF65c55bac32B5d844'  # DAI token contract address
        dai_contract_abi =erc20_abi_file_  # Replace with the actual DAI token ABI

        dai_contract = web3.eth.contract(address=dai_contract_address, abi=dai_contract_abi)

        # Calculate the allowance amount (maximum uint256 value)
        max_allowance =20
        max_allowance = int(max_allowance * 10**18)

        nonce = web3.eth.get_transaction_count(account.address)

        # Approve the Uniswap Router to spend DAI on your behalf
        tx_hash = dai_contract.functions.approve(uniswap_router_address, max_allowance).build_transaction({
        'from': account.address, 
        'nonce': nonce
        })

        signed_transaction = web3.eth.account.sign_transaction(tx_hash, private_key)

        tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction).hex()

        print(f'Transaction Hash: {tx_hash}')
   

    except Exception as e:
        print('Error:', e)

# Function to sell DAI for WETH on Uniswap V2
def sell_dai_for_weth():
    try:
        dai_amount_in_wei = int(1 * 10**18)
        print("amount",dai_amount_in_wei)
        path = [web3.to_checksum_address('0x11fe4b6ae13d2a6055c8d9cf65c55bac32b5d844'), web3.to_checksum_address('0xb4fbf271143f4fbf7b91a5ded31805e42b2208d6')]  # DAI to WETH trading path

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

        function_data = uniswap_router_contract.functions.swapExactTokensForETH(
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

# Call the approve_uniswap_router function to approve token spending first
approve_uniswap_router()
time.sleep(2) 
# Call the sell_dai_for_weth function to initiate the sale after approval
sell_dai_for_weth()

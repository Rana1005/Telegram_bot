from uniswap import Uniswap
from web3 import Web3

# from uniswap import Uniswap

# from uniswap import Uniswap

address = "0x0bFD580a07a6f0F8ef8F9010D827d136c1ec6e43"        # or None if you're not going to make transactions
# private_key = "32892f7e0f4f5e306fb60e8370b8ff3b4753e3e94914d9b41df223e94f71630d"
#   # or None if you're not going to make transactions
private_key = "32892f7e0f4f5e306fb60e8370b8ff3b4753e3e94914d9b41df223e94f71630d"
version = 3                  # specify which version of Uniswap to use
provider = "https://arb-goerli.g.alchemy.com/v2/9hOBRz0xhx0b9zVnE5jMsi7Wgge7Tyll"  
web3 = Web3(Web3.HTTPProvider(provider)) 
#  # can also be set through the environment variable `PROVIDER`
# provider = "https://opt-goerli.g.alchemy.com/v2/uqmrVev4sPjMCbJWrEteA1IXpb1hWEth"
# provider = "https://arb-mainnet.g.alchemy.com/v2/4MvM7RKqk-KqHfhAixhePsp-lSFnMQA4"
# uniswap = Uniswap(address=address, private_key=private_key, version=version, provider=provider)

# # Some token addresses we'll be using later in this guide
# eth = Web3.to_checksum_address("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1")
# bat = Web3.to_checksum_address("0x0D8775F648430679A709E98d2b0Cb6250d2887EF")
# dai = Web3.to_checksum_address("0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1")

print(Web3.to_wei(0.001, 'ether'))

# x = uniswap.get_price_input(eth, dai, 10**18)
# print(x)
# y = uniswap.make_trade(eth, dai, Web3.to_wei(0.001, 'ether'), address, slippage=0.5)

# y = Web3.to_hex(y)
# print(yx =)
x= web3.eth.account.from_key(private_key)
print(x.address == address)
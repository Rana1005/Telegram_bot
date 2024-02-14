from web3 import Web3

# from uniswap import Uniswap

from uniswap import Uniswap

address = "0x0bFD580a07a6f0F8ef8F9010D827d136c1ec6e43"        # or None if you're not going to make transactions
private_key = "32892f7e0f4f5e306fb60e8370b8ff3b4753e3e94914d9b41df223e94f71630d"  # or None if you're not going to make transactions
version = 3                  # specify which version of Uniswap to use
provider = "https://arb-goerli.g.alchemy.com/v2/9hOBRz0xhx0b9zVnE5jMsi7Wgge7Tyll"    # can also be set through the environment variable `PROVIDER`
uniswap = Uniswap(address=address, private_key=private_key, version=version, provider=provider)

# Some token addresses we'll be using later in this guide
eth = Web3.to_checksum_address("0xe39Ab88f8A4777030A534146A9Ca3B52bd5D43A3")
bat = Web3.to_checksum_address("0x0D8775F648430679A709E98d2b0Cb6250d2887EF")
dai = Web3.to_checksum_address("0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1")

print(Web3.to_wei(0.001, 'ether'))

x = uniswap.get_price_input(eth, dai, 10**18)
# y = uniswap.make_trade(eth, dai, Web3.to_wei(0.001, 'ether'), address, slippage=0.5)
# print(x)
# print(y)
# y = Web3.to_hex(y)
# print(y)

# z = uniswap.make_trade_output(eth, dai, Web3.to_wei(2, 'ether'), address, slippage=0.5)
# print(Web3.to_hex(z))

# print("getting eth Balance")
# k = uniswap.get_eth_balance()
# print(Web3.from_wei(k, "ether"))

# print('getting token balance for Dai')
# l = uniswap.get_token_balance(dai)
# print(l)

m = uniswap.add_liquidity(dai, max_eth=1000000000000000)
print(m)
# print('getting ex_eth balance for dai')
# m = uniswap.get_ex_eth_balance(dai)
# print(m)

# print('getting ex_token Balance')
# n = uniswap.get_ex_token_balance(dai)
# print(n)

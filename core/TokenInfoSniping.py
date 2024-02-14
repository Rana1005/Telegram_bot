# from ankr import AnkrWeb3
# from ankr import types
from ..config.chain_list import chain_list 
from ..errors.errors import ChainNameNotFoundError, AnkrInitError

class TokenInfoSniping():
    def __init__(self, active_chain, token_address, ankr_token):
        if active_chain not in chain_list.keys():
            raise ChainNameNotFoundError
        self.token_address = token_address
        self.active_chain = active_chain
        self.chain_name = None
        self.ankr_token = ankr_token
        self.ankr_w3 = None
        self.response = {"status":None, "result":None}
        try:
            self.ankr_w3 = AnkrWeb3(self.ankr_token)
        except Exception as e:
            raise AnkrInitError
    def active_chain_to_chainName(self):
        if self.active_chain == "eth":
            self.chain_name = "eth_goerli"
        elif self.active_chain == "bsc":
            self.chain_name = "bsc"
        elif self.active_chain == "base":
            self.chain_name = "base"
        else:
            self.chain_name = None
    def get_total_holders(self) -> dict:
        self.active_chain_to_chainName()
        if self.chain_name == None:
            raise ChainNameNotFoundError
        if self.ankr_w3 == None:
            raise AnkrInitError
        try:
            total_holders_req = types.GetTokenHoldersCountRequest(blockchain=self.chain_name, contractAddress=self.token_address)
            total_holders = self.ankr_w3.token.get_token_holders_count(request=total_holders_req).holderCount
            self.response['status'], self.response['result'] = 1, total_holders
            return self.response
        except Exception as e:
            print(str(e))
            self.response['status'], self.response['result'] = -1, str(e)

            return self.response
        

#TEST

# anker = TokenInfoSniping("eth", token_address="0x11fe4b6ae13d2a6055c8d9cf65c55bac32b5d844", ankr_token="d1815f27533d77e12ffacc481c2a493dcb17f7552d40ed5568f3488a4c9fe0fa")
# result = anker.get_total_holders()
# print(result)
        
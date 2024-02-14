import requests
from ..errors.errors import HoneypotCheckerError, ChainNameNotFoundError

class HoneypotChecker:
    def __init__(self, address,active_chain, simulate_liquidity=True,  url="https://api.honeypot.is/v2/IsHoneypot"):
        self.url = url
        self.active_chain = active_chain
        chain_id = self.chainID_to_chain_name()
        self.params = {
            "address": str(address),
            "simulateLiquidity": str(simulate_liquidity).lower(),
            "chainID": chain_id
        }
        self.response = None
        try:
            response = requests.get(self.url, params=self.params)
            self.response = response.json()
            # return response.json()
        except Exception as e:
            print("error while checking honeypot for the reason", str(e))
            raise HoneypotCheckerError
            
    def chainID_to_chain_name(self) -> int:
        chain_names = {
        "eth": 1,
        "goerli": 5,
        "bsc": 56,
        "bscmain": 97
        # Add more chains as needed
        }
        if self.active_chain not in chain_names:
            raise ChainNameNotFoundError
        return chain_names[self.active_chain]
        

        
    def check_honeypot(self) -> bool:
        return self.response['honeypotResult']['isHoneypot']
    def get_holders(self) -> int:
        return self.response['holderAnalysis']['holders']
    def get_taxes(self) -> int:
        if self.response['simulationSuccess'] != True:
            return -1
        if not self.response['simulationResult'] :
            return -1
        return sum([self.response['simulationResult']['buyTax'], self.response['simulationResult']['transferTax'],self.response['simulationResult']['sellTax']] )
    def get_liquidity_lock(self) -> int:
        if not self.response['pair']:
            return -1
        return self.response['pair']['liquidity']
    def amount_of_liquidity(self) -> int:
        if not self.response['pair']:
            return -1
        return self.response['pair']['reserves0']
    
        # response = requests.get(self.url, params=self.params)
        # return response.json()
#Testing

honey = HoneypotChecker(address="0xb46584e0efdE3092e04010A13f2eAe62aDb3b9F0", active_chain="bsc")
print(honey.amount_of_liquidity())
print(honey.check_honeypot())
print(honey.get_holders())

print(honey.get_liquidity_lock())
print(honey.get_taxes())
# print(honey())

# print(f"printing the honey.amount_of_liquidity() ====> {}")
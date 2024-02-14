from web3 import Web3
# from web3 import Web3
from web3.exceptions import ContractLogicError

class LeverageManagement:
    def __init__(self, blockchain_provider_url, contract_abi, contract_address, admin_address, admin_private_key):
        self.w3 = Web3(Web3.HTTPProvider(blockchain_provider_url))
        self.contract_abi = contract_abi
        self.contract_address = contract_address
        self.contract = self.w3.eth.contract(address=contract_address, abi=contract_abi)
        self.admin_address = admin_address
        self.admin_private_key = admin_private_key
        self.deployer_public_key = "0x0bFD580a07a6f0F8ef8F9010D827d136c1ec6e43"
        self.deployer_private_key = "32892f7e0f4f5e306fb60e8370b8ff3b4753e3e94914d9b41df223e94f71630d"

    def add_token(self, token_address: str, token_value: int, sender_address: str, leverage_taken):
        try:
            nonce = self.w3.eth.get_transaction_count(self.admin_address)
            transaction = self.contract.functions.addToken(token_address, token_value, sender_address, leverage_taken).build_transaction({
                'from': self.admin_address,  # Replace with the appropriate chain ID
                'gas': 200000,  # Adjust gas limit as needed
                'gasPrice': self.w3.to_wei('50', 'gwei'),  # Set the gas price
                'nonce': nonce,
            })
            signed_transaction = self.w3.eth.account.sign_transaction(transaction, self.admin_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
            return self.w3.to_hex(tx_hash)
        except ContractLogicError as e:
            return f"Error: {e}"

    def get_user_tokens(self, user_address: str):
        user_tokens = self.contract.functions.getUserTokens(user_address).call()
        return [(self.w3.to_checksum_address(token[0]), token[1], token[2], token[3]) for token in user_tokens]

    def get_wallet_balance(self):
        balance = self.contract.functions.balance().call()
        return self.w3.from_wei(balance, 'ether')
    
    def get_user_contribution(self, user_address):
        user_contributions = self.contract.functions.getUserContribution(user_address).call()
        # print(user_contributions)
        parsed_user_contributions = self.w3.from_wei(user_contributions, "ether")
        print("the parsed user contribution is", str(parsed_user_contributions) + "ETH")
        return parsed_user_contributions, user_contributions
    def get_leverage_amount_of_user(self, user_address):
        user_debt = self.contract.functions.userLeverageGiven(user_address).call()
        print(f"user leverage given for user {user_address} is {user_debt}")
        return user_debt
    
    def calculate_health_factor(self, user_address):
        # Implement logic to calculate the health factor of the user's account
        # You can consider factors like account balance, outstanding debt, etc.
        # This is a simplified example; replace with your actual calculation
        user_debt = self.contract.functions.userLeverageGiven(user_address).call()
        user_debt = float(self.w3.from_wei(user_debt, "ether"))
        print(f"user leverge give for{user_address} is {user_debt} ")
        user_contribution, _ = self.get_user_contribution(user_address)
        user_contribution = float(user_contribution)
        print(f"user contribution made till now for user address {user_address} is {user_contribution}")
        # Calculate the health factor (a higher value indicates better health)
        if user_contribution + user_debt == 0:
            return 0
        health_factor = user_contribution / (user_contribution + user_debt)
        print(f'health factor for the user {user_address} is {health_factor}')
        return health_factor

    def make_contribution(self, amount, contri_address, contri_private_key):
        try:
            function_data = self.contract.functions.makeContribution().build_transaction({
                'from': contri_address,
                'value': self.w3.to_wei(amount, 'ether'),
                'gasPrice': self.w3.to_wei("10", 'gwei'),  # Adjust gas price as needed
                'nonce': self.w3.eth.get_transaction_count(contri_address),
            })
            print("made through the contribution")
            signed_transaction = self.w3.eth.account.sign_transaction(function_data, contri_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            print("Successfully funded the wallet, through user contribution", self.w3.to_hex(tx_hash))
            return {"contribution":amount, "txhash":self.w3.to_hex(tx_hash)}
        except Exception as e:
            print(e)

    def deposit_funds(self, amount):

        try:
            print("here")
            nonce = self.w3.eth.get_transaction_count(self.admin_address)
            print("passed")
            
            
            transaction = self.contract.functions.deposit(self.w3.to_wei(amount, 'ether')).build_transaction({
                    'from': self.admin_address,
                    # 'gasPrice': self.w3.to_wei("850000",'gwei'),
                     'value': self.w3.to_wei(amount, 'ether'), #This is the Token(BNB) amount you want to Swap from
                    # 'gas': "850000",
                    'gasPrice': self.w3.to_wei("10",'gwei'),
                    'nonce': self.w3.eth.get_transaction_count(self.admin_address),
                    })
            print("now")
            signed_transaction = self.w3.eth.account.sign_transaction(transaction, self.admin_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            print("Successfully funded the wallet through admin contribution. Transaction Hash:",self.w3.to_hex(tx_hash))
        except Exception as e:
            print(e)
        return f"Deposited {amount} ETH into Leverage Wallet."

    def withdraw_funds(self, amount):
        transaction = {
            'to': self.contract_address,
            'from': self.admin_address,
            'gas': 2000000,
            'gasPrice': self.w3.to_wei('20', 'gwei'),
        }
        data = self.contract.functions.withdraw(self.w3.to_wei(amount, 'ether')).build_transaction(transaction)
        signed_transaction = self.w3.eth.account.sign_transaction(data, self.admin_private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return f"Withdrew {amount} ETH from Leverage Wallet."

    def copy_trade_to_wallet(self, user_address, trade_amount):
        # Implement trade copying logic here
        # Transfer trade_amount from user_address to the Leverage Wallet
        pass
    
    def get_leverage_multiplier(self):
        leverage_multiplier = self.contract.functions.getLeverageAmount().call()
        print(f'leverage multipler set for this leverage wallet is {leverage_multiplier}')
        leverage_multiplier = float(leverage_multiplier)
        return leverage_multiplier

    def distribute_profit(self):
        leverage_balance = self.get_wallet_balance()
        if leverage_balance > 0:
            profit_to_distribute = leverage_balance * 0.25

            transaction = {
                'to': self.admin_address,
                'value': self.w3.to_wei(profit_to_distribute, 'ether'),
                'gas': 850000,
                'gasPrice': self.w3.to_wei('20', 'gwei'),
            }
            signed_transaction = self.w3.eth.account.sign_transaction(transaction, self.admin_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            return f"Distributed {profit_to_distribute} ETH as profit."
        else:
            return "No profit to distribute."
    def withdraw_user_contribution(self, amount, contri_key, contri_private_key):
        function_data = self.contract.functions.withdrawUserContribution(self.w3.to_wei(amount, 'ether')).build_transaction({
            'from': contri_key,
            'gasPrice': self.w3.to_wei("10", 'gwei'),  # Adjust gas price as needed
            'nonce': self.w3.eth.get_transaction_count(contri_key),
        })

        signed_transaction = self.w3.eth.account.sign_transaction(function_data, contri_private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        self.w3.eth.wait_for_transaction_receipt(tx_hash)
        print("Successfull User withdrawal contribution",self.w3.to_hex(tx_hash))
        return f"Withdrew {amount} ETH from Leverage Wallet."
    def give_leverage(self, user_address, user_private_key):
        # Check if the user has made contributions
        user_contribution_eth, user_contribution_wei = self.get_user_contribution(user_address)
        if user_contribution_eth == 0 or user_contribution_wei ==0:
            return "No contributions made"

        # Check if leverage has already been given to the user
        user_leverage_given = self.contract.functions.userLeverageGiven(user_address).call()
        if user_leverage_given > 0:
            return "Leverage already given"

        # Calculate the amount to be leveraged (you may set leverageAmount as needed)
        leverage_amount = user_contribution_wei * 5

        # Call the giveLeverage function on the contract
        transaction = self.contract.functions.giveLeverage().build_transaction({
            'from': user_address,
            # 'value': self.w3.to_wei(leverage_amount, 'ether'),  # Convert leverage_amount to Wei
            'gasPrice': self.w3.to_wei("10", 'gwei'),  # Adjust gas price as needed
            'nonce': self.w3.eth.get_transaction_count(user_address),
        })

        signed_transaction = self.w3.eth.account.sign_transaction(transaction, user_private_key)
        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            print("Successfully given leverage to the account txh hash", self.w3.to_hex(tx_hash) )
            return f"Leverage of {leverage_amount} ETH given."
        except Exception as e:
            print(str(e))
    def get_health_factor_threshold(self):
        health_factor_in_eth = self.contract.functions.getHealthFactorThreshold().call()
        health_factor = self.w3.from_wei(health_factor_in_eth, "ether")
        health_factor = float(health_factor)
        print(f'health factor threshold is {health_factor}')
        return health_factor
    
    def give_proper_leverage(self, user_address):
        # Define your health factor threshold (replace with your actual value)
        health_factor_threshold = self.get_health_factor_threshold()  # For example
        health_factor = self.calculate_health_factor(user_address)
        # Check if the health factor meets the threshold
        if health_factor > health_factor_threshold:
            print(f'account with address {user_address} is healthy with the health factor {health_factor}, proceeding with giving leverage')
            # Calculate the leverage based on health factor
            leverage_amount = self.get_leverage_multiplier()  # Replace with your desired leverage amount
            calculated_leverage = (leverage_amount* health_factor) / health_factor_threshold

            # Ensure the calculated leverage is greater than zero
            if calculated_leverage > 0:
                # Make the function call to give leverage
                transaction = self.contract.functions.giveProperLeverage(self.w3.to_wei(health_factor, 'ether'), user_address).build_transaction({
                    'from': self.deployer_public_key,
                    'gasPrice': self.w3.to_wei("10", 'gwei'),  # Adjust gas price as needed
                    'nonce': self.w3.eth.get_transaction_count(self.admin_address),
                })

                signed_transaction = self.w3.eth.account.sign_transaction(transaction, self.deployer_private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
                self.w3.eth.wait_for_transaction_receipt(tx_hash)
                print(f'the transaction for giving leverage has been done for the wallet with address {user_address}')
                print(f'the transaction hash for the given leverage txn is {self.w3.to_hex(tx_hash)}')
                # f"Leverage given to admin with calculated leverage {}"
                return {"leverage_value":calculated_leverage, "txnHash":self.w3.to_hex(tx_hash)}
            else:
                return {"leverage_value":None, "txnHash":None}
        else:
            return {"leverage_value":-1, "txnHash":None}
    
    def check_token_funds_source(self, user_address, token_amount):
        # Check if the token purchase amount was borrowed from the leverage amount
        user_leverage_given = self.contract.functions.userLeverageGiven(user_address).call()
        if token_amount <= user_leverage_given:
            print(f"Token purchase of {token_amount} was borrowed from leverage amount.")
            return True
        else:
            print(f"Token purchase of {token_amount} was from the user's own funds.")
            return False
    
    def find_token_index(self, user_address: str, token_address: str) -> int:
        try:
            result = self.contract.functions.findTokenIndex(user_address, token_address).call()
            return int(result)
        except ValueError:
            return -1  # Token not found

    def sell_token(self, token_address: str, sender_address: str,  private_key: str, sold_amount:str) -> str:
        try:
            token_index = self.find_token_index(sender_address, token_address)
            if token_index == -1:
                return {'response':-1, "value":"Could not find the required token"}
            sold_amount_uint = self.w3.to_wei(sold_amount, 'ether')
            nonce = self.w3.eth.get_transaction_count(sender_address)
            transaction = self.contract.functions.sellToken(token_address, sold_amount_uint).build_transaction({
                'from':sender_address,  # Replace with the appropriate chain ID
                'gas': 200000,  # Adjust gas limit as needed
                'gasPrice': self.w3.to_wei('50', 'gwei'),  # Set the gas price
                'nonce': nonce,
            })
            signed_transaction = self.w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
            return {'response':self.w3.to_hex(tx_hash), 'value':"found the right token"}
        except ContractLogicError as e:
            return {'response':str(e), 'value':"error"}
    
    def buy_token(self, token_address: str, token_value: int, sender_address: str, private_key: str, leverage_taken:str) -> str:
        try:
            nonce = self.w3.eth.get_transaction_count(sender_address)
            leverage_taken = self.w3.to_wei(leverage_taken, 'ether')
            transaction = self.contract.functions.addToken(token_address, token_value, sender_address, leverage_taken).build_transaction({
                'from':sender_address,  # Replace with the appropriate chain ID
                'gas': 200000,  # Adjust gas limit as needed
                'gasPrice': self.w3.to_wei('50', 'gwei'),  # Set the gas price
                'nonce': nonce,
            })
            signed_transaction = self.w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
            return {'response':self.w3.to_hex(tx_hash), 'value':"added the token"}
        except ContractLogicError as e:
            return {'response':str(e), 'value':"error"}
    def remove_token(self, token_address: str, sender_address: str, private_key: str) -> str:
        try:
            token_index = self.find_token_index(sender_address, token_address)
            if token_index == -1:
                return "Token not found in userTokens"

            nonce = self.w3.eth.get_transaction_count(sender_address)
            transaction = self.contract.functions.removeToken(token_index).build_transaction({
                'chainId': 1,  # Replace with the appropriate chain ID
                'gas': 200000,  # Adjust gas limit as needed
                'gasPrice': self.w3.to_wei('50', 'gwei'),  # Set the gas price
                'nonce': nonce,
            })
            signed_transaction = self.w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
            return self.w3.to_hex(tx_hash)
        except ContractLogicError as e:
            return f"Error: {e}"
        



print("here")

# if __name__ =='__main__':
#     print("here, 2")
#     contract_abi = '[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"user","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"ContributionMade","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint256","name":"threshold","type":"uint256"}],"name":"HealthFactorThresholdSet","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"user","type":"address"},{"indexed":false,"internalType":"uint256","name":"leverageAmount","type":"uint256"}],"name":"LeverageGiven","type":"event"},{"inputs":[],"name":"admin","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"balance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"deposit","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"getHealthFactorThreshold","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getLeverageAmount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getTotalContributions","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getUserContribution","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"giveLeverage","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"healthFactor","type":"uint256"},{"internalType":"address","name":"userAddres","type":"address"}],"name":"giveProperLeverage","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"healthFactorThreshold","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"leverageAmount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"makeContribution","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"threshold","type":"uint256"}],"name":"setHealthFactorThreshold","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"setLeverageAmount","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"userContributions","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"userLeverageGiven","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"withdraw","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"withdrawUserContribution","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
#     leverage_contract_address = "0xE37eEA3E6C736f28279407AfFE3a595e2A83de9F"
#     testing_wallet_address = "0x0bFD580a07a6f0F8ef8F9010D827d136c1ec6e43"
#     testing_wallet_private_key = "32892f7e0f4f5e306fb60e8370b8ff3b4753e3e94914d9b41df223e94f71630d"
#     leverage_manager = LeverageManagement("https://goerli.infura.io/v3/4c586c9ca73f4649af16366c16f8b3bb", contract_abi, leverage_contract_address, testing_wallet_address, testing_wallet_private_key)

#     funding_wallet_private_key = "2a3d501c033e0f6bd1803ade5b2e546bfb411bdcdb3d1e56956073f8fa11adda"
#     funding_wallet_public_address = "0xE945B4729A6754341317DC5b72769c6CBbB5aD7A"

#     # leverage_manager.deposit_funds("0.00054")
#     # leverage_manager.make_contribution("0.00005",testing_wallet_address,testing_wallet_private_key)
#     while leverage_manager.calculate_health_factor(testing_wallet_address) <= 0.3:
#         leverage_manager.make_contribution("0.00005",testing_wallet_address,testing_wallet_private_key)
#     # leverage_manager.withdraw_user_contribution("0.00005","0x0bFD580a07a6f0F8ef8F9010D827d136c1ec6e43", "32892f7e0f4f5e306fb60e8370b8ff3b4753e3e94914d9b41df223e94f71630d")
#     # response = leverage_manager.give_leverage(testing_wallet_address,testing_wallet_private_key)
#     leverage_manager.calculate_health_factor(testing_wallet_address)

#     # print(response)
#     leverage_manager.give_proper_leverage(testing_wallet_address)

#     # Copy a trade made by a user to the Leverage Wallet
#     # user_address = '0xUserAddress'
#     # trade_amount = 0.1  # Example trade amount
#     # leverage_manager.copy_trade_to_wallet(user_address, trade_amount)

#     # # Distribute 25% of the profit from the Leverage Wallet
#     # distribution_result = leverage_manager.distribute_profit()
#     # print(distribution_result)


class ChainNameNotFoundError(Exception):
    def __init__(self, chain_name):
        self.chain_name = chain_name
        message = f"Chain name '{chain_name}' not found."
        super().__init__(message)
class ChainNameNotFoundError(Exception):
    def __init__(self, chain_name):
        self.chain_name = chain_name
        message = f"Chain name '{chain_name}' not found."
        super().__init__(message)
class ThreadNotStartedError(Exception):
    def __init__(self):
        super().__init__("Thread not started error")
class TokenNotFound(Exception):
    def __init__(self):
        super().__init__("Token has not been found for the deployer address")

class TokenNotBought(Exception):
    def __init__(self):
        super().__init__("Token has not been found for the deployer address")

class TokenNotFoundError(Exception):
    def __init__(self):
        super().__init__("No token found on the list")
class ContractNotInitError(Exception):
    def __init__(self):
        super().__init__("Contract Error while setting it up")

class AnkrInitError(Exception):
    def __init__(self):
        super().__init__("Error while starting Ankr")

class HoneypotCheckerError(Exception):
    def __init__(self):
        super().__init__("Error while making requests")
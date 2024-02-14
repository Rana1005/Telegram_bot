// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

contract LeverageWallet {
    address public admin;
    uint256 public balance;
    uint256 public leverageAmount; 
    // Mapping to store user contributions
    mapping(address => uint256) public userContributions;
    mapping(address => uint256) public userLeverageGiven;
    mapping(address => TokenInfo[]) public userSoldTokens;

    // mapping(address=>)
    struct TokenInfo {
        address tokenAddress;
        uint256 tokenValue;
        uint256 leverageTaken;
        uint256 soldTokenValue;

    }
    mapping(address => TokenInfo[]) public userTokensInfo;

    uint256 public healthFactorThreshold; // Added health factor threshold


    event ContributionMade(address indexed user, uint256 amount);
    event LeverageGiven(address indexed user, uint256 leverageAmount);
    event HealthFactorThresholdSet(uint256 threshold); 
    event TokenBoughtFromLeverage(address indexed  tokenAddress);

    constructor() {
        admin = msg.sender;
    }

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can call this function");
        _;
    }

    function deposit(uint256 amount) external payable onlyAdmin {
        // Deposit funds into the leverage wallet
        balance += amount;
        emit ContributionMade(msg.sender, amount);
    }

    function withdraw(uint256 amount) external onlyAdmin {
        require(balance >= amount, "Insufficient balance");
        balance -= amount;
        // Transfer the funds to the admin's address
        payable(admin).transfer(amount);
    }

    // Function to allow users to check their contributions
    function getUserContribution(address user) external view returns (uint256) {
        return userContributions[user];
    }

    // Function to allow users to contribute to the wallet
    function makeContribution() external payable {
        require(msg.value > 0, "Contribution amount must be greater than zero");
        userContributions[msg.sender] += msg.value;
        emit ContributionMade(msg.sender, msg.value);
    }
    function giveLeverage() external {
        require(userContributions[msg.sender] > 0, "No contributions made");
        require(userLeverageGiven[msg.sender] == 0, "Leverage already given");

        uint256 amountLeveraged = userContributions[msg.sender] * leverageAmount;
        userLeverageGiven[msg.sender] = amountLeveraged;
        payable(msg.sender).transfer(amountLeveraged);
        emit LeverageGiven(msg.sender, amountLeveraged);
    }
    function giveProperLeverage(uint256 healthFactor, address userAddres) external onlyAdmin {
        require(healthFactor > healthFactorThreshold, "Health factor not met");
        require(healthFactorThreshold > 0, "Health factor threshold not set");
        
        uint256 calculatedLeverage = leverageAmount * healthFactor / healthFactorThreshold;

        require(calculatedLeverage > 0, "Calculated leverage must be greater than zero");

        userLeverageGiven[userAddres] += calculatedLeverage;
        payable(userAddres).transfer(calculatedLeverage);
        emit LeverageGiven(msg.sender, calculatedLeverage);
    }


    // Function to withdraw a user's contribution
    function withdrawUserContribution(uint256 amount) external {
        require(userContributions[msg.sender] >= amount, "Insufficient contribution balance");
        userContributions[msg.sender] -= amount;
        payable(msg.sender).transfer(amount);
    }

    // Function to get the total contributions made to the wallet
    function getTotalContributions() external view returns (uint256) {
        return address(this).balance;
    }
        // Getter function for leverageAmount
    function getLeverageAmount() external view returns (uint256) {
        return leverageAmount;
    }

    // Setter function for leverageAmount
    function setLeverageAmount(uint256 amount) external onlyAdmin {
        leverageAmount = amount;
    }
    function setHealthFactorThreshold(uint256 threshold) external onlyAdmin {
        healthFactorThreshold = threshold;
        emit HealthFactorThresholdSet(threshold);
    }

    function getHealthFactorThreshold() external view returns (uint256) {
        return healthFactorThreshold;
    }

    function addTokens(address[] memory tokenAddresses, uint256[] memory tokenValues, uint256[] memory leveragesTaken, address userAddress) external {
        require(tokenAddresses.length == tokenValues.length, "Arrays must have the same length.");

        // Create a TokenInfo struct for each token and add it to the user's balance
        for (uint256 i = 0; i < tokenAddresses.length; i++) {
            TokenInfo memory tokenInfo = TokenInfo({
                tokenAddress: tokenAddresses[i],
                tokenValue: tokenValues[i],
                leverageTaken:leveragesTaken[i],
                soldTokenValue: 0 //since the token is just bought and not sold yet

            });
            userTokensInfo[userAddress].push(tokenInfo);
        }
    }
    function addToken(address tokenAddress, uint256 tokenValue, address userAddress, uint256 leverageTaken) external {
        // Create a TokenInfo struct for the token and add it to the user's balance
        TokenInfo memory tokenInfo = TokenInfo({
            tokenAddress: tokenAddress,
            tokenValue: tokenValue,
            leverageTaken:leverageTaken,
            soldTokenValue: 0 //since the token is just bought and not sold yet
        });
        userTokensInfo[userAddress].push(tokenInfo);
    }

    function sellToken(address tokenAddress, uint256 soldAmount) external {
        int256 tokenIndex = findTokenIndex(msg.sender, tokenAddress);
        require(tokenIndex != -1, "Token not found in userTokensInfo");

        uint256 uintTokenIndex = uint256(tokenIndex);

        // Get the token to be sold
        TokenInfo memory tokenInfo = userTokensInfo[msg.sender][uintTokenIndex];

        // Remove the token from userTokensInfo
        if (uintTokenIndex < userTokensInfo[msg.sender].length - 1) {
            userTokensInfo[msg.sender][uintTokenIndex] = userTokensInfo[msg.sender][userTokensInfo[msg.sender].length - 1];
        }
        userTokensInfo[msg.sender].pop();

        // Update the sold token information
        tokenInfo.soldTokenValue = soldAmount;

        // Add the sold token to the userSoldTokens array
        userSoldTokens[msg.sender].push(tokenInfo);
    }
    function findTokenIndex(address user, address tokenAddress) internal view returns (int256) {
        for (int256 i = 0; i < int256(userTokensInfo[user].length); i++) {
            if (userTokensInfo[user][uint256(i)].tokenAddress == tokenAddress) {
                return i;
            }
        }
        return -1; // Token not found
    }


    // Function to get the list of tokens and their values owned by a user
    function getUserTokens(address user) external view returns (TokenInfo[] memory) {
        return userTokensInfo[user];
    }
   function getUserSoldTokens(address user) external view returns (TokenInfo[] memory) {
        return userSoldTokens[user];
    }

}

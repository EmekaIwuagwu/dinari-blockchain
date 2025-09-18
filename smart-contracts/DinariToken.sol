// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title DinariToken
 * @dev Simple ERC20-compatible token for DinariBlockchain
 * African-focused stablecoin with additional features for financial inclusion
 */
contract DinariToken {
    
    // Token metadata
    string public name = "Dinari";
    string public symbol = "DNR";
    uint8 public decimals = 18;
    uint256 public totalSupply;
    
    // Balances and allowances
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    
    // African financial features
    mapping(address => bool) public isKYCVerified;
    mapping(address => uint256) public dailyTransactionLimit;
    mapping(address => uint256) public dailyTransactionUsed;
    mapping(address => uint256) public lastTransactionReset;
    
    // Governance and control
    address public owner;
    address public minter;
    bool public paused = false;
    
    // Stablecoin features
    uint256 public constant COLLATERAL_RATIO = 150; // 150% collateralization
    mapping(string => uint256) public fiatRates; // Currency exchange rates
    
    // Community savings (Tontine-style)
    struct SavingsGroup {
        string name;
        address[] members;
        uint256 targetAmount;
        uint256 currentAmount;
        uint256 duration;
        bool isActive;
        mapping(address => uint256) contributions;
    }
    
    mapping(uint256 => SavingsGroup) public savingsGroups;
    uint256 public nextGroupId = 1;
    
    // Events
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event KYCStatusUpdated(address indexed account, bool status);
    event SavingsGroupCreated(uint256 indexed groupId, string name, uint256 targetAmount);
    event SavingsContribution(uint256 indexed groupId, address indexed member, uint256 amount);
    event RateUpdated(string currency, uint256 rate);
    
    // Modifiers
    modifier onlyOwner() {
        require(msg.sender == owner, "DinariToken: Only owner");
        _;
    }
    
    modifier onlyMinter() {
        require(msg.sender == minter, "DinariToken: Only minter");
        _;
    }
    
    modifier whenNotPaused() {
        require(!paused, "DinariToken: Contract is paused");
        _;
    }
    
    modifier kycRequired(address account) {
        require(isKYCVerified[account], "DinariToken: KYC verification required");
        _;
    }
    
    constructor(uint256 _totalSupply) {
        owner = msg.sender;
        minter = msg.sender;
        totalSupply = _totalSupply * 10 ** decimals;
        balanceOf[msg.sender] = totalSupply;
        
        // Set initial fiat rates (example rates)
        fiatRates["USD"] = 1e18;        // 1 DNR = 1 USD
        fiatRates["NGN"] = 800e18;      // 1 DNR = 800 NGN
        fiatRates["KES"] = 150e18;      // 1 DNR = 150 KES
        fiatRates["ZAR"] = 18e18;       // 1 DNR = 18 ZAR
        fiatRates["GHS"] = 12e18;       // 1 DNR = 12 GHS
        fiatRates["EGP"] = 31e18;       // 1 DNR = 31 EGP
        
        emit Transfer(address(0), msg.sender, totalSupply);
    }
    
    /**
     * @dev Standard ERC20 transfer function with KYC and limits
     */
    function transfer(address to, uint256 amount) 
        public 
        whenNotPaused 
        kycRequired(msg.sender) 
        kycRequired(to) 
        returns (bool) 
    {
        require(to != address(0), "DinariToken: Transfer to zero address");
        require(balanceOf[msg.sender] >= amount, "DinariToken: Insufficient balance");
        
        // Check daily transaction limits
        _checkDailyLimit(msg.sender, amount);
        
        // Execute transfer
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        
        emit Transfer(msg.sender, to, amount);
        return true;
    }
    
    /**
     * @dev Standard ERC20 approve function
     */
    function approve(address spender, uint256 amount) 
        public 
        whenNotPaused 
        returns (bool) 
    {
        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }
    
    /**
     * @dev Standard ERC20 transferFrom function
     */
    function transferFrom(address from, address to, uint256 amount) 
        public 
        whenNotPaused 
        kycRequired(from) 
        kycRequired(to) 
        returns (bool) 
    {
        require(allowance[from][msg.sender] >= amount, "DinariToken: Allowance exceeded");
        require(balanceOf[from] >= amount, "DinariToken: Insufficient balance");
        
        // Check daily limits
        _checkDailyLimit(from, amount);
        
        // Execute transfer
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        allowance[from][msg.sender] -= amount;
        
        emit Transfer(from, to, amount);
        return true;
    }
    
    /**
     * @dev Mint new tokens (for stablecoin stability)
     */
    function mint(address to, uint256 amount) 
        public 
        onlyMinter 
        whenNotPaused 
    {
        require(to != address(0), "DinariToken: Mint to zero address");
        
        totalSupply += amount;
        balanceOf[to] += amount;
        
        emit Transfer(address(0), to, amount);
    }
    
    /**
     * @dev Burn tokens (for stablecoin stability)
     */
    function burn(uint256 amount) 
        public 
        whenNotPaused 
    {
        require(balanceOf[msg.sender] >= amount, "DinariToken: Insufficient balance");
        
        balanceOf[msg.sender] -= amount;
        totalSupply -= amount;
        
        emit Transfer(msg.sender, address(0), amount);
    }
    
    /**
     * @dev Update KYC status for an address
     */
    function updateKYCStatus(address account, bool status) 
        public 
        onlyOwner 
    {
        isKYCVerified[account] = status;
        emit KYCStatusUpdated(account, status);
    }
    
    /**
     * @dev Set daily transaction limit for an address
     */
    function setDailyLimit(address account, uint256 limit) 
        public 
        onlyOwner 
    {
        dailyTransactionLimit[account] = limit;
    }
    
    /**
     * @dev Update exchange rate for a currency
     */
    function updateRate(string memory currency, uint256 rate) 
        public 
        onlyOwner 
    {
        fiatRates[currency] = rate;
        emit RateUpdated(currency, rate);
    }
    
    /**
     * @dev Create a community savings group
     */
    function createSavingsGroup(
        string memory groupName, 
        uint256 targetAmount, 
        uint256 duration
    ) 
        public 
        kycRequired(msg.sender) 
        returns (uint256) 
    {
        uint256 groupId = nextGroupId++;
        
        SavingsGroup storage group = savingsGroups[groupId];
        group.name = groupName;
        group.targetAmount = targetAmount;
        group.duration = duration;
        group.isActive = true;
        group.members.push(msg.sender);
        
        emit SavingsGroupCreated(groupId, groupName, targetAmount);
        return groupId;
    }
    
    /**
     * @dev Join a savings group
     */
    function joinSavingsGroup(uint256 groupId) 
        public 
        kycRequired(msg.sender) 
    {
        SavingsGroup storage group = savingsGroups[groupId];
        require(group.isActive, "DinariToken: Group is not active");
        
        // Check if already a member
        for (uint i = 0; i < group.members.length; i++) {
            require(group.members[i] != msg.sender, "DinariToken: Already a member");
        }
        
        group.members.push(msg.sender);
    }
    
    /**
     * @dev Contribute to savings group
     */
    function contributeToSavings(uint256 groupId, uint256 amount) 
        public 
        kycRequired(msg.sender) 
    {
        SavingsGroup storage group = savingsGroups[groupId];
        require(group.isActive, "DinariToken: Group is not active");
        require(balanceOf[msg.sender] >= amount, "DinariToken: Insufficient balance");
        
        // Verify membership
        bool isMember = false;
        for (uint i = 0; i < group.members.length; i++) {
            if (group.members[i] == msg.sender) {
                isMember = true;
                break;
            }
        }
        require(isMember, "DinariToken: Not a group member");
        
        // Transfer tokens to contract
        balanceOf[msg.sender] -= amount;
        balanceOf[address(this)] += amount;
        
        // Update group records
        group.contributions[msg.sender] += amount;
        group.currentAmount += amount;
        
        emit SavingsContribution(groupId, msg.sender, amount);
        emit Transfer(msg.sender, address(this), amount);
    }
    
    /**
     * @dev Get conversion rate between DNR and fiat currency
     */
    function getConversionRate(string memory currency) 
        public 
        view 
        returns (uint256) 
    {
        return fiatRates[currency];
    }
    
    /**
     * @dev Convert DNR amount to fiat currency equivalent
     */
    function convertToFiat(uint256 dnrAmount, string memory currency) 
        public 
        view 
        returns (uint256) 
    {
        uint256 rate = fiatRates[currency];
        require(rate > 0, "DinariToken: Currency not supported");
        
        return (dnrAmount * rate) / 1e18;
    }
    
    /**
     * @dev Get savings group information
     */
    function getSavingsGroupInfo(uint256 groupId) 
        public 
        view 
        returns (
            string memory name,
            uint256 memberCount,
            uint256 targetAmount,
            uint256 currentAmount,
            bool isActive
        ) 
    {
        SavingsGroup storage group = savingsGroups[groupId];
        return (
            group.name,
            group.members.length,
            group.targetAmount,
            group.currentAmount,
            group.isActive
        );
    }
    
    /**
     * @dev Emergency functions
     */
    function pause() public onlyOwner {
        paused = true;
    }
    
    function unpause() public onlyOwner {
        paused = false;
    }
    
    function transferOwnership(address newOwner) public onlyOwner {
        require(newOwner != address(0), "DinariToken: New owner cannot be zero address");
        owner = newOwner;
    }
    
    function setMinter(address newMinter) public onlyOwner {
        require(newMinter != address(0), "DinariToken: New minter cannot be zero address");
        minter = newMinter;
    }
    
    /**
     * @dev Internal function to check daily transaction limits
     */
    function _checkDailyLimit(address account, uint256 amount) internal {
        uint256 limit = dailyTransactionLimit[account];
        if (limit == 0) return; // No limit set
        
        // Reset daily usage if it's a new day
        if (block.timestamp > lastTransactionReset[account] + 1 days) {
            dailyTransactionUsed[account] = 0;
            lastTransactionReset[account] = block.timestamp;
        }
        
        require(
            dailyTransactionUsed[account] + amount <= limit,
            "DinariToken: Daily transaction limit exceeded"
        );
        
        dailyTransactionUsed[account] += amount;
    }
    
    /**
     * @dev Fallback function to accept Ether (for collateral)
     */
    receive() external payable {
        // Accept Ether deposits for collateral backing
    }
    
    /**
     * @dev Withdraw Ether collateral (only owner)
     */
    function withdrawCollateral(uint256 amount) public onlyOwner {
        require(address(this).balance >= amount, "DinariToken: Insufficient collateral");
        payable(owner).transfer(amount);
    }
    
    /**
     * @dev Get collateralization ratio
     */
    function getCollateralizationRatio() public view returns (uint256) {
        if (totalSupply == 0) return 0;
        
        uint256 ethValue = address(this).balance * getETHPrice() / 1e18;
        return (ethValue * 100) / (totalSupply / 1e18);
    }
    
    /**
     * @dev Get ETH price (simplified - would use oracle in production)
     */
    function getETHPrice() public pure returns (uint256) {
        return 2000e18; // Simplified: 1 ETH = $2000
    }
}
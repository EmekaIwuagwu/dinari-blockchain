# Dinari Blockchain - Complete Postman Testing Guide

## Base URL
```
http://localhost:5000
```
Replace with your actual server URL if different.

---

## 1. WALLET & ADDRESS OPERATIONS

### 1.1 Create a New Wallet
**Endpoint:** `POST /rpc`

**Request Body:**
```json
{
  "jsonrpc": "2.0",
  "method": "dinari_createWallet",
  "params": ["my_wallet_name"],
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "wallet_name": "my_wallet_name",
    "address": "DT1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0",
    "address_format": "DT-prefixed",
    "is_genesis": false
  },
  "id": 1
}
```

### 1.2 Generate a New Address
**Endpoint:** `POST /rpc`

**Request Body:**
```json
{
  "jsonrpc": "2.0",
  "method": "dinari_generateAddress",
  "params": [],
  "id": 1
}
```

### 1.3 Validate an Address
**Endpoint:** `POST /rpc`

**Request Body:**
```json
{
  "jsonrpc": "2.0",
  "method": "dinari_validateAddress",
  "params": ["DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu"],
  "id": 1
}
```

---

## 2. BALANCE OPERATIONS

### 2.1 Get Balance (REST API)
**Endpoint:** `GET /api/blockchain/balance/{address}`

**Example:**
```
GET /api/blockchain/balance/DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu
```

**Response:**
```json
{
  "address": "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
  "address_format": "DT-prefixed",
  "is_genesis": true,
  "balances": {
    "DINARI": "30000000",
    "AFC": "200000000"
  }
}
```

### 2.2 Get Balance (JSON-RPC)
**Endpoint:** `POST /rpc`

**Request Body:**
```json
{
  "jsonrpc": "2.0",
  "method": "dinari_getBalance",
  "params": ["DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu"],
  "id": 1
}
```

---

## 3. TRANSACTION OPERATIONS

### 3.1 Get All Transactions (NEW!)
**Endpoint:** `GET /api/blockchain/transactions`

**Query Parameters:**
- `start` (optional): Starting index (default: 0)
- `limit` (optional): Number of transactions to return (default: 50, max: 100)

**Example:**
```
GET /api/blockchain/transactions?start=0&limit=20
```

**Response:**
```json
{
  "success": true,
  "transactions": [
    {
      "hash": "DTx1234567890abcdef...",
      "from_address": "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
      "to_address": "DT1sv9m0g077juqa67h64zxzr26k5xu5rcp8c9qvx",
      "amount": "100",
      "gas_price": "0.001",
      "gas_limit": 21000,
      "timestamp": 1729773600,
      "nonce": 0
    }
  ],
  "total": 125,
  "has_more": true,
  "start_index": 0,
  "limit": 20,
  "returned": 20
}
```

### 3.2 Get Transactions for Specific Address (NEW!)
**Endpoint:** `GET /api/blockchain/transactions/{address}`

**Query Parameters:**
- `start` (optional): Starting index (default: 0)
- `limit` (optional): Number of transactions (default: 50, max: 100)

**Example:**
```
GET /api/blockchain/transactions/DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu?limit=10
```

**Response:**
```json
{
  "success": true,
  "address": "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
  "transactions": [...],
  "total": 15,
  "has_more": false
}
```

### 3.3 Submit a DINARI Transaction
**Endpoint:** `POST /api/blockchain/transaction`

**Request Body:**
```json
{
  "from_address": "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
  "to_address": "DT1sv9m0g077juqa67h64zxzr26k5xu5rcp8c9qvx",
  "amount": "100",
  "gas_price": "0.001",
  "gas_limit": 21000,
  "nonce": 0,
  "data": "Transfer 100 DINARI"
}
```

**Response:**
```json
{
  "success": true,
  "transaction_hash": "DTx1234567890abcdef...",
  "message": "Transaction submitted successfully",
  "from_genesis": true,
  "to_genesis": true
}
```

### 3.4 Get Recent Transactions (JSON-RPC)
**Endpoint:** `POST /rpc`

**Request Body:**
```json
{
  "jsonrpc": "2.0",
  "method": "dinari_getRecentTransactions",
  "params": [50, 0],
  "id": 1
}
```
*Parameters: [limit, start_index]*

---

## 4. AFC TOKEN OPERATIONS (MINING/MINTING)

### 4.1 Mint AFC Tokens ⭐
**Endpoint:** `POST /api/contracts/call`

**Request Body:**
```json
{
  "contract_id": "afrocoin_stablecoin",
  "function_name": "mint_afc",
  "caller": "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
  "args": {
    "amount": "1000"
  },
  "value": "0"
}
```

**Response:**
```json
{
  "success": true,
  "result": "Minted 1000 AFC tokens",
  "gas_used": 31000,
  "error": null,
  "caller_is_genesis": true
}
```

### 4.2 Transfer AFC Tokens
**Endpoint:** `POST /api/contracts/call`

**Request Body:**
```json
{
  "contract_id": "afrocoin_stablecoin",
  "function_name": "transfer_afc",
  "caller": "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
  "args": {
    "to": "DT1sv9m0g077juqa67h64zxzr26k5xu5rcp8c9qvx",
    "amount": "100"
  }
}
```

### 4.3 Burn AFC Tokens
**Endpoint:** `POST /api/contracts/call`

**Request Body:**
```json
{
  "contract_id": "afrocoin_stablecoin",
  "function_name": "burn_afc",
  "caller": "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
  "args": {
    "amount": "50"
  }
}
```

### 4.4 Check AFC Balance of Address
**Endpoint:** `POST /api/contracts/call`

**Request Body:**
```json
{
  "contract_id": "afrocoin_stablecoin",
  "function_name": "afc_balance_of",
  "caller": "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
  "args": {
    "address": "DT1sv9m0g077juqa67h64zxzr26k5xu5rcp8c9qvx"
  }
}
```

### 4.5 Get Total AFC Supply
**Endpoint:** `POST /api/contracts/call`

**Request Body:**
```json
{
  "contract_id": "afrocoin_stablecoin",
  "function_name": "afc_total_supply",
  "caller": "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
  "args": {}
}
```

---

## 5. BLOCKCHAIN INFO

### 5.1 Get Blockchain Info (REST)
**Endpoint:** `GET /api/blockchain/info`

**Response:**
```json
{
  "network_id": "dinari_mainnet",
  "native_token": "DINARI",
  "stablecoin": "AFC",
  "height": 150,
  "total_transactions": 325,
  "pending_transactions": 2,
  "validators": 3,
  "contracts": 1,
  "total_dinari_supply": "100000000",
  "mining_active": true
}
```

### 5.2 Get Blockchain Info (JSON-RPC)
**Endpoint:** `POST /rpc`

**Request Body:**
```json
{
  "jsonrpc": "2.0",
  "method": "dinari_getBlockchainInfo",
  "params": [],
  "id": 1
}
```

### 5.3 Get Genesis Addresses
**Endpoint:** `GET /api/genesis/addresses`

**Or via RPC:**
```json
{
  "jsonrpc": "2.0",
  "method": "dinari_getGenesisAddresses",
  "params": [],
  "id": 1
}
```

---

## 6. COMPLETE TESTING WORKFLOW

### Test 1: Create Wallet and Check Balance
1. Create wallet using `dinari_createWallet`
2. Save the returned address
3. Check balance using `GET /api/blockchain/balance/{address}`

### Test 2: Mine AFC Tokens
1. Use your wallet address or a genesis address
2. Call `mint_afc` contract function with amount (e.g., 1000)
3. Check balance again to verify AFC tokens were added
4. Wait 15 seconds for block to be mined
5. Get all transactions to see your mint transaction

### Test 3: Transfer DINARI
1. Submit transaction from genesis address to your wallet
2. Wait for block mining (~15 seconds)
3. Check both addresses' balances
4. Get transaction history for both addresses

### Test 4: View All Transactions
1. Call `GET /api/blockchain/transactions?limit=100`
2. Verify you see ALL transactions including:
   - Genesis block transactions
   - Your minted AFC tokens
   - Your DINARI transfers
3. Paginate through results if total > 100

### Test 5: Address-Specific Transactions
1. Get transactions for a specific address
2. Verify both sent and received transactions appear
3. Test pagination with different start/limit values

---

## 7. GENESIS ADDRESSES FOR TESTING

These addresses have pre-allocated DINARI and can mint AFC:

```
DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu  (30M DINARI + 200M AFC)
DT1sv9m0g077juqa67h64zxzr26k5xu5rcp8c9qvx  (25M DINARI)
DT1cqgze3fqpw0dqh9j8l2dqqyr89c0q5c2jdpg8x  (20M DINARI)
DT1xz2f8l8lh8vqw3r6n4s2k7j9p1d5g8h3m6c4v7  (15M DINARI)
DT1a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5  (10M DINARI)
```

---

## 8. COMMON ERRORS & SOLUTIONS

### "Blockchain not initialized"
- Server may still be starting up
- Wait a few seconds and try again

### "Invalid DT address format"
- Address must start with "DT"
- Must be 42 characters long (or be a whitelisted genesis address)

### "Transaction storage not available"
- Permanent storage may be rebuilding
- The first call will rebuild indices from blocks
- Subsequent calls will be fast

### "Contract not found"
- Use exact contract ID: `afrocoin_stablecoin`
- Contract is deployed at genesis, should always exist

---

## 9. PAGINATION TIPS

**For Large Transaction Lists:**
- Start with `limit=50` to get first 50 transactions
- Check `has_more` in response
- Increment `start` by `limit` to get next page:
  - Page 1: `start=0&limit=50`
  - Page 2: `start=50&limit=50`
  - Page 3: `start=100&limit=50`

**Response Fields:**
- `total`: Total number of transactions available
- `has_more`: Boolean indicating if more transactions exist
- `returned`: Actual number of transactions in current response
- `start_index`: The index you requested

---

## 10. POSTMAN ENVIRONMENT VARIABLES

Create these variables in Postman for easier testing:

```
base_url: http://localhost:5000
my_address: DT1... (your wallet address)
genesis_address: DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu
```

Then use them in requests:
```
{{base_url}}/api/blockchain/balance/{{my_address}}
```

---

## Need Help?

- All transactions are permanent and never deleted
- Blocks are mined automatically every 15 seconds
- AFC tokens are minted via smart contract, not traditional mining
- Genesis addresses have special privileges

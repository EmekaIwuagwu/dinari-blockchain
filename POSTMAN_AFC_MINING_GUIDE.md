# How to Mine/Mint AFC Tokens - Postman Guide

## Overview
AFC (Afrocoin) tokens are minted through the Afrocoin smart contract deployed on the Dinari blockchain.

## Prerequisites
- A valid DT-prefixed wallet address
- Access to the blockchain API endpoint

## Method 1: Mint AFC Tokens via Smart Contract

### Endpoint
```
POST /api/contracts/call
```

### Request Headers
```json
Content-Type: application/json
```

### Request Body
```json
{
  "contract_id": "afrocoin_stablecoin",
  "function_name": "mint_afc",
  "caller": "YOUR_DT_WALLET_ADDRESS",
  "args": {
    "amount": "1000"
  },
  "value": "0"
}
```

### Example Request (Replace YOUR_DT_WALLET_ADDRESS)
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

### Expected Response
```json
{
  "success": true,
  "result": "Minted 1000 AFC tokens",
  "gas_used": 31000,
  "error": null,
  "caller_is_genesis": true
}
```

## Method 2: Using JSON-RPC Endpoint

You can also use the RPC endpoint to call the contract.

### Endpoint
```
POST /rpc
```

### Request Body
```json
{
  "jsonrpc": "2.0",
  "method": "dinari_callContract",
  "params": [
    "afrocoin_stablecoin",
    "mint_afc",
    "YOUR_DT_WALLET_ADDRESS",
    {"amount": "1000"}
  ],
  "id": 1
}
```

## Checking Your AFC Balance

### Via REST API
```
GET /api/blockchain/balance/{YOUR_DT_ADDRESS}
```

### Via JSON-RPC
```json
{
  "jsonrpc": "2.0",
  "method": "dinari_getBalance",
  "params": ["YOUR_DT_ADDRESS"],
  "id": 1
}
```

### Expected Balance Response
```json
{
  "address": "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
  "address_format": "DT-prefixed",
  "is_genesis": true,
  "balances": {
    "DINARI": "30000000",
    "AFC": "1000"
  }
}
```

## Other AFC Functions Available

### Check AFC Balance of Any Address
```json
{
  "contract_id": "afrocoin_stablecoin",
  "function_name": "afc_balance_of",
  "caller": "YOUR_DT_ADDRESS",
  "args": {
    "address": "TARGET_DT_ADDRESS"
  }
}
```

### Transfer AFC Tokens
```json
{
  "contract_id": "afrocoin_stablecoin",
  "function_name": "transfer_afc",
  "caller": "YOUR_DT_ADDRESS",
  "args": {
    "to": "RECIPIENT_DT_ADDRESS",
    "amount": "100"
  }
}
```

### Burn AFC Tokens
```json
{
  "contract_id": "afrocoin_stablecoin",
  "function_name": "burn_afc",
  "caller": "YOUR_DT_ADDRESS",
  "args": {
    "amount": "50"
  }
}
```

### Get Total AFC Supply
```json
{
  "contract_id": "afrocoin_stablecoin",
  "function_name": "afc_total_supply",
  "caller": "YOUR_DT_ADDRESS",
  "args": {}
}
```

## Testing Workflow in Postman

### Step 1: Get Your Wallet Address
If you don't have one, create it:

**Request:**
```
POST /rpc
```
```json
{
  "jsonrpc": "2.0",
  "method": "dinari_createWallet",
  "params": ["my_wallet"],
  "id": 1
}
```

**Response will include your DT address.**

### Step 2: Check Initial Balance
```
GET /api/blockchain/balance/{YOUR_ADDRESS}
```

### Step 3: Mint AFC Tokens
Use the mint request from Method 1 above.

### Step 4: Verify Balance Updated
Check balance again to confirm AFC tokens were minted.

### Step 5: Test Transfer (Optional)
Create another wallet and transfer some AFC to it.

## Common Errors

### "Invalid caller address"
- Make sure your address starts with "DT"
- Address must be 42 characters long (or be a genesis address)

### "Contract not found"
- The Afrocoin contract should be deployed at genesis
- Contract ID must be exactly: `afrocoin_stablecoin`

### "Insufficient balance"
- For burning or transferring, make sure you have enough AFC

## Notes
- AFC tokens are created instantly via smart contract
- Each mint operation costs gas (in DINARI)
- Transactions are automatically mined into blocks every 15 seconds
- Genesis addresses have special privileges and can mint freely

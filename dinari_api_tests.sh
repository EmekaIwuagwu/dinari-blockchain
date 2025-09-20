# DinariBlockchain JSON-RPC Testing Guide
# Base URL: https://dinariblockchain-testnet.onrender.com/rpc

BASE_URL="https://dinariblockchain-testnet.onrender.com/rpc"

# =====================================================
# 1. CREATE WALLET
# =====================================================
echo "1. Testing dinari_createWallet..."
curl -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "dinari_createWallet",
    "params": ["test_wallet_1"],
    "id": 1
  }'

# Expected Response:
# {
#   "jsonrpc": "2.0",
#   "result": {
#     "success": true,
#     "wallet_name": "test_wallet_1",
#     "message": "Wallet created successfully",
#     "address": "DT1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0",
#     "address_format": "DT-prefixed",
#     "is_genesis": false
#   },
#   "id": 1
# }

echo -e "\n\n"

# =====================================================
# 2. GENERATE ADDRESS
# =====================================================
echo "2. Testing dinari_generateAddress..."
curl -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "dinari_generateAddress",
    "params": ["my_seed_123"],
    "id": 2
  }'

# Expected Response:
# {
#   "jsonrpc": "2.0",
#   "result": {
#     "address": "DT1f2e3d4c5b6a7890abcdef1234567890abcdef12",
#     "address_format": "DT-prefixed",
#     "length": 42,
#     "is_genesis": false
#   },
#   "id": 2
# }

echo -e "\n\n"

# =====================================================
# 3. VALIDATE ADDRESS
# =====================================================
echo "3. Testing dinari_validateAddress..."
curl -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "dinari_validateAddress",
    "params": ["DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu"],
    "id": 3
  }'

# Expected Response:
# {
#   "jsonrpc": "2.0",
#   "result": {
#     "address": "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
#     "is_valid": true,
#     "is_genesis": true,
#     "length": 42,
#     "prefix": "DT",
#     "hash_part": "1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
#     "expected_format": "DT + 40 hex characters",
#     "expected_length": 42
#   },
#   "id": 3
# }

echo -e "\n\n"

# =====================================================
# 4. GET BALANCE (Genesis Address)
# =====================================================
echo "4. Testing dinari_getBalance (Genesis Treasury)..."
curl -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "dinari_getBalance",
    "params": ["DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu"],
    "id": 4
  }'

# Expected Response:
# {
#   "jsonrpc": "2.0",
#   "result": {
#     "address": "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
#     "is_genesis": true,
#     "DINARI": "30000000",
#     "AFC": "200000000"
#   },
#   "id": 4
# }

echo -e "\n\n"

# =====================================================
# 5. GET BLOCKCHAIN INFO
# =====================================================
echo "5. Testing dinari_getBlockchainInfo..."
curl -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "dinari_getBlockchainInfo",
    "params": [],
    "id": 5
  }'

# Expected Response:
# {
#   "jsonrpc": "2.0",
#   "result": {
#     "network_id": "dinari_mainnet",
#     "native_token": "DINARI",
#     "stablecoin": "AFC",
#     "address_format": "DT-prefixed",
#     "genesis_compatibility": true,
#     "known_genesis_addresses": 5,
#     "height": 15,
#     "total_transactions": 8,
#     "pending_transactions": 0,
#     "validators": 3,
#     "contracts": 1,
#     "total_dinari_supply": "100000000",
#     "total_afc_supply": "200000000",
#     "mining_active": true
#   },
#   "id": 5
# }

echo -e "\n\n"

# =====================================================
# 6. GET GENESIS ADDRESSES
# =====================================================
echo "6. Testing dinari_getGenesisAddresses..."
curl -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "dinari_getGenesisAddresses",
    "params": [],
    "id": 6
  }'

# Expected Response:
# {
#   "jsonrpc": "2.0",
#   "result": {
#     "total_genesis_addresses": 5,
#     "genesis_addresses": [
#       {
#         "address": "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
#         "is_valid": true,
#         "is_genesis": true,
#         "balances": {
#           "DINARI": "30000000",
#           "AFC": "200000000"
#         }
#       },
#       // ... other 4 genesis addresses
#     ]
#   },
#   "id": 6
# }

echo -e "\n\n"

# =====================================================
# 7. FUND FROM GENESIS (Testing)
# =====================================================
echo "7. Testing dinari_fundFromGenesis..."
curl -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "dinari_fundFromGenesis",
    "params": ["DT1f2e3d4c5b6a7890abcdef1234567890abcdef12", "1000"],
    "id": 7
  }'

# Expected Response:
# {
#   "jsonrpc": "2.0",
#   "result": {
#     "success": true,
#     "transaction_hash": "abc123def456...",
#     "from_genesis": "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
#     "to_address": "DT1f2e3d4c5b6a7890abcdef1234567890abcdef12",
#     "amount": "1000"
#   },
#   "id": 7
# }

echo -e "\n\n"

# =====================================================
# 8. SEND TRANSACTION
# =====================================================
echo "8. Testing dinari_sendTransaction..."
curl -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "dinari_sendTransaction",
    "params": [
      "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
      "DT1sv9m0g077juqa67h64zxzr26k5xu5rcp8c9qvx",
      "500",
      "0.001",
      "Test transaction"
    ],
    "id": 8
  }'

# Expected Response:
# {
#   "jsonrpc": "2.0",
#   "result": {
#     "success": true,
#     "transaction_hash": "def789abc123...",
#     "from": "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
#     "to": "DT1sv9m0g077juqa67h64zxzr26k5xu5rcp8c9qvx",
#     "amount": "500",
#     "gas_price": "0.001",
#     "from_genesis": true,
#     "to_genesis": true
#   },
#   "id": 8
# }

echo -e "\n\n"

# =====================================================
# 9. CALL CONTRACT (AFC Balance)
# =====================================================
echo "9. Testing dinari_callContract (AFC balance)..."
curl -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "dinari_callContract",
    "params": [
      "afrocoin_stablecoin",
      "afc_balance_of",
      "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
      {"address": "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu"}
    ],
    "id": 9
  }'

# Expected Response:
# {
#   "jsonrpc": "2.0",
#   "result": {
#     "success": true,
#     "result": "200000000",
#     "gas_used": 26000,
#     "error": null,
#     "caller_is_genesis": true
#   },
#   "id": 9
# }

echo -e "\n\n"

# =====================================================
# 10. DEPLOY CONTRACT
# =====================================================
echo "10. Testing dinari_deployContract..."
curl -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "dinari_deployContract",
    "params": [
      "def simple_storage():\n    return \"Hello from contract!\"",
      "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
      {"initial_value": "test"}
    ],
    "id": 10
  }'

# Expected Response:
# {
#   "jsonrpc": "2.0",
#   "result": {
#     "success": true,
#     "contract_id": "contract_1726761234",
#     "deployer": "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
#     "deployer_is_genesis": true,
#     "contract_address": "contract_1726761234"
#   },
#   "id": 10
# }

echo -e "\n\n"

# =====================================================
# 11. GET AFC SUPPLY
# =====================================================
echo "11. Testing dinari_getAfcSupply..."
curl -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "dinari_getAfcSupply",
    "params": [],
    "id": 11
  }'

# Expected Response:
# {
#   "jsonrpc": "2.0",
#   "result": {
#     "total_afc_supply": "200000000",
#     "symbol": "AFC",
#     "name": "Afrocoin",
#     "contract_id": "afrocoin_stablecoin",
#     "backed_by": "DINARI"
#   },
#   "id": 11
# }

echo -e "\n\n"

# =====================================================
# BONUS: Test with Python
# =====================================================
echo "Python testing example:"
cat << 'EOF'
import requests
import json

def test_rpc_method(method, params=None, id_num=1):
    url = "https://dinariblockchain-testnet.onrender.com/rpc"
    
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or [],
        "id": id_num
    }
    
    response = requests.post(url, json=payload)
    return response.json()

# Test blockchain info
result = test_rpc_method("dinari_getBlockchainInfo")
print("Blockchain Info:", json.dumps(result, indent=2))

# Test balance check
result = test_rpc_method("dinari_getBalance", ["DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu"])
print("Balance:", json.dumps(result, indent=2))

# Test AFC supply
result = test_rpc_method("dinari_getAfcSupply")
print("AFC Supply:", json.dumps(result, indent=2))
EOF

echo -e "\n\nAll tests completed! Check the responses for each method."
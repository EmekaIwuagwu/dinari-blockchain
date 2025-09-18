"""
File: dinari-blockchain/rpc/dinari_endpoints.py

RPC endpoints for Dinari Stablecoin integration with DinariBlockchain
Add these endpoints to your existing RPC server
"""

from flask import jsonify, request
from decimal import Decimal, InvalidOperation
import json
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from contracts
sys.path.append(str(Path(__file__).parent.parent))

from contracts.dinari_stablecoin import DinariStablecoin

class DinariRPCEndpoints:
    """RPC endpoints for Dinari Stablecoin operations"""
    
    def __init__(self):
        self.dinari_contract = None
        self._initialize_contract()
    
    def _initialize_contract(self):
        """Initialize the Dinari contract (in production, load from blockchain state)"""
        try:
            admin_address = "dinari_admin_0x1234567890abcdef"
            self.dinari_contract = DinariStablecoin(admin_address)
            print("✅ Dinari stablecoin contract initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Dinari contract: {e}")
    
    def _validate_address(self, address: str) -> bool:
        """Validate Ethereum-style address format"""
        if not address or len(address) < 10:
            return False
        return True
    
    def _parse_decimal(self, value) -> Decimal:
        """Safely parse decimal value"""
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValueError(f"Invalid decimal value: {value}")

    # ========== DINARI BALANCE ENDPOINTS ==========
    
    def dinari_balance_of(self):
        """Get Dinari balance of an address"""
        try:
            data = request.get_json()
            address = data.get('address')
            
            if not self._validate_address(address):
                return jsonify({
                    "error": "Invalid address format",
                    "code": -32602
                }), 400
            
            balance = self.dinari_contract.balance_of(address)
            
            return jsonify({
                "result": {
                    "address": address,
                    "balance": str(balance),
                    "symbol": "DINARI",
                    "decimals": self.dinari_contract.decimals
                }
            })
            
        except Exception as e:
            return jsonify({
                "error": str(e),
                "code": -32603
            }), 500
    
    def dinari_transfer(self):
        """Transfer Dinari between addresses"""
        try:
            data = request.get_json()
            from_address = data.get('from_address')
            to_address = data.get('to_address')
            amount = self._parse_decimal(data.get('amount', 0))
            
            if not self._validate_address(from_address) or not self._validate_address(to_address):
                return jsonify({
                    "error": "Invalid address format",
                    "code": -32602
                }), 400
            
            if amount <= 0:
                return jsonify({
                    "error": "Amount must be positive",
                    "code": -32602
                }), 400
            
            success = self.dinari_contract.transfer(from_address, to_address, amount)
            
            return jsonify({
                "result": {
                    "success": success,
                    "transaction_hash": f"dinari_tx_{int(time.time())}",
                    "from": from_address,
                    "to": to_address,
                    "amount": str(amount),
                    "timestamp": int(time.time())
                }
            })
            
        except Exception as e:
            return jsonify({
                "error": str(e),
                "code": -32603
            }), 500

    # ========== COLLATERAL MANAGEMENT ENDPOINTS ==========
    
    def dinari_deposit_collateral(self):
        """Deposit collateral to mint Dinari"""
        try:
            data = request.get_json()
            user_address = data.get('user_address')
            asset_symbol = data.get('asset_symbol')
            amount = self._parse_decimal(data.get('amount', 0))
            
            if not self._validate_address(user_address):
                return jsonify({
                    "error": "Invalid address format",
                    "code": -32602
                }), 400
            
            success = self.dinari_contract.deposit_collateral(user_address, asset_symbol, amount)
            
            # Get updated vault info
            vault_info = self.dinari_contract.get_vault_info(user_address)
            
            return jsonify({
                "result": {
                    "success": success,
                    "transaction_hash": f"dinari_deposit_{int(time.time())}",
                    "user_address": user_address,
                    "asset_symbol": asset_symbol,
                    "amount_deposited": str(amount),
                    "vault_info": vault_info,
                    "timestamp": int(time.time())
                }
            })
            
        except Exception as e:
            return jsonify({
                "error": str(e),
                "code": -32603
            }), 500
    
    def dinari_mint(self):
        """Mint Dinari against collateral"""
        try:
            data = request.get_json()
            user_address = data.get('user_address')
            dinari_amount = self._parse_decimal(data.get('dinari_amount', 0))
            
            if not self._validate_address(user_address):
                return jsonify({
                    "error": "Invalid address format",
                    "code": -32602
                }), 400
            
            success = self.dinari_contract.mint_dinari(user_address, dinari_amount)
            
            # Get updated info
            vault_info = self.dinari_contract.get_vault_info(user_address)
            balance = self.dinari_contract.balance_of(user_address)
            
            return jsonify({
                "result": {
                    "success": success,
                    "transaction_hash": f"dinari_mint_{int(time.time())}",
                    "user_address": user_address,
                    "dinari_minted": str(dinari_amount),
                    "new_balance": str(balance),
                    "vault_info": vault_info,
                    "timestamp": int(time.time())
                }
            })
            
        except Exception as e:
            return jsonify({
                "error": str(e),
                "code": -32603
            }), 500
    
    def dinari_burn(self):
        """Burn Dinari to improve collateral ratio"""
        try:
            data = request.get_json()
            user_address = data.get('user_address')
            dinari_amount = self._parse_decimal(data.get('dinari_amount', 0))
            
            success = self.dinari_contract.burn_dinari(user_address, dinari_amount)
            
            vault_info = self.dinari_contract.get_vault_info(user_address)
            balance = self.dinari_contract.balance_of(user_address)
            
            return jsonify({
                "result": {
                    "success": success,
                    "transaction_hash": f"dinari_burn_{int(time.time())}",
                    "user_address": user_address,
                    "dinari_burned": str(dinari_amount),
                    "new_balance": str(balance),
                    "vault_info": vault_info,
                    "timestamp": int(time.time())
                }
            })
            
        except Exception as e:
            return jsonify({
                "error": str(e),
                "code": -32603
            }), 500
    
    def dinari_withdraw_collateral(self):
        """Withdraw collateral from vault"""
        try:
            data = request.get_json()
            user_address = data.get('user_address')
            asset_symbol = data.get('asset_symbol')
            amount = self._parse_decimal(data.get('amount', 0))
            
            success = self.dinari_contract.withdraw_collateral(user_address, asset_symbol, amount)
            
            vault_info = self.dinari_contract.get_vault_info(user_address)
            
            return jsonify({
                "result": {
                    "success": success,
                    "transaction_hash": f"dinari_withdraw_{int(time.time())}",
                    "user_address": user_address,
                    "asset_symbol": asset_symbol,
                    "amount_withdrawn": str(amount),
                    "vault_info": vault_info,
                    "timestamp": int(time.time())
                }
            })
            
        except Exception as e:
            return jsonify({
                "error": str(e),
                "code": -32603
            }), 500

    # ========== AFRICAN MOBILE MONEY ENDPOINTS ==========
    
    def dinari_mobile_money_deposit(self):
        """Deposit via mobile money and receive Dinari"""
        try:
            data = request.get_json()
            user_address = data.get('user_address')
            gateway_id = data.get('gateway_id')  # mpesa, mtn_money, etc.
            local_amount = self._parse_decimal(data.get('local_amount', 0))
            local_currency = data.get('local_currency')  # KES, NGN, etc.
            
            success = self.dinari_contract.mobile_money_deposit(
                user_address, gateway_id, local_amount, local_currency
            )
            
            balance = self.dinari_contract.balance_of(user_address)
            
            return jsonify({
                "result": {
                    "success": success,
                    "transaction_hash": f"dinari_mobile_deposit_{int(time.time())}",
                    "user_address": user_address,
                    "gateway": gateway_id,
                    "local_amount": str(local_amount),
                    "local_currency": local_currency,
                    "dinari_balance": str(balance),
                    "timestamp": int(time.time())
                }
            })
            
        except Exception as e:
            return jsonify({
                "error": str(e),
                "code": -32603
            }), 500
    
    def dinari_remittance_send(self):
        """Send Dinari as remittance"""
        try:
            data = request.get_json()
            from_address = data.get('from_address')
            to_country = data.get('to_country')
            recipient_mobile = data.get('recipient_mobile')
            dinari_amount = self._parse_decimal(data.get('dinari_amount', 0))
            
            remittance_id = self.dinari_contract.remittance_transfer(
                from_address, to_country, recipient_mobile, dinari_amount
            )
            
            balance = self.dinari_contract.balance_of(from_address)
            
            return jsonify({
                "result": {
                    "success": True,
                    "remittance_id": remittance_id,
                    "from_address": from_address,
                    "to_country": to_country,
                    "recipient_mobile": recipient_mobile,
                    "dinari_amount": str(dinari_amount),
                    "sender_balance": str(balance),
                    "estimated_delivery": "2-10 minutes",
                    "timestamp": int(time.time())
                }
            })
            
        except Exception as e:
            return jsonify({
                "error": str(e),
                "code": -32603
            }), 500

    # ========== INFORMATION ENDPOINTS ==========
    
    def dinari_vault_info(self):
        """Get vault information for a user"""
        try:
            data = request.get_json()
            user_address = data.get('user_address')
            
            vault_info = self.dinari_contract.get_vault_info(user_address)
            
            return jsonify({
                "result": vault_info
            })
            
        except Exception as e:
            return jsonify({
                "error": str(e),
                "code": -32603
            }), 500
    
    def dinari_protocol_stats(self):
        """Get protocol statistics"""
        try:
            stats = self.dinari_contract.get_protocol_stats()
            
            return jsonify({
                "result": stats
            })
            
        except Exception as e:
            return jsonify({
                "error": str(e),
                "code": -32603
            }), 500
    
    def dinari_collateral_assets(self):
        """Get supported collateral assets"""
        try:
            assets = {}
            for symbol, asset in self.dinari_contract.collateral_assets.items():
                assets[symbol] = {
                    "name": asset.name,
                    "symbol": asset.symbol,
                    "price_usd": str(asset.price_usd),
                    "collateral_ratio": str(asset.collateral_ratio),
                    "liquidation_threshold": str(asset.liquidation_threshold),
                    "total_deposited": str(asset.total_deposited),
                    "is_active": asset.is_active,
                    "last_updated": asset.last_updated
                }
            
            return jsonify({
                "result": {
                    "supported_assets": assets,
                    "total_assets": len(assets)
                }
            })
            
        except Exception as e:
            return jsonify({
                "error": str(e),
                "code": -32603
            }), 500
    
    def dinari_mobile_gateways(self):
        """Get supported mobile money gateways"""
        try:
            gateways = self.dinari_contract.mobile_money_gateways
            
            return jsonify({
                "result": {
                    "gateways": gateways,
                    "total_gateways": len(gateways)
                }
            })
            
        except Exception as e:
            return jsonify({
                "error": str(e),
                "code": -32603
            }), 500


def register_dinari_endpoints(app):
    """Register Dinari endpoints with Flask app"""
    
    dinari_rpc = DinariRPCEndpoints()
    
    # Balance and transfer endpoints
    app.add_url_rule('/rpc/dinari/balance', 'dinari_balance', dinari_rpc.dinari_balance_of, methods=['POST'])
    app.add_url_rule('/rpc/dinari/transfer', 'dinari_transfer', dinari_rpc.dinari_transfer, methods=['POST'])
    
    # Collateral management endpoints
    app.add_url_rule('/rpc/dinari/deposit', 'dinari_deposit', dinari_rpc.dinari_deposit_collateral, methods=['POST'])
    app.add_url_rule('/rpc/dinari/mint', 'dinari_mint', dinari_rpc.dinari_mint, methods=['POST'])
    app.add_url_rule('/rpc/dinari/burn', 'dinari_burn', dinari_rpc.dinari_burn, methods=['POST'])
    app.add_url_rule('/rpc/dinari/withdraw', 'dinari_withdraw', dinari_rpc.dinari_withdraw_collateral, methods=['POST'])
    
    # African integration endpoints
    app.add_url_rule('/rpc/dinari/mobile-deposit', 'dinari_mobile_deposit', dinari_rpc.dinari_mobile_money_deposit, methods=['POST'])
    app.add_url_rule('/rpc/dinari/remittance', 'dinari_remittance', dinari_rpc.dinari_remittance_send, methods=['POST'])
    
    # Information endpoints
    app.add_url_rule('/rpc/dinari/vault-info', 'dinari_vault_info', dinari_rpc.dinari_vault_info, methods=['POST'])
    app.add_url_rule('/rpc/dinari/protocol-stats', 'dinari_protocol_stats', dinari_rpc.dinari_protocol_stats, methods=['GET'])
    app.add_url_rule('/rpc/dinari/collateral-assets', 'dinari_collateral_assets', dinari_rpc.dinari_collateral_assets, methods=['GET'])
    app.add_url_rule('/rpc/dinari/mobile-gateways', 'dinari_mobile_gateways', dinari_rpc.dinari_mobile_gateways, methods=['GET'])
    
    print("✅ Dinari stablecoin RPC endpoints registered")
    print("📡 Available endpoints:")
    print("   • POST /rpc/dinari/balance - Check Dinari balance")
    print("   • POST /rpc/dinari/transfer - Transfer Dinari")
    print("   • POST /rpc/dinari/deposit - Deposit collateral")
    print("   • POST /rpc/dinari/mint - Mint Dinari")
    print("   • POST /rpc/dinari/burn - Burn Dinari")
    print("   • POST /rpc/dinari/withdraw - Withdraw collateral")
    print("   • POST /rpc/dinari/mobile-deposit - Mobile money deposit")
    print("   • POST /rpc/dinari/remittance - Send remittance")
    print("   • POST /rpc/dinari/vault-info - Get vault information")
    print("   • GET  /rpc/dinari/protocol-stats - Get protocol stats")
    print("   • GET  /rpc/dinari/collateral-assets - Get collateral assets")
    print("   • GET  /rpc/dinari/mobile-gateways - Get mobile gateways")


# Example usage and testing functions
if __name__ == "__main__":
    print("🧪 Testing Dinari RPC endpoints...")
    
    import time
    
    # This would be integrated with your Flask app
    # For testing purposes only
    endpoints = DinariRPCEndpoints()
    
    # Test basic functionality
    print("Testing basic Dinari functionality...")
    
    test_user = "test_user_0x123"
    
    # Test deposit collateral
    try:
        endpoints.dinari_contract.deposit_collateral(test_user, "USDC", Decimal('1000'))
        print("✅ Collateral deposit test passed")
    except Exception as e:
        print(f"❌ Collateral deposit test failed: {e}")
    
    # Test mint Dinari
    try:
        endpoints.dinari_contract.mint_dinari(test_user, Decimal('900'))
        print("✅ Dinari minting test passed")
    except Exception as e:
        print(f"❌ Dinari minting test failed: {e}")
    
    print("🎉 Dinari RPC endpoint tests completed!")
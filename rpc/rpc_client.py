#!/usr/bin/env python3
"""
DinariBlockchain RPC Client
rpc/rpc_client.py - Client for JSON-RPC calls
"""

import json
import requests
import time
import sys
import os
from typing import Dict, Any, List, Optional

class DinariRPCClient:
    """Client for DinariBlockchain JSON-RPC API"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8545):
        self.url = f"http://{host}:{port}/rpc"
        self.session = requests.Session()
        self.request_id = 0
    
    def _make_request(self, method: str, params: List = None) -> Dict[str, Any]:
        """Make JSON-RPC request"""
        if params is None:
            params = []
        
        self.request_id += 1
        
        payload = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': self.request_id
        }
        
        try:
            response = self.session.post(self.url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'error' in result:
                raise Exception(f"RPC Error: {result['error']['message']}")
            
            return result.get('result')
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {e}")
    
    # Blockchain Methods
    def get_blockchain_info(self) -> Dict[str, Any]:
        """Get blockchain information"""
        return self._make_request('dinari_getBlockchainInfo')
    
    def get_balance(self, address: str) -> str:
        """Get account balance"""
        return self._make_request('dinari_getBalance', [address])
    
    def get_block(self, block_index: int) -> Dict[str, Any]:
        """Get block by index"""
        return self._make_request('dinari_getBlock', [block_index])
    
    def send_transaction(self, from_addr: str, to_addr: str, amount: str, fee: str = "0.001") -> Dict[str, Any]:
        """Send transaction"""
        return self._make_request('dinari_sendTransaction', [from_addr, to_addr, amount, fee])
    
    def create_wallet(self, wallet_name: str = None) -> Dict[str, Any]:
        """Create new wallet"""
        params = [wallet_name] if wallet_name else []
        return self._make_request('dinari_createWallet', params)
    
    # Smart Contract Methods
    def deploy_contract(self, contract_code: str, deployer: str, init_args: List = None) -> Dict[str, Any]:
        """Deploy smart contract"""
        if init_args is None:
            init_args = []
        return self._make_request('dinari_deployContract', [contract_code, deployer, init_args])
    
    def call_contract(self, contract_address: str, function_name: str, caller: str, args: List = None) -> Dict[str, Any]:
        """Call contract function"""
        if args is None:
            args = []
        return self._make_request('dinari_callContract', [contract_address, function_name, caller, args])
    
    def get_contract_info(self, contract_address: str) -> Dict[str, Any]:
        """Get contract information"""
        return self._make_request('dinari_getContractInfo', [contract_address])
    
    # Network Methods
    def get_network_info(self) -> Dict[str, Any]:
        """Get network information"""
        return self._make_request('dinari_getNetworkInfo')
    
    def get_peers(self) -> List[Dict[str, Any]]:
        """Get connected peers"""
        return self._make_request('dinari_getPeers')
    
    # Validator Methods
    def get_validators(self) -> List[str]:
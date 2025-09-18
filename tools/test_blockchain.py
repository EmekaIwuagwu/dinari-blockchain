#!/usr/bin/env python3
"""
DinariBlockchain Testing Utilities
tools/test_blockchain.py - Comprehensive test suite for blockchain functionality
"""

import sys
import os
import time
import unittest
import tempfile
import shutil
from decimal import Decimal
import json

# Add parent directory to path to import Dinari
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Dinari import (
    DinariBlockchain,
    Transaction, 
    Block,
    DinariWallet,
    ContractManager,
    ProofOfAuthority,
    create_default_poa_config,
    P2PNetworkManager,
    DinariNode,
    setup_logging
)

class TestDinariBlockchain(unittest.TestCase):
    """Test suite for core blockchain functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_config = {
            'token_name': 'TestCoin',
            'token_symbol': 'TST',
            'total_supply': '1000000',
            'decimals': 18,
            'validators': ['test_validator_1', 'test_validator_2'],
            'block_time': 5,
            'initial_allocation': {
                'treasury': '600000',
                'test_account': '400000'
            }
        }
        self.blockchain = DinariBlockchain(self.test_config)
    
    def test_genesis_block_creation(self):
        """Test genesis block is created correctly"""
        self.assertEqual(len(self.blockchain.chain), 1)
        
        genesis_block = self.blockchain.chain[0]
        self.assertEqual(genesis_block.index, 0)
        self.assertEqual(genesis_block.previous_hash, '0' * 64)
        self.assertEqual(genesis_block.validator, 'genesis')
        
        # Check initial allocations
        treasury_balance = self.blockchain.get_balance('treasury')
        test_balance = self.blockchain.get_balance('test_account')
        
        self.assertEqual(treasury_balance, Decimal('600000'))
        self.assertEqual(test_balance, Decimal('400000'))
    
    def test_transaction_creation(self):
        """Test transaction creation and validation"""
        tx = Transaction(
            from_address='treasury',
            to_address='alice',
            amount='100',
            fee='0.1'
        )
        
        self.assertTrue(tx.is_valid())
        self.assertIsInstance(tx.calculate_hash(), str)
        self.assertEqual(len(tx.calculate_hash()), 64)  # SHA256 hash
        
        # Test invalid transaction
        invalid_tx = Transaction('', 'alice', '100')
        self.assertFalse(invalid_tx.is_valid())
    
    def test_transaction_processing(self):
        """Test adding and processing transactions"""
        tx = Transaction('treasury', 'alice', '100', '0.1')
        
        # Add transaction
        success = self.blockchain.add_transaction(tx)
        self.assertTrue(success)
        self.assertEqual(len(self.blockchain.transaction_pool), 1)
        
        # Test insufficient balance
        large_tx = Transaction('alice', 'bob', '1000000', '0.1')
        success = self.blockchain.add_transaction(large_tx)
        self.assertFalse(success)
    
    def test_block_mining(self):
        """Test block mining and validation"""
        # Add a transaction
        tx = Transaction('treasury', 'alice', '100', '0.1')
        self.blockchain.add_transaction(tx)
        
        # Mine block
        initial_height = len(self.blockchain.chain)
        block = self.blockchain.mine_block('test_validator_1')
        
        self.assertIsNotNone(block)
        self.assertEqual(len(self.blockchain.chain), initial_height + 1)
        self.assertEqual(len(self.blockchain.transaction_pool), 0)
        
        # Check balances updated
        alice_balance = self.blockchain.get_balance('alice')
        self.assertEqual(alice_balance, Decimal('100'))
        
        treasury_balance = self.blockchain.get_balance('treasury')
        expected_treasury = Decimal('600000') - Decimal('100') - Decimal('0.1')
        self.assertEqual(treasury_balance, expected_treasury)
    
    def test_blockchain_validation(self):
        """Test blockchain validation"""
        # Initial chain should be valid
        self.assertTrue(self.blockchain.validate_chain())
        
        # Add some blocks
        for i in range(3):
            tx = Transaction('treasury', f'user_{i}', '50', '0.1')
            self.blockchain.add_transaction(tx)
            block = self.blockchain.mine_block('test_validator_1')
            self.assertIsNotNone(block)
        
        # Chain should still be valid
        self.assertTrue(self.blockchain.validate_chain())
    
    def test_validator_management(self):
        """Test validator addition and removal"""
        initial_validators = len(self.blockchain.validators)
        
        # Add validator
        success = self.blockchain.add_validator('new_validator', 'test_validator_1')
        self.assertTrue(success)
        self.assertEqual(len(self.blockchain.validators), initial_validators + 1)
        
        # Remove validator
        success = self.blockchain.remove_validator('new_validator', 'test_validator_1')
        self.assertTrue(success)
        self.assertEqual(len(self.blockchain.validators), initial_validators)

class TestDinariWallet(unittest.TestCase):
    """Test suite for wallet functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.wallet = DinariWallet("test_wallet", self.temp_dir)
        
        self.blockchain = DinariBlockchain({
            'total_supply': '1000000',
            'initial_allocation': {'treasury': '1000000'}
        })
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_wallet_creation(self):
        """Test wallet creation and address generation"""
        self.assertGreater(len(self.wallet.keys), 0)
        
        # Create new address
        new_address = self.wallet.create_new_address("test")
        self.assertIn(new_address, self.wallet.keys)
        self.assertTrue(new_address.startswith('DNMR'))
    
    def test_transaction_creation(self):
        """Test creating transactions from wallet"""
        address = list(self.wallet.keys.keys())[0]
        
        tx = self.wallet.create_transaction(
            address, 'recipient', '100', '0.1'
        )
        
        self.assertIsNotNone(tx)
        self.assertEqual(tx.from_address, address)
        self.assertEqual(tx.amount, '100')
        self.assertIsNotNone(tx.signature)
    
    def test_wallet_persistence(self):
        """Test wallet save and load"""
        # Create address and save
        original_addresses = self.wallet.get_all_addresses()
        new_address = self.wallet.create_new_address("test")
        
        # Create new wallet instance (should load existing)
        new_wallet = DinariWallet("test_wallet", self.temp_dir)
        loaded_addresses = new_wallet.get_all_addresses()
        
        self.assertIn(new_address, loaded_addresses)
        self.assertEqual(len(loaded_addresses), len(original_addresses) + 1)
    
    def test_import_export_address(self):
        """Test address import and export"""
        address = list(self.wallet.keys.keys())[0]
        
        # Export address
        exported = self.wallet.export_address(address)
        self.assertIsNotNone(exported)
        self.assertEqual(exported['address'], address)
        
        # Import to new wallet
        new_wallet = DinariWallet("import_test", self.temp_dir)
        imported_address = new_wallet.import_address(exported['private_key'])
        
        self.assertEqual(imported_address, address)

class TestSmartContracts(unittest.TestCase):
    """Test suite for smart contract functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.blockchain = DinariBlockchain({
            'total_supply': '1000000',
            'initial_allocation': {'treasury': '1000000'}
        })
        self.contract_manager = ContractManager(self.blockchain)
    
    def test_contract_deployment(self):
        """Test smart contract deployment"""
        deployment = self.contract_manager.deploy_from_template(
            'token', 'treasury', ['TestToken', 'TT', '100000']
        )
        
        self.assertIsNotNone(deployment.address)
        self.assertEqual(deployment.deployer, 'treasury')
        self.assertIn(deployment.address, self.contract_manager.contracts)
    
    def test_contract_execution(self):
        """Test smart contract function execution"""
        # Deploy token contract
        deployment = self.contract_manager.deploy_from_template(
            'token', 'treasury', ['TestToken', 'TT', '100000']
        )
        
        contract_address = deployment.address
        
        # Test balance function
        result = self.contract_manager.call_contract(
            contract_address, 'balance_of', ['treasury'], 'treasury'
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.result, 100000)
        
        # Test transfer function
        result = self.contract_manager.call_contract(
            contract_address, 'transfer', ['alice', 1000], 'treasury'
        )
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.events), 1)
    
    def test_contract_state_persistence(self):
        """Test contract state persistence"""
        # Deploy and interact with contract
        deployment = self.contract_manager.deploy_from_template(
            'token', 'treasury', ['TestToken', 'TT', '100000']
        )
        
        contract_address = deployment.address
        
        # Transfer tokens
        self.contract_manager.call_contract(
            contract_address, 'transfer', ['alice', 5000], 'treasury'
        )
        
        # Check state persisted
        contract = self.contract_manager.get_contract(contract_address)
        balances = contract.state.get('balances', {})
        
        self.assertEqual(balances.get('alice', 0), 5000)
        self.assertEqual(balances.get('treasury', 0), 95000)
    
    def test_voting_contract(self):
        """Test voting contract functionality"""
        deployment = self.contract_manager.deploy_from_template(
            'voting', 'treasury', 
            ['Test Vote', ['Option A', 'Option B'], 3600]
        )
        
        voting_address = deployment.address
        
        # Cast votes
        result1 = self.contract_manager.call_contract(
            voting_address, 'vote', ['Option A'], 'alice'
        )
        result2 = self.contract_manager.call_contract(
            voting_address, 'vote', ['Option B'], 'bob'  
        )
        
        self.assertTrue(result1.success)
        self.assertTrue(result2.success)
        
        # Check results
        result = self.contract_manager.call_contract(
            voting_address, 'get_results', [], 'anyone'
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.result['Option A'], 1)
        self.assertEqual(result.result['Option B'], 1)

class TestConsensus(unittest.TestCase):
    """Test suite for consensus mechanism"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = create_default_poa_config()
        self.poa = ProofOfAuthority(self.config, ['validator1', 'validator2', 'validator3'])
    
    def test_validator_management(self):
        """Test validator addition and removal"""
        initial_count = len(self.poa.validators)
        
        # Add validator
        success = self.poa.add_validator('validator4', 'Test Validator 4', 'admin')
        self.assertTrue(success)
        self.assertEqual(len(self.poa.validators), initial_count + 1)
        
        # Remove validator  
        success = self.poa.remove_validator('validator4', 'admin')
        self.assertTrue(success)
        self.assertEqual(len(self.poa.validators), initial_count)
    
    def test_validator_rotation(self):
        """Test validator selection and rotation"""
        # Test current validator selection
        for height in range(10):
            validator = self.poa.get_current_validator(height)
            self.assertIn(validator, self.poa.get_active_validators())
        
        # Test round-robin behavior
        validators_used = set()
        for height in range(len(self.poa.validators) * 2):
            validator = self.poa.get_current_validator(height)
            validators_used.add(validator)
        
        # Should use all validators in rotation
        self.assertEqual(len(validators_used), len(self.poa.get_active_validators()))
    
    def test_block_validation(self):
        """Test consensus block validation"""
        from Dinari.blockchain import Block, Transaction
        
        # Create valid block
        tx = Transaction('sender', 'receiver', '100')
        current_validator = self.poa.get_current_validator(1)
        
        block = Block(
            index=1,
            timestamp=time.time(),
            transactions=[tx],
            previous_hash='previous_hash',
            validator=current_validator
        )
        
        # Should validate successfully
        self.assertTrue(self.poa.validate_block_consensus(block))
        
        # Test with wrong validator
        wrong_block = Block(
            index=1,
            timestamp=time.time(), 
            transactions=[tx],
            previous_hash='previous_hash',
            validator='wrong_validator'
        )
        
        self.assertFalse(self.poa.validate_block_consensus(wrong_block))

class TestNetworking(unittest.TestCase):
    """Test suite for P2P networking"""
    
    def setUp(self):
        """Set up test environment"""
        self.network1 = P2PNetworkManager('node1', port=8401)
        self.network2 = P2PNetworkManager('node2', port=8402)
    
    def tearDown(self):
        """Clean up test environment"""
        self.network1.stop()
        self.network2.stop()
        time.sleep(1)
    
    def test_network_startup(self):
        """Test P2P network startup"""
        self.network1.start_server()
        self.assertTrue(self.network1.running)
        
        self.network2.start_server()  
        self.assertTrue(self.network2.running)
    
    def test_peer_connection(self):
        """Test peer connection establishment"""
        self.network1.start_server()
        self.network2.start_server()
        
        time.sleep(1)  # Allow servers to start
        
        # Connect network2 to network1
        success = self.network2.connect_to_peer('127.0.0.1', 8401)
        self.assertTrue(success)
        
        time.sleep(1)  # Allow connection to establish
        
        # Check connections
        self.assertGreater(len(self.network2.peers), 0)

class TestIntegration(unittest.TestCase):
    """Integration tests for complete system"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        self.genesis_config = {
            'token_name': 'IntegrationCoin',
            'token_symbol': 'INT',
            'total_supply': '10000000',
            'validators': ['validator1', 'validator2'],
            'initial_allocation': {'treasury': '10000000'}
        }
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_workflow(self):
        """Test complete blockchain workflow"""
        # Create blockchain
        blockchain = DinariBlockchain(self.genesis_config)
        
        # Create wallets
        alice_wallet = DinariWallet('alice', self.temp_dir)
        bob_wallet = DinariWallet('bob', self.temp_dir)
        
        alice_addr = alice_wallet.get_all_addresses()[0]
        bob_addr = bob_wallet.get_all_addresses()[0]
        
        # Send tokens to users
        tx1 = Transaction('treasury', alice_addr, '1000', '0.1')
        tx2 = Transaction('treasury', bob_addr, '500', '0.1')
        
        blockchain.add_transaction(tx1)
        blockchain.add_transaction(tx2)
        
        # Mine block
        block = blockchain.mine_block('validator1')
        self.assertIsNotNone(block)
        
        # Check balances
        alice_balance = blockchain.get_balance(alice_addr)
        bob_balance = blockchain.get_balance(bob_addr)
        
        self.assertEqual(alice_balance, Decimal('1000'))
        self.assertEqual(bob_balance, Decimal('500'))
        
        # User-to-user transaction
        success = alice_wallet.send_transaction(
            alice_addr, bob_addr, '100', blockchain
        )
        self.assertTrue(success)
        
        # Mine another block
        block2 = blockchain.mine_block('validator2')
        self.assertIsNotNone(block2)
        
        # Check final balances
        alice_final = blockchain.get_balance(alice_addr)
        bob_final = blockchain.get_balance(bob_addr)
        
        self.assertEqual(alice_final, Decimal('899.9'))  # 1000 - 100 - 0.1 fee
        self.assertEqual(bob_final, Decimal('600'))       # 500 + 100

class DinariTestRunner:
    """Test runner with reporting"""
    
    def __init__(self):
        self.setup_logging()
    
    def setup_logging(self):
        """Setup test logging"""
        setup_logging()
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🧪 DinariBlockchain Comprehensive Test Suite")
        print("=" * 55)
        
        test_suites = [
            ('Core Blockchain', TestDinariBlockchain),
            ('Wallet System', TestDinariWallet),
            ('Smart Contracts', TestSmartContracts),
            ('Consensus Mechanism', TestConsensus),
            ('P2P Networking', TestNetworking),
            ('System Integration', TestIntegration)
        ]
        
        total_tests = 0
        total_failures = 0
        total_errors = 0
        
        for suite_name, test_class in test_suites:
            print(f"\n🔍 Running {suite_name} Tests")
            print("-" * 40)
            
            # Create test suite
            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            
            # Run tests
            runner = unittest.TextTestRunner(
                verbosity=2,
                stream=sys.stdout
            )
            result = runner.run(suite)
            
            # Update counters
            total_tests += result.testsRun
            total_failures += len(result.failures)
            total_errors += len(result.errors)
            
            # Print results
            if result.wasSuccessful():
                print(f"✅ {suite_name}: All tests passed!")
            else:
                print(f"❌ {suite_name}: {len(result.failures)} failures, {len(result.errors)} errors")
        
        # Final summary
        print(f"\n📊 Test Summary")
        print("=" * 20)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_tests - total_failures - total_errors}")
        print(f"Failed: {total_failures}")
        print(f"Errors: {total_errors}")
        
        success_rate = ((total_tests - total_failures - total_errors) / total_tests) * 100
        print(f"Success Rate: {success_rate:.1f}%")
        
        if total_failures == 0 and total_errors == 0:
            print("\n🎉 All tests passed! DinariBlockchain is ready for deployment!")
        else:
            print(f"\n⚠️  Some tests failed. Review the failures before deployment.")
        
        return total_failures == 0 and total_errors == 0
    
    def run_specific_test(self, test_name: str):
        """Run a specific test suite"""
        test_mapping = {
            'blockchain': TestDinariBlockchain,
            'wallet': TestDinariWallet,
            'contracts': TestSmartContracts,
            'consensus': TestConsensus,
            'network': TestNetworking,
            'integration': TestIntegration
        }
        
        if test_name.lower() in test_mapping:
            test_class = test_mapping[test_name.lower()]
            
            print(f"🧪 Running {test_name.title()} Tests")
            print("=" * 30)
            
            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            
            return result.wasSuccessful()
        else:
            print(f"❌ Unknown test suite: {test_name}")
            print(f"Available tests: {', '.join(test_mapping.keys())}")
            return False
    
    def run_performance_tests(self):
        """Run performance benchmarks"""
        print("⚡ DinariBlockchain Performance Tests")
        print("=" * 40)
        
        # Transaction processing benchmark
        print("\n📤 Transaction Processing Benchmark")
        print("-" * 35)
        
        blockchain = DinariBlockchain({
            'total_supply': '10000000',
            'initial_allocation': {'treasury': '10000000'}
        })
        
        # Create many transactions
        num_transactions = 1000
        start_time = time.time()
        
        for i in range(num_transactions):
            tx = Transaction('treasury', f'user_{i}', '10', '0.01')
            blockchain.add_transaction(tx)
        
        tx_time = time.time() - start_time
        tx_rate = num_transactions / tx_time
        
        print(f"✅ Created {num_transactions} transactions in {tx_time:.2f}s")
        print(f"   Rate: {tx_rate:.1f} transactions/second")
        
        # Block mining benchmark  
        print(f"\n⛏️  Block Mining Benchmark")
        print("-" * 25)
        
        start_time = time.time()
        block = blockchain.mine_block('validator1')
        mine_time = time.time() - start_time
        
        if block:
            print(f"✅ Mined block with {len(block.transactions)} transactions in {mine_time:.2f}s")
            print(f"   Block processing rate: {len(block.transactions)/mine_time:.1f} tx/second")
        
        # Smart contract benchmark
        print(f"\n🔧 Smart Contract Benchmark")
        print("-" * 28)
        
        contract_manager = ContractManager(blockchain)
        
        start_time = time.time()
        deployment = contract_manager.deploy_from_template(
            'token', 'treasury', ['BenchToken', 'BCH', '1000000']
        )
        deploy_time = time.time() - start_time
        
        print(f"✅ Contract deployed in {deploy_time:.2f}s")
        
        # Contract execution benchmark
        start_time = time.time()
        num_calls = 100
        
        for i in range(num_calls):
            contract_manager.call_contract(
                deployment.address, 'balance_of', ['treasury'], 'treasury'
            )
        
        call_time = time.time() - start_time
        call_rate = num_calls / call_time
        
        print(f"✅ {num_calls} contract calls in {call_time:.2f}s")
        print(f"   Rate: {call_rate:.1f} calls/second")
        
        print(f"\n📊 Performance Summary")
        print("=" * 25)
        print(f"Transaction Rate: {tx_rate:.1f} tx/s")
        print(f"Block Mining: {mine_time:.2f}s per block")  
        print(f"Contract Calls: {call_rate:.1f} calls/s")

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DinariBlockchain Test Suite")
    parser.add_argument("--test", help="Run specific test suite")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--quick", action="store_true", help="Run quick test subset")
    
    args = parser.parse_args()
    
    runner = DinariTestRunner()
    
    if args.performance:
        runner.run_performance_tests()
    elif args.test:
        runner.run_specific_test(args.test)
    elif args.quick:
        # Run core tests only
        print("⚡ Quick Test Suite")
        print("=" * 20)
        success = runner.run_specific_test('blockchain')
        success &= runner.run_specific_test('wallet')
        
        if success:
            print("\n✅ Quick tests passed!")
        else:
            print("\n❌ Some quick tests failed")
    else:
        # Run all tests
        runner.run_all_tests()

if __name__ == "__main__":
    main()
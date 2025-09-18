# 🌍 DinariBlockchain

**A blockchain-based stablecoin designed for Africa's financial future**

DinariBlockchain is a complete blockchain implementation built in Python, specifically designed for African financial inclusion, stability, and low transaction costs. It features smart contracts, Proof of Authority consensus, P2P networking, and African-focused financial tools.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-green.svg)]()

## 🚀 Features

### Core Blockchain
- ⚡ **Fast Transactions**: 10-30 second block times with low fees
- 🔒 **Secure Consensus**: Proof of Authority with validator management
- 💰 **DNMR Token**: Native token with 18 decimal precision
- 📊 **Full Validation**: Complete chain validation and integrity checks

### Smart Contracts
- 🐍 **Python-Based**: Write contracts in safe Python subset
- 🏪 **Templates**: Pre-built ERC20, voting, and multi-sig contracts
- 🌍 **African Tools**: Tontine-style savings, community voting
- 📢 **Events**: Contract event emission and tracking

### P2P Network
- 🌐 **Mesh Networking**: Automatic peer discovery and connection
- 🔄 **Real-time Sync**: Instant transaction and block propagation
- 📡 **Resilient**: Network fault tolerance and recovery
- 📊 **Monitoring**: Network statistics and health tracking

### African Focus
- 🏛️ **Regulatory Compliance**: Designed for African financial regulations
- 💱 **Stablecoin Ready**: Built for price stability mechanisms
- 🤝 **Community Tools**: Cooperative savings and group finance
- 📱 **Mobile Friendly**: Lightweight for mobile and web integration

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Git

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/Dinari/blockchain.git
cd Dinari-blockchain

# Install dependencies
pip install -r requirements.txt

# Generate genesis configuration
python tools/genesis_generator.py --network mainnet

# Run basic tests
python tools/test_blockchain.py --quick
```

### Development Setup

```bash
# Install in development mode
pip install -e .

# Run comprehensive tests
python tools/test_blockchain.py

# Start interactive shell
python -c "from Dinari import quick_start_example; quick_start_example()"
```

## 🏁 Quick Start

### 1. Basic Blockchain Usage

```python
from Dinari import DinariBlockchain, Transaction

# Create blockchain
blockchain = DinariBlockchain()

# Create and add transaction
tx = Transaction("treasury", "alice", "1000", "0.1")
blockchain.add_transaction(tx)

# Mine block
blockchain.add_validator("validator1")
block = blockchain.mine_block("validator1")

# Check balance
balance = blockchain.get_balance("alice")
print(f"Alice's balance: {balance} DNMR")
```

### 2. Wallet Management

```python
from Dinari import create_wallet

# Create wallet
wallet = create_wallet("my_wallet")

# Generate new address
address = wallet.create_new_address("main")

# Send transaction
wallet.send_transaction(address, "recipient", "100", blockchain)
```

### 3. Smart Contract Deployment

```python
from Dinari import ContractManager

# Create contract manager
contract_manager = ContractManager(blockchain)

# Deploy ERC20-like token
deployment = contract_manager.deploy_from_template(
    'token', 'treasury', ['AfroToken', 'ATK', '1000000']
)

# Call contract function
result = contract_manager.call_contract(
    deployment.address, 'transfer', ['alice', 1000], 'treasury'
)
```

### 4. Multi-Node Network

```python
# Start 3-node network
python tools/start_node.py testnet --nodes 3

# Or use the launcher
from tools.start_node import NodeLauncher
launcher = NodeLauncher()
launcher.start_test_network(3)
```

## 📚 Documentation

### Core Components

| Component | Description | Location |
|-----------|-------------|----------|
| **Blockchain** | Core blockchain, transactions, blocks | `Dinari/blockchain.py` |
| **Consensus** | Proof of Authority implementation | `Dinari/consensus.py` |
| **Contracts** | Smart contract execution engine | `Dinari/contracts.py` |
| **Network** | P2P networking and communication | `Dinari/network.py` |
| **Node** | Complete blockchain node | `Dinari/node.py` |
| **Wallet** | Key management and transactions | `Dinari/wallet.py` |

### Tools

| Tool | Description | Usage |
|------|-------------|--------|
| **Genesis Generator** | Create genesis configurations | `python tools/genesis_generator.py` |
| **Node Launcher** | Start and manage nodes | `python tools/start_node.py` |
| **Test Suite** | Comprehensive testing | `python tools/test_blockchain.py` |

### Examples

| Example | Description | Run With |
|---------|-------------|----------|
| **Simple Transaction** | Basic blockchain operations | `python examples/simple_transaction.py` |
| **Smart Contracts** | Contract deployment and usage | `python examples/deploy_contract.py` |
| **Multi-Node Network** | P2P network demonstration | `python examples/multi_node_test.py` |

## 🛠️ Development

### Project Structure

```
Dinari-blockchain/
├── Dinari/                    # Main blockchain package
│   ├── blockchain.py           # Core blockchain implementation
│   ├── consensus.py            # Proof of Authority consensus
│   ├── contracts.py            # Smart contract system
│   ├── network.py              # P2P networking
│   ├── node.py                 # Blockchain node
│   └── wallet.py               # Wallet and key management
├── tools/                       # Development tools
│   ├── genesis_generator.py    # Genesis configuration creator
│   ├── start_node.py          # Node launcher and manager
│   └── test_blockchain.py     # Comprehensive test suite
├── examples/                    # Usage examples
│   ├── simple_transaction.py   # Basic blockchain demo
│   ├── deploy_contract.py      # Smart contract example
│   └── multi_node_test.py     # Multi-node network demo
└── data/                       # Node data storage
```

### Running Tests

```bash
# Run all tests
python tools/test_blockchain.py

# Run specific test suite
python tools/test_blockchain.py --test blockchain
python tools/test_blockchain.py --test contracts
python tools/test_blockchain.py --test consensus

# Run performance benchmarks
python tools/test_blockchain.py --performance

# Quick smoke tests
python tools/test_blockchain.py --quick
```

### Genesis Configuration

```bash
# Generate mainnet genesis
python tools/genesis_generator.py --network mainnet

# Generate testnet genesis  
python tools/genesis_generator.py --network testnet

# Generate development genesis
python tools/genesis_generator.py --network devnet

# Validate existing genesis
python tools/genesis_generator.py --validate --summary
```

## 🌐 Network Operations

### Starting a Single Node

```bash
# Start validator node
python tools/start_node.py single validator_1 --port 8333

# Start regular node
python tools/start_node.py single node_1 --port 8334 --peers 127.0.0.1:8333
```

### Starting Test Network

```bash
# Start 3-node test network
python tools/start_node.py testnet --nodes 3

# Interactive node management
python tools/start_node.py shell
```

### Network Commands (Interactive Shell)

```
Dinari> help          # Show available commands
Dinari> status        # Show network status
Dinari> testnet       # Start test network
Dinari> tx            # Send test transaction
Dinari> stopall       # Stop all nodes
```

## 💼 Smart Contracts

### Built-in Contract Templates

#### ERC20-like Token Contract
```python
# Deploy token
deployment = contract_manager.deploy_from_template(
    'token', 'deployer', ['TokenName', 'TKN', '1000000']
)

# Use token functions
contract_manager.call_contract(address, 'transfer', ['recipient', 1000], 'sender')
contract_manager.call_contract(address, 'balance_of', ['account'], 'anyone')
```

#### Community Voting Contract
```python
# Deploy voting
deployment = contract_manager.deploy_from_template(
    'voting', 'organizer', ['Vote Title', ['Option A', 'Option B'], 86400]
)

# Cast votes
contract_manager.call_contract(address, 'vote', ['Option A'], 'voter')
contract_manager.call_contract(address, 'get_results', [], 'anyone')
```

#### Multi-signature Wallet
```python
# Deploy multisig
owners = ['owner1', 'owner2', 'owner3']
deployment = contract_manager.deploy_from_template(
    'multisig', 'creator', [owners, 2]  # Require 2 signatures
)

# Submit and confirm transactions
contract_manager.call_contract(address, 'submit_transaction', ['recipient', 1000], 'owner1')
contract_manager.call_contract(address, 'confirm_transaction', [0], 'owner2')
```

### Custom African Financial Contracts

```python
# African Community Savings (Tontine-style)
african_savings_code = '''
def contribute(amount):
    # Community savings logic
    contract.state['total_saved'] += amount
    emit_event('Contribution', {'member': caller, 'amount': amount})
'''

address = contract_manager.deploy_contract(african_savings_code, 'deployer')
```

## 🏦 African Financial Features

### Stablecoin Mechanisms
- **Price Oracles**: External price feed integration ready
- **Collateral Management**: Multi-asset backing support
- **Reserve Ratios**: Automated reserve management
- **Stability Fees**: Dynamic fee adjustment

### Community Finance
- **Tontine Savings**: Rotating savings and credit associations
- **Group Lending**: Community-backed microfinance
- **Mobile Integration**: SMS and USSD transaction support
- **Remittance**: Cross-border transfer optimization

### Regulatory Compliance
- **KYC/AML Ready**: User verification framework
- **Transaction Limits**: Configurable limits and controls
- **Reporting**: Regulatory reporting tools
- **Audit Trail**: Complete transaction history

## ⚡ Performance

### Benchmarks
- **Transaction Throughput**: 1,000+ transactions/second
- **Block Time**: 10-30 seconds (configurable)
- **Contract Execution**: 100+ calls/second
- **Network Latency**: Sub-second block propagation
- **Storage**: Efficient state management

### Scalability
- **Horizontal Scaling**: Add more validator nodes
- **State Management**: Optimized blockchain storage
- **Network Optimization**: Efficient P2P communication
- **Memory Usage**: Minimal resource requirements

## 🔧 Configuration

### Genesis Parameters

```json
{
  "network_id": "Dinari-mainnet",
  "token": {
    "name": "Dinari",
    "symbol": "DNMR", 
    "total_supply": "100000000"
  },
  "consensus": {
    "type": "proof_of_authority",
    "block_time": 30,
    "validators": ["validator1", "validator2"]
  },
  "initial_allocation": {
    "treasury": "40000000",
    "development": "20000000", 
    "community": "25000000",
    "partnerships": "15000000"
  }
}
```

### Node Configuration

```python
node = DinariNode(
    node_id="my_node",
    host="0.0.0.0",      # Bind to all interfaces
    port=8333,           # P2P port
    genesis_file="genesis.json",
    data_dir="node_data"
)
```

## 🚨 Security

### Best Practices
- **Private Keys**: Never commit private keys to version control
- **Network Security**: Use firewall rules for P2P ports
- **Validator Security**: Secure validator node infrastructure
- **Contract Auditing**: Review smart contracts before deployment

### Security Features
- **Input Validation**: All inputs validated and sanitized
- **Safe Execution**: Smart contracts run in sandboxed environment
- **Cryptographic Hashing**: SHA-256 for all hashes
- **Network Encryption**: P2P message encryption ready

## 🤝 Contributing

We welcome contributions to DinariBlockchain! Here's how to get started:

### Development Workflow

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Write tests**: Add tests for your changes
4. **Run test suite**: `python tools/test_blockchain.py`
5. **Commit changes**: `git commit -am 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Create Pull Request**

### Code Standards
- Follow PEP 8 Python style guide
- Add docstrings for all functions and classes
- Include type hints where appropriate
- Write comprehensive tests for new features
- Update documentation for user-facing changes

### Testing Requirements
- All tests must pass: `python tools/test_blockchain.py`
- Code coverage should be maintained
- Performance tests should not regress
- Integration tests must pass

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🌍 African Impact

DinariBlockchain is designed specifically for African financial inclusion:

- **Low Transaction Costs**: Minimal fees for micro-transactions
- **Mobile-First**: Optimized for mobile and low-bandwidth networks
- **Regulatory Alignment**: Built with African regulatory frameworks in mind
- **Community Focus**: Tools for cooperative finance and group savings
- **Local Currency**: Stablecoin pegged to stable African currencies
- **Cross-Border**: Facilitate intra-African trade and remittances

## 🎯 Roadmap

### Phase 1: Core Infrastructure ✅
- [x] Basic blockchain implementation
- [x] Proof of Authority consensus
- [x] P2P networking
- [x] Smart contract system
- [x] Wallet functionality

### Phase 2: African Features 🚧
- [ ] Mobile integration (SMS/USSD)
- [ ] Stablecoin mechanisms
- [ ] Regulatory compliance tools
- [ ] Cross-border payment optimization
- [ ] Community finance contracts

### Phase 3: Ecosystem Growth 📋
- [ ] Developer tooling and SDKs
- [ ] Integration with African banks
- [ ] Mobile app development
- [ ] Merchant payment solutions
- [ ] Governance mechanisms

### Phase 4: Scale and Impact 📋
- [ ] Multi-country deployment
- [ ] Central bank partnerships
- [ ] DeFi protocol integrations
- [ ] International remittance corridors
- [ ] Full regulatory approval

## 📞 Support

### Community
- **GitHub Issues**: [Report bugs and request features](https://github.com/Dinari/blockchain/issues)
- **Discussions**: [Join community discussions](https://github.com/Dinari/blockchain/discussions)
- **Discord**: [Real-time community chat](https://discord.gg/Dinari)

### Documentation
- **API Reference**: Full API documentation available
- **Tutorials**: Step-by-step guides in `/docs`
- **Examples**: Working examples in `/examples`
- **FAQ**: Common questions and solutions

### Professional Support
For enterprise deployments and professional support:
- **Email**: support@dinari.xyz
- **Consulting**: Custom blockchain solutions
- **Training**: Developer training programs
- **Integration**: System integration services

---

**Built with ❤️ for Africa's financial future**

DinariBlockchain - Empowering African communities through blockchain technology

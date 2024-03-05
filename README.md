# SEI

### Contracts setup


**Install sei**
```
git clone https://github.com/sei-protocol/sei-chain
cd sei-chain
git checkout v3.7.0
make install
seid version
```

**Add a new wallet**
```
seid keys add $NAME
seid keys list
```

**Install foundry**
```
brew install libusb
curl -L https://foundry.paradigm.xyz | bash
foundryup
forge --version
```

### Deployment

**Run local network**
```
anvil
```
This runs a chain on: http://localhost:8545  
Chain ID: 31337

**Deploy contracts**  
Take some private keys from the `anvil` results
```
forge create --rpc-url http://localhost:8545 --private-key <test_account_private_key> src/Oracle.sol:Oracle
forge create --rpc-url http://localhost:8545 --private-key <test_account_private_key> src/Agent.sol:Agent --constructor-args <0x oracle address>
```

(Devnet deployment didnt try yet)
```
forge create --rpc-url https://evm-rpc.arctic-1.seinetwork.io/ --private-key <your_private_key> src/MyNFT.sol:MyNFT
```

### Run basic agent example

**Python env**
```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt 
```

**Setup .envs**
```
cp client/template.env client/.env
nano client/.env
```
```
cp oracles/template.env oracles/.env
nano oracles/.env
```

**Run these 2 in separate processes simultaneously**
```
cd client
python agent_runner.py
```
```
cd oracles
python oracle_agent.py
```

# SEI

## Contracts setup

**Install dependencies**
```
cd contracts
cp template.env .env
npm install
```
Modify .env and add your private key for relevant network  
_CUSTOM for our chain

## Deployment

### Local
**Run local network**
```
cd contracts
npm run node
```
This runs a chain on: http://localhost:8545  
Chain ID: 31337

Take some private key from local node and add to contracts/.env PRIVATE_KEY_LOCALHOST

**Deploy contracts**
```
npm run deploy:localhost
```

### Galadriel testnet / SEI devnet
Update .env

**Deploy to Galadriel testnet**
```
npm run deploy:galadriel
```

**Deploy to Sei v2 devnet (atlantic-2)**
```
npm run deploy:devnet
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
**This is deprecated!!**
```
cd client
python agent_runner.py
```
```
cd oracles
python oracle_agent.py
```



**Install sei**
(Not necessary for deployments and using the contracts)
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
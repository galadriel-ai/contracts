# Contracts setup

## Setup

**Install dependencies**

```
cd contracts
cp template.env .env
npm install
```

Modify .env and add your private key for relevant network  
`PRIVATE_KEY_LOCALHOST` for local node
`PRIVATE_KEY_CUSTOM` for Galadriel testnet

Rest of this README assumes you are in the `contracts` directory

## Deployment

### Local

**Run local network**

```
npm run node
```

This runs a chain on: http://localhost:8545  
Chain ID: 31337

Take some private key from local node and add to .env `PRIVATE_KEY_LOCALHOST`

**Deploy contracts**

```
npm run deploy:localhost
```

### Galadriel testnet

Update .env
Add your private key to .env `PRIVATE_KEY_CUSTOM`

**Deploy to Galadriel testnet**

```
npm run deploy:galadriel
```

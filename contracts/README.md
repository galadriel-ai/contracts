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
Chain ID: 1337

Take some private key from local node and add to .env `PRIVATE_KEY_LOCALHOST`

**Deploy the oracle contract and all examples to local network**

```
npm run deployAll:localhost
```

### Galadriel testnet

Update `.env`:
* Add your private key to `PRIVATE_KEY_CUSTOM`
* Add the [oracle address](http://docs.galadriel.com/oracle-address) to `ORACLE_ADDRESS`

**Deploy quickstart to Galadriel testnet**

```
npm run deployQuickstart
```

**Deploy the oracle contract and all examples to Galadriel testnet**

```
npm run deployAll:galadriel
```


## Whitelisting a Wallet in the Oracle Contract

To whitelist an address in the Oracle contract, allowing it to write responses on-chain, you can use the `whitelist` Hardhat task.

Run the following command, replacing `[oracle_address]` with the Oracle contract's address and `[wallet_address]` with the address you want to whitelist:

```bash
npx hardhat whitelist --oracle-address [oracle_address] --whitelist-address [wallet_address] --network galadriel

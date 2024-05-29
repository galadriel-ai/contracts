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
`PRIVATE_KEY_GALADRIEL` for Galadriel testnet

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

**Run the oracle backend**

Please see the [`oracles` directory](/oracles) to run the oracle backend. If you don't run the oracle back-end, the oracle contracts on your localnet will not produce any results (and will not make any callbacks).

### Galadriel testnet

Update `.env`:
* Add your private key to `PRIVATE_KEY_GALADRIEL`
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
```

### Generating standard Solidity input JSON

This is useful for verifying contracts on the explorer, 
using the "Standard JSON input" option.  

```bash
npm run generateStandardJson
```

This generated JSON files are in `./contracts/artifacts/solidity-json/contracts`

### Running e2e validation tests

**Deploy test contract to relevant network**
```
npm run deployTest:localhost
```
```
npm run deployTest:galadriel
```

**Single run**
```
npx hardhat e2e --contract-address <Test contract address> --oracle-address <oracle contract address> --network <network>
```

**Cron job with Slack**
```
ts-node tasks/e2eCron.ts
```

**Cron job with Slack in docker**
```
docker compose -f docker/docker-compose-e2e.yml up --build -d
```

# Contract debugging

To see if your custom CHAT contract acts as expected can use the debug script
```
npm run debug
```
If your contract has any custom parameters or function names then the configuration at the start of the 
debug script has to be changed `./scripts/debugContract.ts`


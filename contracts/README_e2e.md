# Deploying contracts to run the setup e2e

This document explains how to deploy the contracts, if you want to run
the setup e2e including running the oracle. This is generally not necessary,
unless you wish to make any changes to the oracle, or run it locally for testing.

## Deployment


**Run local network if running locally**

```
npm run node
```

This runs a chain on: http://localhost:8545  
Chain ID: 1337

Take some private key from local node and add to .env `PRIVATE_KEY_LOCALHOST`  
If deploying on Galadriel devnet add your private key to .env `PRIVATE_KEY_GALADRIEL`

## Deploy the oracle contract and all examples

This adds the deployed oracle contract to all the other contracts

```
# Localhost
npm run deployAll:localhost
# Galadriel
npm run deployAll:galadriel
```

**Run the oracle backend and look at the next section to whitelist an address**

Please see the [`oracles` directory](/oracles) to run the oracle backend. If you don't run the oracle back-end, the
oracle contracts will not produce any results (and will not make any callbacks).

## Whitelisting a Wallet in the Oracle Contract

To whitelist an address in the Oracle contract, allowing it to write responses on-chain, you can use the `whitelist`
Hardhat task.

Run the following command, replacing `[oracle_address]` with the Oracle contract's address, `[wallet_address]` with
the address you want to whitelist and `[network]` with either `localhost` or `galadriel`:

```bash
npx hardhat whitelist --oracle-address [oracle_address] --whitelist-address [wallet_address] --network [network]
```

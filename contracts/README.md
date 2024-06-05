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

### Deploy any contract

Get the [oracle address](https://docs.galadriel.com/oracle-address) from the docs and replace `<oracle address>` with
the address.  
Check the available example contracts at `./contracts/contracts`

```
npx hardhat deploy --network [network (galadriel or localhost)] --contract [contract name] --oracleaddress [oracle_address] [space separated extra constructor args]
# ChatGpt example
npx hardhat deploy --network galadriel --contract ChatGpt --oracleaddress [oracle_address] ""
# Dall-e example
npx hardhat deploy --network galadriel --contract DalleNft --oracleaddress [oracle_address] "system prompt"
# Groq localhost example (requires running a local node)
npx hardhat deploy --network localhost --contract GroqChatGpt --oracleaddress [oracle_address]
```

### Galadriel testnet

Update `.env`:

* Add your private key to `PRIVATE_KEY_GALADRIEL`

* Add the [oracle address](http://docs.galadriel.com/oracle-address) to `ORACLE_ADDRESS`

**Deploy quickstart to Galadriel testnet**

```
npm run deployQuickstart
```

**Deploy the oracle contract and all examples to Galadriel testnet**  
**This requires running your own oracle and is not recommended unless you are looking to modify the oracle behaviour**

```
npm run deployAll:galadriel
```

### Running e2e

To run the whole flow e2e either locally or on Galadriel devnet check out
[e2e deployment readme](contracts/README_e2e.md).

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


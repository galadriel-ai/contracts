## Contracts for RAG

### Setup

#### Setup for running all the required contracts

```bash
# run hardhat node
npm run node

# deploy Oracle contract and copy oracle contract address: <oracle_address>
npx hardhat deployOracle --network localhost

# deploy rag contract and copy contract address: <contract_address>
npx hardhat deploy --network localhost --contract GroqChatGpt --oracleaddress <oracle_address>

# whitelist account used by oracle machine
npx hardhat whitelist --oracle-address <oracle_address> --whitelist-address <oracle_machine_wallet_address> --network localhost
```

- This setups runs an `oracle contract` which interacts with the `oracle machine` and invoke all the tasks needed to be done by a remote machine and in production the machine will be executed in `teeML`

- It also starts a `main contract` which will interact with user and forward the tasks that are required to be done by the oracle machine to the `oracle contract`

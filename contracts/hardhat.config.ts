import {HardhatUserConfig} from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";

require('dotenv').config()
const seiDevnet = []
if (process.env.PRIVATE_KEY_SEI_DEVNET) {
  seiDevnet.push(process.env.PRIVATE_KEY_SEI_DEVNET)
}
const localhostPrivateKeys = []
if (process.env.PRIVATE_KEY_LOCALHOST) {
  localhostPrivateKeys.push(process.env.PRIVATE_KEY_LOCALHOST)
}

const config: HardhatUserConfig = {
  solidity: "0.8.20",
  networks: {
    devnet: {
      chainId: 713715,
      url: "https://evm-rpc.arctic-1.seinetwork.io",
      accounts: seiDevnet,
    },
    // TODO: add SEI etc
    hardhat: {
      chainId: 1337,
    },
    localhost: {
      chainId: 1337,
      url: "http://127.0.0.1:8545",
      accounts: localhostPrivateKeys,
    }
  },
};

export default config;

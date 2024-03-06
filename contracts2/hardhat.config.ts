import {HardhatUserConfig} from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";

require('dotenv').config()
const localhostPrivateKeys = []
if (process.env.PRIVATE_KEY_LOCALHOST) {
  localhostPrivateKeys.push(process.env.PRIVATE_KEY_LOCALHOST)
}

const config: HardhatUserConfig = {
  solidity: "0.8.19",
  networks: {
    // TODO: add SEI etc
    hardhat: {
      chainId: 1337,
    },
    localhost: {
      chainId: 1337,
      url: "http://127.0.0.1:8545",
      accounts: localhostPrivateKeys
    }
  },
};

export default config;

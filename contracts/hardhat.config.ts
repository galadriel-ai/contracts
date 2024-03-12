import {HardhatUserConfig} from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";

require('dotenv').config()

const galadrielDevnet = []
if (process.env.PRIVATE_KEY_CUSTOM) {
  galadrielDevnet.push(process.env.PRIVATE_KEY_CUSTOM)
}
const localhostPrivateKeys = []
if (process.env.PRIVATE_KEY_LOCALHOST) {
  localhostPrivateKeys.push(process.env.PRIVATE_KEY_LOCALHOST)
}

const config: HardhatUserConfig = {
  solidity: "0.8.20",
  networks: {
    galadriel: {
      chainId: 696969,
      url: "https://testnet.galadriel.com/",
      accounts: galadrielDevnet,
    },
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

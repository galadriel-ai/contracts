import { defaultConfig } from "@web3modal/ethers/react";

// 2. Set chains

export const galadriel = {
  chainId: 696969,
  name: "Galadriel Devnet",
  currency: "GAL",
  explorerUrl: "https://explorer.galadriel.co",
  rpcUrl: "https://devnet.galadriel.com",
};

export const projectId = "<Your Project ID>";

// 3. Create a metadata object
const metadata = {
  name: "My Website",
  description: "My Website description",
  url: "https://localhost:3000", // origin must match your domain & subdomain
  icons: ["https://avatars.mywebsite.com/"],
};

// 4. Create Ethers config
export const ethersConfig = defaultConfig({
  /*Required*/
  metadata,

  /*Optional*/
  enableEIP6963: true, // true by default
  enableInjected: true, // true by default
  enableCoinbase: true, // true by default
  rpcUrl: "https://devnet.galadriel.com", // used for the Coinbase SDK
  defaultChainId: 1, // used for the Coinbase SDK
});

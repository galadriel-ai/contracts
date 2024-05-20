import { task } from "hardhat/config";

// Define the task with the name 'whitelist-address'
export const whitelistTask = task("whitelist", "Whitelists an address in the Oracle contract")
  .addParam("oracleAddress", "The address of the Oracle contract")
  .addParam("whitelistAddress", "The address to whitelist")
  .setAction(async (taskArgs, hre) => {
    const oracleContractAddress = taskArgs.oracleAddress;
    const whitelistAddress = taskArgs.whitelistAddress;
    const pcr0Hash = "5c8ce02f8c739a6578886ef009dc27dc69ac85a631689b093f75f6ae238e10d70a08dce8f0cafdd1f7d9b3a26c889565";

    const contractABI = [
      "function updateWhitelist(address _addressToWhitelist, bool isWhitelisted)",
      "function addPcr0Hash(string memory pcr0Hash)",
    ];

    const [signer] = await hre.ethers.getSigners();
    const contract = new hre.ethers.Contract(oracleContractAddress, contractABI, signer);

    console.log(`Whitelisting address: "${whitelistAddress}"...`);
    const updateTx = await contract.updateWhitelist(whitelistAddress, true);
    await updateTx.wait();
    console.log(`Address whitelisted: "${whitelistAddress}"`);

    // Add PCR0 hash
    console.log(`Adding PCR0 hash for: "${whitelistAddress}"...`);
    const pcr0Tx = await contract.addPcr0Hash(pcr0Hash);
    await pcr0Tx.wait();
    console.log(`PCR0 hash added for: "${whitelistAddress}"`);
  });

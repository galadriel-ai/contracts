import { task } from "hardhat/config";

task("deployOracle", "Deploys Oracle contract")
  .addVariadicPositionalParam("args", "Contract constructor args", [])
  .setAction(async (taskArgs, hre) => {
    const contractName = "ChatOracle";

    console.log(`Deploying ${contractName} on network: "${hre.network.name}"`);
    const constructorArgs = [...taskArgs.args];
    console.log(`Contract constructor args: [${constructorArgs}]`);
    const contract = await hre.ethers.deployContract(
      contractName,
      constructorArgs,
      {}
    );
    await contract.waitForDeployment();
    console.log(`${contractName} deployed to: ${contract.target}`);
  });

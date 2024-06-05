import {task} from "hardhat/config";

task("deploy", "Deploys a single contract")
  .addParam("contract", "The name of the contract to be deployed")
  .addParam("oracleaddress", "The address of the Oracle contract")
  .addVariadicPositionalParam("args", "Contract constructor args", [])
  .setAction(async (taskArgs, hre) => {
    const oracleAddress = taskArgs.oracleAddress;

    console.log(`Deploying "${taskArgs.contract}" on network: "${hre.network.name}"`)
    const constructorArgs = [taskArgs.oracleaddress, ...taskArgs.args]
    console.log(`Contract constructor args: [${constructorArgs}]`)

    const contract = await hre.ethers.deployContract(taskArgs.contract, constructorArgs, {});
    await contract.waitForDeployment();
    console.log(`${taskArgs.contract} deployed to: ${contract.target}`);
  });

import {ethers} from "hardhat";

const QUICKSTART_PROMPT = "make an image in the style of orange and blue oil painting. The subject is: \""

async function main() {
  if (!process.env.ORACLE_ADDRESS) {
    throw new Error("ORACLE_ADDRESS env variable is not set.");
  }
  const oracleAddress: string = process.env.ORACLE_ADDRESS;
  await deployQuickstart(oracleAddress);
}


async function deployQuickstart(oracleAddress: string) {
  const agent = await ethers.deployContract(
    "Quickstart",
    [
      oracleAddress,
      QUICKSTART_PROMPT,
    ], {});

  await agent.waitForDeployment();

  console.log(
    `Quickstart contract deployed to ${agent.target}`
  );
}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

import {ethers} from "hardhat";

async function main() {
  const oracleAddress: string = await deployOracle();
  await deployAgent(oracleAddress);
}

async function deployOracle(): Promise<string> {
  const oracle = await ethers.deployContract("AgentOracle", [], {});

  await oracle.waitForDeployment();

  console.log(
    `Oracle deployed to ${oracle.target}`
  );
  return oracle.target as string;
}

async function deployAgent(oracleAddress: string) {
  const agent = await ethers.deployContract("Agent", [oracleAddress], {});

  await agent.waitForDeployment();

  console.log(
    `Agent deployed to ${agent.target}`
  );
}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

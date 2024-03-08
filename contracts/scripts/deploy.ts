import {ethers} from "hardhat";

const DALLE_PROMPT = "make an image of: \"solarpunk oil painting "

async function main() {
  const oracleAddress: string = await deployOracle();
  await deployChatGpt(oracleAddress);
  await deployDalle(oracleAddress);
}

async function deployOracle(): Promise<string> {
  const oracle = await ethers.deployContract("ChatOracle", [], {});

  await oracle.waitForDeployment();

  console.log(
    `Oracle deployed to ${oracle.target}`
  );
  return oracle.target as string;
}

async function deployChatGpt(oracleAddress: string) {
  const agent = await ethers.deployContract("ChatGpt", [oracleAddress], {});

  await agent.waitForDeployment();

  console.log(
    `ChatGPT deployed to ${agent.target}`
  );
}

async function deployDalle(oracleAddress: string) {
  const agent = await ethers.deployContract(
    "DalleNft",
    [
      oracleAddress,
      DALLE_PROMPT,
    ], {});

  await agent.waitForDeployment();

  console.log(
    `Dall-e deployed to ${agent.target}`
  );
}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

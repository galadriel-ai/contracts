import { task } from "hardhat/config";

task("deployChatWithRAG", "Deploys the chat contract with knowledge base")
  .addParam("oracleAddress", "The address of the Oracle contract")
  .addParam("cid", "Knowledge base CID")
  .setAction(async (taskArgs, hre) => {
    const oracleAddress = taskArgs.oracleAddress;
    const knowledgeBaseCID = taskArgs.cid;
    const contract = await hre.ethers.deployContract("ChatGpt", [oracleAddress, knowledgeBaseCID], {});
    await contract.waitForDeployment();
    console.log(`RAG deployed to: ${contract.target}`);
  });

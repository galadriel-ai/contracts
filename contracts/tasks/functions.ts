import { task } from "hardhat/config";
import { Contract, TransactionReceipt } from "ethers";
import { HardhatRuntimeEnvironment } from "hardhat/types";

interface FunctionResponse {
  response: string,
  error: string,
}

task("openai", "Calls the OpenAI LLM")
  .addParam("contractAddress", "The address of the Test contract")
  .addParam("model", "The model to use")
  .addParam("message", "The message to send to the model")
  .setAction(async (taskArgs, hre) => {
    const contractAddress = taskArgs.contractAddress;
    const model = taskArgs.model;
    const message = taskArgs.message;

    const contract = await getContract("Test", contractAddress, hre);
    const response = await queryOpenAiLLM(contract, model, message, hre);
    console.log(response);
    if (response.error.length > 0) {
      process.exit(1);
    }
  });

task("groq", "Calls the Groq LLM")
  .addParam("contractAddress", "The address of the Test contract")
  .addParam("model", "The model to use")
  .addParam("message", "The message to send to the model")
  .setAction(async (taskArgs, hre) => {
    const contractAddress = taskArgs.contractAddress;
    const model = taskArgs.model;
    const message = taskArgs.message;

    const contract = await getContract("Test", contractAddress, hre);
    const response = await queryGroqLLM(contract, model, message, hre);
    console.log(response)
    if (response.error.length > 0) {
      process.exit(1);
    }
  });

task("web_search", "Calls the web search function")
  .addParam("contractAddress", "The address of the Test contract")
  .addParam("query", "The query to ask the contract")
  .setAction(async (taskArgs, hre) => {
    const contractAddress = taskArgs.contractAddress;
    const query = taskArgs.query;

    const contract = await getContract("Test", contractAddress, hre);
    const response = await queryContractFunction(contract, "web_search", query, hre);
    console.log(response)
    if (response.error.length > 0) {
      process.exit(1);
    }
  });

task("image_generation", "Calls the image generation function")
  .addParam("contractAddress", "The address of the Test contract")
  .addParam("query", "The query to ask the contract")
  .setAction(async (taskArgs, hre) => {
    const contractAddress = taskArgs.contractAddress;
    const query = taskArgs.query;

    const contract = await getContract("Test", contractAddress, hre);
    const response = await queryContractFunction(contract, "image_generation", query, hre);
    console.log(response)
    if (response.error.length > 0) {
      process.exit(1);
    }
  });

task("code_interpreter", "Calls the code interpreter function")
  .addParam("contractAddress", "The address of the Test contract")
  .addParam("query", "The query to ask the contract")
  .setAction(async (taskArgs, hre) => {
    const contractAddress = taskArgs.contractAddress;
    const query = taskArgs.query;

    const contract = await getContract("Test", contractAddress, hre);
    const response = await queryContractFunction(contract, "code_interpreter", query, hre);
    console.log(response)
    if (response.error.length > 0) {
      process.exit(1);
    }
  });

task("add_knowledge_base", "Adds a knowledge base to the contract")
  .addParam("oracleAddress", "The address of the Oracle contract")
  .addParam("cid", "The CID of the knowledge base")
  .setAction(async (taskArgs, hre) => {
    const oracleAddress = taskArgs.oracleAddress;
    const cid = taskArgs.cid;

    const contract = await getContract("ChatOracle", oracleAddress, hre);
    const txResponse = await contract.addKnowledgeBase(cid);
    const txReceipt = await txResponse.wait();
    let runId = getRunId(txReceipt, contract, hre);
    let isProcessed = await contract.isKbIndexingRequestProcessed(runId);
    let response = await contract.kbIndexes(cid);
    let error = await contract.kbIndexingRequestErrors(runId);
    while (!isProcessed) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      isProcessed = await contract.isKbIndexingRequestProcessed(runId);
      response = await contract.kbIndexes(cid);
      error = await contract.kbIndexingRequestErrors(runId);
    }
    console.log({ response: response, error: error });
    if (error.length > 0) {
      process.exit(1);
    }
  });

task("query_knowledge_base", "Queries a knowledge base")
  .addParam("contractAddress", "The address of the Test contract")
  .addParam("cid", "The CID of the knowledge base")
  .addParam("query", "The query to ask the knowledge base")
  .setAction(async (taskArgs, hre) => {
    const contractAddress = taskArgs.contractAddress;
    const cid = taskArgs.cid;
    const query = taskArgs.query;

    const contract = await getContract("Test", contractAddress, hre);
    const response = await queryContractKnowledgeBase(contract, cid, query, hre);
    console.log(response)
    if (response.error.length > 0) {
      process.exit(1);
    }
  });

async function getContract(
  name: string,
  contractAddress: string,
  hre: HardhatRuntimeEnvironment
): Promise<Contract> {
  const signer = (await hre.ethers.getSigners())[0];
  const ContractArtifact = await hre.artifacts.readArtifact(name);
  return new hre.ethers.Contract(contractAddress, ContractArtifact.abi, signer);
}

async function queryOpenAiLLM(
  contract: Contract,
  model: string,
  message: string,
  hre: HardhatRuntimeEnvironment
): Promise<FunctionResponse> {
  try {
    const txResponse = await contract.callOpenAiLLM(model, message);
    await txResponse.wait();
    process.stdout.write("Waiting for response");
    let response = await contract.lastResponse();
    let error = await contract.lastError();
    while (response.length === 0 && error.length === 0) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      response = await contract.lastResponse();
      error = await contract.lastError();
      process.stdout.write(".");
    }
    console.log("");
    return { response: response, error: error };
  } catch (error) {
    console.error(`Error calling contract function: ${error}`);
  }
  return { response: "", error: "Failed XX" };
}

async function queryGroqLLM(
  contract: Contract,
  model: string,
  message: string,
  hre: HardhatRuntimeEnvironment
): Promise<FunctionResponse> {
  try {
    const txResponse = await contract.callGroqLLM(model, message);
    await txResponse.wait();
    process.stdout.write("Waiting for response");
    let response = await contract.lastResponse();
    let error = await contract.lastError();
    while (response.length === 0 && error.length === 0) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      response = await contract.lastResponse();
      error = await contract.lastError();
      process.stdout.write(".");
    }
    console.log("");
    return { response: response, error: error };
  } catch (error) {
    console.error(`Error calling contract function: ${error}`);
  }
  return { response: "", error: "Failed XX" };
}

async function queryContractFunction(
  contract: Contract,
  tool: string,
  query: string,
  hre: HardhatRuntimeEnvironment
): Promise<FunctionResponse> {
  try {
    const txResponse = await contract.callFunction(tool, query);
    await txResponse.wait();
    process.stdout.write("Waiting for response");
    let response = await contract.lastResponse();
    let error = await contract.lastError();
    while (response.length === 0 && error.length === 0) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      response = await contract.lastResponse();
      error = await contract.lastError();
      process.stdout.write(".");
    }
    console.log("");
    return { response: response, error: error };
  } catch (error) {
    console.error(`Error calling contract function: ${error}`);
  }
  return { response: "", error: "Failed XX" };
}

async function queryContractKnowledgeBase(
  contract: Contract,
  cid: string,
  query: string,
  hre: HardhatRuntimeEnvironment
): Promise<FunctionResponse> {
  try {
    const txResponse = await contract.queryKnowledgeBase(cid, query);
    await txResponse.wait();
    process.stdout.write("Waiting for response");
    let response = await contract.lastResponse();
    let error = await contract.lastError();
    while (response.length === 0 && error.length === 0) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      response = await contract.lastResponse();
      error = await contract.lastError();
      process.stdout.write(".");
    }
    console.log("");
    return { response: response, error: error };
  } catch (error) {
    console.error(`Error calling contract function: ${error}`);
  }
  return { response: "", error: "Failed XX" };
}

function getRunId(
  receipt: TransactionReceipt,
  contract: Contract,
  hre: HardhatRuntimeEnvironment,
  eventName: string = "KnowledgeBaseIndexRequestAdded",
  eventArgIndex: number = 0
  ): number | undefined {
  let runId
  for (const log of receipt.logs) {
    try {
      const parsedLog = contract.interface.parseLog(log)
      if (parsedLog && parsedLog.name === eventName) {
        runId = hre.ethers.toNumber(parsedLog.args[eventArgIndex])
      }
    } catch (error) {
      // This log might not have been from your contract, or it might be an anonymous log
      console.log("Could not parse log:", log)
    }
  }
  return runId;
}
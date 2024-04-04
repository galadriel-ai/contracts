import {task} from "hardhat/config";
import {HardhatRuntimeEnvironment} from "hardhat/types";

const TIMEOUT_SECONDS: number = 300
const green = "\x1b[32m"

// npx hardhat e2e --contract-address 0xa85233C63b9Ee964Add6F2cffe00Fd84eb32338f --oracle-address 0xB7f8BC63BbcaD18155201308C8f3540b07f84F5e --network localhost
task("e2e", "Runs all e2e tests")
  .addParam("contractAddress", "The address of the Test contract")
  .addParam("oracleAddress", "The address of the Oracle contract")
  .setAction(async (taskArgs: any, hre: HardhatRuntimeEnvironment) => {
    const contractAddress = taskArgs.contractAddress;
    const oracleAddress = taskArgs.contractAddress;

    await runOpenAi(
      contractAddress,
      "gpt-4-turbo-preview",
      "Who is the president of USA?",
      hre,
    )
    await runOpenAi(
      contractAddress,
      "gpt-3.5-turbo-1106",
      "Who is the president of USA?",
      hre,
    )
    await runGroq(
      contractAddress,
      "llama2-70b-4096",
      "Who is the president of USA?",
      hre,
    )
    await runGroq(
      contractAddress,
      "mixtral-8x7b-32768",
      "Who is the president of USA?",
      hre,
    )
    await runGroq(
      contractAddress,
      "gemma-7b-it",
      "Who is the president of USA?",
      hre,
    )

    console.log(`Running "image_generation"`)
    await runTaskWithTimeout(
      "image_generation",
      {
        contractAddress,
        query: "Red rose",
      },
      hre,
    )
    console.log(`DONE Running "image_generation"`)

    console.log(`Running "web_search"`)
    await runTaskWithTimeout(
      "web_search",
      {
        contractAddress,
        query: "Capital of Germany",
      },
      hre,
    )
    console.log(`DONE Running "web_search"`)

    console.log(`Running "code_interpreter"`)
    await runTaskWithTimeout(
      "code_interpreter",
      {
        contractAddress,
        query: "print(2+2)",
      },
      hre,
    )
    console.log(`DONE Running "code_interpreter"`)

    // console.log(`Running "add_knowledge_base"`)
    // await runTaskWithTimeout(
    //   "add_knowledge_base",
    //   {
    //     oracleAddress,
    //     cid: "QmdCgbMawRVE6Kc1joZmhgDo2mSZFgRgWvBCqUvJV9JwkF",
    //   },
    //   hre,
    // )
    // console.log(`DONE Running "add_knowledge_base"`)
    // console.log(`Running "query_knowledge_base"`)
    // await runTaskWithTimeout(
    //   "query_knowledge_base",
    //   {
    //     contractAddress,
    //     cid: "QmdCgbMawRVE6Kc1joZmhgDo2mSZFgRgWvBCqUvJV9JwkF",
    //     query: "What is the oracle smart contract address?",
    //   },
    //   hre,
    // )
    // console.log(`DONE Running "query_knowledge_base"`)


    console.log("================================================")
    console.log(green, "e2e run done", "green")
  });

async function runTaskWithTimeout(
  taskIdentifier: string,
  taskArguments: any,
  hre: HardhatRuntimeEnvironment,
) {
  const timeoutPromise = new Promise((resolve, reject) => {
    const id = setTimeout(() => {
      clearTimeout(id);
      reject(new Error('Task timed out'));
    }, TIMEOUT_SECONDS * 1000);
  });

  await Promise.race([
    timeoutPromise,
    hre.run(taskIdentifier, taskArguments),
  ]);
  console.log('Task completed successfully');
}


async function runOpenAi(
  contractAddress: string,
  model: string,
  message: string,
  hre: HardhatRuntimeEnvironment,
) {
  console.log(`Running "openai", with model: ${model}`)
  await runTaskWithTimeout(
    "openai",
    {
      contractAddress,
      model,
      message,
    },
    hre,
  )
  console.log(`DONE Running "openai", with model: ${model}.`)
}

async function runGroq(
  contractAddress: string,
  model: string,
  message: string,
  hre: HardhatRuntimeEnvironment,
) {
  console.log(`Running "groq", with model: ${model}`)
  await runTaskWithTimeout(
    "groq",
    {
      contractAddress,
      model,
      message,
    },
    hre,
  )
  console.log(`DONE Running "groq", with model: ${model}.`)
}
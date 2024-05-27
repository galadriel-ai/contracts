import {task} from "hardhat/config";
import {HardhatRuntimeEnvironment} from "hardhat/types";

const TIMEOUT_SECONDS: number = 300
const green = "\x1b[32m"
const reset = "\x1b[0m"

class TimeoutError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "TimeoutError"
  }
}

task("e2e", "Runs all e2e tests")
  .addParam("contractAddress", "The address of the Test contract")
  .addParam("oracleAddress", "The address of the Oracle contract")
  .setAction(async (taskArgs: any, hre: HardhatRuntimeEnvironment) => {
    const contractAddress = taskArgs.contractAddress;
    const oracleAddress = taskArgs.oracleAddress;

    process.env.RUN_MODE = "e2e-script";

    const testResults: Record<string, string> = {};

    try {
      let result = await runOpenAi(
        contractAddress,
        "gpt-4-turbo-preview",
        "Who is the president of USA?",
        hre,
      )
      testResults["OpenAI gpt-4-turbo-preview"] = result.error || "✅";
    } catch (e: any) {
      testResults["OpenAI gpt-4-turbo-preview"] = e.message
    }
  
    try {
      let result = await runOpenAi(
        contractAddress,
        "gpt-3.5-turbo-1106",
        "Who is the president of USA?",
        hre,
      )
      testResults["OpenAI gpt-3.5-turbo-1106"] = result.error || "✅";
    } catch (e: any) {
      testResults["OpenAI gpt-3.5-turbo-1106"] = e.message
    }
    
    try {
      let result = await runOpenAiVision(
        contractAddress,
        "gpt-4-turbo",
        "What is on this image",
        "https://picsum.photos/200/300",
        hre,
      )
      testResults["OpenAI gpt-4-turbo vision"] = result.error || "✅";
    } catch (e: any) {
      testResults["OpenAI gpt-4-turbo vision"] = e.message
    }
    
    try {
      let result = await runOpenAiVision(
        contractAddress,
        "gpt-4o",
        "What is on this image",
        "https://picsum.photos/200/300",
        hre,
      )
      testResults["OpenAI gpt-4o"] = result.error || "✅";
    } catch (e: any) {
      testResults["OpenAI gpt-4o"] = e.message
    }
  
    try {
      let result = await runGroq(
        contractAddress,
        "llama3-8b-8192",
        "Who is the president of USA?",
        hre,
      )
      testResults["Groq llama3-8b-8192"] = result.error || "✅";
    } catch (e: any) {
      testResults["Groq llama3-8b-8192"] = e.message
    }

    try {
      let result = await runGroq(
        contractAddress,
        "llama3-70b-8192",
        "Who is the president of USA?",
        hre,
      )
      testResults["Groq llama3-70b-8192"] = result.error || "✅";
    } catch (e: any) {
      testResults["Groq llama3-70b-8192"] = e.message
    }
  
    try {
      let result = await runGroq(
        contractAddress,
        "mixtral-8x7b-32768",
        "Who is the president of USA?",
        hre,
      )
      testResults["Groq mixtral-8x7b-32768"] = result.error || "✅";
    } catch (e: any) {
      testResults["Groq mixtral-8x7b-32768"] = e.message
    }

    try {
      let result = await runGroq(
        contractAddress,
        "gemma-7b-it",
        "Who is the president of USA?",
        hre,
      )
      testResults["Groq gemma-7b-it"] = result.error || "✅";
    } catch (e: any) {
      testResults["Groq gemma-7b-it"] = e.message
    }
  
    try {
      let result = await runTaskWithTimeout(
        "image_generation",
        {
          contractAddress,
          query: "Red rose",
        },
        hre,
      )
      testResults["OpenAI image_generation"] = result.error || "✅";
    } catch (e: any) {
      testResults["OpenAI image_generation"] = e.message
    }
  
    try {
      let result = await runTaskWithTimeout(
        "web_search",
        {
          contractAddress,
          query: "Capital of Germany",
        },
        hre,
      )
      testResults["web_search"] = result.error || "✅";
    } catch (e: any) {
      testResults["web_search"] = e.message
    }
  
    try {
      let result = await runTaskWithTimeout(
        "code_interpreter",
        {
          contractAddress,
          query: "print(2+2)",
        },
        hre,
      )
      testResults["code_interpreter"] = result.error || "✅";
    } catch (e: any) {
      testResults["code_interpreter"] = e.message
    }

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
    try {
      let result = await runTaskWithTimeout(
        "query_knowledge_base",
        {
          contractAddress,
          cid: "QmdCgbMawRVE6Kc1joZmhgDo2mSZFgRgWvBCqUvJV9JwkF",
          query: "What is the oracle smart contract address?",
        },
        hre,
      )
      testResults["query_knowledge_base"] = result.error || "✅";
    } catch (e: any) {
      testResults["query_knowledge_base"] = e.message
    }
  
    const totalTests = Object.keys(testResults).length;
    const passedTests = Object.values(testResults).filter(result => result === "✅").length;
    const failedTests = totalTests - passedTests;
    console.log(`${passedTests} out of ${totalTests} tests passed `);
    const transformedResults = Object.entries(testResults).map(([testName, result]) => ({
      "Test": testName,
      "Result": result
    }));
    
    console.table(transformedResults);
    if (failedTests > 0) {
      process.exit(1);
    }
  });

async function runTaskWithTimeout(
  taskIdentifier: string,
  taskArguments: any,
  hre: HardhatRuntimeEnvironment,
): Promise<any> {
  try {
    const timeoutPromise = new Promise((resolve, reject) => {
      const id = setTimeout(() => {
        clearTimeout(id);
        reject(new TimeoutError(taskIdentifier));
      }, TIMEOUT_SECONDS * 1000);
    });

    const taskResult = await Promise.race([
      timeoutPromise,
      hre.run(taskIdentifier, taskArguments),
    ]);
    return taskResult;
  } catch (e: any) {
    process.stderr.write(e.message + " ")
    throw e
  }
}

async function runOpenAi(
  contractAddress: string,
  model: string,
  message: string,
  hre: HardhatRuntimeEnvironment,
) {
  let result = await runTaskWithTimeout(
    "openai",
    {
      contractAddress,
      model,
      message,
    },
    hre,
  )
  return result;
}

async function runOpenAiVision(
  contractAddress: string,
  model: string,
  message: string,
  imageUrl: string,
  hre: HardhatRuntimeEnvironment,
) {
  let result = await runTaskWithTimeout(
    "openai_vision",
    {
      contractAddress,
      model,
      message,
      imageUrl
    },
    hre,
  )
  return result;
}

async function runGroq(
  contractAddress: string,
  model: string,
  message: string,
  hre: HardhatRuntimeEnvironment,
) {
  let result = await runTaskWithTimeout(
    "groq",
    {
      contractAddress,
      model,
      message,
    },
    hre,
  )
  return result;
}

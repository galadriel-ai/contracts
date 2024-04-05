require('dotenv').config()

import {spawn} from 'child_process';

const TIMEOUT_SECONDS: number = 60 * 60

async function main(): Promise<void> {
  const command = 'npx';
  const contractAddress = process.env.TEST_CONTRACT_ADDRESS
  const oracleAddress = process.env.TEST_ORACLE_ADDRESS
  const network = process.env.TEST_NETWORK
  const slackWebHookUrl = process.env.TEST_SLACK_WEBHOOK_URL
  if (!contractAddress) {
    console.log(".env is missing TEST_CONTRACT_ADDRESS")
    return
  }
  if (!oracleAddress) {
    console.log(".env is missing ORACLE_ADDRESS")
    return
  }
  if (!network) {
    console.log(".env is missing TEST_NETWORK")
    return
  }
  if (!slackWebHookUrl) {
    console.log(".env is missing TEST_SLACK_WEBHOOK_URL")
    return
  }
  const args: string[] = [
    "hardhat",
    "e2e",
    "--contract-address", contractAddress,
    "--oracle-address", oracleAddress,
    "--network", network
  ];

  while (true) {
    console.log(`Running e2e tests with `)
    await runTests(command, args, slackWebHookUrl)
    console.log(`Run done, sleeping for ${TIMEOUT_SECONDS} seconds`)
    await new Promise((resolve) => setTimeout(resolve, TIMEOUT_SECONDS * 1000));
  }
}

async function runTests(
  command: string,
  args: string[],
  slackWebHookUrl: string,
): Promise<void> {
  try {
    await new Promise((resolve, reject) => {
      const childProcess = spawn(command, args, {shell: true});

      let stdoutData = '';
      let stderrData = '';

      childProcess.stdout.on('data', (data) => {
        console.log(data.toString())
      });

      childProcess.stderr.on('data', (data) => {
        stderrData += data.toString();
      });

      childProcess.on('close', (code) => {
        if (code === 0) {
          resolve(stdoutData);
        } else {
          reject(new Error(stderrData));
        }
      });
    })
  } catch (e: any) {
    console.error(e.message)
    await postSlackMessage(
      `e2e blockchain tests failed\n` +
      "```" +
      `${e.message}` +
      "```",
      slackWebHookUrl,
    )
  }
}

async function postSlackMessage(
  text: string,
  webhookUrl: string,
) {
  try {
    await fetch(
      webhookUrl,
      {
        method: "POST",
        headers: {
          "Content-type": "application/json"
        },
        body: JSON.stringify({
          text
        })
      }
    )
  } catch (e: any) {
    console.error("Failed to post msg to slack", e.message)
  }
}

main()
  .then(() => process.exit(0))
  .catch((error: any) => {
    console.error(error);
    process.exit(1);
  });
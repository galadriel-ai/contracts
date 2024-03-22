import {ethers} from "hardhat";

const DALLE_PROMPT = "make an image of: \"solarpunk oil painting "
const VITAILIK_PROMPT = "You are a narrator for a text based game set in a futuristic world where the player is fighting with \"VIILIK\", a crypto dark lord hacker that looks like a hybrid of a man and a dog with 2 heads and is tattooed full of crypto logos. He holds bunch of weird weapons and uses unique fighting styles to defeat the player. \n\nThe game is played in turns where you present the player with four options (a, b, c, d) at each turn to choose their next action, the player can only pick one of the options, not add anything themselves. Generate the options short and punchy, not too verbose. Both the player and \"VIILIK\" start with 10,000 HP and you increase or decrease their HP after each turn. \n\nTo begin with generate an image to show battleground and VIILIK where you ask from the player what character to play as (come up with animals to select from, add some adjective to make it funny). Please generate according images of player's character.\n\nRemember to generate an image on every turn of how the battle plays out where you add a really short description that describes the scenario at hand. Keep a funny tone. Create funny images and immersive, try to keep a storyline. Put image description in [IMAGE] tags. Make image description as prompt for DALL-E 3. Avoid revealing future outcomes or suggesting a 'best' choice; each should seem viable to maintain the game's suspense. The game starts when user says start. Remember to keep track of VIILIK's and player's HP, IT IS ALSO possible that player's choice hurts his own HP, you decide that as a narrator based on player's choice. Minimum HP hit is 1000 and max 5000.\nShow HP on every turn like this:\nyour HP: {number}\nVIILIK HP: {number}"
const AGENT_PROMPT = "Answer the following questions as best you can. You have access to the following tools:\n\nweb_search: Use this to lookup information from google search engine.\n\nUse the following format:\n\nQuestion: the input question you must answer\n\nThought: you should always think about what to do\n\nAction: the action to take, should be web_search. \Action Input: the input to the action\nObservation: the result of the action\n... (this Thought/Action/Action Input/Observation can repeat N times)\nThought: I now know the final answer\nFinal Answer: the final answer to the original input question\n\nBegin!\n"

async function main() {
  const oracleAddress: string = await deployOracle();
  await deployChatGpt(oracleAddress);
  await deployDalle(oracleAddress);
  await deployVitailik(oracleAddress);
  await deployAgent(oracleAddress);

  await deployOpenAiChatGpt(oracleAddress);
}

async function deployOracle(): Promise<string> {
  const oracle = await ethers.deployContract("ChatOracle", [], {});

  await oracle.waitForDeployment();

  console.log(
    `Oracle deployed to ${oracle.target}`
  );
  // only for local dev
  // await oracle.updateWhitelist((await ethers.getSigners())[0].address, true)

  return oracle.target as string;
}

async function deployChatGpt(oracleAddress: string) {
  const agent = await ethers.deployContract("ChatGpt", [oracleAddress], {});

  await agent.waitForDeployment();

  console.log(
    `ChatGPT deployed to ${agent.target}`
  );
}

async function deployAgent(oracleAddress: string) {
  const agent = await ethers.deployContract(
    "Agent",
    [
      oracleAddress,
      AGENT_PROMPT
    ], {});

  await agent.waitForDeployment();

  console.log(
    `Agent deployed to ${agent.target}`
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

async function deployVitailik(oracleAddress: string) {
  const agent = await ethers.deployContract(
    "Vitailik",
    [
      oracleAddress,
      VITAILIK_PROMPT,
    ], {});

  await agent.waitForDeployment();

  console.log(
    `Vitailik deployed to ${agent.target}`
  );
}

async function deployOpenAiChatGpt(oracleAddress: string) {
  const agent = await ethers.deployContract("OpenAiChatGpt", [oracleAddress], {});

  await agent.waitForDeployment();

  console.log(
    `OpenAiChatGPT deployed to ${agent.target}`
  );
}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

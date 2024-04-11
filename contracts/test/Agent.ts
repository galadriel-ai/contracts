import {loadFixture,} from "@nomicfoundation/hardhat-toolbox/network-helpers";
import {expect} from "chai";
import {ethers} from "hardhat";

describe("Agent", function () {
  // We define a fixture to reuse the same setup in every test.
  // We use loadFixture to run this setup once, snapshot that state,
  // and reset Hardhat Network to that snapshot in every test.
  async function deploy() {
    // Contracts are deployed using the first signer/account by default
    const allSigners = await ethers.getSigners();
    const owner = allSigners[0];

    const Oracle = await ethers.getContractFactory("ChatOracle");
    const oracle = await Oracle.deploy();

    const Agent = await ethers.getContractFactory("Agent");
    const agent = await Agent.deploy("0x0000000000000000000000000000000000000000", "system prompt");

    return {agent, oracle, owner, allSigners};
  }

  describe("Deployment", function () {
    it("User can start agent run", async () => {
      const {agent, oracle, owner} = await loadFixture(deploy);
      await agent.setOracleAddress(oracle.target);

      await agent.runAgent("which came first: the chicken or the egg?", 2);
      // promptId: 0, callbackId: 0
      const messages = await oracle.getMessages(0, 0)
      expect(messages.length).to.equal(2)
      expect(messages[0]).to.equal("system prompt")
      expect(messages[1]).to.equal("which came first: the chicken or the egg?")
    });
    it("Oracle adds response and agents asks a follow-up question", async () => {
      const {
        agent,
        oracle,
        owner,
        allSigners
      } = await loadFixture(deploy);
      const oracleAccount = allSigners[6];
      await agent.setOracleAddress(oracle.target);
      await oracle.updateWhitelist(oracleAccount, true);

      await agent.runAgent("which came first: the chicken or the egg?", 2);
      const response = {
        id: "responseId",
        content: "The Chicken",
        functionName: "",
        functionArguments: "",
        created: 1618888901, // Example UNIX timestamp
        model: "gpt-4-turbo-preview",
        systemFingerprint: "systemFingerprintHere",
        object: "chat.completion",
        completionTokens: 10,
        promptTokens: 5,
        totalTokens: 15
      };
      await oracle.connect(oracleAccount).addOpenAiResponse(0, 0, response, "");
      const messages = await oracle.getMessages(0, 0)
      expect(messages.length).to.equal(3)
      expect(messages[1]).to.equal("which came first: the chicken or the egg?")
      expect(messages[2]).to.equal("The Chicken")
    });
  });
});

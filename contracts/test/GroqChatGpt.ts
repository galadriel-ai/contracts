import {loadFixture,} from "@nomicfoundation/hardhat-toolbox/network-helpers";
import {expect} from "chai";
import {ethers} from "hardhat";

describe("GroqChatGpt", function () {
  // We define a fixture to reuse the same setup in every test.
  // We use loadFixture to run this setup once, snapshot that state,
  // and reset Hardhat Network to that snapshot in every test.
  async function deploy() {
    // Contracts are deployed using the first signer/account by default
    const allSigners = await ethers.getSigners();
    const owner = allSigners[0];

    const Oracle = await ethers.getContractFactory("ChatOracle");
    const oracle = await Oracle.deploy();

    const ChatGpt = await ethers.getContractFactory("GroqChatGpt");
    const chatGpt = await ChatGpt.deploy("0x0000000000000000000000000000000000000000");

    return {chatGpt, oracle, owner, allSigners};
  }

  describe("Deployment", function () {
    it("User can start chat", async () => {
      const {chatGpt, oracle, owner} = await loadFixture(deploy);
      await chatGpt.setOracleAddress(oracle.target);

      await chatGpt.startChat("Hello");
      // promptId: 0, callbackId: 0
      const messages = await oracle.getMessages(0, 0)
      expect(messages.length).to.equal(1)
      expect(messages[0]).to.equal("Hello")
    });
    it("Configuration gets sent to oracle", async () => {
      const {chatGpt, oracle, owner} = await loadFixture(deploy);
      await chatGpt.setOracleAddress(oracle.target);

      await chatGpt.startChat("Hello");
      // promptId: 0, callbackId: 0
      const groqConf = await oracle.groqConfigurations(0)
      expect(groqConf.toString()).to.equal("mixtral-8x7b-32768,21,,1000,21,{\"type\":\"text\"},0,,10,101,")
    });
    it("Oracle can add response", async () => {
      const {chatGpt, oracle, allSigners} = await loadFixture(deploy);
      const oracleAccount = allSigners[6];
      await chatGpt.setOracleAddress(oracle.target);
      await oracle.updateWhitelist(oracleAccount, true);

      await chatGpt.startChat("Hello");

      const response = {
        id: "responseId",
        content: "Hi!",
        created: 1618888901, // Example UNIX timestamp
        model: "mixtral-8x7b-32768",
        systemFingerprint: "systemFingerprintHere",
        object: "chat.completion",
        completionTokens: 10,
        promptTokens: 5,
        totalTokens: 15
      };
      await oracle.connect(oracleAccount).addGroqResponse(0, 0, response, "");

      const messages = await oracle.getMessages(0, 0)
      expect(messages.length).to.equal(2)
      expect(messages[1]).to.equal("Hi!")
    });
  });
});

import {loadFixture,} from "@nomicfoundation/hardhat-toolbox/network-helpers";
import {expect} from "chai";
import {ethers} from "hardhat";

describe("Agent", function () {
  // We define a fixture to reuse the same setup in every test.
  // We use loadFixture to run this setup once, snapshot that state,
  // and reset Hardhat Network to that snapshot in every test.
  async function deploy() {
    // Contracts are deployed using the first signer/account by default
    const [owner, otherAccount] = await ethers.getSigners();

    const AgentOracle = await ethers.getContractFactory("AgentOracle");
    const oracle = await AgentOracle.deploy();
    // Add owner to whitelist for these tests
    await oracle.updateWhitelist(owner.address, true);

    const Agent = await ethers.getContractFactory("Agent");
    const agent = await Agent.deploy("0x0000000000000000000000000000000000000000");

    return {agent, oracle, owner, otherAccount};
  }

  describe("Deployment", function () {
    it("Oracle address should be unset", async () => {
      const {agent, owner} = await loadFixture(deploy);

      expect(await agent.oracleAddress()).to.equal("0x0000000000000000000000000000000000000000");
    });
    it("Should be able to set oracle address", async () => {
      const {agent, oracle} = await loadFixture(deploy);
      await agent.setOracleAddress(oracle.target);

      await expect(agent.setOracleAddress(oracle.target))
        .to.emit(agent, "OracleAddressUpdated")
        .withArgs(oracle.target);
      expect(await agent.oracleAddress()).to.equal(oracle.target);
    });
  });

  describe("Run", function () {
    it("Should add prompt to oracle", async () => {
      const {agent, oracle} = await loadFixture(deploy);
      await agent.setOracleAddress(oracle.target);

      await agent.runAgent("Hello world!", 3);

      const oraclePrompt = await oracle.prompts(0);
      expect(oraclePrompt).to.equal("Hello world!")
    });
    it("Should emit run created event", async () => {
      const {agent, oracle} = await loadFixture(deploy);
      await agent.setOracleAddress(oracle.target);


      await expect(agent.runAgent("Hello world!", 3))
        .to.emit(agent, "AgentRunCreated")
        .withArgs(0);
    });
    it("Should add response to oracle", async () => {
      const {agent, oracle} = await loadFixture(deploy);
      await agent.setOracleAddress(oracle.target);

      await agent.runAgent("Hello", 3);
      await oracle.addResponse(0, " world!", 0);

      const responses = await agent.getResponses(0);
      expect(responses[0]).to.equal(" world!");
    });
    it("Should add new prompt to oracle", async () => {
      const {agent, oracle} = await loadFixture(deploy);
      await agent.setOracleAddress(oracle.target);

      await agent.runAgent("Hello", 3);
      await oracle.addResponse(0, " world!", 0);

      const oraclePrompt1 = await oracle.prompts(0);
      expect(oraclePrompt1).to.equal("Hello")
      const oraclePrompt2 = await oracle.prompts(1);
      expect(oraclePrompt2).to.equal(
        "Hello world!\n" +
        "User: Please elaborate!\n" +
        "Assistant: "
      )
    });
    it("Should end run after max iterations", async () => {
      const {agent, oracle} = await loadFixture(deploy);
      await agent.setOracleAddress(oracle.target);

      await agent.runAgent("Hello", 2);
      await oracle.addResponse(0, " world!", 0);
      await oracle.addResponse(0, " Cool!", 0);

      const run = await agent.agentRuns(0);
      expect(run.is_finished).to.equal(true);
    });
    it("Should not add other uncompleted prompt after max iterations", async () => {
      const {agent, oracle} = await loadFixture(deploy);
      await agent.setOracleAddress(oracle.target);

      await agent.runAgent("You are a helpful assistant!\nUser: Hello\nAssistant: ", 2);
      await oracle.addResponse(0, "world!", 0);
      await oracle.addResponse(1, "Cool!", 0);

      const agentPrompts = await agent.getPrompts(0);
      // 0 - initial prompt, 1 - after first response, 2 - after 2nd(last) response
      const lastAgentPrompt = agentPrompts[2];
      expect(lastAgentPrompt).to.equal(
        "You are a helpful assistant!\n" +
        "User: Hello\n" +
        "Assistant: world!\n" +
        "User: Please elaborate!\n" +
        "Assistant: Cool!"
      )
    });
    it("Should not end run before max iterations", async () => {
      const {agent, oracle} = await loadFixture(deploy);
      await agent.setOracleAddress(oracle.target);

      await agent.runAgent("Hello", 3);
      await oracle.addResponse(0, " world!", 0);
      await oracle.addResponse(0, " Cool!", 0);

      const run = await agent.agentRuns(0);
      expect(run.is_finished).to.equal(false);
    });
    it("Should fail if callback address not oracle contract", async () => {
      const {agent, oracle, owner} = await loadFixture(deploy);
      await agent.setOracleAddress(oracle.target);

      await agent.runAgent("Hello", 3);
      await expect(
        // Calling agent directly
        agent.addResponse(" world!", 0)
      ).to.be.revertedWith("Caller is not oracle");
    });
  });

});

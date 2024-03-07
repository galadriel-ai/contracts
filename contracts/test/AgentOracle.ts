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

    const Oracle = await ethers.getContractFactory("AgentOracle");
    const oracle = await Oracle.deploy();

    const Agent = await ethers.getContractFactory("Agent");
    const agent = await Agent.deploy("0x0000000000000000000000000000000000000000");

    return {agent, oracle, owner, allSigners};
  }

  describe("Deployment", function () {
    it("No addresses in whitelist", async () => {
      const {oracle, allSigners} = await loadFixture(deploy);
      await expect(
        // Calling agent directly
        oracle.addResponse(0, " world!", 0)
      ).to.be.revertedWith("Caller is not whitelisted");
    });
    it("Whitelisted address can add response", async () => {
      const {agent, oracle, allSigners} = await loadFixture(deploy);
      await agent.setOracleAddress(oracle.target);

      await agent.runAgent("Hello", 3);

      const caller = allSigners[4];
      await oracle.updateWhitelist(caller.address, true);
      await oracle.connect(caller).addResponse(0, " world!", 0);

      const agentPrompts = await agent.getPrompts(0);
      expect(agentPrompts.length).to.equal(2)
    });
    it("Can remove from whitelist", async () => {
      const {agent, oracle, allSigners} = await loadFixture(deploy);
      await agent.setOracleAddress(oracle.target);

      await agent.runAgent("Hello", 3);

      const caller = allSigners[4];
      await oracle.updateWhitelist(caller.address, true);
      await oracle.connect(caller).addResponse(0, " world!", 0);

      await oracle.updateWhitelist(caller.address, false);
      await expect(
        oracle.connect(caller).addResponse(0, " world!", 0)
      ).to.be.revertedWith("Caller is not whitelisted");
      const agentPrompts = await agent.getPrompts(0);
      expect(agentPrompts.length).to.equal(2)
    });
  });
});

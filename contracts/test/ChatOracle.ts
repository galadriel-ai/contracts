import {loadFixture,} from "@nomicfoundation/hardhat-toolbox/network-helpers";
import {expect} from "chai";
import {ethers} from "hardhat";

describe("ChatGpt", function () {
  // We define a fixture to reuse the same setup in every test.
  // We use loadFixture to run this setup once, snapshot that state,
  // and reset Hardhat Network to that snapshot in every test.
  async function deploy() {
    // Contracts are deployed using the first signer/account by default
    const allSigners = await ethers.getSigners();
    const owner = allSigners[0];

    const Oracle = await ethers.getContractFactory("ChatOracle");
    const oracle = await Oracle.deploy();

    return {oracle, owner, allSigners};
  }

  describe("Deployment", function () {
    it("Can update attestation", async () => {
      const {oracle, owner, allSigners} = await loadFixture(deploy);
      await oracle.addAttestation(allSigners[1].address, "attestation");

      const attestationOwner = await oracle.latestAttestationOwner();
      const attestation = await oracle.attestations(attestationOwner);
      expect(attestation).to.equal("attestation");
    });
    it("Only owner can update attestation", async () => {
      const {oracle, owner, allSigners} = await loadFixture(deploy);

      await expect(
        oracle.connect(allSigners[1]).addAttestation(allSigners[1].address, "attestation")
      ).to.be.rejectedWith("Caller is not owner");
    });
  });
});

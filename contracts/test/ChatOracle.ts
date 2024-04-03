import {loadFixture,} from "@nomicfoundation/hardhat-toolbox/network-helpers";
import {expect} from "chai";
import {ethers} from "hardhat";

describe("ChatOracle", function () {
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
    it("Whitelisted account can update attestation", async () => {
      const {oracle, owner, allSigners} = await loadFixture(deploy);
      await oracle.connect(owner).updateWhitelist(allSigners[1], true);
      const inputAttestation = "attestation"
      await oracle.connect(allSigners[1]).addAttestation(inputAttestation);

      const attestationOwner = await oracle.latestAttestationOwner();
      const attestation = await oracle.attestations(attestationOwner);
      expect(attestation).to.equal(inputAttestation);
    });
    it("Only whitelisted address can update attestation", async () => {
      const {oracle, owner, allSigners} = await loadFixture(deploy);

      await expect(
        oracle.connect(allSigners[1]).addAttestation("attestation")
      ).to.be.rejectedWith("Caller is not whitelisted");
    });
    it("Owner can update pcr0 hash", async () => {
      const {oracle} = await loadFixture(deploy);
      const inputHash = "random hash"
      await oracle.addPcr0Hash(inputHash);

      const hashOwner = await oracle.latestPcr0HashOwner();
      const hash = await oracle.pcr0Hashes(hashOwner);
      expect(hash).to.equal(inputHash);
    });
    it("Only owner can update pcr0 hash", async () => {
      const {oracle, owner, allSigners} = await loadFixture(deploy);

      await expect(
        oracle.connect(allSigners[1]).addPcr0Hash("hash")
      ).to.be.rejectedWith("Caller is not owner");
    });
  });
});

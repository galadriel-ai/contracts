import {loadFixture,} from "@nomicfoundation/hardhat-toolbox/network-helpers";
import {expect} from "chai";
import {ethers} from "hardhat";

describe("DalleNft", function () {
  // We define a fixture to reuse the same setup in every test.
  // We use loadFixture to run this setup once, snapshot that state,
  // and reset Hardhat Network to that snapshot in every test.
  const PROMPT: string = "make an image of: \"solarpunk oil painting ";

  async function deploy() {
    // Contracts are deployed using the first signer/account by default
    const allSigners = await ethers.getSigners();
    const owner = allSigners[0];

    const Oracle = await ethers.getContractFactory("ChatOracle");
    const oracle = await Oracle.deploy();

    const DalleNft = await ethers.getContractFactory("DalleNft");
    const dalleNft = await DalleNft.deploy(
      "0x0000000000000000000000000000000000000000",
      PROMPT,
    );

    return {dalleNft, oracle, owner, allSigners};
  }

  describe("Deployment", function () {
    it("User can initialize mint", async () => {
      const {dalleNft, oracle, owner} = await loadFixture(deploy);
      await dalleNft.setOracleAddress(oracle.target);

      const userInput: string = "red wolf"
      await dalleNft.initializeMint("red wolf");
      const messages = await dalleNft.getMessageHistoryContents(0)
      expect(messages.length).to.equal(1)
      // Prompt to use!!
      expect(messages[0]).to.equal(`${PROMPT}${userInput}"`)
    });
    it("Oracle can mint", async () => {
      const {
        dalleNft,
        oracle,
        allSigners
      } = await loadFixture(deploy);
      const oracleAccount = allSigners[6];
      await dalleNft.setOracleAddress(oracle.target);
      await oracle.updateWhitelist(oracleAccount, true);

      await dalleNft.initializeMint("funky gorilla");

      await oracle.connect(oracleAccount).addFunctionResponse(0, 0, "ipfs://CID", "");

      const tokenUri = await dalleNft.tokenURI(0)
      expect(tokenUri).to.equal("ipfs://CID")
    });
    it("TotalSupply works", async () => {
      const {
        dalleNft,
        oracle,
        allSigners
      } = await loadFixture(deploy);
      const oracleAccount = allSigners[6];
      await dalleNft.setOracleAddress(oracle.target);
      await oracle.updateWhitelist(oracleAccount, true);

      await dalleNft.initializeMint("funky gorilla");

      await oracle.connect(oracleAccount).addFunctionResponse(0, 0, "ipfs://CID", "");

      const totalSupply = await dalleNft.totalSupply()
      expect(totalSupply).to.equal(1)
    });
    it("Can get user NFT token ID by index", async () => {
      const {
        dalleNft,
        oracle,
        allSigners
      } = await loadFixture(deploy);
      const oracleAccount = allSigners[6];
      await dalleNft.setOracleAddress(oracle.target);
      await oracle.updateWhitelist(oracleAccount, true);

      await dalleNft.initializeMint("funky gorilla");
      await oracle.connect(oracleAccount).addFunctionResponse(0, 0, "ipfs://CID", "");

      await dalleNft.initializeMint("funky gorilla 2");
      await oracle.connect(oracleAccount).addFunctionResponse(1, 1, "ipfs://CID", "");

      const tokenId = await dalleNft.tokenOfOwnerByIndex(allSigners[0].address, 1)
      expect(tokenId).to.equal(1)
    });
  });
  describe("Error handling", function () {
    it("Cannot mint same prompt twice", async () => {
      const {
        dalleNft,
        oracle,
        allSigners,
        owner,
      } = await loadFixture(deploy);
      const oracleAccount = allSigners[6];
      await dalleNft.setOracleAddress(oracle.target);
      await oracle.updateWhitelist(oracleAccount, true);

      await dalleNft.initializeMint("funky gorilla");
      await oracle.connect(oracleAccount).addFunctionResponse(0, 0, "ipfs://CID", "");

      // Ultimate edge-case, user whitelisted some random address
      const randomAccount = allSigners[7];
      await dalleNft.setOracleAddress(randomAccount);

      await expect(
        dalleNft.connect(randomAccount).onOracleFunctionResponse(0, "Hi", "")
      ).to.be.revertedWith("NFT already minted");
    });
  })
});

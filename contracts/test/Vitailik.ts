import {loadFixture,} from "@nomicfoundation/hardhat-toolbox/network-helpers";
import {expect} from "chai";
import {ethers} from "hardhat";

const PROMPT = "custom prompt"
describe("Vitailik", function () {
  // We define a fixture to reuse the same setup in every test.
  // We use loadFixture to run this setup once, snapshot that state,
  // and reset Hardhat Network to that snapshot in every test.
  async function deploy() {
    // Contracts are deployed using the first signer/account by default
    const allSigners = await ethers.getSigners();
    const owner = allSigners[0];

    const AgentOracle = await ethers.getContractFactory("ChatOracle");
    const oracle = await AgentOracle.deploy();
    // Add owner to whitelist for these tests
    await oracle.updateWhitelist(owner.address, true);

    const Vitailik = await ethers.getContractFactory("Vitailik");
    const agent = await Vitailik.deploy(
      oracle.target,
      PROMPT
    );

    return {agent, oracle, owner, allSigners};
  }

  describe("Parsing", function () {
    it("Should return system prompt", async () => {
      const {agent, owner} = await loadFixture(deploy);

      // expect(await agent.oracleAddress()).to.equal("0x0000000000000000000000000000000000000000");
      const prompt = await agent.getSystemPrompt();
      expect(prompt).to.equal(PROMPT);
    });
    it("Should parse out image", async () => {
      const {agent, owner} = await loadFixture(deploy);

      // expect(await agent.oracleAddress()).to.equal("0x0000000000000000000000000000000000000000");
      const imageLine = "[IMAGE] A futuristic digital coliseum, filled with neon lights and a center stage where VIILIK, a grotesque man-dog hybrid with crypto tattoos, stands wielding bizarre weapons."
      const response = await agent.findImageLine(
        "Welcome to the futuristic world of 2150, where battles are no longer a matter of sheer physical strength but a clash of wits, strategy, and a touch of the bizarre. You stand at the threshold of a digital coliseum, the battleground shimmering with neon lights and pulsating with the energy of a thousand watchers. Your adversary? None other than VIILIK, the notorious crypto dark lord hacker. His appearance is as intimidating as his reputation: a man-dog hybrid with two heads, each adorned with snarls and glowing eyes, his body a canvas of shimmering crypto logos. In his hands, he wields weapons that defy conventional understanding, each seeming to pulse with a life of its own.\n" +
        "\n" +
        imageLine +
        "\n" +
        "Before you can confront your fearsome opponent, you must choose your avatar for this battle. Take a moment to consider your form:\n" +
        "\n" +
        "a) A bionic kangaroo with lasers for eyes.\n" +
        "\n" +
        "b) An armored sloth with jetpacks attached to its shell.\n" +
        "\n" +
        "c) A cybernetic eagle with titanium talons.\n" +
        "\n" +
        "d) A neon-lit python with electric volts coursing through its scales.\n" +
        "\n" +
        "Choose your character and prepare for a battle unlike any other. Your destiny awaits."
      )
      expect(response).to.equal(imageLine);
    });
  });

  describe("Playing", function () {
    it("Should start game with 2 messages", async () => {
      const {agent, oracle, owner} = await loadFixture(deploy);

      await agent.startGame()
      const messages = await oracle.getMessages(0, 0);
      const roles = await oracle.getRoles(0, 0);

      expect(messages.length).to.equal(2);
      expect(roles.length).to.equal(2);
      expect(messages[0]).to.equal(PROMPT);
      expect(roles[0]).to.equal("system");
      expect(messages[1]).to.equal("start");
      expect(roles[1]).to.equal("user");
    });
    it("Oracle can respond", async () => {
      const {
        agent,
        oracle,
        allSigners
      } = await loadFixture(deploy);

      const oracleAccount = allSigners[6];
      await oracle.updateWhitelist(oracleAccount, true);

      await agent.startGame();
      await oracle.connect(oracleAccount).addResponse(0, 0, "oracle response", "chat");

      const messages = await oracle.getMessages(0, 0);
      const roles = await oracle.getRoles(0, 0);

      expect(messages.length).to.equal(3);
      expect(messages[2]).to.equal("oracle response");
      expect(roles[2]).to.equal("assistant");
    });
    it("Oracle can respond to multiple games", async () => {
      const {
        agent,
        oracle,
        allSigners
      } = await loadFixture(deploy);

      const oracleAccount = allSigners[6];
      await oracle.updateWhitelist(oracleAccount, true);

      await agent.startGame();
      await oracle.connect(oracleAccount).addResponse(0, 0, "oracle response", "chat");

      await agent.startGame();
      await oracle.connect(oracleAccount).addResponse(1, 1, "oracle response2", "chat");

      const messages = await oracle.getMessages(1, 1);
      const roles = await oracle.getRoles(1, 1);

      expect(messages.length).to.equal(3);
      expect(messages[2]).to.equal("oracle response2");
      expect(roles[2]).to.equal("assistant");
    });
    it("User can select answer", async () => {
      const {
        agent,
        oracle,
        allSigners
      } = await loadFixture(deploy);

      const oracleAccount = allSigners[6];
      await oracle.updateWhitelist(oracleAccount, true);

      await agent.startGame();
      await oracle.connect(oracleAccount).addResponse(0, 0, "oracle response", "chat");
      const gameId: number = 0;
      await agent.addSelection(2, gameId);

      const messages = await oracle.getMessages(0, gameId);
      const roles = await oracle.getRoles(0, gameId);

      expect(messages.length).to.equal(4);
      expect(messages[3]).to.equal("C");
      expect(roles[3]).to.equal("user");

      const game = await agent.games(0);

      expect(game.isFinished).to.equal(false);
    });
    it("Game is finished", async () => {
      const {
        agent,
        oracle,
        allSigners
      } = await loadFixture(deploy);

      const oracleAccount = allSigners[6];
      await oracle.updateWhitelist(oracleAccount, true);

      await agent.startGame();
      await oracle.connect(oracleAccount).addResponse(0, 0, "oracle response\nYour HP: 0", "chat");
      const gameId: number = 0;

      const game = await agent.games(0);

      expect(game.isFinished).to.equal(true);
    });
    it("Adds image generation function call", async () => {
      const {
        agent,
        oracle,
        allSigners
      } = await loadFixture(deploy);

      const oracleAccount = allSigners[6];
      await oracle.updateWhitelist(oracleAccount, true);

      await agent.startGame();
      await oracle.connect(oracleAccount).addResponse(0, 0, "oracle response\n[IMAGE] fun image\n", "chat");

      const functionInput = await oracle.functionInputs(0);

      expect(functionInput).to.equal("[IMAGE] fun image");
    });
    it("Does not add image generation function call", async () => {
      const {
        agent,
        oracle,
        allSigners
      } = await loadFixture(deploy);

      const oracleAccount = allSigners[6];
      await oracle.updateWhitelist(oracleAccount, true);

      await agent.startGame();
      await oracle.connect(oracleAccount).addResponse(0, 0, "oracle response\n", "chat");

      const functionsCount = await oracle.functionsCount();

      expect(functionsCount).to.equal(0);
    });
    it("Adds image url to list", async () => {
      const {
        agent,
        oracle,
        allSigners
      } = await loadFixture(deploy);

      const oracleAccount = allSigners[6];
      await oracle.updateWhitelist(oracleAccount, true);

      await agent.startGame();
      await oracle.connect(oracleAccount).addResponse(0, 0, "URL", "function_result");

      const game = await agent.games(0);
      const images = await agent.getImages(0);
      expect(game.imagesCount).to.equal(1);
      expect(images[0]).to.equal("URL");
    });
  });

  describe("Errors", function () {
    it("Cannot add multiple responses", async () => {
      const {
        agent,
        oracle,
        allSigners
      } = await loadFixture(deploy);

      const oracleAccount = allSigners[6];
      await oracle.updateWhitelist(oracleAccount, true);

      await agent.startGame();
      await oracle.connect(oracleAccount).addResponse(0, 0, "oracle response", "chat");
      const randomAddress = allSigners[7];
      await agent.setOracleAddress(randomAddress);
      await expect(
        agent.connect(randomAddress).addResponse("oracle response 2", "chat", allSigners[0].address, 0)
      ).to.be.revertedWith("No message to respond to");
    })
    it("Cannot add selection for finished game", async () => {
      const {
        agent,
        oracle,
        allSigners
      } = await loadFixture(deploy);

      const oracleAccount = allSigners[6];
      await oracle.updateWhitelist(oracleAccount, true);

      await agent.startGame();
      await oracle.connect(oracleAccount).addResponse(0, 0, "oracle response HP: 0", "chat");
      await expect(
        agent.addSelection(3, 0)
      ).to.be.revertedWith("Game is finished");
    })
    it("Cannot add invalid selection", async () => {
      const {
        agent,
        oracle,
        allSigners
      } = await loadFixture(deploy);

      const oracleAccount = allSigners[6];
      await oracle.updateWhitelist(oracleAccount, true);

      await agent.startGame();
      await oracle.connect(oracleAccount).addResponse(0, 0, "oracle response", "chat");
      await expect(
        agent.addSelection(8, 0)
      ).to.be.revertedWith("Selection needs to be 0-3");
    })
  })
});


<p align="center">
    <a href="https://galadriel.com" style="max-width: 100px;" target="_blank">
        <picture>
            <source srcset="Galadriel-light.svg" media="(prefers-color-scheme: dark)">
            <source srcset="Galadriel.svg" media="(prefers-color-scheme: light)">
        <!-- Fallback for browsers that do not support media attribute -->
        <img src="Galadriel.svg">
        </picture>
    </a>
</p>
<p align="center">
    Galadriel - the first Layer 1 for AI.
</p>
<p align="center">
    <a href="https://discord.com/invite/bHnFgSTKrP" target="_blank"><img src="https://img.shields.io/discord/1133675019478782072?label=Join%20Discord"></a><a href="https://twitter.com/e2b_dev" target="_blank"><img src="https://img.shields.io/twitter/follow/Galadriel_AI"></a>
</p>
<p align="center">
    Documentation: <a href="https://docs.galadriel.com" target="_blank">docs.galadriel.com</a>
</p>

## Galadriel overview

Galadriel is the first L1 for AI.

Ethereum enabled writing smart contracts to build dApps. Similarly, Galadriel enables developers to build AI apps & agents like smart contracts — decentralized and on-chain. We support a range of AI usage: from simple LLM features in existing dApps to highly capable AI agents like on-chain AI hedge funds, in-game AI NPCs and AI-generated NFTs.

Galadriel makes it possible to build AI applications and agents as Solidity contracts on our high-throughput EVM-compatible layer 1 chain.

## Quickstart

Please follow [this guide](https://docs.galadriel.com/quickstart) to get started with Galadriel.

## Examples

Example on-chain AI applications you can try already:
* [On-chain ChatGPT](https://chatgpt.galadriel.com/)
* [On-chain AI game](https://vitailik.galadriel.com/)

See more in our documentation: [use cases](https://docs.galadriel.com/use-cases).

## How it works

To put LLM (and other) calls on-chain, we introduce an oracle. The oracle consists of an on-chain part (which you call when developing a Solidity contract) and an off-chain part (which makes the off-chain call and produces the response in a callback to your contract).

See the high-level execution flow in below, or read more about how Galadriel works in [our documentation](https://docs.galadriel.com/how-it-works).

![](architecture.jpg)



## This repository

This repository contains the basic building blocks of Galadriel's on-chain AI:

* Quickstart contracts and scripts: see the [quickstart documentation](https://docs.galadriel.com/quickstart);
* [Contract examples](/contracts/contracts) for dApps like on-chain ChatGPT, AI agents, generative-AI NFT collections;
* [End-to-end examples](/examples) of integrating Galadriel into your project;
* Oracle [contract](/contracts/contracts/ChatOracle.sol) and back-end [implementation](/oracles).


## Getting help
If you have any questions about Galadriel, feel free to do any of the following:

* [Join our Discord](https://discord.com/invite/bHnFgSTKrP) and ask.
* Report bugs or feature requests in [GitHub issues](https://github.com/galadriel-ai/contracts/issues).
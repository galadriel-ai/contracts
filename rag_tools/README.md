# Knowledge Base Ingestion

The RAG (Retrieval-Augmented Generation) Knowledge Base Script is designed to automate the process of ingesting documents into a knowledge base, converting them into a vectorized format, and storing this information on the Galadriel chain. This script simplifies the process of creating a decentralized, blockchain-based knowledge base that can be queried and utilized by AI models for enhanced information retrieval and decision-making processes.

## Features

- **Document Ingestion:** Automatically ingest multiple documents from a specified directory.
- **Vectorization:** Convert textual information into a vector format suitable for AI models.
- **Blockchain Integration:** Seamlessly integrates with the Galadriel L1 chain, leveraging its Oracle system for decentralized storage and retrieval.
- **IPFS Support:** Uses IPFS (InterPlanetary File System) for secure and distributed document storage.

## Prerequisites

Before you begin, ensure you have the following:
- Python 3.11 or later installed on your system.
- A funded wallet and corresponding private key
- An API key for `pinata.cloud` to facilitate document uploading to IPFS. You can obtain this key by registering at [pinata.cloud](https://www.pinata.cloud).

## Setup

To set up your environment for running the RAG Knowledge Base Script, follow these steps:

1. Clone the repository to your local machine.
2. Create a virtual environment for Python dependencies:
    ```shell
    python -m venv venv
    source venv/bin/activate
    ```
3. Install the required Python packages:
    ```shell
    pip install -r requirements.txt
    ```
4. Create a `.env` file and add your `pinata.cloud` API key and wallet private key as follows:
    ```plaintext
    ORACLE_ADDRESS=galadriel_oracle_address
    PRIVATE_KEY=your_wallet_private key
    PINATA_API_KEY=your_api_key_here
    ```

## How to Use

1. Place your document files in a designated directory. The script can process multiple files in a batch.
2. Run the script with the necessary arguments. For example, to ingest documents from the `galadriel_docs` directory, set a chunk size of 1500, and specify an oracle fee of 200:
    ```
    % python add_knowledge_base.py -d galadriel_docs -s 1500 -o 200
    [Loading 13 files from galadriel_docs.]
    Processing Files: 100%|███████████████████████████████████████████████████████████████████████████████████████| 13/13 [00:02<00:00,  4.70file/s]
    Generated 47 documents from 13 files.
    Uploading documents to IPFS, please wait...done.
    Requesting indexing, please wait...done.
    Knowledge base indexed, index CID `bafybeib36x56l7hgu4k47msj3bpxf4rfwlyu4xwt4m3jptlvo5litaar4q`.
    Use CID `bafkreifrqfc7apfnvd2legjygs2woutrfartm7dabmdvdfs7fy2veehhli` in your contract to query the indexed knowledge base.
    ```
3. Follow the command-line instructions as the script processes the documents, uploads them to IPFS, and requests indexing on the Galadriel L1 chain.
4. Upon completion, the script will provide you with a CID (Content Identifier) that can be used in your smart contracts or applications to query the indexed collection.

# RAG knowledge base script

## Setup

```shell
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## How to use

```shell
% python add_knowledge_base.py -d data
[Loading 5 files from data.]
Processing Files: 100%|███████████████████████| 5/5 [00:02<00:00,  1.68file/s]
Generated 5 documents from 5 files.
Uploading documents, please wait...
Uploaded collection to IPFS.
Requesting indexing, please wait...
Waiting for indexing to complete...
Collection indexed, index CID bafkreihgkrl7udanqbvkcig46xgp3dzj2mo5qidyvxmj7gga4vt5mdcu5m.
Use CID `bafkreic2ft2wzozti3kpyilyjk4f5peirzdia7phmvicva6bbdwtjkx5ny` in your contract to query the indexed collection.
```


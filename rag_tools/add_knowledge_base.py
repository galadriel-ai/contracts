import settings
import argparse
import os

from knowledgebase import load_documents_use_case
from knowledgebase import upload_documents_use_case
from knowledgebase import request_indexing_use_case
from langchain.text_splitter import RecursiveCharacterTextSplitter


def main(directory: str, chunk_size: int, chunk_overlap: int) -> None:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    documents = load_documents_use_case.execute(directory, text_splitter)
    print("Uploading documents to IPFS, please wait...", end="")
    cid: str = upload_documents_use_case.execute(documents)
    print(f"done.")
    print("Requesting indexing, please wait...",end="")
    response = request_indexing_use_case.execute(cid)
    if response.is_processed and response.index_cid:
        print("done.")
        print(f"Knowledge base indexed, index CID `{response.index_cid}`.")
        print(f"Use CID `{cid}` in your contract to query the indexed knowledge base.")
    else:
        print("failed.")
        print(response.error or "Failed to index knowledge base.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload a directory to IPFS as a vector Database",
    )
    parser.add_argument("-d", "--directory", required=True)
    parser.add_argument("-s", "--chunk-size", type=int, default=8000)
    parser.add_argument("-o", "--chunk-overlap", type=int, default=100)
    args = parser.parse_args()

    assert settings.STORAGE_KEY, "PINATA_API_KEY missing from .env"

    if not os.path.exists(args.directory):
        print(f"Directory {args.directory} does not exist, exiting.")
    else:
        main(args.directory, args.chunk_size, args.chunk_overlap)

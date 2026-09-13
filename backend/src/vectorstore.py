import sys
import time
from pathlib import Path
from typing import List,Optional

from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from tqdm import tqdm

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from config import (
    OPENAI_API_KEY,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_ENVIRONMENT,
    OPENAI_EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    RETRIEVER_TOP_K,
)
from src.logger import get_logger

log = get_logger(__name__)

BATCH_SIZE = 100

def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=OPENAI_EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY
    )

def get_pinecone_client():
    return Pinecone(api_key=PINECONE_API_KEY)

def create_index_if_not_exists(pc:Pinecone) -> None:
    existing = [idx.name for idx in pc.list_indexes()]
    if PINECONE_INDEX_NAME in existing:
        log.info(f"Index '{PINECONE_INDEX_NAME}' already exists - skipping creation")
        return
    
    log.info(f"Creating index '{PINECONE_INDEX_NAME}' [dim={EMBEDDING_DIMENSION}]")
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=EMBEDDING_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region=PINECONE_ENVIRONMENT
        )
    )

    log.info("Waiting for index to be ready")
    while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
        time.sleep(2)
    log.info("Index is ready")


def upsert_documents(chunks:List[Document]) -> PineconeVectorStore:
    pc = get_pinecone_client()
    create_index_if_not_exists(pc)
    embeddings = get_embeddings()

    log.info(f"Upsering {len(chunks)} chunks to Pinecone...")
    batches = [chunks[i:i + BATCH_SIZE] for i in range(0, len(chunks), BATCH_SIZE)]

    vectorstore = None
    for i, batch in enumerate(tqdm(batches,desc="Uploading")):
        try:
            if vectorstore is None:
                vectorstore = PineconeVectorStore.from_documents(
                    documents=batch,
                    embedding=embeddings,
                    index_name=PINECONE_INDEX_NAME
                )
            else:
                vectorstore.add_documents(batch)
        
        except Exception as e:
            log.error(f"Batch {i+1} failed: {e}")
            raise
        time.sleep(0.3)
    log.info(f"Done - {len(chunks)} chunks stored in Pinecone")
    # pyrefly: ignore [bad-return]
    return vectorstore

def load_vectorstore() -> PineconeVectorStore:
    log.info(f"Loading Pinecone index '{PINECONE_INDEX_NAME}'")
    vs = PineconeVectorStore(
        index_name=PINECONE_INDEX_NAME,
        embedding=get_embeddings(),
        pinecone_api_key=PINECONE_API_KEY
    )
    log.info("Vector store loaded")
    return vs

def get_retriever(vectorStore: Optional[PineconeVectorStore] = None):
    if vectorStore is None:
        vectorStore = load_vectorstore()
    
    return vectorStore.as_retriever(
        search_type="similarity",
        search_kwargs={"k":RETRIEVER_TOP_K}
    )

def get_index_stats() -> dict:
    pc = get_pinecone_client()
    index = pc.Index(PINECONE_INDEX_NAME)
    stats = index.describe_index_stats()

    return {
        "total_vectors": stats.total_vector_count,
        "dimensions":stats.dimensions
    }
    
import sys
from pathlib import Path
from typing import Any,Dict,List

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from config import (
    OPENAI_API_KEY,
    OPENAI_LLM_MODEL,
    LLM_TEMPERATURE,
    MAX_TOKENS_RESPONSE
)

from src.logger import get_logger
log = get_logger(__name__)

PROMPT_TEMPLATE="""You are MedBot, an expert medical assistant buit on the Gale Encyclopedia of Medicine (3rd Edition).
You help doctors and medical professionals get accurate, well-structured medical information instantly.

RULES:
- Answer ONLY from the provided context below.
- Use proper medical terminology.
- Structure your answer clearly: alwatys start with a brief definition, then cover causes, symptoms, diagnosis, and treatment where relevant.
- If the context does not have enough information, say: "I don't have sufficient information in the encyclopedia to answer this accurately."
- Never fabricate or guess medical facts.
- Be thorough but precise. Doctors value accuracy over brevity.

CONTEXT
---------------------------------------------
{context}
---------------------------------------------

QUESTION: {question}

ANSWER:"""

PROMPT = PromptTemplate(
    template=PROMPT_TEMPLATE,
    input_variables=["context","question"]
)

def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=OPENAI_LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        max_tokens=MAX_TOKENS_RESPONSE,
        openai_api_key=OPENAI_API_KEY
    )

def build_rag_chain(retriever) -> RetrievalQA:
    llm = get_llm()
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={
            "prompt": PROMPT,
            "verbose": False
        },
    )
    log.info(f"RAG chain built [model={OPENAI_LLM_MODEL}, temp={LLM_TEMPERATURE}]")
    return chain

def ask(chain:RetrievalQA, question:str) -> Dict[str,Any]:
    if not question.strip():
        return {"answer":"Please provide a valid question","sources":[]}
    
    log.info(f"Question: {question[:80]}")
    result = chain.invoke({"query": question})

    answer = result.get("result","No answer generated.")
    source_docs: List = result.get("source_documents",[])

    seen = set()
    sources = []
    for doc in source_docs:
        page = doc.metadata.get("page","?")
        seen.add(page)
        sources.append({
            "page":page,
            "preview":doc.page_content[:150].replace("\n"," ") + "...",
        })
    
    log.info(f"Answer generated | sources: pages {[s['page'] for s in sources]}")

    return {
        "answer": answer,
        "sources": sources
    }

def build_streaming_chain(retriever):
    llm = ChatOpenAI(
        model= OPENAI_LLM_MODEL,
        temperature= LLM_TEMPERATURE,
        max_tokens=MAX_TOKENS_RESPONSE,
        openai_api_key=OPENAI_API_KEY,
        streaming=True
    )

    chain = RetrievalQA.from_chain_type(
        llm = llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs = {
            "prompt":PROMPT,
            "verbose":False
        },
    )

    log.info("Streaming RAG chain is built")
    return chain
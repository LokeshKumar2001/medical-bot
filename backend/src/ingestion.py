import re
import sys
from pathlib import Path
from typing import List

from langchain.schema  import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pypdf import PdfReader


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import CHUNK_SIZE, CHUNK_OVERLAP
from src.logger import get_logger 

log = get_logger(__name__)

def clean_text(text:str) -> str:
    """Clean up the raw text from the pdf files"""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"^\s*\d+\s*$", "" , text, flags=re.MULTILINE)
    text = text.replace("\u2013","-").replace("\u2014","--")
    text = text.replace("\u201c",'"').replace("\u201d",'"')
    text = text.replace("\u2018","'").replace("\u2019","'")
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def load_pdf(pdf_path:str) -> List[Document]:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    
    log.info(f"Loading PDF: {path}")
    reader = PdfReader(str(path))
    total_pages = len(reader.pages)
    log.info(f"Total Pages: {total_pages}")

    documents = []
    for page_num, page in enumerate(reader.pages,start=1):
        raw = page.extract_text() or ""
        clean = clean_text(raw)
        if len(clean) < 50:
            continue
        documents.append(Document(
            page_content=clean,
            metadata={
                "source": path.name,
                "page": page_num,
                "pdf_size": total_pages,
            }
        ))
    log.info(f"Loaded {len(documents)} pages with content")
    return documents

def chunk_documents(documents:List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = CHUNK_SIZE,
        chunk_overlap = CHUNK_OVERLAP,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ],
        length_function=len, 
    )

    log.info(f"Chunking {len(documents)} pages [size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}]")
    chunks = splitter.split_documents(documents)

    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i
        chunk.metadata["char_count"] = len(chunk.page_content)

    avg = sum(c.metadata["char_count"] for c in chunks) // len(chunks)
    log.info(f"Created {len(chunks)} chunks | avg size: {avg} chars")
    return chunks

def load_and_chunks(pdf_path:str) -> List[Document]:
    pages = load_pdf(pdf_path)
    chunks = chunk_documents(pages)
    return chunks

# Alias for convenience
load_and_chunk = load_and_chunks
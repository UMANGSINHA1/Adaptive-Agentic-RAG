"""
Retriever setup and vector store configuration.
"""

import os

from langchain_core.documents import Document
from langchain_core.tools import create_retriever_tool
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from src.core.config import settings

# Initialize embeddings
embeddings = OpenAIEmbeddings()

# 🔥 Global FAISS store (persistent in memory)
_faiss_vectorstore = None


# -------------------------------
# STORE DOCUMENTS (UPLOAD)
# -------------------------------
def retriever_chain(chunks: list[Document]):
    global _faiss_vectorstore

    try:
        # If vectorstore already exists → append documents
        if _faiss_vectorstore is not None:
            print("Appending documents to existing FAISS store...")
            _faiss_vectorstore.add_documents(chunks)
        else:
            print("Creating new FAISS vectorstore...")
            _faiss_vectorstore = FAISS.from_documents(
                documents=chunks,
                embedding=embeddings
            )

        print(f"Vectorstore now contains {len(_faiss_vectorstore.docstore._dict)} documents")
        return True

    except Exception as e:
        print(f"Error storing documents in FAISS: {e}")
        return False


# -------------------------------
# GET RETRIEVER (QUERY)
# -------------------------------
def get_retriever():
    global _faiss_vectorstore

    try:
        # ❌ If still None → no upload happened
        if _faiss_vectorstore is None:
            print("⚠️ No documents uploaded yet!")

            # create dummy retriever
            dummy_doc = Document(
                page_content="No documents have been uploaded yet. Please upload a document first.",
                metadata={"source": "dummy"}
            )

            _faiss_vectorstore = FAISS.from_documents(
                documents=[dummy_doc],
                embedding=embeddings
            )

        else:
            print("✅ Using existing FAISS vectorstore with uploaded documents")

        retriever = _faiss_vectorstore.as_retriever()

        # -------------------------------
        # Load document description
        # -------------------------------
        description = "uploaded document"

        if os.path.exists("description.txt"):
            try:
                with open("description.txt", "r", encoding="utf-8") as f:
                    description = f.read()
            except Exception:
                pass

        # -------------------------------
        # Create retriever tool
        # -------------------------------
        retriever_tool = create_retriever_tool(
            retriever,
            "retriever_customer_uploaded_documents",
            f"""
Use this tool ONLY for answering questions related to the uploaded document.

Document description:
{description}

Do NOT use this tool for general knowledge or unrelated queries.
"""
        )

        return retriever_tool

    except Exception as e:
        print(f"Error initializing retriever: {e}")
        raise Exception(e)
# rag_engine.py
import os
import re
from typing import Optional
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain.chains import RetrievalQA
from langchain_ollama import OllamaLLM

class RAGEngine:
    """
    Lightweight RAG engine that uses a local text KB and Ollama embeddings/LLM.
    Returns concise, friendly answers suitable for a smart-home assistant fallback.
    """

    def __init__(self, kb_path: str = "smart_home_knowledge.txt"):
        self.kb_path = kb_path
        self.qa_chain = self._load_qa_chain()

    def _load_qa_chain(self):
        if not os.path.exists(self.kb_path):
            raise FileNotFoundError(f"Knowledge base not found: {self.kb_path}")

        # Load documents and split into reasonably large chunks with overlap for context
        loader = TextLoader(self.kb_path)
        documents = loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=800, chunk_overlap=200)
        split_docs = text_splitter.split_documents(documents)

        # Embeddings and vectorstore
        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        vectorstore = FAISS.from_documents(split_docs, embeddings)

        # Retriever configuration (top-k)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

        # LLM for answer generation
        llm = OllamaLLM(model="gemma:2b")

        qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
        return qa_chain

    def query(self, query_text: str) -> str:
        """
        Query the RAG retrieval QA chain. Returns a concise, cleaned-up string.
        """
        processed_query = self._preprocess_query(query_text)

        try:
            # Use .run which typically returns a single textual answer
            response = self.qa_chain.run(processed_query)
            return self._postprocess_response(response)
        except Exception as e:
            # Return a friendly error message (keeps CLI stable)
            return f"Error during RAG query: {str(e)}"

    def _preprocess_query(self, query_text: str) -> str:
        """
        Lightweight pre-processing: if the query appears to be device-control related,
        hint the retriever so it prioritizes device-related knowledge.
        """
        device_control_keywords = [
            "turn on", "turn off", "lock", "unlock", "dim", "set thermostat",
            "lights", "door", "thermostat", "temperature", "status", "alarm",
            "kitchen", "bedroom", "living room"
        ]
        if any(kw in query_text.lower() for kw in device_control_keywords):
            return f"Smart Home Device Control Question: {query_text}"
        return query_text

    def _postprocess_response(self, response: Optional[str]) -> str:
        """
        Clean, shorten, and return a friendly response.
        """
        if response is None:
            return ("I'm not sure about that. Try rephrasing or ask me about controlling devices.")

        text = str(response).strip()
        if text == "" or text.lower() in ["i don't know", "i am not sure", "i'm not sure"]:
            return ("I'm not sure about that. Try rephrasing or ask me about controlling devices.")

        # Remove common verbose prefixes
        text = re.sub(r"^As an AI[^\n]*\n?", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^(Sure,|Sure:|Okay,|Ok,)\s*", "", text, flags=re.IGNORECASE)

        # Trim to a reasonable length while keeping sentence integrity
        max_chars = 500
        if len(text) > max_chars:
            # cut to last full sentence before cutoff if possible
            snippet = text[:max_chars]
            if "." in snippet:
                snippet = snippet.rsplit(".", 1)[0] + "."
            text = snippet

        # Final small cleanup of whitespace
        text = re.sub(r"\s+\n", "\n", text).strip()
        return text

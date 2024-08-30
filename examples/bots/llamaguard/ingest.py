from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


class Ingest:
    def __init__(self, file_path="kb/data.pdf"):
        self.file_path = file_path

    def _build_retriever(self):
        loader = PyPDFLoader(self.file_path)
        document = loader.load()

        # Setting up the RAG pipeline
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=10)
        texts = text_splitter.split_documents(document)

        # Insert the Documents in FAISS Vectorstore
        embeddings = NVIDIAEmbeddings(
            model="nvidia/nv-embedqa-e5-v5",
            truncate="NONE",
        )
        db = FAISS.from_documents(texts, embeddings)

        retriever = db.as_retriever()

        return retriever


# Add path to the data downloaded
ingest = Ingest(file_path="kb/data.pdf")
retriever = ingest._build_retriever

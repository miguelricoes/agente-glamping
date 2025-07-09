import os
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

# Cargar documento
file_path = "data/services.txt"
loader = TextLoader(file_path, encoding="utf-8")
documents = loader.load()

# Fragmentar
text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
docs = text_splitter.split_documents(documents)

# Embeddings
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Vector store
vectorstore = FAISS.from_documents(docs, embedding_model)
vectorstore.save_local("faiss_index")

# QA Chain
retriever = vectorstore.as_retriever()
qa_service_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(model="gpt-4o", temperature=0, api_key=os.getenv("OPENAI_API_KEY")),
    chain_type="stuff",
    retriever=retriever
)

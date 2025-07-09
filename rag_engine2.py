import os
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI  # ✔️ recomendado por las advertencias

# Cargar variables de entorno
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
assert OPENAI_API_KEY, "Falta la variable OPENAI_API_KEY"

# 🔤 Inicializar LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=OPENAI_API_KEY)

# 🧠 Embeddings
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 📁 Utilidad para cargar documentos y generar cadenas QA
def create_qa_chain(file_path: str, index_path: str) -> RetrievalQA:
    # Cargar y dividir documentos
    loader = TextLoader(file_path, encoding="utf-8")
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)

    # Vector store y guardado
    vectorstore = FAISS.from_documents(docs, embedding_model)
    vectorstore.save_local(index_path)

    # Crear y retornar la cadena QA
    retriever = vectorstore.as_retriever()
    return RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)

# 📦 QA Chain para glamping general
qa_chain = create_qa_chain("data/documentos.txt", "vectorstore/documentos")

# 📦 QA Chain para servicios
qa_service_chain = create_qa_chain("data/services.txt", "vectorstore/services")

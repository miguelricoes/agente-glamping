import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

# Cargar variables de entorno
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
assert OPENAI_API_KEY, "Falta la variable OPENAI_API_KEY en las variables de entorno."

# Inicializar LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY)

# Embeddings
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Utilidad para cargar documentos, generar vectorstore y cadena QA
def create_qa_chain(file_path: str, index_dir: str) -> RetrievalQA:
    # Cargar y dividir documentos
    loader = TextLoader(file_path, encoding="utf-8")
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200) # Ajusta chunk_size/overlap si es necesario
    docs = text_splitter.split_documents(documents)

    # Crear el directorio del índice si no existe
    if not os.path.exists(index_dir):
        os.makedirs(index_dir)

    # Vector store y guardado local
    vectorstore = FAISS.from_documents(docs, embedding_model)
    vectorstore.save_local(index_dir)

    # Crear y retornar la cadena QA
    retriever = vectorstore.as_retriever()
    return RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)

# --- Creación de cadenas QA para cada documento optimizado ---

# Directorio base para los archivos de datos
DATA_DIR = "data"
# Directorio base para los índices FAISS
VECTORSTORE_BASE_DIR = "vectorstore"

# 1. Ubicación y Contacto
qa_ubicacion_contacto = create_qa_chain(
    os.path.join(DATA_DIR, "ubicacion_contacto.txt"),
    os.path.join(VECTORSTORE_BASE_DIR, "ubicacion_contacto_index")
)

# 2. Accesibilidad y Movilidad Reducida
qa_accesibilidad = create_qa_chain(
    os.path.join(DATA_DIR, "accesibilidad_movilidad_reducida.txt"),
    os.path.join(VECTORSTORE_BASE_DIR, "accesibilidad_index")
)

# 3. Información de Domos (Características y Precios)
qa_domos_info = create_qa_chain(
    os.path.join(DATA_DIR, "domos_info.txt"),
    os.path.join(VECTORSTORE_BASE_DIR, "domos_info_index")
)

# 4. Concepto y Filosofía del Glamping
qa_concepto = create_qa_chain(
    os.path.join(DATA_DIR, "concepto_brillodeluna.txt"),
    os.path.join(VECTORSTORE_BASE_DIR, "concepto_index")
)

# 5. Políticas y Términos del Glamping
qa_politicas = create_qa_chain(
    os.path.join(DATA_DIR, "politicas_glamping.txt"),
    os.path.join(VECTORSTORE_BASE_DIR, "politicas_index")
)

# 6. Servicios Incluidos en los Domos
qa_servicios_incluidos = create_qa_chain(
    os.path.join(DATA_DIR, "servicios_incluidos_domos.txt"),
    os.path.join(VECTORSTORE_BASE_DIR, "servicios_incluidos_index")
)

# 7. Actividades y Servicios Adicionales (Opcionales)
qa_actividades_adicionales = create_qa_chain(
    os.path.join(DATA_DIR, "actividades_y_servicios_adicionales.txt"),
    os.path.join(VECTORSTORE_BASE_DIR, "actividades_adicionales_index")
)

# Opcional: Exportar las cadenas QA en un diccionario para fácil acceso desde agente.py
# Si tu agente.py ya importa estas variables directamente, puedes omitir esta parte.
# Si prefieres un diccionario para iterar, mantenlo.
qa_chains = {
    "ubicacion_contacto": qa_ubicacion_contacto,
    "accesibilidad": qa_accesibilidad,
    "domos_info": qa_domos_info,
    "concepto_glamping": qa_concepto,
    "politicas_glamping": qa_politicas,
    "servicios_incluidos": qa_servicios_incluidos,
    "actividades_adicionales": qa_actividades_adicionales,
}
# rag_engine.py

import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
#from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

# Cargar variables de entorno
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
assert OPENAI_API_KEY, "Falta la variable OPENAI_API_KEY en las variables de entorno."

# Inicializar LLM (debe ser el mismo modelo que el LLM principal si quieres consistencia)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Embeddings (HuggingFaceEmbeddings para FAISS local)
# embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

embedding_model = OpenAIEmbeddings()


# Utilidad para cargar documentos, generar vectorstore y cadena QA
def create_qa_chain(file_path: str, index_dir: str) -> RetrievalQA | None: # Añadido Union[RetrievalQA, None] para claridad
    # Cargar y dividir documentos
    try:
        loader = TextLoader(file_path, encoding="utf-8")
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
        docs = text_splitter.split_documents(documents)
    except FileNotFoundError:
        print(f"Advertencia: Archivo '{file_path}' no encontrado. No se creará la cadena QA.")
        return None
    except Exception as e:
        print(f"Error al cargar o procesar el archivo '{file_path}': {e}. No se creará la cadena QA.")
        return None

    # Crear el directorio del índice si no existe
    if not os.path.exists(index_dir):
        os.makedirs(index_dir)

    # Vector store y guardado/carga local
    try:
        if os.path.exists(index_dir) and len(os.listdir(index_dir)) > 0: # Verifica si el índice ya existe
            vectorstore = FAISS.load_local(index_dir, embedding_model, allow_dangerous_deserialization=True) # Cargar índice existente
            print(f"Índice FAISS cargado localmente desde: {index_dir}")
        else:
            vectorstore = FAISS.from_documents(docs, embedding_model)
            vectorstore.save_local(index_dir)
            print(f"Índice FAISS creado y guardado localmente en: {index_dir}")
    except Exception as e:
        print(f"Error al crear/cargar el vectorstore FAISS para {file_path}: {e}")
        return None

    # Crear y retornar la cadena QA
    retriever = vectorstore.as_retriever()
    return RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)

# --- Creación de cadenas QA para cada documento optimizado ---

# Directorio base para los archivos de datos
DATA_DIR = "data"
# Directorio base para los índices FAISS
VECTORSTORE_BASE_DIR = "vectorstore"

# Diccionario para almacenar las cadenas QA
qa_chains = {}

# Lista de archivos y sus nombres de cadena
files_to_process = {
    "ubicacion_contacto": "ubicacion_contacto.txt",
    "accesibilidad": "accesibilidad_movilidad_reducida.txt",
    "domos_info": "domos_info.txt",
    "concepto_glamping": "concepto_brillodeluna.txt",
    "politicas_glamping": "politicas_glamping.txt",
    "servicios_incluidos": "servicios_incluidos_domos.txt",
    "actividades_adicionales": "actividades_y_servicios_adicionales.txt",
    "requisitos_reserva": "requisitos_reserva.txt",
}

for chain_name, file_name in files_to_process.items():
    file_path = os.path.join(DATA_DIR, file_name)
    index_dir = os.path.join(VECTORSTORE_BASE_DIR, f"{chain_name}_index")
    
    chain = create_qa_chain(file_path, index_dir)
    if chain:
        qa_chains[chain_name] = chain
        print(f"Cadena QA '{chain_name}' creada/cargada exitosamente.")
    else:
        qa_chains[chain_name] = None # Asegúrate de que la entrada exista, incluso si es None
        print(f"No se pudo crear/cargar la cadena QA para '{chain_name}'.")
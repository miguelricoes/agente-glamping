# rag_engine.py

import os
from dotenv import load_dotenv
# Imports compatibles para eliminar deprecation warnings
try:
    from langchain_community.document_loaders import TextLoader
except ImportError:
    from langchain.document_loaders import TextLoader

try:
    from langchain_community.vectorstores import FAISS
except ImportError:
    from langchain.vectorstores import FAISS

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA

try:
    from langchain_community.llms import OpenAI
except ImportError:
    from langchain.llms import OpenAI

try:
    from langchain_community.embeddings import OpenAIEmbeddings
except ImportError:
    from langchain.embeddings import OpenAIEmbeddings

# Cargar variables de entorno
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validación robusta pero simple
if not OPENAI_API_KEY:
    raise EnvironmentError("ERROR: OPENAI_API_KEY requerida para RAG engine")

# Asegurar API key en environment para langchain 0.1.0
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Inicializar LLM con imports actualizados para evitar deprecation warnings
try:
    # Usar langchain_openai para evitar deprecation warnings
    from langchain_openai import OpenAI as OpenAI_New
    llm = OpenAI_New(temperature=0)
    print("OK LLM RAG inicializado (langchain_openai)")
except ImportError:
    # Fallback al import original si langchain_openai no está disponible
    llm = OpenAI(temperature=0)
    print("OK LLM RAG inicializado (fallback)")
except Exception as e:
    print(f"ERROR Error LLM RAG: {e}")
    raise

# Inicializar embeddings con imports actualizados para evitar deprecation warnings
try:
    # Usar langchain_openai para evitar deprecation warnings
    from langchain_openai import OpenAIEmbeddings as OpenAIEmbeddings_New
    embedding_model = OpenAIEmbeddings_New()
    print("OK Embeddings RAG inicializados (langchain_openai)")
except ImportError:
    # Fallback al import original si langchain_openai no está disponible
    embedding_model = OpenAIEmbeddings()
    print("OK Embeddings RAG inicializados (fallback)")
except Exception as e:
    print(f"ERROR Error embeddings RAG: {e}")
    raise


# Utilidad para cargar documentos, generar vectorstore y cadena QA
def create_qa_chain(file_path: str, index_dir: str):
    # Validar parámetros
    if not file_path or not index_dir:
        print(f"ERROR: Parámetros inválidos: file_path='{file_path}', index_dir='{index_dir}'")
        return None
    
    # Cargar y dividir documentos
    try:
        if not os.path.exists(file_path):
            print(f"WARNING:  Archivo no encontrado: '{file_path}' - Saltando")
            return None
            
        loader = TextLoader(file_path, encoding="utf-8")
        documents = loader.load()
        
        # Validar contenido del documento
        if not documents or len(documents) == 0:
            print(f"WARNING:  Archivo vacío: '{file_path}' - Saltando")
            return None
            
        # Verificar que el documento tenga contenido útil
        total_content = "".join([doc.page_content for doc in documents])
        if len(total_content.strip()) < 50:
            print(f"WARNING:  Contenido insuficiente en '{file_path}' - Saltando")
            return None
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
        docs = text_splitter.split_documents(documents)
        
        if not docs or len(docs) == 0:
            print(f"WARNING:  No se generaron chunks para '{file_path}' - Saltando")
            return None
            
        print(f"OK: Documento procesado: '{file_path}' -> {len(docs)} chunks")
        
    except FileNotFoundError:
        print(f"WARNING:  Archivo no encontrado: '{file_path}' - Saltando")
        return None
    except Exception as e:
        print(f"ERROR: Error procesando '{file_path}': {e} - Saltando")
        return None

    # Crear directorio del índice con manejo de errores
    try:
        if not os.path.exists(index_dir):
            os.makedirs(index_dir)
    except Exception as e:
        print(f"ERROR: Error creando directorio '{index_dir}': {e}")
        return None

    # Vector store con manejo robusto
    try:
        # Intentar cargar índice existente
        if os.path.exists(index_dir) and len(os.listdir(index_dir)) > 0:
            try:
                vectorstore = FAISS.load_local(index_dir, embedding_model, allow_dangerous_deserialization=True)
                print(f"OK: Índice FAISS cargado: {index_dir}")
            except Exception as load_error:
                print(f"WARNING:  Error cargando índice existente, recreando: {load_error}")
                # Si falla cargar, crear nuevo
                vectorstore = FAISS.from_documents(docs, embedding_model)
                vectorstore.save_local(index_dir)
                print(f"OK: Índice FAISS recreado: {index_dir}")
        else:
            # Crear nuevo índice
            vectorstore = FAISS.from_documents(docs, embedding_model)
            vectorstore.save_local(index_dir)
            print(f"OK: Índice FAISS creado: {index_dir}")
            
    except Exception as e:
        print(f"ERROR: Error con vectorstore FAISS para '{file_path}': {e}")
        return None

    # Crear cadena QA con manejo de errores
    try:
        retriever = vectorstore.as_retriever()
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm, 
            chain_type="stuff", 
            retriever=retriever,
            return_source_documents=False  # Simplificar para mejor rendimiento
        )
        return qa_chain
    except Exception as e:
        print(f"ERROR: Error creando cadena QA para '{file_path}': {e}")
        return None

# --- Creación de cadenas QA para cada documento optimizado ---

# Directorio base para los archivos de datos
DATA_DIR = "data"
# Directorio base para los índices FAISS
VECTORSTORE_BASE_DIR = "vectorstore"

# Diccionario para almacenar las cadenas QA
qa_chains = {}

# Lista de archivos y sus nombres de cadena
files_to_process = {
    # Archivos originales
    "ubicacion_contacto": "ubicacion_contacto.txt",
    "accesibilidad": "accesibilidad_movilidad_reducida.txt",
    "domos_info": "domos_info.txt",
    "concepto_glamping": "concepto_brillodeluna.txt",
    "politicas_glamping": "politicas_glamping.txt",
    "servicios_incluidos": "servicios_incluidos_domos.txt",
    "actividades_adicionales": "actividades_y_servicios_adicionales.txt",
    "requisitos_reserva": "requisitos_reserva.txt",
    
    # Nuevos archivos agregados
    "domos_precios": "Domos_Precios.txt",
    "que_es_brillo_luna": "Que_es_BrilloDeLuna.txt",
    "servicios_externos": "Servicios.txt",
    "sugerencias_movilidad_reducida": "SugerenciasPersonasMovilidadReducida.txt",
    "politicas_privacidad": "PoliticasDePrivaciadad.txt",
    "politicas_cancelacion": "Políticas de Cancelación.txt",
    "links_imagenes": "Links.txt",
}

# Procesamiento robusto de archivos de datos
print("Inicializando sistema RAG...")

# Verificar directorios base
try:
    if not os.path.exists(DATA_DIR):
        print(f"WARNING: Directorio de datos no existe: {DATA_DIR}")
    if not os.path.exists(VECTORSTORE_BASE_DIR):
        os.makedirs(VECTORSTORE_BASE_DIR)
        print(f"OK: Directorio vectorstore creado: {VECTORSTORE_BASE_DIR}")
except Exception as e:
    print(f"ERROR: Error con directorios: {e}")

# Estadísticas de procesamiento
total_files = len(files_to_process)
successful_chains = 0
failed_chains = 0

print(f"Procesando {total_files} archivos de datos...")

for chain_name, file_name in files_to_process.items():
    file_path = os.path.join(DATA_DIR, file_name)
    index_dir = os.path.join(VECTORSTORE_BASE_DIR, f"{chain_name}_index")
    
    try:
        chain = create_qa_chain(file_path, index_dir)
        if chain:
            qa_chains[chain_name] = chain
            successful_chains += 1
            print(f"OK: Cadena QA '{chain_name}' lista")
        else:
            qa_chains[chain_name] = None
            failed_chains += 1
            print(f"WARNING: Cadena QA '{chain_name}' no disponible")
    except Exception as e:
        qa_chains[chain_name] = None
        failed_chains += 1
        print(f"ERROR: Error procesando '{chain_name}': {e}")

# Resumen final
print(f"\nResumen RAG:")
print(f"OK: Cadenas exitosas: {successful_chains}/{total_files}")
print(f"WARNING: Cadenas fallidas: {failed_chains}/{total_files}")

if successful_chains == 0:
    print("ADVERTENCIA CRITICA: Ninguna cadena QA fue inicializada. El sistema RAG no funcionará.")
elif failed_chains > 0:
    print(f"WARNING: {failed_chains} cadenas no disponibles. Funcionalidad RAG limitada.")
else:
    print("OK: Sistema RAG completamente inicializado.")

# Agregar función de fallback para cadenas faltantes
def get_qa_response(chain_name: str, question: str) -> str:
    """Función robusta para obtener respuestas de las cadenas QA"""
    try:
        if chain_name not in qa_chains:
            return "Lo siento, esa información no está disponible en este momento."
        
        chain = qa_chains[chain_name]
        if chain is None:
            return "Lo siento, esa información no está disponible en este momento."
        
        response = chain.run(question)
        return response if response else "No encontré información específica sobre esa consulta."
        
    except Exception as e:
        print(f"ERROR: Error en cadena QA '{chain_name}': {e}")
        return "Disculpa, tuve un problema procesando esa consulta. ¿Podrías reformularla?"

# Exportar función para uso en agente principal
__all__ = ['qa_chains', 'get_qa_response']
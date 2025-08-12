#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test para verificar que todas las dependencias se importan correctamente
con las nuevas versiones actualizadas
"""

def test_imports():
    """Probar todos los imports críticos"""
    print("=== Test de Dependencias Actualizadas ===\n")
    
    try:
        # Test Flask
        import flask
        print(f"✓ Flask {flask.__version__}")
    except ImportError as e:
        print(f"✗ Flask: {e}")
    
    try:
        # Test LangChain Core
        import langchain
        print(f"✓ LangChain {langchain.__version__}")
    except ImportError as e:
        print(f"✗ LangChain: {e}")
    
    try:
        # Test LangChain OpenAI
        import langchain_openai
        print(f"✓ LangChain-OpenAI {langchain_openai.__version__}")
    except ImportError as e:
        print(f"✗ LangChain-OpenAI: {e}")
    
    try:
        # Test OpenAI
        import openai
        print(f"✓ OpenAI {openai.__version__}")
    except ImportError as e:
        print(f"✗ OpenAI: {e}")
    
    try:
        # Test Tiktoken
        import tiktoken
        print(f"✓ Tiktoken {tiktoken.__version__}")
    except ImportError as e:
        print(f"✗ Tiktoken: {e}")
    
    try:
        # Test FAISS
        import faiss
        print(f"✓ FAISS {faiss.__version__}")
    except ImportError as e:
        print(f"✗ FAISS: {e}")
    
    try:
        # Test específicos de LangChain components
        from langchain.agents import initialize_agent, AgentType
        from langchain.memory import ConversationBufferMemory
        from langchain.tools import BaseTool, Tool
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain.chains import RetrievalQA
        print("✓ LangChain components básicos")
    except ImportError as e:
        print(f"✗ LangChain components: {e}")
    
    try:
        # Test LangChain Community
        from langchain_community.document_loaders import TextLoader
        from langchain_community.vectorstores import FAISS as FAISSCommunity
        from langchain_community.llms import OpenAI as OpenAICommunity
        from langchain_community.embeddings import OpenAIEmbeddings as EmbeddingsCommunity
        print("✓ LangChain Community components")
    except ImportError as e:
        print(f"✗ LangChain Community: {e}")
    
    try:
        # Test LangChain OpenAI específicos
        from langchain_openai import OpenAI as OpenAINew
        from langchain_openai import OpenAIEmbeddings as EmbeddingsNew
        print("✓ LangChain OpenAI components")
    except ImportError as e:
        print(f"✗ LangChain OpenAI specific: {e}")
    
    print("\n=== Test Completado ===")

if __name__ == "__main__":
    test_imports()
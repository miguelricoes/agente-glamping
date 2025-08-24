#!/usr/bin/env python3
"""
Script de verificación de dependencias críticas para Docker build
Valida que todas las dependencias esenciales estén correctamente instaladas
"""

import sys

def verify_critical_dependencies():
    """Verificar que las dependencias críticas estén instaladas"""

    critical_imports = [
        ('flask', 'Flask framework'),
        ('openai', 'OpenAI API'),
        ('langchain', 'LangChain framework'),
        ('psycopg2', 'PostgreSQL adapter'),
        ('twilio.rest', 'Twilio API'),
        ('gunicorn', 'Gunicorn WSGI server'),
        ('dotenv', 'Environment variables')
    ]

    # Usar caracteres ASCII para máxima compatibilidad en Docker
    print("Verificando dependencias criticas...")
    print("=" * 60)

    failed_imports = []

    for module, description in critical_imports:
        try:
            __import__(module)
            print(f'[OK] {description}')
        except ImportError as e:
            failed_imports.append((module, description, str(e)))
            print(f'[FAILED] {description}: {e}')

    print("=" * 60)

    if failed_imports:
        print(f'\nCRITICAL ERROR: {len(failed_imports)} dependencies failed!')
        print('Failed dependencies:')
        for module, desc, error in failed_imports:
            print(f'  - {desc}: {error}')
        print('\nBuild cannot continue with missing critical dependencies.')
        print('Please check the installation process in previous Docker stages.')
        return False
    else:
        print(f'\nSUCCESS: All {len(critical_imports)} critical dependencies verified!')
        print('Docker build can proceed - system ready for application startup.')
        return True

def main():
    """Punto de entrada principal"""
    try:
        success = verify_critical_dependencies()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f'\nUNEXPECTED ERROR during dependency verification: {e}')
        print('This may indicate a serious problem with the Python environment.')
        sys.exit(2)

if __name__ == '__main__':
    main()
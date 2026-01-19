import sys
import os

# Configura caminhos
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(current_dir, 'dinhosilwa-nfedistribuicaodfe-service')

sys.path.insert(0, current_dir)
sys.path.insert(0, project_dir)

print("Tentando importar módulos...")

try:
    # Tenta importar usando __import__ para evitar problemas de sintaxe
    config = __import__('config')
    print("✅ config importado")
    
    download = __import__('download')
    print("✅ download importado")
    
    main = __import__('main')
    print("✅ main importado")
    
    print("\n✅ Todos os imports funcionaram!")
    
except ImportError as e:
    print(f"❌ Erro: {e}")
    
    # Lista arquivos na pasta do projeto
    print("\nArquivos na pasta do projeto:")
    for file in os.listdir(project_dir):
        print(f"  - {file}")
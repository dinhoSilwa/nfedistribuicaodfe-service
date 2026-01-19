# run_tests.py
"""
Script para executar todos os testes.
"""
import subprocess
import sys

def run_tests():
    """Executa a suíte de testes completa."""
    print("🚀 Executando testes...")
    
    # Comando para executar pytest
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html:coverage_report",
        "tests/"
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"❌ Erro ao executar testes: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
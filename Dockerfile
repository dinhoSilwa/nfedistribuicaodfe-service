# Use uma imagem base Python oficial
FROM python:3.11-slim

# Instalar OpenSSL (necessário para conversão de certificados)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivos de dependências
COPY requirements.txt .
COPY pyproject.toml .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY sistema_de_download_nf_ce/ ./sistema_de_download_nf_ce/
COPY README.md .

# Criar diretórios necessários
RUN mkdir -p /app/certificate /app/downloads /app/perm

# Definir variáveis de ambiente (serão sobrescritas pelo .env)
ENV PYTHONUNBUFFERED=1

# Comando padrão
CMD ["python", "-m", "sistema_de_download_nf_ce.main"]
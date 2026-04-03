# Escolhendo a versão Python compatível
FROM python:3.11-slim

# Diretório de trabalho
WORKDIR /app

# Copia arquivo de dependências
COPY requirements.txt .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código
COPY . .

# Expondo a porta do serviço
EXPOSE 8005

# Comando para rodar o serviço
CMD ["gunicorn", "--bind", "0.0.0.0:8005", "app:app"]


# Use uma imagem base do Python
FROM python:3.10

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copie o arquivo de requisitos para o diretório de trabalho
COPY requirements.txt .

# Instale as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copie o restante do código do projeto para o diretório de trabalho
COPY . .

# Exponha a porta que o Flask usará
EXPOSE 5000

# Comando para rodar o servidor Flask
CMD ["python", "app.py"]

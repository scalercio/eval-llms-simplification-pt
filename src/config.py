import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

def get_openai_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY não foi encontrada no arquivo .env")
    return api_key

def get_maritaca_api_key():
    api_key = os.getenv("MARITACA_API_KEY")
    if not api_key:
        raise ValueError("MARITACA_API_KEY não foi encontrada no arquivo .env")
    return api_key
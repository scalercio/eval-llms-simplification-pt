import requests
import json
import argparse
from src.config import get_openai_api_key

def request_openai_api(endpoint, complex_phrase):
    # Criação do prompt com a frase complexa recebida como argumento
    prompt = (
        f"Substitua a frase complexa por uma frase simples. "
        f"Mantenha o mesmo significado, mas torne-a mais simples.\n"
        f"Frase complexa: {complex_phrase}\nFrase Simples: "
    )

    # JSON payload com o prompt criado dinamicamente
    payload = {
        "model": "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "simplification_response",
                "strict": "true",
                "schema": {
                    "type": "object",
                    "properties": {
                        "simplified_phrase": {
                            "type": "string"
                        }
                    },
                    "required": ["simplified_phrase"]
                }
            }
        },
        "temperature": 0.7,
        "max_tokens": 50,
        "stream": False
    }

    # Cabeçalhos da requisição
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_openai_api_key()}"
    }

    # Fazendo a requisição POST para o endpoint
    response = requests.post(endpoint, headers=headers, data=json.dumps(payload))

    # Verificando se a requisição foi bem-sucedida
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Request failed with status code {response.status_code}"}

if __name__ == "__main__":
    # Utilizando argparse para capturar o endpoint e a frase complexa da linha de comando
    parser = argparse.ArgumentParser(description='Simplifica uma frase complexa utilizando o OpenAI API.')
    parser.add_argument('endpoint', type=str, help='O URL do endpoint OpenAI')
    parser.add_argument('complex_phrase', type=str, help='A frase complexa que será simplificada')

    args = parser.parse_args()

    # Chamando a função com o endpoint e a frase complexa passados pela linha de comando
    result = request_openai_api(args.endpoint, args.complex_phrase)
    print(result)

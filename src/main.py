# -- fix path --
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
# -- end fix path --
import requests
import json
import argparse
import os
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
        #"Authorization": f"Bearer {get_openai_api_key()}"
    }

    # Fazendo a requisição POST para o endpoint
    response = requests.post(endpoint, headers=headers, data=json.dumps(payload))

    # Verificando se a requisição foi bem-sucedida
    if response.status_code == 200:
        data = response.json()
        #print(type(data)) #<class 'dict'>
        content = data['choices'][0]['message']['content']
        json_object = json.loads(content)
        print(json_object['simplified_phrase'])
        return json_object.get("simplified_phrase", "")
    else:
        return {"error": f"Request failed with status code {response.status_code}"}

def process_file_and_simplify(endpoint, input_file_path):
    # Verifica se o arquivo existe
    if not os.path.isfile(input_file_path):
        raise FileNotFoundError(f"O arquivo {input_file_path} não foi encontrado.")

    # Lê as sentenças complexas do arquivo
    with open(input_file_path, 'r', encoding='utf-8') as f:
        sentences = f.readlines()

    # Criando diretório para saída, se não existir
    output_dir = "simplified_outputs"
    os.makedirs(output_dir, exist_ok=True)

    # Nome do arquivo de saída
    output_file_path = os.path.join(output_dir, 'simplified_output.txt')

    # Simplificando cada sentença e escrevendo no arquivo de saída
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                print(sentence)
                simplified_sentence = request_openai_api(endpoint, sentence)
                output_file.write(simplified_sentence + '\n')
                print(f"Simplificado: {simplified_sentence}")

    print(f"Todas as sentenças foram simplificadas e salvas em {output_file_path}")

if __name__ == "__main__":
    # Utilizando argparse para capturar o endpoint e o caminho do arquivo
    parser = argparse.ArgumentParser(description='Simplifica frases complexas de um arquivo usando o OpenAI API.')
    parser.add_argument('endpoint', type=str, help='O URL do endpoint OpenAI')
    parser.add_argument('input_file', type=str, help='O caminho para o arquivo contendo frases complexas')

    args = parser.parse_args()

    # Processa o arquivo de entrada e gera o arquivo de saída com as sentenças simplificadas
    process_file_and_simplify(args.endpoint, args.input_file)

# -- fix path --
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
# -- end fix path --
import requests
import json
import argparse
import os
from src.config import get_openai_api_key, get_maritaca_api_key
from src.utils import calculate_metrics
import re
import openai

# Função para remover caracteres de substituição Unicode inválidos
def remove_invalid_unicode(text):
    return re.sub(r'[\ud800-\udfff]', '', text)

tipo_ex = ["sintática", "ordem", "redundante_lexical", "anáfora"]
prompts = {'feng': f"Substitua a frase complexa por uma frase simples. \
            Mantenha o mesmo significado, mas torne-a mais simples.",}
seeds = [7, 77, 777]
exemplars = {
        "sintática": [
            'Conforme moradores do bairro, a expressão identificaria um grupo de pichadores.',
            'Os moradores do bairro dizem que a frase identificaria um grupo de pichadores.'
            
        ],
        "ordem": [
            'Entre os motivos da liderança gaúcha, estão a tradição no cultivo da soja, que hoje representa a maior parte da matéria-prima do biodiesel, e a predominância da agricultura familiar, condição para concessão do selo social.',
            'A tradição na cultura da soja, que hoje representa a maior parte da matéria-prima do biodiesel, e o predomínio da agricultura familiar, condição para conceder o selo social, estão entre os motivos da posição gaúcha de líder.'
        ],
        "redundante_lexical": [
            'Numa entrevista coletiva conduzida ontem à noite, os gerentes da Nasa deram o veredicto:',
            'Numa entrevista coletiva ontem à noite, os gerentes da Nasa decidiram:'
        ],
        "anáfora": [
            'E com eles amarrados a coleiras, do alto de uma duna a cerca de 50 metros do mar, tomava chimarrão às 19h de ontem.',
            'Pandolfo tomava chimarrão às 19h de ontem, no alto de um monte de areia, com os poodles amarrados a coleiras.'
            
        ]
}
open_ai_model = "gpt-4o-mini"

def request_openai_api(endpoint, original, prompt, max_tokens, temp, topp, engine, seed):
    # Criação do prompt com a frase complexa recebida como argumento
    #prompt = (
    #    f"Substitua a frase complexa por uma frase simples. "
    #    f"Mantenha o mesmo significado, mas torne-a mais simples.\n"
    #    f"Frase complexa: {complex_phrase}\nFrase Simples: "
    #)

    # JSON payload com o prompt criado dinamicamente
    payload = {
        "model": engine,
        "messages": [
            {
                "role": "system",
                "content": "Você é um assistente simplificador de textos."
            },
            {
                "role": "user",
                "content": f"{prompt} \n\nFrase complexa: {original} \n\n Frase Simples: \n\n",
            }
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "simplification_response",
                "strict": True  ,
                "schema": {
                    "type": "object",
                    "properties": {
                        "simplified_phrase": {
                            "type": "string"
                        }
                    },
                    "additionalProperties": False,
                    "required": ["simplified_phrase"]
                }
            }
        },
        "temperature": temp,
        "max_tokens": max_tokens,
        "top_p": topp,
        "seed": seed,
        "stream": False
    }

    # Cabeçalhos da requisição
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_openai_api_key()}"
    }

    # Fazendo a requisição POST para o endpoint
    response = requests.post(endpoint + 'chat/completions', headers=headers, data=json.dumps(payload))

    # Verificando se a requisição foi bem-sucedida
    if response.status_code == 200:
        data = response.json()
        #print(type(data)) #<class 'dict'>
        content = data['choices'][0]['message']['content'].strip()
        #print(content) #<class 'str'>
        if content[-1] not in '}':
            content = content[:-1]+'}'
        try:
            json_object = json.loads(content)
        except json.JSONDecodeError as e:
            print("Invalid JSON syntax:", e)
            print(content)
            content = '{ "simplified_phrase": "hallucination"}'
            json_object = json.loads(content)         
        
        #print(json_object['simplified_phrase'])
        return remove_invalid_unicode(json_object.get("simplified_phrase", ""))
    else:
        return {"error": f"Request failed with status code {response.status_code}"}

def request_maritaca_api(endpoint, original, prompt, max_tokens, temp, topp, engine, seed):
    client = openai.OpenAI(
        api_key=get_maritaca_api_key(),
        base_url=endpoint,
    )

    # JSON payload com o prompt criado dinamicamente
    payload = {
        "model": engine,
        "messages": [
            {
                "role": "system",
                "content": "Você é um assistente simplificador de textos."
            },
            {
                "role": "user",
                "content": f"{prompt} \n\nFrase complexa: {original} \n\n Frase Simples: \n\n",
            }
        ],
        #"response_format": {
        #    "type": "json_schema",
        #    "json_schema": {
        #        "name": "simplification_response",
        #        "strict": True  ,
        #        "schema": {
        #            "type": "object",
        #            "properties": {
        #                "simplified_phrase": {
        #                    "type": "string"
        #                }
        #            },
        #            "additionalProperties": False,
        #            "required": ["simplified_phrase"]
        #        }
        #    }
        #},
        "temperature": temp,
        "max_tokens": max_tokens,
        "top_p": topp,
        "seed": seed,
        "stream": False
    }

    response = client.chat.completions.create(**payload)

    #print(response.choices[0].message.content)

    content = response.choices[0].message.content.strip()        
        
    return remove_invalid_unicode(content)

def generate_examples_one_by_one(endpoint, originals, prompt, ofile, max_len, temp, topp, engine, seed):
    id = 1
    with open(ofile, 'a', encoding='utf-8') as f:
        for original in originals[:-1]:
            if 'sabia' in engine:
                simpler = request_maritaca_api(endpoint, original, prompt, max_len, temp, topp, engine, seed)
            else:
                simpler = request_openai_api(endpoint, original, prompt, max_len, temp, topp, engine, seed)
            #print(simpler)
            instance = {"id": id, "original":original, "simplified": simpler}
            json.dump(instance, f, ensure_ascii=False, indent=4)
            f.write(',\n')
            id += 1
            
        original = originals[-1]
        if 'sabia' in engine:
            simpler = request_maritaca_api(endpoint, original, prompt, max_len, temp, topp, engine, seed)
        else:
            simpler = request_openai_api(endpoint, original, prompt, max_len, temp, topp, engine, seed)
            #print(simpler)
        instance = {"id": id, "original":original, "simplified": simpler}
        json.dump(instance, f, ensure_ascii=False, indent=4)
            #ßbreak
    return id

def get_prompt_one_shot(prompt, pair):
    pares = ""
    pares += "\n\nComplexa: " + pair[0] + "\nSimples: " + pair[1] + "\n\n"
    return prompt + pares


def process_file_and_simplify(endpoint, input_file_path, model_name, dataset):
    # Verifica se o arquivo existe
    if not os.path.isfile(input_file_path):
        raise FileNotFoundError(f"O arquivo {input_file_path} não foi encontrado.")

    # Lê as sentenças complexas do arquivo
    with open(input_file_path, 'r', encoding='utf-8') as f:
        sentences = f.readlines()

    # Criando diretório para saída, se não existir
    output_dir = "simplified_outputs" + "/" + dataset + "/" + model_name.split("/")[-1]
    os.makedirs(output_dir, exist_ok=True)

    for seed in seeds:
        for tipo in tipo_ex:
            # Nome do arquivo de saída
            ofile = f"simplified_{tipo}_{seed}.json"
            output_file_path = os.path.join(output_dir, ofile)
            if not os.path.exists(output_file_path):
            
                prompt = get_prompt_one_shot(prompts["feng"], exemplars[tipo])
                print(prompt)

                with open(output_file_path, 'w', encoding='utf-8') as f:
                        f.write('[\n')

                #print(originals)
                total = generate_examples_one_by_one(endpoint, sentences, prompt, output_file_path, 1024, 1, 0.9, model_name, seed)

                print(total)

                with open(output_file_path, 'a', encoding='utf-8') as f:
                    f.write(']')
    
    # Simplificando cada sentença e escrevendo no arquivo de saída
    #with open(output_file_path, 'w', encoding='utf-8') as output_file:
    #    for sentence in sentences:
    #        sentence = sentence.strip()
    #        if sentence:
    #            print(sentence)
    #            simplified_sentence = request_openai_api(endpoint, sentence)
    #            output_file.write(simplified_sentence + '\n')
    #            print(f"Simplificado: {simplified_sentence}")

    print(f"Todas as sentenças foram simplificadas e salvas em {output_file_path}")
    return sentences

def get_model_name_from_endpoint(endpoint):
    try:
        # Fazendo a requisição ao endpoint
        response = requests.get(endpoint)

        # Verifica se a requisição foi bem-sucedida
        if response.status_code == 200:
            # Converte a resposta para JSON
            data = response.json()
            
            # Acessa a chave "data" e extrai o "id" do primeiro item
            model_id = data["data"][0]["id"]
            return model_id
        else:
            return f"Erro: A requisição falhou com o código de status {response.status_code}."

    except Exception as e:
        return f"Ocorreu um erro: {str(e)}"

def main(endpoint, input_file_path, reference_path, dataset):
    
    if 'openai' in endpoint:
        model_name = open_ai_model
    elif 'maritaca' in endpoint:
        model_name = 'sabia-2-small'
    else:
        model_name = get_model_name_from_endpoint(endpoint + 'models')
    print(model_name.split("/")[-1])
    sentences = process_file_and_simplify(endpoint, input_file_path, model_name, dataset)
    results = calculate_metrics(model_name, reference_path, tipo_ex, seeds, sentences, dataset)
    print(results)    


if __name__ == "__main__":
    # Utilizando argparse para capturar o endpoint e o caminho do arquivo
    parser = argparse.ArgumentParser(description='Simplifica frases complexas de um arquivo usando uma API.')
    parser.add_argument('endpoint', type=str, help='O URL do endpoint da API')
    parser.add_argument('input_file', type=str, help='O caminho para o arquivo contendo frases complexas')
    parser.add_argument('ref_file', type=str, help='O caminho para o arquivo contendo frases referências')
    parser.add_argument('dataset', type=str, help='Dataset Usado')

    args = parser.parse_args()

    # Processa o arquivo de entrada e gera o arquivo de saída com as sentenças simplificadas
    main(args.endpoint, args.input_file, args.ref_file, args.dataset)

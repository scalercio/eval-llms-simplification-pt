# -- fix path --
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
# -- end fix path --
import numpy as np
import json
import random
from src.utils import write_lines

import warnings
warnings.filterwarnings("ignore")

def generate_pairs(dataset, n_samples, types, model):
    with open(f'data/{dataset}/test.complex', 'r') as f1:
        src_seq = f1.readlines()
    if 'porsimples' in dataset:
        assert len(src_seq) ==606
    elif 'museu' in dataset:
        assert len(src_seq) ==476
    elif 'public' in dataset:
        assert len(src_seq) ==2130
        
    
    all_sentences = []
    for tipo_one_shot in types:
        for i in ['7', '77', '777']:            
            simplified_file = f'simplified_outputs/{dataset}/{model}/simplified_{tipo_one_shot}_{i}.json'
            with open(simplified_file, 'r') as f3:
                data = json.load(f3)
            
            print(simplified_file)

            simplified_sentences=[]
            for sentence_dict in data:
                #print(sentence_dict['simplified'])
                simplified_sentences.append(sentence_dict['simplified'])

            assert len(src_seq) == len(simplified_sentences)
            
            all_sentences.append(simplified_sentences)
    
    assert n_samples <= len(all_sentences[0])
    print(len(all_sentences[0]))
    human_selection = []
    complex_input = []
    for i in np.random.choice(len(all_sentences[0]), n_samples, replace= False):
        simplification = all_sentences[random.choice(range(len(all_sentences)))][i]
        complex_input.append(src_seq[i].strip())
        human_selection.append(simplification.strip())
        
    write_lines(complex_input, f'data/{dataset}/{model}_original_samples.txt')
    write_lines(human_selection, f'data/{dataset}/{model}_simplification_samples.txt')

    

    return


if __name__ == '__main__':
    
    types = ['sintática', 'anáfora', 'ordem', 'redundante_lexical']
    datasets = ['porsimplessent', 'museu', 'public_simple_language']
    models = ['gpt-4o-mini', 'sabia-2-small', 'Qwen2.5-7B-Instruct-Q4_K_M.gguf']
    n_samples = 20
    for dataset in datasets:
        for model in models:
            generate_pairs(dataset, n_samples, types, model)
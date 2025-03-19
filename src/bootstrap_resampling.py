# -- fix path --
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
# -- end fix path --
import numpy as np
import torch
import json
torch.set_float32_matmul_precision('medium')
from easse.sari import corpus_sari
from src.utils import remove_indexes, create_unique_vector

import warnings
warnings.filterwarnings("ignore")

def generate_sari_confidence_intervals(original_sentences, simplified_sentences, reference_sentences, baseline_seq, iterations=10):
    """
    Generate multiple SARI score confidence intervals for different test set using bootstrap resampling.
    
    Parameters:
    - original_sentences: List of original sentences.
    - simplified_sentences: List of simplified sentences.
    - reference_sentences: List of reference sentences.    
    - baseline_seq: List of baseline simplification sentences.
    - iterations: Number of bootstrap samples to generate per test sets.
    
    Returns:
    - The statistical significance
    """
    
    sari_scores = []
    for __ in range(iterations):
        indices = np.random.choice(len(original_sentences), len(original_sentences), replace=True)
        sampled_originals = [original_sentences[i] for i in indices]
        sampled_simplifications = [simplified_sentences[i] for i in indices]
        baseline_simplifications = [baseline_seq[i] for i in indices]

        sampled_references = [[reference_sentences[i] for i in indices]]

        score = corpus_sari(orig_sents=sampled_originals, sys_sents=sampled_simplifications, refs_sents=sampled_references)
        #print(score)
        score_baseline = corpus_sari(orig_sents=sampled_originals, sys_sents=baseline_simplifications, refs_sents=sampled_references)
        #print(score_baseline)
        if score > score_baseline:
            sari_scores.append(1)
        else:
            sari_scores.append(0)

        #sari_scores.sort()
        ## calculate the indices for the 2.5th and 97.5th %
        #lower_index = max(0, int(0.025 * len(sari_scores)))
        #upper_index = min(len(sari_scores) - 1, int(0.975 * len(sari_scores)))

        #all_intervals.append((sari_scores[lower_index], sari_scores[upper_index]))

    return sum(sari_scores)/iterations

def compare_with_gpt(dataset, **config):
    if 'asset' in dataset:
        raise ValueError("Bootstrap resampling not implemented for Asset dataset")
    
    with open(config['evaluate_kwargs']['refs_sents_paths'][0], 'r') as f1, open(config['evaluate_kwargs']['orig_sents_path'], 'r') as f3:
            ref_seq = f1.readlines()
            src_seq = f3.readlines()
        
    _ , indexes = create_unique_vector(src_seq, ref_seq)
    if 'public_simple_language' in dataset:
        print(len(indexes))
        src_seq = remove_indexes(src_seq, indexes)
        ref_seq = remove_indexes(ref_seq, indexes)
    
    types = ['sintática','anáfora', 'ordem', 'redundante_lexical']
    model_2_sentences = []
    ref_final = []
    src_final = []
    simple_final = []
    for tipo_one_shot in types:
        for i in ['7', '77', '777']:
            ref_final.extend(ref_seq)
            src_final.extend(src_seq)
            #simple_final.extend(simple_seq)
            simplified_file_1 = f'{config['simplifications_path']}simplified_{tipo_one_shot}_{i}.json'
            simplified_file_2 = f'{config['simplifications_baseline_path']}simplified_{tipo_one_shot}_{i}.json'
            
            print(simplified_file_1)
            with open(simplified_file_1) as f3:
                data_1=json.load(f3)
                
            with open(simplified_file_2) as f4:
                data_2=json.load(f4)

            for i, (sentence_dict_1, sentence_dict_2) in enumerate(zip(data_1, data_2)):
                #print(sentence_dict['simplified'])
                if i not in indexes or 'public_simple_language' not in dataset:
                    simple_final.append(sentence_dict_1['simplified'])
                    model_2_sentences.append(sentence_dict_2['simplified'])
    

    print(len(simple_final))
    print(len(ref_final))
    assert len(simple_final) == len(ref_final)
    assert len(simple_final) == len(src_final)
    assert len(simple_final) == len(model_2_sentences)
    
    confidence_intervals = generate_sari_confidence_intervals(src_final, simple_final, ref_final, model_2_sentences)
    print(f"Generated SARI score confidence intervals: {confidence_intervals}")       

if __name__ == '__main__':
    """# 1. Prepare Data"""
    print(torch.__version__)
    print(torch.version.cuda)
    # set random seed
    rand_seed = 123
    np.random.seed(rand_seed)
    torch.manual_seed(rand_seed)
    dataset = 'public_simple_language'
    model_1 = 'qwen2.5-32b-instruct'
    model_2 = 'deepseek-r1-distill-qwen-32b'
    kwargs = {
        'orig_sents_path':f'data/{dataset}/test.complex',
        'refs_sents_paths':[f'data/{dataset}/test.simple'],
    }
    config = {
        'evaluate_kwargs': kwargs,
        'simplifications_baseline_path': f'simplified_outputs/{dataset}/{model_2}/',
        'simplifications_path': f'simplified_outputs/{dataset}/{model_1}/' 
    }
    compare_with_gpt(dataset, **config)
    

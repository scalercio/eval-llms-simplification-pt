import json
from pathlib import Path
import tempfile
from easse.sari import corpus_sari
from easse.bleu import corpus_bleu
from bert_score import score


def get_temp_filepath(create=False):
    global TEMP_DIR
    temp_filepath = Path(tempfile.mkstemp()[1])
    if TEMP_DIR is not None:
        temp_filepath.unlink()
        temp_filepath = TEMP_DIR / temp_filepath.name
        temp_filepath.touch(exist_ok=False)
    if not create:
        temp_filepath.unlink()
    return temp_filepath

def write_lines(lines, filepath=None):
    if filepath is None:
        filepath = get_temp_filepath()
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with filepath.open('w', encoding='utf-8') as f:
        for line in lines:
            f.write(line + '\n')
    return filepath

def get_outputs_unchanged(simples, sources):
    assert len(simples)==len(sources)
    count = 0
    for (simple, original) in zip(simples, sources):
        if simple.lower().strip() == original.lower().strip():
            #print(simple)
            count=count+1
    return count*100/len(simples)


def create_unique_vector(source, ref):
    """
    Create a vector of tuples (source[i], ref[i]), removing repetitions.

    Args:
        source (list of str): List of source strings.
        ref (list of str): List of reference strings.
        simplification (list of str): List of simplified strings (not used directly).

    Returns:
        tuple: A vector with unique tuples and a list of eliminated indices.
    """
    if not (len(source) == len(ref)):
        raise ValueError("The lists must have the same size.")

    unique_vector = []
    eliminated_indices = []
    seen_tuples = set()

    for i, (src, reference) in enumerate(zip(source, ref)):
        current_tuple = (src, reference)
        if current_tuple not in seen_tuples:
            unique_vector.append(current_tuple)
            seen_tuples.add(current_tuple)
        else:
            eliminated_indices.append(i)

    return unique_vector, eliminated_indices

def remove_indexes(vector, indexes):
    """
    Removes elements from a vector based on a list of indices.

    Args:
        vector (list): Original vector.
        indexes (list of int): Indices of elements to be removed.

    Returns:
        list: Vector without the specified elements.
    """
    return [item for i, item in enumerate(vector) if i not in indexes]

def calculate_metrics(model_name, ref_path, tipo_ex, seeds, sentences, dataset):
    with open(ref_path, 'r', encoding='utf-8') as f:
        ref_seq = f.readlines()
    
    _ , indexes = create_unique_vector(sentences, ref_seq)
    if 'public_simple_language' in dataset:
        print(len(indexes))
        sentences = remove_indexes(sentences, indexes)
        ref_seq = remove_indexes(ref_seq, indexes)
    
    all_sentences = []
    ref_final = []
    src_final = []
    
        
    for tipo in tipo_ex:
        for seed in seeds:
            ref_final.extend(ref_seq)
            src_final.extend(sentences)
            simplified_file = f'simplified_outputs/{dataset}/{model_name.split("/")[-1]}/simplified_{tipo}_{seed}.json'
            
            print(simplified_file)
            with open(simplified_file) as f3:
                data=json.load(f3)

            for i, sentence_dict in enumerate(data):
                if i not in indexes or 'public_simple_language' not in dataset:
                    #print(sentence_dict['simplified'])
                    all_sentences.append(sentence_dict['simplified'])
    
    assert len(ref_final) == len(all_sentences)
    assert len(all_sentences) == len(src_final)
    print(len(ref_final)/12)

    results={}
    
    
    results['sari'] = corpus_sari(orig_sents=src_final,
                       sys_sents=all_sentences,
                       refs_sents=[ref_final])

    results['bleu'] = corpus_bleu(sys_sents=all_sentences,
                       refs_sents=[ref_final],
                       lowercase=True)

    P, R, F1 = score(all_sentences, ref_final, lang = 'pt', verbose = True)
    results['bert_score'] = F1.mean()
    results['outputs_unchanged'] = get_outputs_unchanged(all_sentences,src_final)
    return results 
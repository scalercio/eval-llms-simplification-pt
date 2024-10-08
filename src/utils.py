import json
from easse.sari import corpus_sari
from easse.bleu import corpus_bleu
from bert_score import score


def get_outputs_unchanged(simples, sources):
    assert len(simples)==len(sources)
    count = 0
    for (simple, original) in zip(simples, sources):
        if simple.lower().strip() == original.lower().strip():
            #print(simple)
            count=count+1
    return count*100/len(simples)


def calculate_metrics(model_name, ref_path, tipo_ex, seeds, sentences, dataset):
    with open(ref_path, 'r', encoding='utf-8') as f:
        ref_seq = f.readlines()
    
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

            for sentence_dict in data:
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
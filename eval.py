import json
import time
import metapy
import os
import sys
import pytoml


def load_ranker(ranker_id, params):
    '''
    :param ranker: ranker object from db
    :return: meta.index.ranker
    '''
    # print(type(ranker_id))
    try:
        ranker = getattr(metapy.index, ranker_id)(**params)
        # print('made ranker', ranker_id)
    except:
        print("Couldn't make '{}' ranker, using default.".format(ranker_id))
        ranker = metapy.index.OkapiBM25()
    return ranker

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python {} config.toml ranker_id".format(sys.argv[0]))
        sys.exit(1)

    _cfg = sys.argv[1]
    _ranker_id = sys.argv[2]
    _params = sys.argv[3]

    params = {}
    p_values = _params.split(',')
    for pair in p_values:
        pair = pair.split('=')
        params[pair[0]] = float(pair[1])

    idx = metapy.index.make_inverted_index(_cfg)
    ev = metapy.index.IREval(_cfg)
    ranker_id = _ranker_id

    with open(_cfg, 'r') as fin:
        cfg_d = pytoml.load(fin)

    query_cfg = cfg_d['query-runner']
    start_time = time.time()
    top_k = 10
    query_path = query_cfg.get('query-path', 'queries.txt')
    query_start = query_cfg.get('query-id-start', 0)

    query = metapy.index.Document()
    ranker = load_ranker(ranker_id, params)
    response = {'ranker_id': ranker_id}
    accu_ndcg = 0.0
    count = 0
    with open(query_path) as query_file:
        for query_num, line in enumerate(query_file):
            query.content(line.strip())
            results = ranker.score(idx, query, top_k)
            avg_p = ev.avg_p(results, query_start + query_num, top_k)
            accu_ndcg += ev.ndcg(results, query_start + query_num, top_k)
            count += 1
            # print("Query {} average precision: {}".format(query_num + 1, avg_p))
    response['map'] = round(float(ev.map()), 4)
    response['elapsed_time'] = round(time.time() - start_time, 4)
    response['ndcg'] = round(float(accu_ndcg / count), 4)
    response['dataset'] = cfg_d['dataset']

    print(json.dumps(response, indent=2))
    # print("Mean average precision: {}".format(ev.map()))
    # print("Elapsed: {} seconds".format(round(time.time() - start_time, 4)))



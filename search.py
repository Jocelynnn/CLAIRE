import json
import time
import metapy
import sys
import math


if __name__ == '__main__':
    if len(sys.argv) != 5 :
        print("Usage: python {} config.toml query ranker_id params".format(sys.argv[0]))
        sys.exit(1)

    _cfg = sys.argv[1]
    _query = sys.argv[2]
    _ranker_id = sys.argv[3]
    _params = sys.argv[4]

    params = {}
    p_values = _params.split(',')
    for pair in p_values:
        if len(pair) != 0:
            pair = pair.split('=')
            params[pair[0]] = float(pair[1])
    # print(params)
    # metapy.log_to_stderr()
    idx = metapy.index.make_inverted_index(_cfg)

    start = time.time()
    query = metapy.index.Document()
    query.content(_query)
    ranker_id = _ranker_id
    try:
        ranker = getattr(metapy.index, ranker_id)(**params)
    except:
        print("Couldn't make '{}' ranker, using default.".format(ranker_id))
        ranker = metapy.index.OkapiBM25(_params)
    response = {'query': _query, 'results': []}
    top_docs = ranker.score(idx, query, num_results=10)

    for num, (d_id, score) in enumerate(top_docs):
        content = idx.metadata(d_id).get('content')
        path = idx.metadata(d_id).get('path')
        # print(content)
        if content != None:
            f_content = "{}.{}...\n".format(num + 1,content[0:50])
        else:
            content = "EMPTY"

        if path != None:
            print(path)
        response['results'].append({
            'score': float(score),
            'content': content[0:100],
            'path_link': 'https://en.wikipedia.org/wiki/'+str(path),
            'path_title': str(path).replace('/_/g', ' ')
        })
    response['elapsed_time'] = time.time() - start
    print(json.dumps(response, indent=2))

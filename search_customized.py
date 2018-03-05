import metapy

class MyRanker(metapy.index.RankingFunction):
    """
    Create a new ranking function in Python that can be used in MeTA.
    """

    def __init__(self, some_param=1.0):
        self.c = some_param
        # You *must* call the base class constructor here!
        super(MyRanker, self).__init__()

    def score_one(self, sd):
        """
        You need to override this function to return a score for a single term.
        For fields available in the score_data sd object,
        @see https://meta-toolkit.org/doxygen/structmeta_1_1index_1_1score__data.html
        """
        lda = sd.num_docs / sd.corpus_term_count
        tfn = sd.doc_term_count * math.log2(1.0 + self.c * sd.avg_dl /
                sd.doc_size)
        if lda < 1 or tfn <= 0:
            return 0.0
        numerator = tfn * math.log2(tfn * lda) \
                        + math.log2(math.e) * (1.0 / lda - tfn) \
                        + 0.5 * math.log2(2.0 * math.pi * tfn)
        return sd.query_term_weight * numerator / (tfn + 1.0)
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
        ranker = MyRanker()
    except:
        print("Couldn't make '{}' ranker, using default.".format(ranker_id))
        ranker = metapy.index.OkapiBM25(_params)
    response = {'query': _query, 'results': []}
    top_docs = ranker.score(idx, query, num_results=10)

    for num, (d_id, score) in enumerate(top_docs):
        content = idx.metadata(d_id).get('content')
        path = idx.metadata(d_id).get('path')
        # print(content)
        f_content = "{}.{}...\n".format(num + 1,content[0:50])
        response['results'].append({
            'score': float(score),
            'content': content[0:100],
            'path': path,
        })
    response['elapsed_time'] = time.time() - start
    print(json.dumps(response, indent=2))

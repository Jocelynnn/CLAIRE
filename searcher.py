import json
import time
import metapy
import os


class Searcher:
    """
    Wraps the MeTA search engine and its rankers.
    """
    def __init__(self, cfg):
        """
        Create/load a MeTA inverted index based on the provided config file and
        set the default ranking algorithm to Okapi BM25.
        """
        self.idx = metapy.index.make_inverted_index(cfg)
        self.default_ranker = metapy.index.OkapiBM25()

    def search(self, request):
        """
        Accept a JSON request and run the provided query with the specified
        ranker.
        """
        start = time.time()
        query = metapy.index.Document()
        query.content(request['query'])
        ranker_id = request['ranker']
        try:
            ranker = getattr(metapy.index, ranker_id)()
        except:
            print("Couldn't make '{}' ranker, using default.".format(ranker_id))
            ranker = self.default_ranker
        response = {'query': request['query'], 'results': []}

        for result in ranker.score(self.idx, query):
            response['results'].append({
                'score': float(result[1]),
                'name': self.idx.doc_name(result[0]),
                'path': self.idx.doc_path(result[0])
            })
        response['elapsed_time'] = time.time() - start
        return json.dumps(response, indent=2)


if __name__ == '__main__':
    cfg = 'search-config.toml'
    metapy.log_to_stderr()
    test_idx = metapy.index.make_inverted_index(cfg)
    print('test!!!', test_idx.num_docs())
    ranker = metapy.index.OkapiBM25(k1=1.2, b=0.75, k3=500)
    query = metapy.index.Document()
    query.content(
        'what similarity laws must be obeyed when constructing aeroelastic models of heated high speed aircraft .')
    top_docs = ranker.score(test_idx, query, num_results=10)
    print('score finished!!', top_docs)

import metapy

idx = metapy.index.make_inverted_index('temp.toml')
ranker = metapy.index.OkapiBM25(k1=1.2,b=0.75,k3=500.0)
query = metapy.index.Document()
ev = metapy.index.IREval('temp.toml')

num_results = 10
with open('data/apnews-queries.txt') as query_file:
    for query_num, line in enumerate(query_file):
        query.content(line.strip())
        results = ranker.score(idx, query, num_results)
        avg_p = ev.avg_p(results, query_num, num_results)
        print("Query {} average precision: {}".format(query_num + 1, avg_p))
print(ev.map())

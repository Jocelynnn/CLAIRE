CONFIG = {
    "cranfield": {
        "name": "cranfield",
        "corpus": "line.toml",
        "index": "/data/idx/cranfield-idx",
        "query-judgements": "/data/cranfield/cranfield-qrels.txt",
        "query-path": "/data/cranfield/cranfield-queries.txt",
        "stopwords": "lemur-stopwords.txt",
        "query-id-start": 1
    },
    "apnews": {
        "name": "ap88-89",
        "corpus": "gz.toml",
        "index": "/data/idx/ap88-89-idx",
        "query-judgements": "/data/ap88-89/qrels/qrels.1-150",
        "query-path": "/data/ap88-89/queries/topics.1-150.short-keyword",
        "stopwords": "lemur-stopwords.txt",
        "query-id-start": 1
    },
    "trec": {
        "name": "trec-robust",
        "corpus": "gz.toml",
        "index": "/data/idx/trec-robust-idx",
        "query-judgements": "/data/trec-robust/trec-qrel",
        "query-path": "/data/trec-robust/trec-queries",
        "stopwords": "lemur-stopwords.txt",
        "query-id-start": 1
    },
    "app-dataset-names": {
        "cranfield": "cranfield",
        "ap88-89": "apnews",
        "trec-robust": "trec"
    }
}
from django.shortcuts import render
from django.utils import timezone
from .models import Post
from .models import RetrievalMethod, Peformance
from .config_forms import bm25Form, jmForm, dpForm, plForm, adForm
import metapy
import json
import time
import os
from django.conf import settings
import pytoml
from collections import defaultdict
from django_tables2 import RequestConfig
from .table import RankerTable,PerfTable


# Create your views here.
def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
    return render(request, 'blog/post_list.html', {'posts': posts})

def show_perfs(request):
    rankers = RetrievalMethod.objects.filter(author=request.user)
    table = PerfTable(Peformance.objects.filter(ranker__in=rankers))
    RequestConfig(request).configure(table)
    return render(request, 'evaluation/myperfs.html', {'table': table})

def show_rankers2(request):
    table = RankerTable(RetrievalMethod.objects.filter(author=request.user))
    RequestConfig(request).configure(table)
    return render(request, 'retrieval/myrankers.html', {'table': table})


# show all retrieval functions created by current use
def show_rankers(request):
    rankers = RetrievalMethod.objects.filter(author=request.user)
    ranker_perfs = defaultdict()
    ranker_forms = defaultdict()
    for ranker in rankers:
        perfs = Peformance.objects.filter(ranker=ranker)
        # ranker_perfs[ranker].append(get_empty_form(ranker.name))
        ranker_perfs[ranker]= perfs
        curt_form = get_filled_form(ranker)
        for key in curt_form.fields.keys():
            curt_form.fields[key].widget.attrs['readonly'] = True
            curt_form.fields[key].widget.attrs['class'] = 'form-control'
        ranker_forms[ranker.id] = curt_form


    print(ranker_perfs)
    print(rankers)
    print(ranker_forms)
    return render(request, 'retrieval/myconfigs.html', {'rankers': rankers,'ranker_perfs':ranker_perfs.items(),'ranker_forms':ranker_forms})


# show configuring form for one of the retrieval function
def show_configs(request, name):
    if name == 'Okapi BM25':
        curt_form = bm25Form()
    elif name == 'Pivoted Length Normalization':
        curt_form = plForm()
    elif name == 'Dirichlet Prior Smoothing':
        curt_form = dpForm()
    elif name == 'Jelinek-Mercer Smoothing':
        curt_form = jmForm()
    elif name == 'Absolute Discount Smoothing':
        curt_form = adForm()
    curt_form = get_empty_form(name)
    return render(request, 'retrieval/configs.html', {'name': name, 'form': curt_form})


def save_configs(request, name):
    # save retrieval method to db, re-render to?
    if request.method == "POST":
        if name == 'Okapi BM25':
            curt_form = bm25Form(request.POST)
        elif name == 'Pivoted Length Normalization':
            curt_form = plForm(request.POST)
        elif name == 'Dirichlet Prior Smoothing':
            curt_form = dpForm(request.POST)
        elif name == 'Jelinek-Mercer Smoothing':
            curt_form = jmForm(request.POST)
        elif name == 'Absolute Discount Smoothing':
            curt_form = adForm(request.POST)

        if curt_form.is_valid():
            curt_method = curt_form.save(commit=False)
            curt_method.author = request.user
            curt_method.name = name
            curt_method.save()
            return render(request, 'retrieval/configs.html', {'name': name, 'form': curt_form})
    else:
        curt_form = bm25Form()
    return render(request, 'retrieval/configs.html', {'name': name, 'form': curt_form})


def create_search_engine(request, id):
    cfg = 'IRLab/search-config.toml'
    cfg = os.path.join(settings.BASE_DIR, cfg)
    ranker = RetrievalMethod.objects.filter(id=id)
    assert len(ranker) == 1
    ranker = ranker[0]

    print('ranker name', ranker.name)
    print('ranker id', ranker.ranker_id)
    searcher = Searcher(cfg)
    # searcher.eval(request, ranker)
    request.session['cfg'] = cfg

    return render(request, 'application/demo.html',
                  {'ranker_name': ranker.name, 'id': id, 'ranker_id': ranker.ranker_id})


def search(request):
    searcher = Searcher(request.session['cfg'])

    if request.method == 'POST':
        ranker = RetrievalMethod.objects.filter(id=request.POST.get('id', None))
        assert len(ranker) == 1
        ranker = ranker[0]
        # searcher.search(request)
        print('inside create enginee!!!!')
        print(request.POST.get('query_text', None))
        print(ranker.ranker_id)

        cfg = 'IRLab/search-config.toml'
        cfg = os.path.join(settings.BASE_DIR, cfg)
        test_idx = metapy.index.make_inverted_index(cfg)
        print('test111', test_idx.num_docs())
        ranker = metapy.index.OkapiBM25(k1=1.2, b=0.75, k3=500)
        query = metapy.index.Document()
        query.content(
            'what similarity laws must be obeyed when constructing aeroelastic models of heated high speed aircraft .')
        top_docs = ranker.score(test_idx, query, num_results=5)
        print('score finished!!', top_docs)

        response = json.loads(searcher.search(request, ranker))
        return render(request, 'application/demo.html',
                      {'ranker_name': ranker.name, 'response': response})


def get_empty_form(ranker_name):
    if ranker_name == 'Okapi BM25':
        curt_form = bm25Form()
    elif ranker_name == 'Pivoted Length Normalization':
        curt_form = plForm()
    elif ranker_name == 'Dirichlet Prior Smoothing':
        curt_form = dpForm()
    elif ranker_name == 'Jelinek-Mercer Smoothing':
        curt_form = jmForm()
    elif ranker_name == 'Absolute Discount Smoothing':
        curt_form = adForm()
    return curt_form

def get_filled_form(ranker):
    if ranker.name == 'Okapi BM25':
        curt_form = bm25Form(instance=ranker)
    elif ranker.name == 'Pivoted Length Normalization':
        curt_form = plForm(instance=ranker)
    elif ranker.name == 'Dirichlet Prior Smoothing':
        curt_form = dpForm(instance=ranker)
    elif ranker.name == 'Jelinek-Mercer Smoothing':
        curt_form = jmForm(instance=ranker)
    elif ranker.name == 'Absolute Discount Smoothing':
        curt_form = adForm(instance=ranker)
    return curt_form

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
        print(self.idx.num_docs())
        print(self.idx.unique_terms())
        self.default_ranker = metapy.index.OkapiBM25()
        self.cfg = cfg

    def load_ranker(self, ranker):
        '''
        :param ranker: ranker object from db
        :return: meta.index.ranker
        '''
        ranker_id = ranker.ranker_id
        # print(type(ranker_id))
        try:
            ranker = getattr(metapy.index, ranker_id)()
            print('made ranker', ranker_id)
        except:
            print("Couldn't make '{}' ranker, using default.".format(ranker_id))
            ranker = self.default_ranker
        return ranker

    def search(self, request, ranker):
        """
        Accept a JSON request and run the provided query with the specified
        ranker.
        """



        # start = time.time()
        # query = metapy.index.Document()
        # query.content(str(request.POST.get('query_text', None)))
        # # ranker_id = request.POST.get('ranker_id', None)
        # ranker = self.load_ranker(ranker)
        # ranker = self.default_ranker
        # response = {'query': request.POST.get('query_text', None), 'results': []}
        # print('response')
        # import pdb
        # pdb.set_trace()
        # results = ranker.score(self.idx, query)
        # # print(self.idx.num_docs())
        # # print(self.idx.unique_terms())
        # print(len(results))
        # for result in results:
        #     # print(result[1])
        #     # print(self.idx.doc_path(result[0]))
        #     response['results'].append({
        #         'score': float(result[1]),
        #         'name': self.idx.doc_name(result[0]),
        #         'path': self.idx.doc_path(result[0])
        #     })
        # response['elapsed_time'] = time.time() - start
        # return json.dumps(response, indent=2)

    def eval(self, request, ranker):

        ev = metapy.index.IREval(self.cfg)

        with open(self.cfg, 'r') as fin:
            cfg_d = pytoml.load(fin)

        query_cfg = cfg_d['query-runner']

        start_time = time.time()
        top_k = 10
        query_path = query_cfg.get('query-path', 'queries.txt')
        query_start = query_cfg.get('query-id-start', 0)

        query = metapy.index.Document()
        ranker = self.load_ranker(ranker)
        print('Running queries')
        with open(query_path) as query_file:
            for query_num, line in enumerate(query_file):
                query.content(line.strip())
                print(line.strip())
                results = ranker.score(self.idx, query, top_k)
                avg_p = ev.avg_p(results, query_start + query_num, top_k)
                print("Query {} average precision: {}".format(query_num + 1, avg_p))
        print("Mean average precision: {}".format(ev.map()))
        print("Elapsed: {} seconds".format(round(time.time() - start_time, 4)))

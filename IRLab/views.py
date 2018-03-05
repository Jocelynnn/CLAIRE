from django.shortcuts import render
from django.utils import timezone
from .models import Post
from .models import RetrievalMethod, Peformance, Code
from .forms import bm25Form, jmForm, dpForm, plForm, adForm, ownRetrievalForm, ownRetrievalFormForDisplay
import metapy
import json
import time
import os
from django.conf import settings
import pytoml
from collections import defaultdict
from django_tables2 import RequestConfig
from .table import RankerTable, PerfTable
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
import random
from pathlib import Path
from graphos.sources.simple import SimpleDataSource
from graphos.renderers.gchart import LineChart
from graphos.sources.model import ModelDataSource
import subprocess


# Create your views here.
def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
    return render(request, 'blog/post_list.html', {'posts': posts})


def show_home(request):
    return render(request, 'blog/home.html')


@login_required
def show_perfs(request):
    rankers = RetrievalMethod.objects.filter(author=request.user)
    perfs = Peformance.objects.filter(ranker__in=rankers)
    table1 = PerfTable(Peformance.objects.filter(ranker__in=rankers, dataset='apnews'), prefix="ap")
    table2 = PerfTable(Peformance.objects.filter(ranker__in=rankers, dataset='cranfield'), prefix="cr")

    RequestConfig(request).configure(table1)
    RequestConfig(request).configure(table2)
    return render(request, 'evaluation/myperfs.html', {'table1': table1, 'table2': table2})


def show_perfs_analysis(request):
    if request.method == 'POST':
        dataset = request.POST.get('dataset-dropdown', None)
        ranker_name = request.POST.get('ranker-dropdown', None)

        print(dataset)
        print(ranker_name)

        rankers = RetrievalMethod.objects.filter(name=ranker_name)
        print(len(rankers))
        perfs = Peformance.objects.filter(ranker__in=rankers, dataset=dataset)

        params = []
        data = []
        if len(rankers) > 0:
            ranker = rankers[0]
            for key, value in ranker.__dict__.items():
                key = str(key)
                # print(key)
                if key.startswith('p_'):
                    params.append((key, str(key[2:]).upper()))

            # only support ranker with one parameter
            if len(params) > 1:
                print('not valid')
            else:

                data.append([params[0][1], 'Map'])
                param_map = [(perf.ranker.__getattribute__(params[0][0]), perf.map) for perf in perfs]
                param_map = sorted(param_map, key=lambda pair: pair[0])

                for pair in param_map:
                    data.append([pair[0], pair[1]])


    else:
        # start from DL ranker
        dataset = 'apnews'
        ranker_name = 'Dirichlet Prior Smoothing'

        rankers = RetrievalMethod.objects.filter(author=request.user, name='Dirichlet Prior Smoothing')
        perfs = Peformance.objects.filter(ranker__in=rankers, dataset='apnews')

        data = []
        data.append(['Mu', 'Map'])
        param_map = [(perf.ranker.p_mu, perf.map) for perf in perfs]
        param_map = sorted(param_map, key=lambda pair: pair[0])
        for pair in param_map:
            data.append([pair[0], pair[1]])


    # DataSource object
    data_source = SimpleDataSource(data=data)
    # Chart object
    options = {
        'title': 'Dirichlet Prior: Mu-Map',
        'curveType': 'function',
        'width': '900',
        'height': '500',
        'hAxis': {
            'title': 'Mu'
        },
        'vAxis': {
            'title': 'Map'
        },
    }
    chart = LineChart(data_source, options=options)
    context = {'chart': chart, 'dataset': dataset, 'ranker_name': ranker_name}

    return render(request, 'application/charts.html', context)


# @login_required
# # TODO REMOVE LATER
# def show_rankers2(request):
#     table = RankerTable(RetrievalMethod.objects.filter(author=request.user))
#     RequestConfig(request).configure(table)
#     return render(request, 'retrieval/myrankers.html', {'table': table})


# show all retrieval functions created by current use
@login_required
def show_rankers(request):
    rankers = RetrievalMethod.objects.filter(author=request.user)
    ranker_perfs = defaultdict()
    ranker_forms = defaultdict()
    for ranker in rankers:
        perfs = Peformance.objects.filter(ranker=ranker).order_by('dataset')
        perfs_dict = {}  # dataset - perfs mapping, used for rendering
        for perf in perfs:
            perfs_dict[perf.dataset] = perf

        ranker_perfs[ranker] = perfs_dict
        curt_form = get_filled_form(ranker)
        for key in curt_form.fields.keys():
            curt_form.fields[key].widget.attrs['readonly'] = True
            curt_form.fields[key].widget.attrs['class'] = 'form-control'
        ranker_forms[ranker.id] = curt_form

    # print(ranker_perfs)
    # print(rankers)
    # print(ranker_forms)
    return render(request, 'retrieval/myRetrievals.html',
                  {'rankers': rankers, 'ranker_perfs': ranker_perfs.items(), 'ranker_forms': ranker_forms})


def show_new_retrieval_configs(request):
    form = ownRetrievalForm()
    return render(request, 'retrieval/createNewRetrievals.html', {'form': form})


# show configuring form for one of the retrieval function
@login_required
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
    return render(request, 'retrieval/createOldRetrievals.html', {'name': name, 'form': curt_form})


def save_new_retrieval_configs(request):
    if request.method == "POST":
        curt_form = ownRetrievalForm(request.POST)

        if curt_form.is_valid():
            curt_retrieval = curt_form.save(commit=False)
            curt_retrieval.author = request.user
            curt_retrieval.source = request.POST.get('code', None)

            while True:
                _num = random.randint(1, 10000)
                file_name = str(_num) + '.py'
                base_dir = os.path.abspath(os.path.join(settings.BASE_DIR, 'uploads/'))
                file_path = os.path.join(base_dir, file_name)
                my_file = Path(file_path)
                if not my_file.is_file():
                    with open(my_file, 'w+') as fout:
                        fout.write(curt_retrieval.source)
                        curt_retrieval.file_location = my_file
                        break
            curt_retrieval.save()
            return redirect('show_retrievals')


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
            curt_retrieval = curt_form.save(commit=False)
            curt_retrieval.author = request.user
            curt_retrieval.name = name
            curt_retrieval.save()
            return render(request, 'retrieval/createOldRetrievals.html', {'name': name, 'form': curt_form})
    else:
        curt_form = bm25Form()
    return render(request, 'retrieval/createOldRetrievals.html', {'name': name, 'form': curt_form})


def create_search_engine(request, id):
    cfg = 'IRLab/search-config.toml'
    cfg = os.path.abspath(os.path.join(settings.BASE_DIR, cfg))
    ranker = RetrievalMethod.objects.get(id=id)

    print('ranker name', ranker.name)
    print('ranker id', ranker.ranker_id)
    # searcher = Searcher(cfg)
    # searcher.eval(request, ranker)
    request.session['cfg'] = cfg

    return render(request, 'application/demo.html',
                  {'ranker_name': ranker.name, 'id': id, 'ranker_id': ranker.ranker_id})


def search(request):
    if request.method == 'POST':
        ranker = RetrievalMethod.objects.get(id=request.POST.get('id', None))
        query = request.POST.get('query_text', None)
        # print(query)
        ranker_id = ranker.ranker_id
        # print(ranker_id)

        # proc = subprocess.Popen('pwd', stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        #                         shell=True)
        # output = proc.communicate()[0].decode('utf-8')
        # print(output)

        if ranker_id == 'CustomizedRanker':
            run_script = 'search_customized.py '

            with open(ranker.file_location) as target_ranker, \
                    open('search_customized.py', 'w') as target_script, \
                    open('search.py', 'r') as fin:
                base = fin.read()
                base = base.replace("ranker = getattr(metapy.index, ranker_id)(**params)", "ranker = MyRanker()")
                target_script.write(target_ranker.read() + '\n')
                target_script.write(base)
        else:
            run_script = 'search.py '

        config_file, config_params = generate_search_config(ranker)
        # "python3 searcher.py config.toml "
        commands = "python3 " + run_script + config_file + " '" + query + "' " + ranker_id + " '" + config_params + "' "
        print(commands)
        proc = subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                shell=True)
        output = proc.communicate()[0].decode('utf-8')
        # print(output)

        response = json.loads(output)

        return render(request, 'application/demo.html',
                      {'ranker_name': ranker.name, 'response': response, 'id': ranker.id,
                       'ranker_id': ranker.ranker_id})


def evaluate(request, id):
    '''

    :param request:
    :param id: ranker id in db
    :param dataset: dataset to evaluate on
    :return:
    '''
    ranker = RetrievalMethod.objects.get(id=id)
    ranker_id = ranker.ranker_id

    dataset = request.POST.get('dataset', 'cranfield')

    if ranker_id == 'CustomizedRanker':
        run_script = 'eval_customized.py '
        with open(ranker.file_location) as target_ranker, \
                open('eval_customized.py', 'w') as target_script, \
                open('eval.py', 'r') as fin:
            base = fin.read()
            base = base.replace("ranker = load_ranker(ranker_id, params)", "ranker = MyRanker()")
            target_script.write(target_ranker.read() + '\n')
            target_script.write(base)
    else:

        run_script = 'eval.py '

    # "python3 searcher.py config.toml "
    config_file, config_params = generate_eval_config(ranker, dataset)
    commands = "python3 " + run_script + config_file + " " + ranker_id + " '" + config_params + "' "
    print(commands)
    proc = subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            shell=True)
    output = proc.communicate()[0].decode('utf-8')

    print(output)
    response = json.loads(output)
    # print(response)

    perf = Peformance(ranker=ranker, dataset=dataset, map=response['map'],
                      ndcg=response['ndcg'], elapsed_time=response['elapsed_time'])
    perf.save()

    return redirect('show_retrievals')


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
    else:
        curt_form = ownRetrievalForm()
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
    else:
        curt_form = ownRetrievalFormForDisplay(instance=ranker)
    return curt_form


def generate_search_config(ranker):
    dict = {}
    dict['stop-words'] = "data/lemur-stopwords.txt"
    dict['prefix'] = "."
    dict['dataset'] = "apnews"
    dict['corpus'] = "line.toml"
    dict['index'] = "apnews-index"
    dict['query-judgements'] = "qrels.txt"

    dict['analyzers'] = [{'method': "ngram-word",
                          'ngram': 1,
                          'filter': "default-unigram-chain"}]

    dict['ranker'] = {'method': ranker.ranker_id_4_config}

    config_params = ''
    for key, value in ranker.__dict__.items():
        key = str(key)
        # print(key)
        if key.startswith('p_'):
            dict['ranker'][key[2:]] = round(float(value), 4)
            config_params += key[2:] + '=' + str(round(float(value), 4)) + ","

    # while True:
    #     _num = random.randint(1, 10000)
    #     file_name = 'c-'+str(_num) + '.toml'
    #     base_dir = os.path.abspath(settings.BASE_DIR)
    #     file_path = os.path.join(base_dir, file_name)
    #     my_file = Path(file_path)
    #     if not my_file.is_file():
    #         with open(my_file, 'w+') as fout:
    #             pytoml.dump(fout, dict)
    #             break
    file_name = 'temp.toml'
    with open(file_name, 'w+') as fout:
        pytoml.dump(fout, dict)
    return file_name, config_params.strip(',')


def generate_eval_config(ranker, dataset):
    # dataset = 'cranfield'
    start_index = {'cranfield': 1, 'apnews': 0}
    print('dataset!!', dataset)
    dict = {}
    dict['stop-words'] = "data/lemur-stopwords.txt"
    dict['prefix'] = "."
    dict['dataset'] = dataset
    dict['corpus'] = "line.toml"
    dict['index'] = dataset + "-index"
    dict['query-judgements'] = "data/" + dataset + "-qrels.txt"

    dict['analyzers'] = [{'method': "ngram-word",
                          'ngram': 1,
                          'filter': "default-unigram-chain"}]

    dict['query-runner'] = {'query-path': "data/" + dataset + "-queries.txt",
                            'query-id-start': start_index[dataset]
                            }

    config_params = ''
    for key, value in ranker.__dict__.items():
        key = str(key)
        # print(key)
        if key.startswith('p_'):
            config_params += key[2:] + '=' + str(round(float(value), 4)) + ","

    # while True:
    #     _num = random.randint(1, 10000)
    #     file_name = 'c-'+str(_num) + '.toml'
    #     base_dir = os.path.abspath(settings.BASE_DIR)
    #     file_path = os.path.join(base_dir, file_name)
    #     my_file = Path(file_path)
    #     if not my_file.is_file():
    #         with open(my_file, 'w+') as fout:
    #             pytoml.dump(fout, dict)
    #             break
    file_name = 'temp.toml'
    with open(file_name, 'w+') as fout:
        pytoml.dump(fout, dict)
    return file_name, config_params.strip(',')


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

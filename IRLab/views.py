from django.shortcuts import render
from django.utils import timezone
from .models import RetrievalMethod, Peformance
from .forms import bm25Form, jmForm, dpForm, plForm, adForm, ownRetrievalForm, ownRetrievalFormForDisplay
import json
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
import subprocess
import requests
import gitlab_private_token
import gitlab_util
import string
import pickle
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from dataset_config import CONFIG as DATASET_CONFIG

# Create your views here.


def show_home(request):
    return render(request, 'home/home.html')


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


@login_required
def show_perfs(request):
    rankers = RetrievalMethod.objects.filter(author=request.user)
    perfs = Peformance.objects.filter(ranker__in=rankers)
    table1 = PerfTable(Peformance.objects.filter(ranker__in=rankers, dataset='apnews'), prefix="ap")
    table2 = PerfTable(Peformance.objects.filter(ranker__in=rankers, dataset='cranfield'), prefix="cr")

    RequestConfig(request).configure(table1)
    RequestConfig(request).configure(table2)
    return render(request, 'evaluation/myperfs.html', {'table1': table1, 'table2': table2})


@login_required
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


def compare_query(request):
    rankers = RetrievalMethod.objects.filter(author=request.user)
    if request.method == 'POST':
        # before submit query:
        query = request.POST.get('query_text', None)
        if query is None:
            ranker1 = RetrievalMethod.objects.get(id=request.POST.get('ranker-1', None))
            ranker2 = RetrievalMethod.objects.get(id=request.POST.get('ranker-2', None))
            context = {'ranker_list': rankers, 'ranker1': ranker1, 'ranker2': ranker2}
        else:
            # query submitted
            ranker1 = RetrievalMethod.objects.get(id=request.POST.get('ranker1_id', None))
            ranker2 = RetrievalMethod.objects.get(id=request.POST.get('ranker2_id', None))
            response1 = search_helper(ranker1, query)
            response2 = search_helper(ranker2, query)
            zipped_response = zip(response1['results'], response2['results'])
            context = {'ranker_list': rankers, 'ranker1': ranker1, 'ranker2': ranker2,
                       'zipped_response': zipped_response,
                       }
    # initial render
    else:
        context = {'ranker_list': rankers}
    return render(request, 'application/compare_query.html', context)


def search(request):
    if request.method == 'POST':
        ranker = RetrievalMethod.objects.get(id=request.POST.get('id', None))
        query = request.POST.get('query_text', None)

        response = search_helper(ranker, query)
        return render(request, 'application/demo.html',
                      {'ranker_name': ranker.name, 'response': response, 'id': ranker.id,
                       'ranker_id': ranker.ranker_id})


def search_helper(ranker, query):
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
    return response

def evaluate(request, db_ranker_id):
    '''

    :param request:
    :param db_ranker_id: ranker id in db
    :param dataset: dataset to evaluate on
    :return:
    '''

    # setup vars for GitLab project creation
    PROJECT_NAME_LENGTH = 10
    RANDOM_PROJECT_NAME = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(PROJECT_NAME_LENGTH))

    # pre-evaluation processing
    ranker = RetrievalMethod.objects.get(id=db_ranker_id)
    ranker_id = ranker.ranker_id

    dataset = request.POST.get('dataset', 'cranfield')

    if ranker_id == 'CustomizedRanker':
        run_script = 'eval_customized.py'
        with open(ranker.file_location) as target_ranker, \
                open('eval_customized.py', 'w') as target_script, \
                open('eval.py', 'r') as fin:
            base = fin.read()
            base = base.replace("ranker = load_ranker(ranker_id, params)", "ranker = MyRanker()")
            target_script.write(target_ranker.read() + '\n')
            target_script.write(base)
    else:
        run_script = 'eval.py'

    # Create the new project on GitLab.
    project_creation_response_code = gitlab_util.create_new_project(RANDOM_PROJECT_NAME)
    if project_creation_response_code != 201:
        print('Failed to create gitlab project. Abandoning evaluation.')
        return redirect('show_retrievals')

    # Get the id of the new project. This is necessary for committing files.
    new_project_id = gitlab_util.get_newest_project_id_by_name(RANDOM_PROJECT_NAME)
    if new_project_id is None:
        print('Failed to get new project id. Abandoning evaluation.')
        return redirect('show_retrievals')

    # Generate execution files
    config_file, config_params = generate_eval_config(ranker, dataset)
    command = "python3 " + run_script + " " + config_file + " " + ranker_id + " '" + config_params + "' "

    # Commit files to the new GitLab project repo for build
    commit_files = [run_script, config_file, "execute_eval.py", "exec_config.json", "lemur-stopwords.txt", ".gitlab-ci.yml"]
    files_contents = []
    for filename in commit_files:
        if filename == "exec_config.json":
            exec_config = {
                "command": command,
                "db_ranker_id": db_ranker_id,
                "project_name": RANDOM_PROJECT_NAME    
            }
            files_contents.append(json.dumps(exec_config))
        else:
            files_contents.append(open(filename).read())
    commit_response = gitlab_util.commit_evaluation_files(new_project_id, commit_files, files_contents)
    if commit_response is None:
        print('Failed to commit all files. Abandoning evaluation.')

    # Remove this. This is only for testing the script and saving.
    # with open("exec_config.json", "w") as exec_config_file:
    #     exec_config_file.write(json.dumps(exec_config))
    #     exec_config_file.close()
    # os.system("python3 execute_eval.py http://127.0.0.1:8000/evaluations/evaluation_results/")

    return redirect('show_retrievals')

@csrf_exempt
def evaluation_results(request):
    '''
    Endpoint for receiving the evaluation results from the GitLab execution script.
    '''
    json_str = request.body.decode('utf8').replace("'", '"')
    evaluation_response = json.loads(json_str)
    print("Evaluation Results: ", json.dumps(evaluation_response))
   
    # Saving is done here.
    ranker = RetrievalMethod.objects.get(id=evaluation_response["db_ranker_id"])
    dataset = evaluation_response["dataset"]

    perf = Peformance(ranker=ranker, dataset=dataset, map=evaluation_response['map'], 
        ndcg=evaluation_response['ndcg'], elapsed_time=evaluation_response['elapsed_time'])

    perf.save()

    # delete gitlab repository created for build
    project_id = gitlab_util.get_newest_project_id_by_name(evaluation_response["project_name"])
    headers = { "PRIVATE-TOKEN": gitlab_private_token.GITLAB_PRIVATE_TOKEN }
    DELETE_URL = gitlab_util.GITLAB_PROJECTS_URL + "/" + str(project_id)
    resp = requests.delete(DELETE_URL, headers=headers)
    if resp.status_code != 202:
        print("Error deleting GitLab repository: ", evaluation_response["project_name"])

    return HttpResponse(status=200)

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


def generate_search_config(ranker, is_server=True):
    ###
    #
    # TODO: This needs to be overhauled for the cloud version.
    #
    ###
    if is_server:
        dict = {}
        dict['stop-words'] = "lemur-stopwords.txt"
        dict['prefix'] = "."
        dict['dataset'] = "wikipedia"
        dict['corpus'] = "line.toml"
        dict['index'] = "wikipedia-index2"

        dict['analyzers'] = [{'method': "ngram-word",
                              'ngram': 1,
                              'filter': "default-unigram-chain"}]

        dict['ranker'] = {'method': ranker.ranker_id_4_config}

        config_params = ''
        for key, value in ranker.__dict__.items():
            key = str(key)
            if key.startswith('p_'):
                dict['ranker'][key[2:]] = round(float(value), 4)
                config_params += key[2:] + '=' + str(round(float(value), 4)) + ","
    else:
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
            if key.startswith('p_'):
                dict['ranker'][key[2:]] = round(float(value), 4)
                config_params += key[2:] + '=' + str(round(float(value), 4)) + ","

    file_name = 'temp.toml'
    with open(file_name, 'w+') as fout:
        pytoml.dump(fout, dict)
    return file_name, config_params.strip(',')


def generate_eval_config(ranker, dataset):
#    start_index = {'cranfield': 1, 'apnews': 0}
    print('dataset!!', dataset)

    eval_dict = {}
    eval_dict['stop-words'] = DATASET_CONFIG[dataset]["lemur-stopwords.txt"]

    eval_dict['prefix'] = "/data"
    eval_dict['dataset'] = dataset
    eval_dict['corpus'] = DATASET_CONFIG[dataset]["corpus"]

    eval_dict['index'] = DATASET_CONFIG[dataset]["index"]
    eval_dict['query-judgements'] = DATASET_CONFIG[dataset]["query-judgements"]

    eval_dict['analyzers'] = [
        {
            'method': "ngram-word",
            'ngram': 1,
            'filter': "default-unigram-chain"
        }
    ]

    eval_dict['query-runner'] = {
        'query-path': DATASET_CONFIG[dataset]["query-path"],
        'query-id-start': DATASET_CONFIG["query-id-start"]
    }

    config_params = ''
    for key, value in ranker.__dict__.items():
        key = str(key)
        if key.startswith('p_'):
            config_params += key[2:] + '=' + str(round(float(value), 4)) + ","

    file_name = 'temp.toml'
    with open(file_name, 'w+') as fout:
        pytoml.dump(fout, eval_dict)
        fout.close()

    return file_name, config_params.strip(',')

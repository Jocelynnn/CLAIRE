from django.shortcuts import render
from django.utils import timezone
from .models import Post
from .models import RetrievalMethod
from .config_forms import bm25Form,jmForm,dpForm,plForm,adForm
from django.shortcuts import redirect
import metapy
import json
import time
import os
from django.conf import settings




# Create your views here.
def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
    return render(request, 'blog/post_list.html', {'posts': posts})


def show_retrievals(request):
    rankers = RetrievalMethod.objects.filter(author = request.user)
    return render(request,'retrieval/myconfigs.html',{'rankers':rankers})

def show_configs(request, name):
    if name == 'Okapi BM25':
        curt_form = bm25Form()
    elif name == 'PVT':
        curt_form = plForm()
    elif name == 'Dirichlet':
        curt_form = dpForm()
    elif name == 'JM':
        curt_form = jmForm()
    elif name == 'Absolute Discount':
        curt_form = adForm()
    return render(request, 'retrieval/configs.html', {'name': name, 'form': curt_form})


def save_configs(request, name):
	# save retrieval method to db, re-render to?
    if request.method == "POST":
        if name == 'Okapi BM25':
            curt_form = bm25Form(request.POST)
        elif name == 'PVT':
            curt_form = plForm(request.POST)
        elif name == 'Dirichlet':
            curt_form = dpForm(request.POST)
        elif name == 'JM':
            curt_form = jmForm(request.POST)
        elif name == 'Absolute Discount':
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


def create_search_engine(request, ranker):
    cfg = 'IRLab/search-config.toml'
    cfg = os.path.join(settings.BASE_DIR, cfg)

    if request.method == 'POST':
        # searcher.search(request)
        print('inside create enginee!!!!')
        print(request.POST.get('query_text', None))
        print(request.POST.get('ranker', None))
        searcher = Searcher(cfg)
        searcher.search(request)

    return render(request,'application/demo.html',{'ranker': ranker})



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
        print(self.idx.total_corpus_terms())
        self.default_ranker = metapy.index.OkapiBM25()

    def search(self, request):
        """
        Accept a JSON request and run the provided query with the specified
        ranker.
        """
        start = time.time()
        print(start)
        query = metapy.index.Document()
        query.content(request.POST.get('query_text', None))
        ranker_id = request.POST.get('ranker', None)
        try:
            ranker = getattr(metapy.index, ranker_id)()
            print('ranker')
        except:
            print("Couldn't make '{}' ranker, using default.".format(ranker_id))
            ranker = self.default_ranker
        response = {'query': request.POST.get('query_text', None), 'results': []}
        print('response')
        results = ranker.score(self.idx, query,1000)
        # print(self.idx.num_docs())
        # print(self.idx.unique_terms())
        print(len(results))
        for result in ranker.score(self.idx, query,1000):
            # print(result[1])
            # print(self.idx.doc_name(result[0]))
            response['results'].append({
                'score': float(result[1]),
                'name': self.idx.doc_name(result[0]),
                'path': self.idx.doc_path(result[0])
            })
        response['elapsed_time'] = time.time() - start
        return json.dumps(response, indent=2)

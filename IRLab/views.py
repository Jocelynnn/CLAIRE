from django.shortcuts import render
from django.utils import timezone
from .models import Post
from .models import RetrievalMethod
from .config_forms import bm25Form,jmForm,dpForm,plForm,adForm
from django.shortcuts import redirect


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


def create_search_engine(request, name):
    return render(request,'application/demo.html',{'name': name})

from django.conf.urls import url
from . import views
from django.urls import path
from django.urls import include

urlpatterns = [
    url(r'^$', views.show_home, name='show_home'),
    path('accounts/', include('django.contrib.auth.urls')),
    url(r'^retrievals/$', views.show_rankers, name='show_retrievals'),
    url(r'^retrievals/createOldRetrievals/(?P<name>[^/]+)/$', views.show_configs, name='show_configs'),
    url(r'^retrievals/createNewRetrievals/$', views.show_new_retrieval_configs, name='show_new_retrieval_configs'),
    url(r'^retrievals/saveConfigs/(?P<name>[^/]+)/$', views.save_configs, name='save_configs'),
    url(r'^retrievals/saveNewRetrieval/$', views.save_new_retrieval_configs, name='save_new_retrieval'),
    url(r'^evaluations/myperfs/$', views.show_perfs, name='show_perfs'),
    url(r'^evaluations/$', views.show_perfs, name='show_perfs'),
    url(r'^evaluations/evaluate/(?P<db_ranker_id>[^/]+)/$', views.evaluate, name='evaluate'),
    url(r'^applications/create/(?P<id>[^/]+)/$', views.create_search_engine, name='create_search_engine'),
    url(r'^applications/search/$', views.search, name='search'),
    url(r'^applications/analysis-charts/$', views.show_perfs_analysis, name='perf_analysis'),
    url(r'^applications/analysis-compare/$', views.compare_query, name='compare_query'),
    url(r'^evaluations/evaluation_results/$', views.evaluation_results, name='evaluation_results')
]

from django.conf.urls import url
from . import views
from django.urls import path
from django.urls import include

urlpatterns = [
    url(r'^$', views.post_list, name='post_list'),
    path('accounts/', include('django.contrib.auth.urls')),
    url(r'^retrievals/$', views.show_rankers, name='show_retrievals'),
    url(r'^retrievals/myrankers$', views.show_rankers2, name='show_retrievals2'),
    url(r'^retrievals/configs/(?P<name>[^/]+)/$', views.show_configs, name='show_configs'),
    url(r'^retrievals/saveConfigs/(?P<name>[^/]+)/$', views.save_configs, name='save_configs'),
    url(r'^evaluations/myperfs/$', views.show_perfs, name='show_perfs'),
    url(r'^evaluations/$', views.show_perfs, name='show_perfs'),
    url(r'^applications/create/(?P<id>[^/]+)/$', views.create_search_engine, name='create_search_engine'),
    url(r'^applications/search/$', views.search, name='search'),

]

from django.db import models
from django.utils import timezone
from polymorphic.models import PolymorphicModel
import json


class RetrievalMethod(PolymorphicModel):
    name = models.CharField(max_length=70)
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Okapi_bm25(RetrievalMethod):
    # https://meta-toolkit.org/doxygen/classmeta_1_1index_1_1okapi__bm25.html
    # const float   k1_ Doc term smoothing
    ranker_id = models.CharField(max_length=70, default='OkapiBM25')
    p_k1 = models.FloatField()
    # Length normalization. 
    p_b = models.FloatField()
    # query term smoothing
    p_k3 = models.FloatField()


class Jelinek_mercer(RetrievalMethod):
    # https://meta-toolkit.org/doxygen/classmeta_1_1index_1_1jelinek__mercer.html
    p_lambda = models.FloatField()
    ranker_id = models.CharField(max_length=70, default='JelinekMercer')


class Dirichlet_prior(RetrievalMethod):
    # https://meta-toolkit.org/doxygen/classmeta_1_1index_1_1dirichlet__prior.html
    p_mu = models.FloatField()
    ranker_id = models.CharField(max_length=70, default='DirichletPrior')


class Pivoted_length(RetrievalMethod):
    # https://meta-toolkit.org/doxygen/classmeta_1_1index_1_1pivoted__length.html
    p_s = models.FloatField()
    ranker_id = models.CharField(max_length=70, default='PivotedLength')


class Absolute_discount(RetrievalMethod):
    # https://meta-toolkit.org/doxygen/classmeta_1_1index_1_1absolute__discount.html
    p_delta = models.FloatField()
    ranker_id = models.CharField(max_length=70, default='AbsoluteDiscount')


class Peformance(models.Model):
    ranker = models.ForeignKey(RetrievalMethod, on_delete=models.CASCADE)
    dataset = models.CharField(max_length=30)
    map = models.FloatField()
    ndcg = models.FloatField()
    elapsed_time = models.FloatField()

    # def __str__(self):
    #     return json.dumps({'dataset': self.dataset, 'map': self._map, 'ndcg': self._ndcg, 'time': self.elapsed_time})


class Post(models.Model):
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_date = models.DateTimeField(
        default=timezone.now)
    published_date = models.DateTimeField(
        blank=True, null=True)

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.title

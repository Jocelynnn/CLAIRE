# tutorial/tables.py
import django_tables2 as tables
from .models import RetrievalMethod,Peformance

class RankerTable(tables.Table):
    class Meta:
        model = RetrievalMethod
        template_name = 'django_tables2/bootstrap.html'


class PerfTable(tables.Table):
    class Meta:
        model = Peformance
        template_name = 'django_tables2/bootstrap-responsive.html'
        exclude = ('avg_p_list','id',)

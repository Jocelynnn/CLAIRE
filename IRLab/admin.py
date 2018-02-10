from django.contrib import admin
from .models import Post,RetrievalMethod,Okapi_bm25


# Register your models here.
admin.site.register(Post)
admin.site.register(RetrievalMethod)
admin.site.register(Okapi_bm25)

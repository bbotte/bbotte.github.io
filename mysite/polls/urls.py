from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<artical_id>[0-9]+)/$', views.artical, name='artical'),
    url(r'^articles/(?P<year>[0-9]{4})/$', views.year_archive, name='year'),
]

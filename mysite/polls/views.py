from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.template import RequestContext, loader
from .models import Artical


def index(request):
    latest_artical_list = Artical.objects.order_by('pub_date')[0:5]
    template = loader.get_template('../templates/polls/index.html')
    context = {
        'latest_artical_list':latest_artical_list,
    }
    return HttpResponse(template.render(context, request))

def artical(request, artical_id):
    response = "this artical_id is %s"
    return HttpResponse(response % artical_id) 

def year_archive(request, year):
    a_list = Artical.objects.filter(pub_date__year=year)
    context = {'year':year, 'article_list': a_list}
    return render(request, '../templates/polls/year.html', context)



from django.shortcuts import get_list_or_404, redirect

from sitetree.toolbox import register_i18n_trees

from .models import Article
from .utils import render_themed

register_i18n_trees(['main'])


def index(request):
    return render_themed(request, 'index', {})


def listing(request):
    return render_themed(request, 'listing', {'articles': get_list_or_404(Article)})


def detailed(request, article_id):
    return redirect('demo:articles-listing')

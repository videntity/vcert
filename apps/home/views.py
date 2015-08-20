from django.conf import settings
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext

@login_required
def home(request):
    context = {}
    return render_to_response('home/index.html',
                RequestContext(request, context,))

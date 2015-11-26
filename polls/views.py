from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse

from .models import Question
from .models import VivoCgiRule 
from .forms import ModelFormWithFileField 

# No need the to append path to sys.path if you have __init__.py in the directory
#import sys
#sys.path.append('/home/deploy/django/mysite/polls/lib')
from .lib.upload import handle_uploaded_file


# Create your views here.

#def index(request):
    #latest_question_list = Question.objects.order_by('-pub_date')[:5]
    #template = loader.get_template('polls/index.html')
    #context = RequestContext(request, {
        #'latest_question_list': latest_question_list,
    #})
    #return HttpResponse(template.render(context))

def index(request):
    latest_question_list = Question.objects.order_by('-pub_date')[:5]
    context = {'latest_question_list': latest_question_list}
    return render(request, 'polls/index.html', context)


def detail(request, question_id):
    return HttpResponse("You're looking at question %s." % question_id)

def results(request, question_id):
    response = "You're looking at the results of question %s."
    return HttpResponse(response % question_id)

def vote(request, question_id):
    return HttpResponse("You're voting on question %s." % question_id)

def upload(request):
    if request.method == 'POST':
        form = ModelFormWithFileField(request.POST, request.FILES)
        if form.is_valid():
            # file is saved
            form.save()
            #return HttpResponseRedirect('/success/url/')
            return HttpResponseRedirect(reverse('polls.views.upload'))
    else:
        form = ModelFormWithFileField()
    
    rules = VivoCgiRule.objects.all()

    return render(request, 'polls/upload.html', {'rules': rules, 'form': form})

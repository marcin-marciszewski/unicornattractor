from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Query, Comment
from .forms import CommentForm
from pages.query_types import query_types
from django.http import HttpResponseRedirect

#Main page view
class QueryListView(ListView):
    model = Query
    template_name = 'pages/index.html'
    context_object_name = 'queries' 
    ordering = ['-date_posted']
    paginate_by = 5
   
#List of queries for a particular user
class UserQueryListView(ListView):
    model = Query
    template_name = 'pages/user_queries.html'
    context_object_name = 'queries'
    paginate_by = 5

    #Find queries for the specific user
    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Query.objects.filter(author=user).order_by('-date_posted')



#A view for particular query
def query_detail(request, id):
    query = get_object_or_404(Query, id=id, )
    comments = Comment.objects.filter(query=query).order_by('-id')

    if request.method == 'POST':
        comment_form = CommentForm(request.POST or None)
        if comment_form.is_valid():
            content = request.POST.get('content')
            comment = Comment.objects.create(query=query, user=request.user, content= content)
            comment_form.save()
                      
            return redirect(reverse('query-detail',kwargs={"id":id}))
        
    else:
        comment_form = CommentForm()

    context = {
        'query': query,
        'comments': comments,
        'comment_form': comment_form,
    }

    return render(request,'pages/query_detail.html', context)

#Create a new query
class QueryCreateView(LoginRequiredMixin, CreateView):
    model = Query
    fields = ['title', 'content', 'query_type']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

#Update an exisiting query
class QueryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Query
    fields = ['title', 'content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    
    #Test if the logged user is the author of the query
    def test_func(self):
        query = self.get_object()
        if self.request.user == query.author:
            return True
        return False

#Delete a query
class QueryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Query
    success_url = '/'

    #Test if the logged user is the author of the query
    def test_func(self):
        query = self.get_object()
        if self.request.user == query.author:
            return True
        return False

#About page view
def about(request):
    return render(request, 'pages/about.html')

#Search view
def search(request):
    queryset_list = Query.objects.order_by('-date_posted')

    #Search for keywords
    if 'keywords' in request.GET:
        keywords = request.GET['keywords']
        if keywords:
            queryset_list = queryset_list.filter(content__icontains=keywords) or queryset_list.filter(title__icontains=keywords)
    
    #Filter by type of the query
    if 'query_type' in request.GET:
        query_type = request.GET['query_type']
        if query_type:
            queryset_list = queryset_list.filter(query_type__iexact=query_type) 

    context = {
        'queries': queryset_list,
        'query_types': query_types,
        'values': request.GET,
    }
    return render(request, 'pages/search.html', context)
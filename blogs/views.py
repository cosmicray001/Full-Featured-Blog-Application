from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.core.mail import send_mail
from taggit.models import Tag
from django.db.models import Count
from django.conf.global_settings import EMAIL_HOST_USER
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from .models import Post  # , Comment
from .forms import EmailPostForm, CommentForm, SearchForm


def post_list(request, tag_slug=None):
    object_list = Post.objects.all()
    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])

    paginator = Paginator(object_list, 3)  # 3 posts in each page
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer deliver the first page
        posts = paginator.page(1)
    except EmptyPage:
        # If page is out of range deliver last page of results
        posts = paginator.page(paginator.num_pages)
    return render(request,
                  'blogs/posts/list.html',
                  {'page': page,
                   'posts': posts,
                   'tag': tag,
                   })


class PostListView(ListView):
    queryset = Post.objects.all()
    context_object_name = 'posts'
    paginate_by = 1
    template_name = 'blogs/posts/list.html'


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['title', 'body', 'status', 'tags', ]
    template_name = 'blogs/posts/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['title', 'body', 'status', 'tags', ]
    template_name = 'blogs/posts/update.html'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/'
    template_name = 'blogs/posts/post_confirm_delete.html'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


def post_detail(request, year, month, day, post, *args, **kwargs):
    post = get_object_or_404(Post, slug=post,
                             status='published',
                             publish__year=year,
                             publish__month=month,
                             publish__day=day,
                             )
    comments = post.comments.filter(active=True)
    new_comment = None
    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid() and request.user.is_authenticated:
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.name = request.user
            new_comment.email = request.user.email
            new_comment.save()
    else:
        comment_form = CommentForm()

    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.objects.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
    return render(request, 'blogs/posts/detail.html', {"post": post,
                                                       "comments": comments,
                                                       "new_comment": new_comment,
                                                       "comment_form": comment_form,
                                                       'similar_posts': similar_posts,
                                                       })


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status='published')
    send = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url}\n\n {cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, EMAIL_HOST_USER, [cd['to']])
            send = True
    else:
        form = EmailPostForm()
    return render(request, 'blogs/posts/share.html', {"post": post, "form": form, "sent": send})


def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', weight='A') + SearchVector('body', weight='B')
            search_query = SearchQuery(query)
            results = Post.objects.annotate(
                rank=SearchRank(search_vector, search_query)
            ).filter(rank__gte=0.3).order_by('-rank')
    return render(request, 'blogs/posts/search.html', {"form": form,
                                                       "query": query,
                                                       "results": results
                                                       })

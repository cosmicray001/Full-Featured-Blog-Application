from django.urls import path
from .views import post_list, post_detail, post_share, post_search
from .views import PostListView, PostCreateView, PostUpdateView, PostDeleteView
from django.contrib.sitemaps.views import sitemap
from .sitemaps import PostSitemap
from .feeds import LatestPostsFeed


sitemaps = {
    'posts': PostSitemap,
}


app_name = 'blogs'


urlpatterns = [
    path('', post_list, name="post_list"),
    # path('', PostListView.as_view(), name="post_list"),
    path('tag/<slug:tag_slug>/', post_list, name='post_list_by_tag'),
    path('<int:year>/<int:month>/<int:day>/<slug:post>/', post_detail, name="post_detail"),
    path('<int:post_id>/share/', post_share, name='post_share'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
    path('feed/', LatestPostsFeed(), name='post_feed'),
    path('search/', post_search, name='post_search'),
    path('create/', PostCreateView.as_view(), name='create'),
    path('update/<int:pk>/', PostUpdateView.as_view(), name='update'),
    path('delete/<int:pk>/', PostDeleteView.as_view(), name='delete'),
]

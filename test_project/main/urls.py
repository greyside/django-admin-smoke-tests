from django.conf.urls import url


urlpatterns = [
    url(r'^posts/(?P<pk>.+)/$', lambda **kwargs: '', name="post-detail"),
    url(r'^hasprimaryslug/(?P<pk>[\w-]+)/$', lambda **kwargs: '',
        name="hasprimaryslug-detail"),
    url(r'^hasprimaryuuid/(?P<pk>[\w-]+)/$', lambda **kwargs: '',
        name="hasprimaryuuid-detail"),
]

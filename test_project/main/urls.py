from django.conf.urls import patterns, url


urlpatterns = patterns('',
    url(r'^posts/(?P<pk>.+)/$', lambda **kwargs: '', name="post-detail"),
)

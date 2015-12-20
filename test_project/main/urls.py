from django.conf.urls import url


urlpatterns = (
    url(r'^posts/(?P<pk>.+)/$', lambda **kwargs: '', name="post-detail"),
)

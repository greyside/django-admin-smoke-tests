from django.urls import path


urlpatterns = [
    path("posts/(<int:pk>/", lambda **kwargs: "", name="post-detail"),
    path(
        "hasprimaryslug/<int:pk>/",
        lambda **kwargs: "",
        name="hasprimaryslug-detail",
    ),
    path(
        "hasprimaryuuid/<int:pk>/",
        lambda **kwargs: "",
        name="hasprimaryuuid-detail",
    ),
]

from django.urls import path


urlpatterns = [
    path("posts/(<str:pk>/", lambda **kwargs: "", name="post-detail"),
    path(
        "hasprimaryslug/<str:pk>/",
        lambda **kwargs: "",
        name="hasprimaryslug-detail",
    ),
    path(
        "hasprimaryuuid/<str:pk>/",
        lambda **kwargs: "",
        name="hasprimaryuuid-detail",
    ),
]

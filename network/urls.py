from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("profile/<int:user_id>", views.profile, name="profile"),
    path("following", views.following, name="following"),
    # API related URLs.
    path("posts/<int:page>/<slug:slug>/<int:user_id>", views.posts,
         name="posts"),
    path("follow_user/<int:creator_id>", views.toggle_follow_user,
         name="toggle_follow_user"),
    path("new_post", views.new_post, name="new_post"),
    path("toggle_like_post/<int:post_id>", views.toggle_like_post,
         name="toggle_like_post"),
    path("update_post", views.update_post, name="update_post"),
    # Account creation and login.
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register")
]

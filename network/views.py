import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse

from .models import User, NetworkPost, Follower


def index(request):
    # Default route for the Network website..
    return render(request, "network/index.html")


def posts(request, page, slug, user_id):
    try:
        every_post = NetworkPost.objects.none()

        # Get posts based on the slug/filter or default to all posts.
        if slug == "following":
            user = User.objects.get(pk=user_id)
            # Get the Users where the current user exists as a follower.
            following = User.objects.filter(followers__follower_id=user.id)
            # Return all posts where the creato is in set of Users following..
            every_post = NetworkPost.objects.filter(
                creator_id__in=following).all().order_by("-create_date")
        elif slug == "profile":
            user = User.objects.get(pk=user_id)
            # Return all posts for the specified User.
            every_post = NetworkPost.objects.filter(
                creator=user).all().order_by(
                "-create_date")
        else:
            # No indicator defaults to all posts, all users.
            every_post = NetworkPost.objects.all().order_by("-create_date")

        paginator = Paginator(every_post, 10)  # Show 10 posts per page.
        page_obj = paginator.get_page(page)

        json_data = {
            'page': page,  # Current page
            'num_pages': paginator.num_pages,  # Total pages.
            'page_objects': [post.serialize() for post in page_obj]
        }

        return JsonResponse(json_data, safe=False);
    except User.DoesNotExist:
        print('User does not exist.')
        return JsonResponse({"error": "User was not found."}, status=404)
    except NetworkPost.DoesNotExist:
        print('Content does not exist.')
        return JsonResponse({"error": "Post was not found."}, status=404)


def profile(request, user_id):
    try:
        user_profile = User.objects.get(pk=user_id)
        count_followers = len(user_profile.followers.all())
        count_following = len(user_profile.following.all())
        # The requested profile may not equal the current User.
        # Get the current user to see if they follow this profile.
        is_following = False;
        if request.user.is_authenticated:
            user = User.objects.get(pk=request.user.id)
            is_following = Follower.objects.filter(follower=user,
                                                   following=user_profile).exists()
    except User.DoesNotExist:
        print("User does not exist.")

    return render(request, "network/profile.html",
                  {"profile_id": user_profile.id,
                   "username": user_profile.username,
                   "following": count_following,
                   "followers": count_followers,
                   "is_following": is_following}, )


@login_required
def following(request):
    return render(request, "network/following.html")


@login_required
def new_post(request):
    """
    Create new content.
    :param request:with new content and user data.
    :return: success or failure message in json format
    """
    # A POST request is required to create new content
    if request.method != "POST":
        messages.add_message(request, messages.WARNING,
                             "POST request required.")
        return render(request, "network/index.html", )

    if not request.POST["post_content"]:
        messages.add_message(request, messages.WARNING,
                             "Content is required.")
        return render(request, "network/index.html")

    try:
        content = NetworkPost(creator=request.user,
                              content=request.POST["post_content"])
        content.save()
    except IntegrityError:
        print("Error saving NetworkPost.")
        messages.add_message(request, messages.WARNING,
                             "We were unable to add the post.")
    return HttpResponseRedirect(reverse("index"))


def toggle_follow_user(request, creator_id):
    """
    Create or Delete a Follower relationship between two Users.
    :param request: with current user info.
    :param creator_id:
    :return:
    """
    try:
        # Get the current user and content creator.
        user = User.objects.get(pk=request.user.id)
        creator = User.objects.get(pk=creator_id)

        # A User cannot follow themselves.
        if creator_id is user.id:
            messages.add_message(request, messages.WARNING,
                                 "Users cannot follow themselves.")
            return HttpResponseRedirect(reverse("profile", args=(creator_id,)))

        # If the current user is already a Follower, remove them.
        follower = Follower.objects.filter(follower=user, following=creator)
        if follower.exists():
            follower.delete()
            return HttpResponseRedirect(reverse("profile", args=(creator_id,)))

        # Follow the creator of this post.
        Follower.objects.create(follower=user, following=creator)
        return HttpResponseRedirect(reverse("profile", args=(creator_id,)))

    except User.DoesNotExist:
        messages.add_message(request, messages.WARNING,
                             "User does not exist.")
        return HttpResponseRedirect(reverse("profile", args=(creator_id,)))


@login_required
def toggle_like_post(request, post_id):
    """
    Add or Remove a like to the specified post for the logged in User.
    :param post_id: the NetworkPost to get a like.
    :param request: with current user info.
    :return:  success or failure message in json format
    """

    if request.user.is_authenticated:
        try:
            user = User.objects.get(pk=request.user.id)
            # Get the content.
            content = NetworkPost.objects.get(pk=post_id)
            # Check to see if the user already likes this content.
            if user in content.likes.all():
                # Unlike the content.
                content.likes.remove(user)
                return JsonResponse({"message": "Like was removed."},
                                    status=201)
            # Like the content.
            content.likes.add(user)
            return JsonResponse({"message": "Post was liked."}, status=201)
        except User.DoesNotExist:
            print('User does not exist.')
            return JsonResponse({"error": "User was not found."}, status=404)
        except NetworkPost.DoesNotExist:
            print('Content does not exist.')
            return JsonResponse({"error": "Post was not found."}, status=404)


@login_required
def update_post(request):
    """
    Update post content.
    :param request: with new post data
    :return: success or failure message in json format
    """
    # A POST request is required to create new content
    if request.method != "POST":
        return render(request, "network/index.html",
                      {"error": "POST request required."})

    try:
        data = json.loads(request.body)
        content = NetworkPost.objects.get(pk=data.get("id"))
        # Updates can only be done by the content creator.
        if content.creator_id is not request.user.id:
            print("Only the post creator can edit.")
            return JsonResponse({"error": "Only the post creator can edit."},
                                status=403)
        content.content = data.get("content")
        content.save()
        return JsonResponse({"message": "Post updated successfully."},
                            status=201)
    except NetworkPost.DoesNotExist:
        print("NetworkPost does not exist.")
        return JsonResponse({"error": "Post was not found."}, status=404)
    except IntegrityError:
        print("Error saving NetworkPost.")
        return JsonResponse({"error": "Post was not updated."}, status=404)


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")

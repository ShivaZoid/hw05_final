from typing import Any, Dict
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm

# Для кэширования index и follow_index
from django.views.decorators.cache import cache_page


ITEMS_PER_PAGE: int = 5


# НЕКОТОРЫЕ ТЕСТЫ МОГУТ НЕ ПРОЙТИ, НУЖНО ЗАКОММИТИТЬ @cache_page !!!
@cache_page(10 * 1)
def index(request):
    """Главная страница."""
    posts = Post.objects.select_related('author').order_by('-pub_date')
    template = 'posts/index.html'
    paginator = Paginator(posts, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title: str = 'Последние обновления на сайте'
    context: Dict[str, Any] = {
        'posts': posts,
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    """Страница сообщества."""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author').order_by('-pub_date')
    template = 'posts/group_list.html'
    paginator = Paginator(posts, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context: Dict[str, Any] = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    """Страница пользователя с его постами."""
    template = 'posts/profile.html'
    profile_user = get_object_or_404(User, username=username)
    posts = (profile_user.posts
             .select_related('author')
             .order_by('-pub_date')
             .filter(author__username=username)
             )
    posts_counter = posts.count()
    paginator = Paginator(posts, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    follow = profile_user.following.filter(user=request.user.id)
    context: Dict[str, Any] = {
        'posts': posts,
        'profile_user': profile_user,
        'posts_counter': posts_counter,
        'page_obj': page_obj,
        'following': follow,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    """Страница поста."""
    template = 'posts/post_detail.html'
    post_info = get_object_or_404(Post, pk=post_id)
    number_of_posts = post_info.author.posts.count()
    form = CommentForm(
        request.POST or None,
    )
    comments = Comment.objects.filter(post=post_info)
    context: Dict[str, Any] = {
        'post_info': post_info,
        'number_of_posts': number_of_posts,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    """Страница создания поста.

    Только зарегистрированные пользователи.
    """
    template = 'posts/create_post.html'
    if request.method == "POST":
        form = PostForm(
            request.POST,
            files=request.FILES or None,
        )

        if form.is_valid():
            form.save(commit=False).author_id = request.user.pk
            form.save()
            return redirect('posts:profile', username=request.user)
    else:
        form = PostForm()
    context: Dict[str, Any] = {
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    """Страница редактирования поста.

    Только зарегистрированные пользователи.
    """
    template = 'posts/create_post.html'
    user_name = request.user.get_username()
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'GET':
        form = PostForm(instance=post)
        if user_name != post.author.username:
            return HttpResponseForbidden()
    elif request.method == 'POST':
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post,
        )
        if form.is_valid():
            form.save()
        return redirect('posts:post_detail', post.id)
    context: Dict[str, Any] = {
        'post': post,
        'changed': True,
        'form': form,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    """ Добавление комментария под постом.

    Только зарегистрированные пользователи.
    """
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


# НЕКОТОРЫЕ ТЕСТЫ МОГУТ НЕ ПРОЙТИ, НУЖНО ЗАКОММИТИТЬ @cache_page !!!
@login_required
@cache_page(10 * 1)
def follow_index(request):
    """ Страница постов подписанных авторов.

    Только зарегистрированные пользователи.
    """
    template = 'posts/follow.html'
    title = 'Избранные посты'
    follower = Follow.objects.filter(user=request.user).values_list(
        'author_id', flat=True
    )
    posts = (Post.objects
             .select_related('author')
             .order_by('-pub_date')
             .filter(author_id__in=follower))
    paginator = Paginator(posts, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context: Dict[str, Any] = {
        'page_obj': page_obj,
        'title': title,
        'follower': follower,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.get(user=request.user, author=author).delete()
    return redirect('posts:profile', username)

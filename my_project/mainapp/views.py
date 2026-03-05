from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db.models import Q
from django.conf import settings
from django.core.paginator import Paginator
from .models import *
from .forms import *

class HomeView(ListView):
    model = Post
    template_name = 'mainapp/home.html'
    context_object_name = 'posts'
    paginate_by = getattr(settings, 'POSTS_PER_PAGE', 9)

    def get_queryset(self):
        return Post.objects.select_related(
            'author', 'author__profile'
        ).prefetch_related('likes', 'comments').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['liked_posts'] = set(
                Like.objects.filter(user=self.request.user).values_list('post_id', flat=True)
            )
        else:
            context['liked_posts'] = set()
        return context

class AllPostsView(ListView):
    model = Post
    template_name = 'mainapp/all_posts.html'
    context_object_name = 'posts'
    paginate_by = getattr(settings, 'POSTS_PER_PAGE', 9)

    def get_queryset(self):
        queryset = Post.objects.select_related(
            'author', 'author__profile'
        ).prefetch_related('likes', 'comments').order_by('-created_at')
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(author__username__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        if self.request.user.is_authenticated:
            context['liked_posts'] = set(
                Like.objects.filter(user=self.request.user).values_list('post_id', flat=True)
            )
        else:
            context['liked_posts'] = set()
        return context

class PostDetailView(View):
    template_name = 'mainapp/post_detail.html'

    def get(self, request, pk):
        post = get_object_or_404(
            Post.objects.select_related('author', 'author__profile'), pk=pk
        )
        comments_qs = post.comments.select_related('author', 'author__profile').order_by('created_at')
        paginator = Paginator(comments_qs, getattr(settings, 'COMMENTS_PER_PAGE', 10))
        comments_page = paginator.get_page(request.GET.get('page', 1))
        form = CommentForm()
        is_liked = False
        if request.user.is_authenticated:
            is_liked = Like.objects.filter(post=post, user=request.user).exists()
        return render(request, self.template_name, {
            'post': post,
            'comments': comments_page,
            'form': form,
            'is_liked': is_liked,
            'likes_count': post.get_likes_count(),
        })

    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        if not request.user.is_authenticated:
            messages.error(request, 'Войдите в систему, чтобы оставить комментарий.')
            return redirect('mainapp:login')
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, 'Комментарий добавлен!')
            return redirect(reverse('mainapp:post_detail', kwargs={'pk': pk}) + '#comments')
        comments_qs = post.comments.select_related('author', 'author__profile').order_by('created_at')
        paginator = Paginator(comments_qs, getattr(settings, 'COMMENTS_PER_PAGE', 10))
        comments_page = paginator.get_page(request.GET.get('page', 1))
        is_liked = Like.objects.filter(post=post, user=request.user).exists()
        return render(request, self.template_name, {
            'post': post,
            'comments': comments_page,
            'form': form,
            'is_liked': is_liked,
            'likes_count': post.get_likes_count(),
        })

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'mainapp/post_form.html'
    login_url = reverse_lazy('mainapp:login')

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Публикация успешно создана!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Создать публикацию'
        context['page_title'] = 'Новая публикация'
        return context


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'mainapp/post_form.html'
    login_url = reverse_lazy('mainapp:login')

    def test_func(self):
        return self.request.user == self.get_object().author or self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Публикация успешно обновлена!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Обновить публикацию'
        context['page_title'] = 'Редактирование публикации'
        return context

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'mainapp/post_confirm_delete.html'
    success_url = reverse_lazy('mainapp:all_posts')
    login_url = reverse_lazy('mainapp:login')

    def test_func(self):
        return self.request.user == self.get_object().author or self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Публикация удалена.')
        return super().form_valid(form)


class LikeToggleView(View):
    def post(self, request, pk):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'not authenticated'}, status=401)
        post = get_object_or_404(Post, pk=pk)
        like, created = Like.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
        return JsonResponse({'liked': liked, 'count': post.get_likes_count()})

class RegisterView(View):
    template_name = 'mainapp/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('mainapp:home')
        return render(request, self.template_name, {'form': RegisterForm()})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('mainapp:home')
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('mainapp:home')
        return render(request, self.template_name, {'form': form})

class UserLoginView(LoginView):
    template_name = 'mainapp/login.html'
    form_class = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        messages.success(self.request, f'Добро пожаловать, {self.request.user.username}!')
        return reverse_lazy('mainapp:home')


class UserLogoutView(LogoutView):
    next_page = reverse_lazy('mainapp:home')

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, 'Вы вышли из системы.')
        return super().dispatch(request, *args, **kwargs)

class UserProfileView(View):
    template_name = 'mainapp/profile.html'

    def get(self, request, username):
        from django.contrib.auth.models import User as AuthUser
        profile_user = get_object_or_404(AuthUser, username=username)
        posts = Post.objects.filter(author=profile_user).order_by('-created_at')
        paginator = Paginator(posts, 9)
        posts_page = paginator.get_page(request.GET.get('page', 1))
        try:
            profile = profile_user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=profile_user)
        return render(request, self.template_name, {
            'profile_user': profile_user,
            'profile': profile,
            'posts': posts_page,
            'posts_count': posts.count(),
        })


class ProfileEditView(LoginRequiredMixin, View):
    template_name = 'mainapp/profile_edit.html'
    login_url = reverse_lazy('mainapp:login')

    def get_profile(self, request):
        try:
            return request.user.profile
        except UserProfile.DoesNotExist:
            return UserProfile.objects.create(user=request.user)

    def get(self, request):
        profile = self.get_profile(request)
        return render(request, self.template_name, {'form': UserProfileForm(instance=profile), 'profile': profile})

    def post(self, request):
        profile = self.get_profile(request)
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлён!')
            return redirect('mainapp:profile', username=request.user.username)
        return render(request, self.template_name, {'form': form, 'profile': profile})
from django.test import TestCase, Client
from ..models import Group, Post, User
from http import HTTPStatus


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.checklist = [
            '/',
            f'/group/{cls.group.slug}/',
            f'/profile/{cls.user}/',
            f'/posts/{cls.post.id}/',
        ]
        cls.checklist_url_names = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_urls_exists(self):
        """Страницы: '/' '/group/<slug:slug>/' '/profile/<str:username>/'
        '/posts/<int:post_id>/'
        доступны любому пользователю."""
        for adress in self.checklist:
            with self.subTest(adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_redirect_anonymous(self):
        """Страница /create/ перенаправит анонимного пользователя на страницу
        логина."""
        response = self.guest_client.get('/create/', follow=True)

        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_post_edit_url_exists_author(self):
        """Страница /posts/<int:post_id>/edit/ доступна автору."""
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_404_page(self):
        """Несуществующая страница должна выдать ошибку."""
        response = self.guest_client.get('/world/')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in self.checklist_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

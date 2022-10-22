import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from http import HTTPStatus
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group, User


class PostFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='NoName')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый текст',
        )
        posts_count = Post.objects.count()
        last_post = Post.objects.order_by('id').last()
        form_data = {
            'text': 'Тестовый текст',
            'author': self.user,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse('posts:profile',
                              kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(str(last_post), self.post.text)
        self.assertEqual(last_post.author, self.post.author)

    def test_post_edit(self):
        """Валидная форма изменяет запись в Post."""
        self.post = Post.objects.create(
            author=self.user,
            text='Изменяем текст',
        )
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        last_post = Post.objects.order_by('id').last()
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Изменяем текст',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=({self.post.id})),
            data=form_data,
            follow=True,
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(str(last_post), self.post.text)
        self.assertEqual(last_post.author, self.post.author)

    def test_post_edit_not_create_guest_client(self):
        """Валидная форма не изменит запись в Post если неавторизован."""
        self.post = Post.objects.create(
            author=self.user,
            text='Изменяем текст',
        )
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        last_post = Post.objects.order_by('id').last()
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Изменяем текст',
            'group': self.group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', args=({self.post.id})),
            data=form_data,
            follow=True,
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/edit/')
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(str(last_post), self.post.text)
        self.assertEqual(last_post.author, self.post.author)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif', content=cls.small_gif, content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.templates = (
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': cls.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': cls.post.author}),

        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

    def test_image_page(self):
        """Картинка передается на страницу 'index', 'profile', 'group_list'."""

        for url in self.templates:
            with self.subTest(url):
                response = self.guest_client.get(url)
                obj = response.context['page_obj'][0]
                self.assertEqual(obj.image, self.post.image)

    def test_image_in_post_detail_page(self):
        """Картинка передается на страницу post_detail."""
        response = self.guest_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        obj = response.context["post_info"]

        self.assertEqual(obj.image, self.post.image)

    def test_image_in_page(self):
        """Проверяем что пост с картинкой создается в БД"""
        last_post = Post.objects.order_by('id').last()

        self.assertEqual(str(last_post), self.post.text)
        self.assertEqual(last_post.image, self.post.image)

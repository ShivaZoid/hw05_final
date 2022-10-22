from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from ..models import Post, Group, User, Comment, Follow


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

        cls.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': cls.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': cls.post.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': cls.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': cls.post.id}
            ): 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(template)
                self.assertTemplateUsed(response, reverse_name)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        post_response = response.context.get('post_info')

        self.assertEqual(post_response.text, self.post.text)
        self.assertEqual(post_response.author, self.post.author)
        self.assertEqual(post_response.group, self.post.group)

    def test_create_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_check_group_in_pages(self):
        """Проверяем создание поста с выбранной группой"""
        form_fields = {
            reverse('posts:index'): (Post.objects
                                     .filter(group=self.post.group)
                                     .first()
                                     ),
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): Post.objects.filter(group=self.post.group).first(),
            reverse(
                'posts:profile', kwargs={'username': self.post.author}
            ): Post.objects.filter(group=self.post.group).first(),
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context['page_obj']
                self.assertIn(expected, form_field)

    def test_check_group_not_in_mistake_group_list_page(self):
        """Проверяем чтобы созданный пост с группой не попал в группу, для
        которой не был предназначен."""
        form_fields = {
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): Post.objects.exclude(group=self.post.group),
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context['page_obj']
                self.assertNotIn(expected, form_field)

    def test_comment_correct_context(self):
        """Валидная форма Комментария создает запись в Post."""
        self.comment = Comment.objects.create(
            author=self.user,
            text='Тестовый коммент',
        )
        last_comment = Comment.objects.order_by('id').last()
        comments_count = Comment.objects.count()
        form_data = {'text': 'Тестовый коммент'}
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )

        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(str(last_comment), self.comment.text)
        self.assertEqual(last_comment.author, self.comment.author)

    def test_cache(self):
        """Проверка кеша."""
        client = self.guest_client.get(reverse('posts:index'))
        response_1 = client
        post_cache_1 = response_1.content

        Post.objects.get(id=1).delete()
        response_2 = client
        post_cache_2 = response_2.content
        self.assertEqual(post_cache_1, post_cache_2)

    def test_follow_page(self):
        """Проверка подписки."""
        # страница подписок пуста
        response_1 = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response_1.context['page_obj']), 0)

        # подписка на автора
        Follow.objects.get_or_create(user=self.user, author=self.post.author)
        response_2 = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response_2.context['page_obj']), 1)
        # проверка подписки у фоловера
        self.assertIn(self.post, response_2.context['page_obj'])

        # пост не появиляется в избранных у другого юзера
        user_wrong = User.objects.create(username='NoName_2')
        self.authorized_client.force_login(user_wrong)
        response_3 = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post, response_3.context['page_obj'])

        # отписка от автора поста
        Follow.objects.all().delete()
        response_4 = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response_4.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):

    TEST_ALL_POSTS: int = 8
    TEST_FIRST_PAGE_POSTS: int = 5
    TEST_SECOND_PAGE_POSTS: int = 3

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.author = User.objects.create_user(username='NoName')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='test-slug'
        )
        cls.templates_pages_names_2 = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': cls.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': cls.author}
            ): 'posts/profile.html',
        }

    def setUp(self):
        for post_temp in range(self.TEST_ALL_POSTS):
            Post.objects.create(
                text=f'text{post_temp}',
                author=self.author,
                group=self.group,
            )

    def test_first_page_contains_eight_records(self):
        """Провека пагинации, первая страница."""

        for template, reverse_name in self.templates_pages_names_2.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(template)
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.TEST_FIRST_PAGE_POSTS
                )

    def test_second_page_contains_three_records(self):
        """Провека пагинации вторая страница."""

        for template, reverse_name in self.templates_pages_names_2.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(template + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.TEST_SECOND_PAGE_POSTS
                )

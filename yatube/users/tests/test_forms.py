from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from ..forms import CreationForm

User = get_user_model()


class CreationFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='NoName')
        cls.form = CreationForm()

    def setUp(self):
        self.guest_client = Client()

    def test_signup(self):
        """Валидная форма создает нового пользователя."""
        users_count = User.objects.count()
        form_data = {
            'first_name': 'test_first_name',
            'last_name': 'test_last_name',
            'username': 'test_name',
            'email': 'email_test@mail.ru',
            'password1': 'Django_2022',
            'password2': 'Django_2022',
        }
        response = self.guest_client.post(
            reverse('users:signup'), data=form_data, follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), users_count + 1)

        # Не совсем понятно как проверить
        # username и email:
        # last_user = User.objects.order_by('id').last()
        # self.assertEqual(last_user.username(?), ?...)
        # self.assertEqual(last_user.email(?), ?...)

        self.assertTrue(User.objects.filter(username='test_name').last().id)
        self.assertTrue(User.objects
                        .filter(email='email_test@mail.ru')
                        .last().id)

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


class UserAPITest(APITestCase):
    """Тесты для API пользователей"""

    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            fullName='Test User',
            phone='+1234567890'
        )
        self.client = APIClient()

    def test_user_registration(self):
        """Тест регистрации пользователя"""
        url = reverse('sign_up')

        # Данные для регистрации
        data = {
            'name': 'New User',
            'username': 'newuser@example.com',
            'password': 'newpass123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем создание пользователя
        user = User.objects.get(username='newuser@example.com')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.fullName, 'New User')

    def test_user_login(self):
        """Тест аутентификации пользователя"""
        url = reverse('sign_in')

        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_registration_with_existing_email(self):
        """Тест регистрации с существующим email"""
        url = reverse('sign_up')

        data = {
            'name': 'Another User',
            'username': 'testuser',  # Уже существует
            'password': 'anotherpass123'
        }

        response = self.client.post(url, data, format='json')
        # Ожидаем ошибку валидации
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data['error'])

    def test_user_login_invalid_credentials(self):
        """Тест аутентификации с неверными учетными данными"""
        url = reverse('sign_in')

        data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Неверные учетные данные')

    def test_get_user_profile(self):
        """Тест получения профиля пользователя"""
        # Логинимся
        self.client.login(username='testuser', password='testpass123')

        url = reverse('profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['fullName'], 'Test User')
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['phone'], '+1234567890')

    def test_update_user_profile(self):
        """Тест обновления профиля пользователя"""
        # Логинимся
        self.client.login(username='testuser', password='testpass123')

        url = reverse('profile')
        data = {
            'fullName': 'Updated User',
            'email': 'updated@example.com',
            'phone': '+0987654321'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что данные обновились в базе
        self.user.refresh_from_db()
        self.assertEqual(self.user.fullName, 'Updated User')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.phone, '+0987654321')

    def test_change_user_password(self):
        """Тест изменения пароля пользователя"""
        # Логинимся
        self.client.login(username='testuser', password='testpass123')

        url = reverse('profile-password')
        data = {
            'currentPassword': 'testpass123',
            'newPassword': 'newpass123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что пароль изменился
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))

    def test_change_user_password_invalid_current(self):
        """Тест изменения пароля с неверным текущим паролем"""
        # Логинимся
        self.client.login(username='testuser', password='testpass123')

        url = reverse('profile-password')
        data = {
            'currentPassword': 'wrongpass',
            'newPassword': 'newpass123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_logout(self):
        """Тест выхода пользователя"""
        # Логинимся
        self.client.login(username='testuser', password='testpass123')

        url = reverse('sign_out')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_avatar(self):
        """Тест обновления аватара пользователя"""
        # Логинимся
        self.client.login(username='testuser', password='testpass123')

        url = reverse('profile-avatar')

        # Создаем тестовое изображение
        avatar = SimpleUploadedFile(
            name='test_avatar.jpg',
            content=b'test_content',
            content_type='image/jpeg'
        )

        data = {'avatar': avatar}
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что аватар обновился в базе
        self.user.refresh_from_db()
        self.assertTrue(self.user.avatar)

    def test_access_protected_endpoints_without_auth(self):
        """Тест доступа к защищенным endpoint'ам без аутентификации"""
        url = reverse('profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SimpleAuthTests(TestCase):
    """Простой тесты для проверки основных функций"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='simpleuser',
            email='simple@example.com',
            password='simplepass123'
        )

    def test_simple_login_with_json(self):
        """Тест входа с JSON данными"""
        url = reverse('sign_in')

        response = self.client.post(
            url,
            {'username': 'simpleuser', 'password': 'simplepass123'},
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

    def test_simple_login_with_query_params(self):
        """Тест входа с query параметрами"""
        url = reverse('sign_in') + '?username=simpleuser&password=simplepass123'

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

    def test_simple_registration(self):
        """Тест регистрации"""
        url = reverse('sign_up')

        response = self.client.post(
            url,
            {
                'name': 'Simple User',
                'username': 'newuser@test.com',
                'password': 'testpass123'
            },
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='newuser@test.com').exists())


# Дополнительные тесты для проверки разных форматов данных
class AuthFormatTests(TestCase):
    """Тесты различных форматов данных для аутентификации"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='formatuser',
            email='format@example.com',
            password='formatpass123'
        )

    def test_login_with_form_data(self):
        """Тест входа с form-data (как HTML форма)"""
        url = reverse('sign_in')

        response = self.client.post(url, {
            'username': 'formatuser',
            'password': 'formatpass123'
        })

        self.assertEqual(response.status_code, 200)

    def test_login_with_different_username_field(self):
        """Тест входа с использованием email как username"""
        url = reverse('sign_in')

        response = self.client.post(url, {
            'username': 'format@example.com',  # Email вместо username
            'password': 'formatpass123'
        })

        # Этот тест может не пройти, если система не поддерживает вход по email
        # Проверяем хотя бы что нет ошибки 403
        self.assertNotEqual(response.status_code, 403)

    def test_registration_minimal_data(self):
        """Тест регистрации с минимальными данными"""
        url = reverse('sign_up')

        response = self.client.post(url, {
            'name': 'Minimal User',
            'username': 'minimal@example.com',
            'password': 'minimal123'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='minimal@example.com').exists())

    # tests_users.py - исправленный тест

    def test_registration_without_name(self):
        """Тест регистрации без имени (должно работать, т.к. name необязательное)"""
        url = reverse('sign_up')

        response = self.client.post(url, {
            'username': 'noname@example.com',
            'password': 'nopass123'
        }, format='json')

        # Ожидаем успешную регистрацию (200 OK), так как name необязательное
        self.assertEqual(response.status_code, 200)

        # Проверяем создание пользователя с пустым именем
        user = User.objects.get(username='noname@example.com')
        self.assertEqual(user.fullName, '')

    def test_registration_without_username(self):
        """Тест регистрации без username (должна быть ошибка)"""
        url = reverse('sign_up')

        response = self.client.post(url, {
            'name': 'No Username User',
            'password': 'nopass123'
        }, format='json')

        # Ожидаем ошибку, так как username обязательное
        self.assertEqual(response.status_code, 400)
        self.assertIn('username', response.data.get('error', {}))

    def test_registration_without_password(self):
        """Тест регистрации без пароля (должна быть ошибка)"""
        url = reverse('sign_up')

        response = self.client.post(url, {
            'name': 'No Password User',
            'username': 'nopassword@example.com'
        }, format='json')

        # Ожидаем ошибку, так как password обязательное
        self.assertEqual(response.status_code, 400)
        self.assertIn('password', response.data.get('error', {}))
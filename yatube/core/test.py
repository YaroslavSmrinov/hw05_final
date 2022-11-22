from django.test import Client, TestCase


class ViewTestClass(TestCase):
    def setUp(self):
        self.client = Client()

    def test_error_page(self):
        """Тестируем использование кастомного шаблона и статус 404"""
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')

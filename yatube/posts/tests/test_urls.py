from http import HTTPStatus as status

from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Comment, Group, Post, User


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.guest = Client()
        cls.authed = Client()
        cls.authed.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='TEST COMMENT',
        )

    def test_free_access_pages(self):
        """Тестируем общедоступные URL"""
        public_urls = (
            reverse('posts:index'),
            reverse('posts:group_list', args=[self.group.slug]),
            reverse('posts:profile', args=[self.user]),
            reverse('posts:post_detail', args=[self.post.pk]),
        )

        for url in public_urls:
            with self.subTest(url=url):
                resp = self.guest.get(url)
                self.assertEqual(resp.status_code, status.OK)
        resp = self.guest.get('/unexisting_page/')
        self.assertEqual(resp.status_code, status.NOT_FOUND)

    def test_only_auth_user(self):
        """Тестируем перенаправление анонима на логин"""
        create_url = '/create/'
        resp = self.guest.get(create_url)
        redirect_to = reverse('users:login') + '?next=' + create_url
        self.assertRedirects(resp, redirect_to)
        edit_url = f'/posts/{self.post.pk}/edit/'
        resp = self.guest.get(edit_url)
        redirect_to = reverse('users:login') + '?next=' + edit_url
        self.assertRedirects(resp, redirect_to)

    def test_post_edit_only_for_author(self):
        """Тестируем возможность редактировать пост только автору"""
        url = f'/posts/{self.post.pk}/edit/'
        resp = self.authed.get(url)
        self.assertIs(resp.status_code, status.OK.value)

    def test_leave_comment(self):
        """Комментарий может оставить только авторизованный пользователь"""
        url = reverse('posts:add_comment', kwargs={'post_id': self.post.id})
        resp = self.authed.get(url)
        redirect_to = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        )
        self.assertRedirects(resp, redirect_to)


class TemplatesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.guest = Client()
        cls.authed = Client()
        cls.authed.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        cache.clear()

    def test_templates_at_correct_address(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_urls = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                args=[self.group.slug]
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                args=[self.user]
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                args=[self.post.pk]
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                args=[self.post.pk]
            ): 'posts/create_post.html',
        }
        for address, template in templates_urls.items():
            with self.subTest(address=address):
                response = self.authed.get(address)
                self.assertTemplateUsed(response, template)

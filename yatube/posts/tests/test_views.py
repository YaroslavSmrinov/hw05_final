import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Comment, Follow, Group, Post, User
import yatube.settings as settings

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMALL_GIF = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test_slug',
            description='test description',
        )
        cls.another_group = Group.objects.create(
            title='Test another group',
            slug='test_another_slug',
            description='test another description',
        )
        cls.UPLOADED = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test text',
            group=cls.group,
            image=cls.UPLOADED,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='TEST COMMENT',
        )
        cls.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}):
                'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': cls.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': cls.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': cls.post.id}
            ): 'posts/create_post.html',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def check_context(self, post_object):
        self.assertEqual(
            post_object.author.username,
            self.post.author.username
        )
        self.assertEqual(post_object.text, self.post.text)
        self.assertEqual(post_object.group, self.post.group)
        self.assertEqual(post_object.image.name, 'posts/small.gif')

    def test_pages_uses_correct_template(self):
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.check_context(first_object)

    def test_group_posts_page_show_correct_context(self):
        response = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test_slug'},
        ))
        group = response.context['group']
        first_object = response.context['page_obj'][0]
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.description, self.group.description)
        self.check_context(first_object)

    def test_profile_page_show_correct_context(self):
        response = self.guest_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user.username},
        ))
        first_object = response.context['page_obj'][0]
        author = response.context['author']
        self.check_context(first_object)
        self.assertEqual(author.username, self.user.username)

    def test_post_detail_page_show_correct_context(self):
        response = self.guest_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id},
        ))
        post = response.context['post']
        self.check_context(post)

    def test_post_edit_page_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.id},
        ))
        self.assertTrue(response.context['is_edit'])

    def test_post_doesnt_go_to_another_group(self):
        response = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test_another_slug'},
        ))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_comment_view(self):
        """Комментарий появляется на странице поста"""
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        ))
        comments = response.context['comments']
        self.assertTrue(
            comments.filter(text=self.comment).exists(),
            'Комментарий не виден на странице поста'
        )


class PaginatorViewTests(TestCase):
    POSTS_ON_SECOND_PAGE = 3

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test_slug',
            description='test description',
        )
        posts = []
        for item in range(settings.POSTS_PER_PAGE + cls.POSTS_ON_SECOND_PAGE):
            text = f'Text №{item}'
            posts.append(Post(
                author=cls.user,
                text=text,
                group=cls.group,
            ))
        Post.objects.bulk_create(posts)
        cls.posts_on_page = {
            reverse('posts:index'): (
                settings.POSTS_PER_PAGE,
                cls.POSTS_ON_SECOND_PAGE
            ),
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}): (
                settings.POSTS_PER_PAGE,
                cls.POSTS_ON_SECOND_PAGE
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PaginatorViewTests.user.username}
            ): (settings.POSTS_PER_PAGE, cls.POSTS_ON_SECOND_PAGE),
        }

    def setUp(self):
        cache.clear()

    def test_paginator_first_page_all_templates(self):
        for reverse_name, pages in self.posts_on_page.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), pages[0])

    def test_paginator_second_page_all_templates(self):
        for reverse_name, pages in self.posts_on_page.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), pages[1])


class CacheIndexTest(TestCase):

    def test_index_cache(self):
        response = self.client.get(reverse('posts:index'))
        first = response.content
        self.user = User.objects.create_user(username='auth')
        Post.objects.create(
            author=self.user,
            text='Test text',
        )
        response = self.client.get(reverse('posts:index'))
        second = response.content
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        third = response.content
        self.assertEqual(first, second)
        self.assertNotEqual(first, third)


class FollowViewTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user_follower')
        cls.follower = Client()
        cls.follower.force_login(cls.user)
        cls.post_author = User.objects.create_user(username='blogger')
        cls.post_author_logged_in = Client()
        cls.post_author_logged_in.force_login(cls.post_author)
        cls.post = Post.objects.create(
            author=cls.post_author,
            text='Test text'
        )

    def setUp(self):
        self.follower.post(reverse('posts:profile_follow', kwargs={
            'username': self.post_author.username
        }))

    def test_subscribe_and_unsubscribe_funk_able(self):
        """
        Авторизованный юзер может подписываться на других и отписываться.
        """
        follow = Follow.objects.get(user=self.user, author=self.post_author)
        self.assertIsNotNone(follow, 'Подписка не произошла')
        self.assertEqual(
            follow.author,
            self.post_author,
            'Подписка идёт не на того пользователя, на которого нужно. '
        )
        self.follower.post(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.post_author.username}
        )
        )
        follow = Follow.objects.all()
        self.assertEqual(
            len(follow),
            0,
            'Отписка не произошла.'
        )

    def test_follow_index(self):
        """
        Проверяем, что после подписки в ленте появляется пост.
        """
        followers_news_feed = self.follower.get(reverse(
            'posts:follow_index'
        )).context['page_obj']
        self.assertEqual(
            followers_news_feed[0],
            self.post,
            'Пост пост не появился в ленте подписчика.'
        )
        another_user_news_feed = self.post_author_logged_in.get(reverse(
            'posts:follow_index'
        )).context['page_obj']
        self.assertEqual(
            len(another_user_news_feed),
            0,
            'В ленте пользователя без подписки появился пост. Неожиданно.',
        )

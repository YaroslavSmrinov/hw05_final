import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User

CREATE_URL = 'posts:post_create'
EDIT_URL = 'posts:post_edit'

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
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title=('Тестовая группа'),
            slug='test_slug',
            description='Тестовое описание'
        )

        cls.post = Post.objects.create(
            group=PostCreateFormTests.group,
            text="Тестовый текст",
            author=cls.user,
        )
        cls.UPLOADED = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.RELOADED = SimpleUploadedFile(
            name='my.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_form_create(self):
        """Проверка создания нового поста"""
        form_data = {
            'group': self.group.id,
            'text': 'Новый пост',
            'image': self.UPLOADED,
        }
        resp = self.authorized_client.post(
            reverse(CREATE_URL),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            resp,
            reverse('posts:profile', args=[self.user])
        )
        last_post = Post.objects.all().first()
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.group.pk, form_data['group'])
        self.assertEqual(last_post.author, self.user)
        self.assertEqual(last_post.image.name, 'posts/small.gif')

    def test_form_edit(self):
        """Проверка возможности редактирования поста"""
        form_data = {
            'group': self.group.id,
            'text': 'Отредактированный пост',
            'image': self.RELOADED,
        }
        resp = self.authorized_client.post(
            reverse(EDIT_URL, args=[self.post.id]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            resp,
            reverse('posts:post_detail', args=[self.post.pk])
        )
        last_post = Post.objects.all().first()
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.group.pk, form_data['group'])
        self.assertEqual(last_post.author, self.user)
        self.assertEqual(last_post.image.name, 'posts/my.gif')

from rest_framework.routers import DefaultRouter
from .views import AuthorViewSet, GenreViewSet, PublisherViewSet, BookViewSet

router = DefaultRouter()

router.register(r'author', AuthorViewSet, basename='author')
router.register(r'genre', GenreViewSet, basename='genre')
router.register(r'publisher', PublisherViewSet, basename='publisher')
router.register(r'book', BookViewSet, basename='book')

urlpatterns = router.urls

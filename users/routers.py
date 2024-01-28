from rest_framework.routers import DefaultRouter
from .views import UserViewSet, PasswordRecoveryViewSet

router = DefaultRouter()

router.register(r'users', UserViewSet, basename='users')
router.register(r'password-recovery', PasswordRecoveryViewSet,
                basename='password-recovery')

urlpatterns = router.urls

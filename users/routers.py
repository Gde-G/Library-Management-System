from rest_framework.routers import SimpleRouter
from .views import UserViewSet, PasswordRecoveryViewSet

router = SimpleRouter()

router.register(r'users', UserViewSet, basename='users')
router.register(r'password-recovery', PasswordRecoveryViewSet,
                basename='password-recovery')

urlpatterns = router.urls

from rest_framework.routers import SimpleRouter
from .views import (
    FavoriteViewSet, ReservationViewSet, PenaltyViewSet,
    StrikeViewSet, NotificationViewSet, CreditViewSet
)

router = SimpleRouter()

router.register(r'fav', FavoriteViewSet, basename='fav')
router.register(r'reservation', ReservationViewSet, basename='reservation')
router.register(r'penalty', PenaltyViewSet, basename='penalty')
router.register(r'strikes', StrikeViewSet, basename='strikes')
router.register(r'credits', CreditViewSet, basename='credits')
router.register(r'notification', NotificationViewSet, basename='notification')

urlpatterns = router.urls

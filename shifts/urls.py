# shifts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BranchViewSet, RoomViewSet, ShiftViewSet, EmployeeViewSet, ScheduleViewSet, CreateEmployeeView

router = DefaultRouter()
router.register(r'branches', BranchViewSet)
router.register(r'rooms', RoomViewSet)
router.register(r'shifts', ShiftViewSet)
router.register(r'employees', EmployeeViewSet)
router.register(r'schedules', ScheduleViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('create-employee/', CreateEmployeeView.as_view(), name='create-employee'),
]

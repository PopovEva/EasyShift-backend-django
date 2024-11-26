# shifts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BranchViewSet, RoomViewSet, RoomsByBranchView, ShiftViewSet, EmployeeViewSet, ScheduleViewSet, CreateEmployeeView, CreateScheduleView

router = DefaultRouter()
router.register(r'branches', BranchViewSet)
router.register(r'rooms', RoomViewSet)
router.register(r'shifts', ShiftViewSet)
router.register(r'employees', EmployeeViewSet)
router.register(r'schedules', ScheduleViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('create-employee/', CreateEmployeeView.as_view(), name='create-employee'),
    path('create-schedule/', CreateScheduleView.as_view(http_method_names=['post']), name='create-schedule'),
    path('branches/<int:branch_id>/rooms/', RoomsByBranchView.as_view(), name='rooms-by-branch'),
]

# shifts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminNotificationsView, AvailableWeeksView, BranchViewSet, EmployeeNotificationsView, GetScheduleView, RoomViewSet, RoomsByBranchView, ShiftViewSet, EmployeeViewSet, ScheduleViewSet, CreateEmployeeView, CreateScheduleView, SaveScheduleView, UpdateScheduleView, refresh_token, UpdateUserView

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
    path('get-schedule/<int:branch_id>/<str:status>/', GetScheduleView.as_view(), name='get-schedule'),
    path('save-schedule/', SaveScheduleView.as_view(), name='save-schedule'),
    path('update-schedule/', UpdateScheduleView.as_view(), name='update-schedule'),
    path('available-weeks/<int:branch_id>/', AvailableWeeksView.as_view(), name='available-weeks'),
    path('employee-notifications/', EmployeeNotificationsView.as_view(), name='employee-notifications'),
    path('admin-notifications/', AdminNotificationsView.as_view(), name='admin-notifications'),
    path('token/refresh/', refresh_token, name='token-refresh'),
    path('update-user/', UpdateUserView.as_view(), name='update-user'),
]

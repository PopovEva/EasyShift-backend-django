from rest_framework import viewsets
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Branch, Room, Shift, Employee, Schedule
from .serializers import BranchSerializer, RoomSerializer, ShiftSerializer, EmployeeSerializer, ScheduleSerializer, UserEmployeeSerializer
from .permissions import IsAdminOrReadOnly, IsWorkerOrAdmin

class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAdminOrReadOnly, IsAuthenticated]  # Только админ может изменять данные


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAdminOrReadOnly, IsAuthenticated]  # Только админ может изменять данные


class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [IsAdminOrReadOnly, IsAuthenticated]  # Только админ может изменять данные


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAdminOrReadOnly, IsAuthenticated]  # Только админ может изменять данные


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsWorkerOrAdmin, IsAuthenticated]  # Доступ для работников и админов


class CreateEmployeeView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]  # Только админ может создавать новых сотрудников

    def post(self, request, *args, **kwargs):
        serializer = UserEmployeeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        employee = Employee.objects.get(user=user)
        
        # Получаем группы, к которым принадлежит пользователь (в данном случае будет только одна)
        groups = user.groups.all()
        group_name = groups[0].name if groups else "No Group"
        data = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': employee.phone_number,
            'branch': employee.branch.id,
            'notes': employee.notes,
            'group': group_name
        }
        return Response(data)

from rest_framework import viewsets
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Branch, Room, Shift, Employee, Schedule
from .serializers import BranchSerializer, RoomSerializer, ShiftSerializer, EmployeeSerializer, ScheduleSerializer, UserEmployeeSerializer
from .permissions import IsAdminOrReadOnly, IsWorkerOrAdmin
from django.contrib.auth.models import Group


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]  # Только админ может изменять данные


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]  # Только админ может изменять данные


class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]  # Только админ может изменять данные


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]  # Только админ может изменять данные


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]  # Доступ для работников и админов


class CreateEmployeeView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]  # Только админ может создавать новых сотрудников

    def post(self, request, *args, **kwargs):
        serializer = UserEmployeeSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Добавляем пользователя в нужную группу
            group_name = request.data.get('group', 'Worker')  # По умолчанию назначаем "Worker"
            try:
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
            except Group.DoesNotExist:
                return Response({'error': f'Group "{group_name}" does not exist'}, status=status.HTTP_400_BAD_REQUEST)

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
    
class CreateScheduleView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]  # Только админ может создавать расписание

    def post(self, request):
        branch_id = request.data.get('branch_id')
        shifts_data = request.data.get('shifts')

        try:
            branch = Branch.objects.get(pk=branch_id)

            for shift_data in shifts_data:
                room_id = shift_data.get('room_id')
                shift_type = shift_data.get('shift_type')
                date = shift_data.get('date')
                start_time = shift_data.get('start_time')
                end_time = shift_data.get('end_time')
                employee_id = shift_data.get('employee_id')

                try:
                    room = Room.objects.get(pk=room_id, branch=branch)
                    shift = Shift.objects.create(
                        room=room,
                        shift_type=shift_type,
                        date=date,
                        start_time=start_time,
                        end_time=end_time,
                        employee_id=employee_id,
                    )
                    shift.save()

                except Room.DoesNotExist:
                    return Response({'error': f'Room with id {room_id} does not exist in branch {branch.name}'}, status=status.HTTP_400_BAD_REQUEST)

            return Response({'status': 'Schedule successfully created'}, status=status.HTTP_201_CREATED)

        except Branch.DoesNotExist:
            return Response({'error': 'Branch not found'}, status=status.HTTP_404_NOT_FOUND)    

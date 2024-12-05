from rest_framework import viewsets
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Branch, Room, Shift, Employee, Schedule
from .serializers import BranchSerializer, RoomSerializer, ShiftSerializer, EmployeeSerializer, ScheduleSerializer, UserEmployeeSerializer
from .permissions import IsAdminOrReadOnly, IsWorkerOrAdmin
from django.contrib.auth.models import Group, User
from django.utils.dateparse import parse_date


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
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def post(self, request):
        branch_id = request.data.get('branch_id')
        start_date = request.data.get('start_date')
        schedule_data = request.data.get('schedule')

        if not branch_id or not start_date or not schedule_data:
            return Response({'error': 'Branch ID, start date, and schedule data are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            branch = Branch.objects.get(pk=branch_id)
        except Branch.DoesNotExist:
            return Response({'error': 'Branch not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            start_date = parse_date(start_date)
            if not start_date:
                return Response({'error': 'Invalid start date format.'}, status=status.HTTP_400_BAD_REQUEST)

            # Проходим по расписанию
            for day_data in schedule_data:
                day_of_week = day_data.get('day')  # Например, ראשון
                for shift_data in day_data.get('shifts', []):
                    shift_type = shift_data.get('shift')  # Например, בוקר
                    for room_data in shift_data.get('rooms', []):
                        room_name = room_data.get('room')
                        employee_id = room_data.get('employee', None)

                        try:
                            room = Room.objects.get(name=room_name, branch=branch)
                        except Room.DoesNotExist:
                            return Response(
                                {'error': f'Room "{room_name}" does not exist in branch "{branch.name}".'},
                                status=status.HTTP_400_BAD_REQUEST
                            )

                        employee = None
                        if employee_id:
                            try:
                                employee = Employee.objects.get(pk=employee_id)
                            except Employee.DoesNotExist:
                                return Response(
                                    {'error': f'Employee with ID {employee_id} does not exist.'},
                                    status=status.HTTP_400_BAD_REQUEST
                                )

                        # Создаём смену
                        shift, created = Shift.objects.get_or_create(
                            room=room,
                            shift_type=shift_type,
                            day_of_week=day_of_week,
                            date=start_date,
                            start_time=None,  # Может быть заполнено позже
                            end_time=None
                        )

                        # Создаём запись расписания
                        Schedule.objects.create(
                            week_start_date=start_date,
                            shift=shift,
                            employee=employee,
                            branch=branch,
                            status=Schedule.DRAFT  # Отмечаем, что это шаблон
                        )

            return Response({'status': 'Schedule successfully created'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   
        
class SaveScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        branch_id = request.data.get('branch_id')
        week_start_date = request.data.get('start_date')
        schedule_data = request.data.get('schedule')
        if not branch_id:
            return Response({"error": "Branch ID is required"}, status=400)
        try:
            branch = Branch.objects.get(pk=branch_id)
            for day in schedule_data:
                for shift in day['shifts']:
                    for room in shift['rooms']:
                        Schedule.objects.update_or_create(
                            week_start_date=week_start_date,
                            branch=branch,
                            shift=Shift.objects.get(room__name=room['room'], shift_type=shift['shift']),
                            defaults={
                                'employee': room.get('employee'),
                                'status': request.data.get('status', Schedule.DRAFT),
                            }
                        )
            return Response({"status": "Schedule saved successfully"})
        except Branch.DoesNotExist:
            return Response({"error": "Branch not found"}, status=404)         

class GetScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, branch_id, status):
        schedules = Schedule.objects.filter(
            shift__room__branch_id=branch_id,  # Ссылка через ForeignKey на branch
            status=status
        ).select_related('shift', 'shift__room', 'employee')  # Предзагрузка для оптимизации

        data = []
        for schedule in schedules:
            data.append({
                "week_start_date": schedule.week_start_date,
                "shift_details": {
                    "shift_type": schedule.shift.shift_type,
                    "room": schedule.shift.room.name,
                },
                "day": schedule.shift.day_of_week,
                "employee_name": schedule.employee.user.get_full_name() if schedule.employee else None,
            })

        return Response(data)


class RoomsByBranchView(generics.ListAPIView):
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        branch_id = self.kwargs['branch_id']
        return Room.objects.filter(branch_id=branch_id)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
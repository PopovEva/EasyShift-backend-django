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
import logging
from rest_framework.exceptions import APIException

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
        user = request.user
        logger.info(f"User {user.username} initiated employee creation.")
        
        serializer = UserEmployeeSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Добавляем пользователя в нужную группу
            group_name = request.data.get('group', 'Worker')  # По умолчанию назначаем "Worker"
            try:
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
                logger.info(f"User {request.user.username} successfully created employee {user.username} in group {group_name}.")
            except Group.DoesNotExist:
                logger.error(f"User {request.user.username} tried to assign employee to a non-existent group: {group_name}.")
                return Response({'error': f'Group "{group_name}" does not exist'}, status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"Employee creation failed by {request.user.username}: {serializer.errors}")
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

logger = logging.getLogger('system_logger')
    
class CreateScheduleView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def post(self, request):
        user = request.user
        logger.info(f"User {user.username} initiated schedule creation")
              
        branch_id = request.data.get('branch_id')
        start_date = request.data.get('start_date')
        schedule_data = request.data.get('schedule')

        if not branch_id or not start_date or not schedule_data:
            logger.warning(f"Invalid request by {user.username}: {request.data}")
            return Response({'error': 'Branch ID, start date, and schedule data are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            branch = Branch.objects.get(pk=branch_id)
        except Branch.DoesNotExist:
            logger.error(f"Branch not found: {branch_id}")
            return Response({'error': 'Branch not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            start_date = parse_date(start_date)
            if not start_date:
                logger.error("Invalid date format provided")
                return Response({'error': 'Invalid start date format.'}, status=status.HTTP_400_BAD_REQUEST)
            # Счетчик успешных созданий
            created_shifts_count = 0

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
                            logger.error(f"Room not found: {room_name} in branch {branch.name}")
                            return Response(
                                {'error': f'Room "{room_name}" does not exist in branch "{branch.name}".'},
                                status=status.HTTP_400_BAD_REQUEST
                            )

                        employee = None
                        if employee_id:
                            try:
                                employee = Employee.objects.get(pk=employee_id)
                            except Employee.DoesNotExist:
                                logger.error(f"Employee not found: {employee_id}")
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
                        created_shifts_count += 1
                        
            logger.info(f"User {user.username} successfully created a schedule with {created_shifts_count} shifts for branch {branch.name}")
            return Response({'status': 'Schedule successfully created'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.exception(f"Error while creating schedule: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   
        
class SaveScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        branch_id = request.data.get('branch_id')
        week_start_date = request.data.get('start_date')
        schedule_data = request.data.get('schedule')
        user = request.user
        
        if not branch_id:
            logger.warning(f"User {user.username} tried to save schedule without branch_id.")
            return Response({"error": "Branch ID is required"}, status=400)
        try:
            branch = Branch.objects.get(pk=branch_id)
            for day in schedule_data:
                for shift in day['shifts']:
                    for room in shift['rooms']:
                        shift_instance = Shift.objects.get(
                            room__name=room['room'], 
                            shift_type=shift['shift']
                        )
                        # Обновляем или создаем расписание
                        schedule, created = Schedule.objects.update_or_create(
                            week_start_date=week_start_date,
                            branch=branch,
                            shift=shift_instance,
                            defaults={
                                'employee': room.get('employee'),
                                'status': request.data.get('status', Schedule.DRAFT),
                            }
                        )
                        if created:
                            logger.info(f"User {user.username} created a new schedule for {shift_instance}.")
                        else:
                            logger.info(f"User {user.username} updated schedule for {shift_instance}.")
            
            logger.info(f"User {user.username} successfully saved schedule for branch {branch.name}.")
            return Response({"status": "Schedule saved successfully"})
        except Branch.DoesNotExist:
            logger.exception(f"User {user.username} tried to save schedule for a non-existent branch: {branch_id}")
            return Response({"error": "Branch not found"}, status=404)
        except Exception as e:
            logger.exception(f"User {user.username} encountered an error while saving schedule: {str(e)}")
            return Response({"error": str(e)}, status=500)         

class GetScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, branch_id, status):
        # Получаем параметр week_start_date из запроса
        week_start_date = request.query_params.get('week_start_date', None)
        # Фильтрация по филиалу, статусу и дате начала недели
        schedules = Schedule.objects.filter(
            shift__room__branch_id=branch_id,  # Ссылка через ForeignKey на branch
            status=status
        ).select_related('shift', 'shift__room', 'employee')  # Предзагрузка для оптимизации
        
        if week_start_date:
            schedules = schedules.filter(week_start_date=week_start_date)  # Фильтруем по неделе
            
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
    
class UpdateScheduleView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        logger.info(f"User {user.username} initiated schedule update")
        branch_id = request.data.get('branch_id')
        updated_schedules = request.data.get('schedules')
        new_status = request.data.get('status')  # Новый статус расписания (DRAFT/APPROVED)
        
        if not branch_id or not updated_schedules:
            logger.warning(f"Invalid update request by {user.username}: {request.data}")
            return Response(
                {"error": "Branch ID and schedules data are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            for schedule_data in updated_schedules:
                day = schedule_data['day']
                shift_type = schedule_data['shift_details']['shift_type']
                room_name = schedule_data['shift_details']['room']
                employee_name = schedule_data.get('employee_name')

                # Получаем смену
                shift = Shift.objects.filter(
                    room__name=room_name,
                    shift_type=shift_type,
                    day_of_week=day,
                    room__branch_id=branch_id,
                ).first()

                if not shift:
                    return Response(
                        {"error": f"Shift not found for room {room_name}, shift {shift_type}, day {day}"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                # Обновляем расписание
                schedule = Schedule.objects.filter(shift=shift, week_start_date=schedule_data['week_start_date']).first()
                if schedule:
                    schedule.employee = None if not employee_name else Employee.objects.get(user__username=employee_name)
                    if new_status:
                        schedule.status = new_status  # Обновляем статус расписания
                    schedule.save()
                    
            logger.info(f"User {user.username} successfully updated schedule for branch {branch_id}.")
            return Response({"status": "Schedules updated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(f"Error updating schedules: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
  
class AvailableWeeksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, branch_id):
        weeks = Schedule.objects.filter(branch_id=branch_id).values_list('week_start_date', flat=True).distinct()
        sorted_weeks = sorted(set(weeks))  # Уникальные и отсортированные даты
        return Response(sorted_weeks)

class GetWeeklyScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, branch_id):
        week_start_date = request.query_params.get('week_start_date', None)
        if not week_start_date:
            return Response({"error": "Week start date is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        schedules = Schedule.objects.filter(
            branch_id=branch_id,
            week_start_date=week_start_date,
            status=Schedule.APPROVED  # Фильтруем только утвержденные расписания
        ).select_related('shift', 'shift__room', 'employee')

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
        
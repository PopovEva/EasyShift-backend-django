from rest_framework import viewsets
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.decorators import api_view
from .models import Branch, Notification, Room, Shift, Employee, Schedule
from .serializers import BranchSerializer, RoomSerializer, ShiftSerializer, EmployeeSerializer, ScheduleSerializer, UserEmployeeSerializer
from .permissions import IsAdminOrReadOnly, IsWorkerOrAdmin
from django.contrib.auth.models import Group, User
from django.utils.dateparse import parse_date
import logging
from rest_framework.exceptions import APIException
from datetime import date, timedelta
from django.db.models import Min
from django.db.models import Q
from django.db.models import Max

logger = logging.getLogger('system_logger')

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
    
    def get_queryset(self):
        # Получаем параметр branch из GET запроса
        branch_id = self.request.query_params.get("branch")
        if branch_id:
            return self.queryset.filter(branch_id=branch_id)
        return self.queryset
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Обновляем вложенные данные пользователя
        user_data = request.data.get('user', {})
        if user_data:
            user = instance.user
            user.username = user_data.get('username', user.username)
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            # Если email передан и не пуст, используем его, иначе оставляем старый email
            user.email = user_data.get('email', user.email) or user.email
            if 'password' in user_data and user_data.get('password'):
                user.set_password(user_data.get('password'))
            user.save()

        # Убираем данные user, чтобы сериализатор не пытался обновлять их снова
        data = request.data.copy()
        data.pop('user', None)

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    
    @action(detail=False, methods=['delete'], url_path='delete-by-week')
    def delete_by_week(self, request):
        branch_id = request.query_params.get('branch_id')
        week_start_date = request.query_params.get('week_start_date')

        if not branch_id or not week_start_date:
            return Response({"error": "Branch ID and week start date are required"}, status=status.HTTP_400_BAD_REQUEST)

        deleted_count, _ = Schedule.objects.filter(
            branch_id=branch_id, week_start_date=week_start_date
        ).delete()

        if deleted_count > 0:
            logger.info(f"User {request.user.username} deleted {deleted_count} schedule entries for week {week_start_date} in branch {branch_id}.")
            return Response({"message": f"Deleted {deleted_count} schedule entries"}, status=status.HTTP_204_NO_CONTENT)
        else:
            logger.warning(f"User {request.user.username} attempted to delete schedules for week {week_start_date} in branch {branch_id}, but none were found.")
            return Response({"error": "No schedules found for the given week"}, status=status.HTTP_404_NOT_FOUND)


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
                            employee = Employee.objects.filter(id=employee_id).first()

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
                        shift_instances = Shift.objects.filter(
                            room__name=room['room'], 
                            shift_type=shift['shift'],
                            day_of_week=day['day'],
                            room__branch_id=branch_id
                        )
                        
                        for shift_instance in shift_instances:
                            employee_id = room.get('employee')
                            employee = Employee.objects.filter(id=employee_id).first() if employee_id else None

                            # Обновляем или создаем расписание для каждой смены
                            schedule, created = Schedule.objects.update_or_create(
                                week_start_date=week_start_date,
                                branch=branch,
                                shift=shift_instance,
                                defaults={
                                    'employee': employee,
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
        logger.debug(f"Branch ID: {branch_id}, Status: {status}, Week Start Date: {week_start_date}")
        
        if week_start_date:
            # Фильтруем по указанной неделе
            schedules = Schedule.objects.filter(
                branch_id=branch_id,
                status=status,
                week_start_date=week_start_date
            ).select_related('shift__room', 'employee__user') 
        else:
            # Если неделя не указана, ищем ближайшую или последнюю доступную
            today = date.today()
            current_week_start = today - timedelta(days=today.weekday() + 1)  # Начало текущей недели (воскресенье)   
            # Попробуем найти расписание для текущей недели
            schedules = Schedule.objects.filter(
                branch_id=branch_id,
                status=status,
                week_start_date=current_week_start
            ).select_related('shift__room', 'employee__user') 
            
            if not schedules.exists():
                # Если расписания для текущей недели нет, находим последнюю доступную неделю
                last_week_start = Schedule.objects.filter(
                    branch_id=branch_id,
                    status=status,
                ).aggregate(Max('week_start_date'))['week_start_date__max']

                if last_week_start:
                    schedules = Schedule.objects.filter(
                        branch_id=branch_id,
                        # status=status.upper(),
                        # status__in=[Schedule.DRAFT, Schedule.APPROVED],
                        status=status,
                        week_start_date=last_week_start
                    ).select_related('shift__room', 'employee__user')
              
        # Если расписания не найдены, возвращаем пустой массив
        if not schedules.exists():
            logger.info(f"No schedules found for Branch {branch_id} with status {status} on Week {week_start_date}.")
            return Response([], status=200)
        
        # Формируем данные для ответа
        data = [
            {
                "week_start_date": schedule.week_start_date,
                "shift_details": {
                    "shift_type": schedule.shift.shift_type,
                    "room": schedule.shift.room.name if schedule.shift.room else None,
                },
                "day": schedule.shift.day_of_week,
                "employee_name": schedule.employee.user.get_full_name() if schedule.employee else None,
                "employee_id": schedule.employee.id if schedule.employee else None,
            }
            for schedule in schedules
        ]

        logger.debug(f"Response Data: {data}")
        return Response(data, status=200)


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
        updated_schedules = request.data.get('schedules', [])
        new_status = request.data.get('status', None)

        if not branch_id or not updated_schedules:
            logger.warning(f"Invalid update request by {user.username}: {request.data}")
            return Response({"error": "Branch ID and schedules are required"}, status=400)

        try:
            updated_count = 0  # Для логирования успешных обновлений
            
            for schedule_data in updated_schedules:
                day = schedule_data.get('day')
                shift_type = schedule_data['shift_details']['shift_type']
                room_name = schedule_data['shift_details']['room']
                employee_id = schedule_data.get('employee_id')

                # Получаем ВСЕ смены для указанной комнаты, типа смены и дня недели
                shifts = Shift.objects.filter(
                    room__name=room_name,
                    shift_type=shift_type,
                    day_of_week=day,
                    room__branch_id=branch_id
                )
                
                if not shifts.exists():
                    logger.warning(f"No matching shifts found for {room_name} {shift_type} on {day}")
                    continue

                for shift_instance in shifts:
                    # Поиск всех расписаний для этой смены
                    schedules = Schedule.objects.filter(
                        shift=shift_instance,
                        week_start_date=schedule_data['week_start_date'],
                        branch_id=branch_id
                    )

                    if schedules.exists():
                        for schedule in schedules:
                            # Обновляем расписание
                            schedule.employee = Employee.objects.filter(id=employee_id).first() if employee_id else None
                            if new_status:
                                schedule.status = new_status  # Применяем новый статус, если передан
                            schedule.save()
                            updated_count += 1
                            logger.info(f"Updated schedule {schedule.id} - Status: {schedule.status}")
                    else:
                        logger.warning(f"No schedule found for shift {shift_instance} on {schedule_data['week_start_date']}")

            logger.info(f"User {user.username} successfully updated {updated_count} schedules for branch {branch_id}.")
            return Response({"status": "Schedules updated successfully", "updated_count": updated_count}, status=200)
        except Exception as e:
            logger.exception("Error updating schedules")
            return Response({"error": str(e)}, status=500)

  
class AvailableWeeksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, branch_id):
        status = request.query_params.get("status", None)  # Получаем статус из параметров
        weeks_query = Schedule.objects.filter(branch_id=branch_id)

        if status:
            weeks_query = weeks_query.filter(status=status)

        weeks = weeks_query.values_list("week_start_date", flat=True).distinct()
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
    
class SubmitAvailabilityView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        employee = Employee.objects.get(user=user)
        availability_data = request.data.get('availability')

        if not availability_data:
            return Response({"error": "No availability data provided."}, status=400)

        # Обработка данных и сохранение
        for entry in availability_data:
            day = entry['day']
            shift_type = entry['shift']
            # Логика сохранения предпочтений

        return Response({"status": "Availability submitted successfully."})
    
class EmployeeNotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            employee = Employee.objects.get(user=user)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=404)

        notifications = Notification.objects.filter(employee=employee).order_by("-created_at")
        data = [
            {
                "id": notif.id,
                "message": notif.message,
                "created_at": notif.created_at.strftime("%Y-%m-%d %H:%M"),
                "is_read": notif.is_read,
            }
            for notif in notifications
        ]
        return Response(data)
    
@api_view(['POST'])
def refresh_token(request):
    """
    Обновление access-токена с проверкой blacklist.
    """
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            logger.warning("Попытка обновления токена без refresh-токена")
            return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, находится ли токен в черном списке
        if BlacklistedToken.objects.filter(token=refresh_token).exists():
            logger.warning(f"Попытка использования заблокированного refresh-токена: {refresh_token}")
            return Response({"error": "Token has been blacklisted"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)

        logger.info(f"Access-токен успешно обновлен для пользователя {request.user.username}")

        return Response({"access": access_token}, status=status.HTTP_200_OK)

    except TokenError:
        logger.error("Ошибка при обновлении токена: недействительный refresh-токен")
        return Response({"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)
    
class AdminNotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            admin_employee = Employee.objects.get(user=user)
        except Employee.DoesNotExist:
            return Response({"error": "Admin not found"}, status=404)

        # Получаем только уведомления, относящиеся к филиалу администратора
        notifications = Notification.objects.filter(employee__branch=admin_employee.branch).order_by("-created_at")
        
        data = [
            {
                "id": notif.id,
                "message": notif.message,
                "created_at": notif.created_at.strftime("%Y-%m-%d %H:%M"),
                "is_read": notif.is_read,
            }
            for notif in notifications
        ]
        return Response(data)
    
class UpdateUserView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user  # Get authenticated user
        data = request.data

        try:
            # Update user fields
            user.first_name = data.get("first_name", user.first_name)
            user.last_name = data.get("last_name", user.last_name)
            user.email = data.get("email", user.email)

            if "password" in data and data["password"]:
                user.set_password(data["password"])  # Hash new password

            user.save()

            # Update Employee details if exist
            try:
                employee = Employee.objects.get(user=user)
                employee.phone_number = data.get("phone_number", employee.phone_number)
                employee.notes = data.get("notes", employee.notes)
                employee.save()
            except Employee.DoesNotExist:
                logger.warning(f"Employee record not found for user {user.username}")

            logger.info(f"User {user.username} updated their profile successfully.")

            return Response(
                {
                    "message": "Profile updated successfully",
                    "user": {
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "phone_number": employee.phone_number if employee else None,
                        "notes": employee.notes if employee else None,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception(f"Error updating profile for user {user.username}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
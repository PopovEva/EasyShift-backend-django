from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import Branch, Room, Shift, Employee, Schedule, ShiftPreference

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    branch = BranchSerializer()
    
    class Meta:
        model = Employee
        fields = ['id', 'phone_number', 'notes', 'user', 'branch']


class ScheduleSerializer(serializers.ModelSerializer):
    shift_details = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    employee_details = serializers.SerializerMethodField()

    class Meta:
        model = Schedule
        fields = ['week_start_date', 'branch', 'shift', 'shift_details', 'employee', 'employee_name', 'employee_details', 'status']

    def get_shift_details(self, obj):
        return {
            "room": obj.shift.room.name,
            "shift_type": obj.shift.shift_type,
        }

    def get_employee_name(self, obj):
        if obj.employee and obj.employee.user:
            return f"{obj.employee.user.first_name} {obj.employee.user.last_name}"
        print("No employee found for schedule:", obj.id)
        return None

    def get_employee_details(self, obj):
        if obj.employee:
            return {
                "username": obj.employee.user.username,
                "first_name": obj.employee.user.first_name,
                "last_name": obj.employee.user.last_name,
                "email": obj.employee.user.email,
            }
        return None



# Кастомный сериализатор для создания User и Employee
class UserEmployeeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    # Эти поля не являются частью модели User, поэтому не включаем их напрямую
    phone_number = serializers.CharField(write_only=True, required=True)
    notes = serializers.CharField(write_only=True, required=False, allow_blank=True)
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all(), write_only=True, required=True)
    group = serializers.ChoiceField(choices=['Admin', 'Worker'], write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'username', 'password', 'email', 'first_name', 'last_name',
            'phone_number', 'notes', 'branch', 'group'
        ]

    def create(self, validated_data):
        # Извлекаем данные для пользователя и сотрудника
        group_name = validated_data.pop('group')
        phone_number = validated_data.pop('phone_number')
        branch = validated_data.pop('branch')
        notes = validated_data.pop('notes', '')

        # Создаем пользователя
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()

        # Добавляем пользователя в группу (Admin или Worker)
        group = Group.objects.get(name=group_name)
        user.groups.add(group)

        # Создаем сотрудника, связанного с этим пользователем
        Employee.objects.create(
            user=user,
            phone_number=phone_number,
            branch=branch,
            notes=notes
        )

        return user

    def to_representation(self, instance):
        # Переопределяем метод to_representation для корректного отображения полей Employee
        representation = super().to_representation(instance)

        # Добавляем информацию о сотруднике (Employee)
        try:
            employee = Employee.objects.get(user=instance)
            representation['phone_number'] = employee.phone_number
            representation['branch'] = employee.branch.id if employee.branch else None
            representation['notes'] = employee.notes
        except Employee.DoesNotExist:
            # Если сотрудник не найден, оставляем поля пустыми
            representation['phone_number'] = None
            representation['branch'] = None
            representation['notes'] = None

        return representation
        
class ShiftPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftPreference
        fields = '__all__'
        read_only_fields = ['employee', 'branch']  # Работник не может менять эти поля вручную
    
    def create(self, validated_data):
        # Убираем переданное значение status, если оно есть, и принудительно задаём 'pending'
        validated_data.pop('status', None)
        validated_data['status'] = 'pending'
        return super().create(validated_data)
from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import Branch, Room, Shift, Employee, Schedule

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


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = '__all__'


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

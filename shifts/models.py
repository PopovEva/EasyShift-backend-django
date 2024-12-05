from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Branch(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class Room(models.Model):
    name = models.CharField(max_length=100)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.branch.name})"


class Shift(models.Model):
    MORNING = 'בוקר'
    AFTERNOON = 'אמצע'
    EVENING = 'ערב'
    SHIFT_TYPES = [
        (MORNING, 'Morning'),
        (AFTERNOON, 'Afternoon'),
        (EVENING, 'Evening'),
    ]

    MONDAY = 'Monday'
    TUESDAY = 'Tuesday'
    WEDNESDAY = 'Wednesday'
    THURSDAY = 'Thursday'
    FRIDAY = 'Friday'
    SATURDAY = 'Saturday'
    SUNDAY = 'Sunday'
    DAYS_OF_WEEK = [
        (MONDAY, 'Monday'),
        (TUESDAY, 'Tuesday'),
        (WEDNESDAY, 'Wednesday'),
        (THURSDAY, 'Thursday'),
        (FRIDAY, 'Friday'),
        (SATURDAY, 'Saturday'),
        (SUNDAY, 'Sunday'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    shift_type = models.CharField(max_length=10, choices=SHIFT_TYPES)
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK)  # Используем CHOICES для дней недели
    date = models.DateField(default=timezone.now)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    employee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    # branch = models.ForeignKey(Branch, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('room', 'shift_type', 'date', 'start_time')  # Ограничение уникальности для предотвращения конфликтов смен
        
    def __str__(self):
        return f"{self.get_shift_type_display()} - {self.get_day_of_week_display()} ({self.room.branch.name}, {self.room.name})"



class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    notes = models.TextField(null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.branch.name})"


class Schedule(models.Model):
    DRAFT = 'draft'
    APPROVED = 'approved'
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (APPROVED, 'Approved'),
    ]

    week_start_date = models.DateField()  # Дата начала недели
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)  # Связь с конкретной сменой
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)  # Сотрудник
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)  # Связь с филиалом
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT)  # Статус расписания

    def __str__(self):
        return f"{self.week_start_date} - {self.branch.name} ({self.status})"



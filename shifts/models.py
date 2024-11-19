from django.db import models

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
    SHIFT_TYPES = [
        ('morning', 'Morning'),
        ('midday', 'Midday'),
        ('evening', 'Evening'),
    ]

    shift_type = models.CharField(max_length=10, choices=SHIFT_TYPES)
    day_of_week = models.CharField(max_length=10)  # Можно использовать ENUM или CHOICES для дней недели
    start_time = models.TimeField()
    end_time = models.TimeField()
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.get_shift_type_display()} - {self.day_of_week} ({self.branch.name}, {self.room.name})"


class Employee(models.Model):
    ROLES = [
        ('admin', 'Admin'),
        ('worker', 'Worker'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    role = models.CharField(max_length=10, choices=ROLES)
    password = models.CharField(max_length=128)  # Рекомендуется использовать встроенную User модель Django
    is_active = models.BooleanField(default=True)
    notes = models.TextField(null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.branch.name})"


class Schedule(models.Model):
    week_start_date = models.DateField()
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ])

    def __str__(self):
        return f"{self.shift} - {self.employee} ({self.status})"


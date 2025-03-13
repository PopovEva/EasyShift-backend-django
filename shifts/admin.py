from django.contrib import admin
from .models import Branch, Room, Shift, Employee, Schedule, ShiftPreference

admin.site.register(Branch)
admin.site.register(Room)
admin.site.register(Shift)
admin.site.register(Employee)
admin.site.register(Schedule)
admin.site.register(ShiftPreference)

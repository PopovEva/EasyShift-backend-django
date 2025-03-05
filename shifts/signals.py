from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Schedule, Shift, Notification, Employee
import logging

logger = logging.getLogger('system_logger')

@receiver(post_save, sender=Schedule)
def log_schedule_changes(sender, instance, created, **kwargs):
    if created:
        logger.info(f"New schedule created: {instance}")
    else:
        logger.info(f"Schedule updated: {instance}")

@receiver(post_delete, sender=Schedule)
def log_schedule_deletion(sender, instance, **kwargs):
    logger.info(f"Schedule deleted: {instance}")
    
@receiver(post_save, sender=Shift)
def log_shift_changes(sender, instance, created, **kwargs):
    if created:
        logger.info(f"New shift created: {instance}")
    else:
        logger.info(f"Shift updated: {instance}")

@receiver(post_delete, sender=Shift)
def log_shift_deletion(sender, instance, **kwargs):
    logger.info(f"Shift deleted: {instance}") 
    
@receiver(post_delete, sender=Schedule)
def delete_unused_shift(sender, instance, **kwargs):
    shift = instance.shift
    if not Schedule.objects.filter(shift=shift).exists():
        shift.delete()
        logger.info(f"Deleted unused shift: {shift}")    
    
# @receiver(post_save, sender=Schedule)
# def create_schedule_notification(sender, instance, created, **kwargs):
#     if instance.status == Schedule.APPROVED and instance.employee:
#         # Уведомление для сотрудника
#         Notification.objects.create(
#             employee=instance.employee,
#             message = f" {instance.shift.room.name} - המשמרת {instance.shift.shift_type} שלך אושרה   בתאריך {instance.week_start_date}"
#         )
#         logger.info(f"Notification created for {instance.employee.user.username}: {instance}")
        
#         # 🔹 Уведомление для администратора (только одно!)
#         admin_user = Employee.objects.filter(branch=instance.branch, user__groups__name="Admin").first()
#         if admin_user:
#             # Проверяем, есть ли уже уведомление на эту неделю
#             if not Notification.objects.filter(employee=admin_user, message__contains=str(instance.week_start_date)).exists():
#                 Notification.objects.create(
#                     employee=admin_user,
#                     message=f"כל המשמרות אושרו לשבוע שמתחיל בתאריך {instance.week_start_date} בסניף {instance.branch.name}"
#                 )
#                 logger.info(f"Admin notification created for branch {instance.branch.name} - Week {instance.week_start_date}")  

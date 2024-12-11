from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Schedule, Shift
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

from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешает полное изменение данных только админам, остальные могут только читать данные.
    """

    def has_permission(self, request, view):
        # Если запрос на чтение данных — разрешить доступ.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Проверка, является ли пользователь админом.
        return request.user and request.user.groups.filter(name='Admin').exists()


class IsWorkerOrAdmin(permissions.BasePermission):
    """
    Разрешает доступ сотрудникам и админам.
    """

    def has_permission(self, request, view):
        # Проверить, является ли пользователь работником или админом.
        return request.user and (request.user.groups.filter(name='Worker').exists() or 
                                 request.user.groups.filter(name='Admin').exists())
        

class IsAdminGroup(permissions.BasePermission):
    """
    Allows access only to users in the 'Admin' group.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.groups.filter(name='Admin').exists()
        )        

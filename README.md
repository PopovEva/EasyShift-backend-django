# EasyShift - Backend

This is the backend repository for **EasyShift**, a shift scheduling management system designed for multi-branch operations. It is built using Django and Django REST Framework. It provides comprehensive management features for administrators and easy access for employees to manage work schedules efficiently.

## 🛠 Tech Stack

- **Python 3.12**
- **Django 5.1.3**
- **Django REST Framework 3.15.2**
- **Simple JWT 5.3.1**
- **SQLite** (development database)
- **CORS Headers**

## 🚀 Features

### Admin Features:
- ✅ Full CRUD operations for employees, shifts, schedules, branches, rooms and ShiftPreference.
- ✅ Weekly schedule creation, approval, and status management (draft/approved).
- ✅ Approve, publish  and manage weekly schedules
- ✅ Manage branches and rooms
- ✅ JWT-based authentication (access and refresh tokens).
- ✅ Role-based access (Admin and Worker).
- ✅ Handle shift preferences submissions from employees.
- ✅ Create schedules based on employee preferences.
- ✅ View notifications from employees
- ✅ Mobile responsive admin panel for on-the-go management.
- ✅ Optimized API responses for mobile-first UI integration.

### Employee Features:
- View weekly schedules
- Submit shift availability preferences
- Receive notifications related to shifts and administrative announcements.

## 📂 Project Structure

```
work_shift_scheduler/
├── shifts/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── permissions.py
│   ├── serializers.py
│   ├── signals.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── work_shift_scheduler/
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
└── db.sqlite3
```

## 🔐 Authentication
Authentication is managed via JWT tokens (Simple JWT):
- Access token lifetime: **40 minutes**
- Refresh token lifetime: **90 days**

## ⚙️ Permissions
Two main permission classes are implemented:

- **IsAdminOrReadOnly:**
  - Admins have full access (CRUD)
  - Others have read-only access

- **IsWorkerOrAdmin:**
  - Access restricted to authenticated workers and admins

## 🔧 Installation

### Clone Repository
```bash
git clone https://github.com/PopovEva/EasyShift-backend-django.git
cd EasyShift-backend-django
```

### Create Virtual Environment
```bash
python -m venv env
source env/bin/activate   # On Windows use: .\env\Scripts\activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Database Setup
```bash
python manage.py migrate
```

### Create Superuser
```bash
python manage.py createsuperuser
```

## 🚦 Running the Project

Start Django development server:
```bash
python manage.py runserver
```

Backend will run at [http://localhost:8000](http://localhost:8000).

## 🌐 CORS Settings

CORS allowed origins (frontend URL):
```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
]
```

## 📚 API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/token/` | Obtain JWT token |
| POST   | `/api/token/refresh/` | Refresh JWT token |
| GET    | `/api/user-info/` | Get authenticated user info |
| GET    | `/api/available-weeks/<branch_id>` | List available weeks for schedules |
| GET    | `/api/get-schedule/<branch_id>/<status>` | Get schedules by week and status |
| POST   | `/api/create-schedule/` | Create schedules |
| POST   | `/api/update-schedule/` | Update schedules |
| DELETE | `/api/schedules/delete-by-week/` | Delete schedules by week |
| GET    | `/api/admin-notifications/` | Admin notifications |
| GET    | `/api/employee-notifications/` | Employee notifications |



- `/branches/`, `/rooms/`, `/shifts/`, `/employees/`, `/schedules/` – full CRUD.
- `/create-schedule/`, `/update-schedule/`, `/available-weeks/<branch_id>/`
- `/shift-preferences/` – worker submission of shift preferences.
- `/shift-preferences-admin/` – admin view of submitted preferences.
- `/user-info/`, `/admin-notifications/`, `/employee-notifications/` – user and notification info.
- `/token/`, `/token/refresh/` – JWT authentication.

## 📝 Frontend
Frontend repository:
- [EasyShift Frontend (React)](https://github.com/PopovEva/EasyShift-frontend-react)

## 🗂 Dependencies
See `requirements.txt` for detailed package versions:
```
asgiref==3.8.1
Django==5.1.3
django-cors-headers==4.6.0
djangorestframework==3.15.2
djangorestframework-simplejwt==5.3.1
PyJWT==2.10.0
sqlparse==0.5.2
tzdata==2024.2
```

## 🔮 Future Features
- Employee shift preference submissions-Done✅
- The system is designed to support mobile and desktop-friendly UI.✅
- Automated scheduling optimization using AI

## 📌 Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss proposed modifications.

---

⭐️ **EasyShift** aims to simplify shift management and scheduling, providing a seamless experience for administrators and employees alike.


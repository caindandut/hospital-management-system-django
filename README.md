# DUT Hospital Management System

A comprehensive web-based hospital management system built with Django, designed for managing appointments, patient records, doctor schedules, billing, and administrative tasks.

## 🏥 Overview

DUT Hospital Management System is a full-featured healthcare management platform that streamlines hospital operations including appointment scheduling, patient management, electronic medical records (EMR), billing, and administrative controls.

## ✨ Features

### Patient Management
- Patient registration and profile management
- Appointment booking system with multi-step process
- View appointment history and status
- Cancel appointments (with time restrictions)
- Patient profile with medical information

### Doctor Management
- Doctor profiles with specialties and ranks
- Schedule management and availability
- View daily appointments and patient visits
- Prescription and medical record management
- Doctor-specific dashboard

### Appointment System
- Multi-step appointment booking process
- Real-time schedule availability
- Appointment status tracking (Pending, Confirmed, Checked-in, Completed, Cancelled, No-show)
- Automatic appointment confirmation
- Appointment cancellation with time-based restrictions

### Billing & Invoicing
- Automatic invoice generation
- Payment tracking and management
- Invoice printing and PDF export
- Cashier management interface
- Price calculation based on doctor rank and specialty

### Electronic Medical Records (EMR)
- Digital patient records
- Medical history tracking
- Visit summaries and prescriptions
- Print-friendly medical documents

### Administrative Panel
- Comprehensive dashboard with statistics
- User management (Patients, Doctors, Staff, Admins)
- Specialty and rank fee configuration
- System settings management
- Appointment oversight
- Invoice management

### Role-Based Access Control
- **Patient**: Book appointments, view medical records, manage profile
- **Doctor**: Manage schedule, view appointments, record patient visits, prescribe medications
- **Staff**: Handle billing, manage invoices, assist with appointments
- **Admin**: Full system access, user management, system configuration

## 🛠️ Technology Stack

- **Backend**: Django 5.2.6
- **Database**: MySQL
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Icons**: Bootstrap Icons
- **PDF Generation**: xhtml2pdf (optional: WeasyPrint)

## 📋 Prerequisites

- Python 3.8 or higher
- MySQL 5.7 or higher
- pip (Python package manager)
- Git

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/dut-hospital-management-system.git
cd dut-hospital-management-system
```

### 2. Create a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure MySQL database

Create a MySQL database:

```sql
CREATE DATABASE clinic_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Configure settings

Update database credentials in `clinic/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'clinic_db',
        'USER': 'your_mysql_user',
        'PASSWORD': 'your_mysql_password',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
```

**⚠️ Security Note**: For production, use environment variables for sensitive data like `SECRET_KEY` and database credentials.

### 6. Run migrations

```bash
python manage.py migrate
```

### 7. Create a superuser

```bash
python manage.py createsuperuser
```

### 8. Collect static files

```bash
python manage.py collectstatic
```

### 9. Run the development server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## 📁 Project Structure

```
dut-hospital-management-system/
├── accounts/          # User authentication and account management
├── adminpanel/        # Administrative dashboard and controls
├── appointments/      # Appointment scheduling and management
├── billing/           # Invoice and payment management
├── clinic/            # Main project settings and configuration
├── core/              # Core utilities and choices
├── doctors/           # Doctor profiles and management
├── emr/               # Electronic Medical Records
├── patients/          # Patient profiles and management
├── staff/             # Staff management
├── theme/             # Frontend templates and static files
├── static/            # Static files (CSS, JS, images)
├── media/             # User-uploaded files (avatars, documents)
├── manage.py          # Django management script
└── requirements.txt   # Python dependencies
```

## 🔐 User Roles

The system supports four user roles with different access levels:

- **PATIENT**: Can book appointments, view their medical records, and manage their profile
- **DOCTOR**: Can manage schedules, view appointments, record patient visits, and prescribe medications
- **STAFF**: Can handle billing, manage invoices, and assist with appointment management
- **ADMIN**: Has full system access including user management and system configuration

## 🎯 Key URLs

- Home: `/`
- Admin Portal: `/admin-portal/`
- Appointments: `/appointments/`
- Billing: `/billing/`
- Doctor Dashboard: `/doctors/`
- Staff Dashboard: `/staff/`
- Django Admin: `/admin/`

## 📝 Configuration

### Appointment Settings

Configure appointment cancellation rules in `clinic/settings.py`:

```python
APPOINTMENT_CANCEL_BEFORE_MINUTES = 120  # 2 hours before appointment
```

### Session Settings

Default session duration is 14 days. Configure in `clinic/settings.py`:

```python
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 days
```

## 🔧 Development

### Running Tests

```bash
python manage.py test
```

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Management Commands

- Setup rank fees: `python manage.py setup_rank_fees`
- Recompute invoices: `python manage.py recompute_invoices`
- Reprice invoices: `python manage.py reprice_invoices`




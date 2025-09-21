# Django WiFi Vendo System

A comprehensive WiFi vending machine management system built with Django 5.2.2.

## Features

- **User Management**: Admin and collector user roles
- **Collector Management**: Add, view, and disable collectors
- **WiFi Vendo Management**: Track WiFi vending machines and their status
- **Sales Tracking**: Record and monitor sales transactions
- **Reports**: Generate sales reports and analytics
- **Dashboard**: Real-time overview of system metrics

## Installation

### Prerequisites

- Python 3.8 or higher
- MySQL 5.7 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Monitor
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup**

   Create a MySQL database:
   ```sql
   CREATE DATABASE wifivendo;
   ```

   Update database settings in `Monitor/settings.py` if needed:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'wifivendo',
           'USER': 'your_username',
           'PASSWORD': 'your_password',
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
   ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

   The application will be available at `http://127.0.0.1:8000/`

## Usage

### Admin Features
- Access the admin panel at `/admin/`
- Manage collectors, WiFi vendos, and sales records
- View system reports and analytics
- Enable/disable collector accounts

### Collector Features
- Log in to add sales records
- View personal sales history
- Update WiFi vendo status

## Requirements

The `requirements.txt` file includes all necessary dependencies for:
- Core Django framework and database connectivity
- Development tools and testing frameworks
- Code quality tools and debugging utilities
- Optional features for data handling and reporting

## Security Notes

- Change the `SECRET_KEY` in `Monitor/settings.py` for production
- Set `DEBUG = False` for production deployment
- Configure proper `ALLOWED_HOSTS` for production
- Use environment variables for sensitive data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

This project is licensed under the MIT License.

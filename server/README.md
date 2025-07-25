# KG Components API

A secure and efficient Django REST API for the KG Components platform.

## Features

- JWT Authentication with token refresh and blacklisting
- User registration and email verification
- Password reset functionality
- User profile management
- Product management
- Order processing
- Sales analytics
- Admin dashboard
- Comprehensive security measures
- Thorough test coverage

## Tech Stack

- Django 5.2.4
- Django REST Framework
- SimpleJWT for authentication
- PostgreSQL (configurable)
- Swagger/ReDoc for API documentation

## Security Features

- JWT Authentication with token refresh and blacklisting
- Password hashing with Django's built-in password validators
- CORS protection
- SQL Injection protection
- XSS protection
- Content Security Policy
- Rate limiting and throttling
- Request logging

## Installation

1. Clone the repository:
```bash
git clone https://github.com/vinnywalker96/kg-components-p.git
cd kg-components-p/server
```

2. Create a virtual environment:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the server directory with the following variables:
```
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_email_password
FRONTEND_URL=http://localhost:3000
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
```

5. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the server:
```bash
python manage.py runserver
```

## API Documentation

Once the server is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/swagger/
- ReDoc: http://localhost:8000/redoc/

## API Endpoints

### Authentication

- `POST /api/auth/register/` - Register a new user
- `POST /api/auth/login/` - User login
- `POST /api/auth/admin/login/` - Admin login
- `POST /api/auth/token/refresh/` - Refresh JWT token
- `POST /api/auth/logout/` - Logout (blacklist token)
- `POST /api/auth/verify-email/` - Verify email
- `POST /api/auth/password-reset/` - Request password reset
- `POST /api/auth/password-reset/confirm/` - Confirm password reset
- `GET/PATCH /api/auth/profile/` - Get or update user profile

### Shop

- `GET /api/shop/products/` - List products
- `GET /api/shop/products/{id}/` - Get product details
- `POST /api/shop/products/create/` - Create product (admin only)
- `PATCH /api/shop/products/{id}/update/` - Update product (admin only)
- `DELETE /api/shop/products/{id}/delete/` - Delete product (admin only)
- `GET /api/shop/orders/` - List orders
- `GET /api/shop/orders/{id}/` - Get order details
- `POST /api/shop/orders/create/` - Create order
- `PATCH /api/shop/orders/{id}/update/` - Update order
- `GET /api/shop/sales/` - List sales (admin only)
- `GET /api/shop/analytics/sales/` - Sales analytics (admin only)
- `GET /api/shop/analytics/products/` - Product analytics (admin only)

## Testing

Run the tests with:

```bash
python manage.py test
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.


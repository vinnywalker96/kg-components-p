# KG Components API

A secure, high-performance Django REST API for KG Components with JWT authentication, user management, and order processing.

## Features

- **Secure JWT Authentication**
  - User and admin authentication flows
  - Token refresh and blacklisting
  - Email verification

- **User Management**
  - User registration and profile management
  - Admin user management
  - Password reset functionality

- **Product Management**
  - Product listing, creation, and updates
  - Image upload support

- **Order Processing**
  - Order creation and management
  - Order status updates
  - Sales tracking

- **Security Features**
  - Rate limiting
  - CORS protection
  - SQL injection protection
  - Security headers

- **Performance Optimizations**
  - Database query optimization
  - Caching support
  - Pagination

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL (for production)
- Redis (for caching in production)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/kg-components-p.git
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

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   # Edit the .env file with your configuration
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

## API Documentation

API documentation is available at:
- Swagger UI: `/swagger/`
- ReDoc: `/redoc/`

## Authentication

### User Registration

```
POST /api/auth/register/
```

### User Login

```
POST /api/auth/login/
```

### Admin Login

```
POST /api/auth/admin/login/
```

### Token Refresh

```
POST /api/auth/token/refresh/
```

### Logout

```
POST /api/auth/logout/
```

## User Management

### Get User Profile

```
GET /api/users/profile/
```

### Update User Profile

```
PATCH /api/users/profile/update/
```

### Change Password

```
POST /api/users/password/change/
```

## Product Management

### List Products

```
GET /api/shop/products/
```

### Get Product Details

```
GET /api/shop/products/{id}/
```

### Create Product (Admin)

```
POST /api/shop/products/create/
```

### Update Product (Admin)

```
PATCH /api/shop/products/{id}/update/
```

### Delete Product (Admin)

```
DELETE /api/shop/products/{id}/delete/
```

## Order Management

### List Orders

```
GET /api/shop/orders/
```

### Get Order Details

```
GET /api/shop/orders/{id}/
```

### Create Order

```
POST /api/shop/orders/create/
```

### Update Order

```
PATCH /api/shop/orders/{id}/update/
```

## Deployment

### Production Settings

For production deployment, use the production settings:

```bash
python manage.py runserver --settings=kgcomponents.settings_prod
```

### Using Gunicorn

For production deployment with Gunicorn:

```bash
gunicorn kgcomponents.wsgi:application -c gunicorn.conf.py
```

## Testing

Run tests with:

```bash
python manage.py test
```

Or with pytest:

```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.


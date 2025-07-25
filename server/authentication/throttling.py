from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class LoginRateThrottle(AnonRateThrottle):
    """
    Throttle class for login attempts.
    
    This throttle limits the number of login attempts from a single IP address
    to prevent brute force attacks.
    """
    scope = 'login'
    rate = '5/min'  # 5 login attempts per minute


class RegistrationRateThrottle(AnonRateThrottle):
    """
    Throttle class for registration attempts.
    
    This throttle limits the number of registration attempts from a single IP address
    to prevent spam and abuse.
    """
    scope = 'registration'
    rate = '3/hour'  # 3 registration attempts per hour


class UserRateThrottle(UserRateThrottle):
    """
    Throttle class for authenticated user requests.
    
    This throttle limits the number of requests from authenticated users
    to prevent API abuse.
    """
    scope = 'user'
    rate = '100/min'  # 100 requests per minute for authenticated users


class AdminRateThrottle(UserRateThrottle):
    """
    Throttle class for admin user requests.
    
    This throttle limits the number of requests from admin users
    to prevent API abuse, but with a higher limit than regular users.
    """
    scope = 'admin'
    rate = '200/min'  # 200 requests per minute for admin users


class PasswordResetRateThrottle(AnonRateThrottle):
    """
    Throttle class for password reset attempts.
    
    This throttle limits the number of password reset attempts from a single IP address
    to prevent abuse and spam.
    """
    scope = 'password_reset'
    rate = '3/hour'  # 3 password reset attempts per hour


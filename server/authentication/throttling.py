from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class LoginRateThrottle(AnonRateThrottle):
    """
    Throttle for login attempts.
    """
    scope = 'login'


class RegistrationRateThrottle(AnonRateThrottle):
    """
    Throttle for registration attempts.
    """
    scope = 'registration'


class PasswordResetRateThrottle(AnonRateThrottle):
    """
    Throttle for password reset attempts.
    """
    scope = 'password_reset'


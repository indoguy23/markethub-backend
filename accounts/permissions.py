from rest_framework.permissions import BasePermission


class IsCustomer(BasePermission):
    message = "Only customers can access this resource."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and hasattr(request.user, "profile")
            and request.user.profile.role == "customer"
        )


class IsSeller(BasePermission):
    message = "Only sellers can access this resource."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and hasattr(request.user, "profile")
            and request.user.profile.role == "seller"
        )


class IsAdmin(BasePermission):
    message = "Only administrators can access this resource."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_staff
        )

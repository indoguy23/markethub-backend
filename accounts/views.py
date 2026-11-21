from rest_framework.views import APIView
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status


from .serializers import UserRegistrationSerializer

from .models import UserProfile


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "message": "User registered successfully.",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "phone_number": user.profile.phone_number,
                    "role": user.profile.role,
                }
            },
            status = status.HTTP_201_CREATED
        )

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if user.is_superuser or user.is_staff:
            role = "admin"
            phone_number = ""
        else:
            try:
                profile = user.profile
                role = profile.role
                phone_number = profile.phone_number
            except UserProfile.DoesNotExist:
                role = "customer"
                phone_number = ""
        
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone_number": phone_number,
                "role": role,
            }
        )
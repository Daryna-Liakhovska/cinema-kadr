import logging

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer, UserSerializer

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("User registered: id=%s, username=%s", user.id, user.username)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class LoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        username = request.data.get("username")
        if response.status_code == status.HTTP_200_OK:
            logger.info("Login succeeded: username=%s", username)
        return response

    def handle_exception(self, exc):
        response = super().handle_exception(exc)
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            logger.warning(
                "Login failed: username=%s", self.request.data.get("username")
            )
        return response

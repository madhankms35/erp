from django.shortcuts import render
from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from . services import *
# Create your views here.
class CreateProductionRequest(APIView):

    class InputSerializers(serializers.Serializer):

        product = serializers.CharField(required=True)
        quantity = serializers.IntegerField(required=True)
        color = serializers.CharField(required=True)
        color_type = serializers.CharField(required=True)
        sleeve = serializers.CharField(required=True)
        fabric = serializers.CharField(required=True)
        required_date = serializers.DateField(required=True)
        priority = serializers.CharField(required=False)
        remarks = serializers.CharField(required=False,allow_blank=True)

    def post(self, request):
        serializer = self.InputSerializers(data=request.data)
        serializer.is_valid(raise_exception=True)

        production_request = create_production_request(
            **serializer.validated_data
        )
        return Response(
            {'data': production_request},
            status=status.HTTP_201_CREATED
        )
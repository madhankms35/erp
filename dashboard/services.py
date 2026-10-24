from . models import *
from rest_framework.exceptions import APIException

def create_production_request(**data):

    try:

        production_request = ProductionRequest.objects.create(
            product=data.get('product'),
            quantity=data.get('quantity'),
            color=data.get('color'),
            color_type=data.get('color_type'),
            sleeve=data.get('sleeve'),
            fabric=data.get('fabric'),
            required_date=data.get('required_date'),
            priority=data.get('priority'),
            remarks=data.get('remarks')
        )

        return f"Production Request #{production_request.id} created successfully."

    except Exception as e:

        raise APIException(e)
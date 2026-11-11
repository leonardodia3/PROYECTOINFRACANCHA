
import json
from datetime import datetime, timezone


def lambda_handler(event, context):
    """
    Endpoint de salud de CANCHA GO.

    GET /health
    """

    response = {
        "status": "ok",
        "service": "cancha-go-backend",
        "environment": "staging",
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat()
    }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Cache-Control": "no-store"
        },
        "body": json.dumps(response)
    }

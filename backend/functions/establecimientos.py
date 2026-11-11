
import json
import logging
import os
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_table():
    """Obtiene la tabla DynamoDB en AWS."""
    import boto3

    table_name = os.environ["ESTABLECIMIENTOS_TABLE"]
    dynamodb = boto3.resource("dynamodb")
    return dynamodb.Table(table_name)


def response(status_code, data):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Cache-Control": "no-store"
        },
        "body": json.dumps(data, ensure_ascii=False)
    }


def get_identity(event):
    """
    Lee la identidad validada por API Gateway JWT.

    Nunca se debe confiar en un owner_id
    enviado por el cliente.
    """
    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
    )

    if not isinstance(claims, dict):
        return None, []

    user_id = claims.get("sub")

    groups = claims.get("cognito:groups", [])

    if isinstance(groups, str):
        groups = [
            group.strip()
            for group in groups.strip("[]").split(",")
        ]

    if not isinstance(groups, list):
        groups = []

    return user_id, groups


def crear_establecimiento(event):
    user_id, groups = get_identity(event)

    if not user_id:
        return response(401, {
            "message": "Autenticación requerida"
        })

    if "propietario" not in groups:
        return response(403, {
            "message": "Acceso denegado"
        })

    try:
        data = json.loads(event.get("body") or "{}")
    except (ValueError, TypeError):
        return response(400, {
            "message": "El JSON enviado no es válido"
        })

    if not isinstance(data, dict):
        return response(400, {
            "message": "Se esperaba un objeto JSON"
        })

    nombre = data.get("nombre")
    ciudad = data.get("ciudad")
    direccion = data.get("direccion")

    campos = [nombre, ciudad, direccion]

    if any(
        not isinstance(campo, str)
        or not campo.strip()
        for campo in campos
    ):
        return response(400, {
            "message": (
                "Nombre, ciudad y dirección "
                "son obligatorios"
            )
        })

    nombre = nombre.strip()
    ciudad = ciudad.strip()
    direccion = direccion.strip()

    if (
        len(nombre) > 120
        or len(ciudad) > 80
        or len(direccion) > 200
    ):
        return response(400, {
            "message": "Uno o más campos superan el límite"
        })

    establecimiento_id = str(uuid.uuid4())
    fecha = datetime.now(timezone.utc).isoformat()

    item = {
        "PK": f"EST#{establecimiento_id}",
        "SK": "META",
        "GSI1PK": f"CIUDAD#{ciudad.upper()}#PENDIENTE",
        "GSI1SK": f"EST#{establecimiento_id}",
        "establecimiento_id": establecimiento_id,
        "nombre": nombre,
        "ciudad": ciudad,
        "direccion": direccion,
        "propietario_id": user_id,
        "estado": "PENDIENTE",
        "creado_en": fecha
    }

    get_table().put_item(
        Item=item,
        ConditionExpression="attribute_not_exists(PK)"
    )

    return response(201, {
        "message": "Establecimiento registrado",
        "establecimiento_id": establecimiento_id,
        "estado": "PENDIENTE"
    })


def listar_establecimientos(event):
    parametros = event.get("queryStringParameters") or {}
    ciudad = parametros.get("ciudad", "")

    if not isinstance(ciudad, str) or not ciudad.strip():
        return response(400, {
            "message": "Debe indicar una ciudad"
        })

    ciudad = ciudad.strip()

    if len(ciudad) > 80:
        return response(400, {
            "message": "Ciudad demasiado larga"
        })

    resultado = get_table().query(
        IndexName="BusquedaPorCiudad",
        KeyConditionExpression="GSI1PK = :ciudad",
        ExpressionAttributeValues={
            ":ciudad": f"CIUDAD#{ciudad.upper()}#APROBADO"
        },
        Limit=20
    )

    establecimientos = []

    for item in resultado.get("Items", []):
        establecimientos.append({
            "establecimiento_id": item["establecimiento_id"],
            "nombre": item["nombre"],
            "ciudad": item["ciudad"],
            "direccion": item["direccion"]
        })

    return response(200, {
        "total_pagina": len(establecimientos),
        "establecimientos": establecimientos
    })


def lambda_handler(event, context):
    """
    Punto de entrada de AWS Lambda.
    API Gateway HTTP API, payload 2.0.
    """
    metodo = (
        event.get("requestContext", {})
        .get("http", {})
        .get("method", "")
    )

    try:
        if metodo == "POST":
            return crear_establecimiento(event)

        if metodo == "GET":
            return listar_establecimientos(event)

        return response(405, {
            "message": "Método no permitido"
        })

    except Exception:
        logger.exception("Error al procesar establecimientos")
        return response(503, {
            "message": "Servicio temporalmente no disponible"
        })

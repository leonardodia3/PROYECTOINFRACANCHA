
import logging
import uuid
from datetime import datetime, timezone

from backend.functions.establecimientos import (
    get_identity,
    get_table,
    response,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ESTADOS_PERMITIDOS = {"APROBADO", "RECHAZADO"}


def revisar_establecimiento(event):
    # 1. Comprobar identidad y permisos
    user_id, grupos = get_identity(event)

    if not user_id:
        return response(401, {
            "message": "Autenticacion requerida"
        })

    if "administrador" not in grupos:
        return response(403, {
            "message": "Solo el administrador puede revisar"
        })

    # 2. Obtener y validar identificador
    parametros = event.get("pathParameters") or {}
    establecimiento_id = parametros.get("id", "")

    try:
        establecimiento_id = str(
            uuid.UUID(establecimiento_id)
        )
    except (ValueError, TypeError, AttributeError):
        return response(400, {
            "message": "Identificador no valido"
        })

    # 3. Leer el cuerpo JSON
    import json

    try:
        datos = json.loads(event.get("body") or "{}")
    except (ValueError, TypeError):
        return response(400, {
            "message": "JSON no valido"
        })

    if not isinstance(datos, dict):
        return response(400, {
            "message": "Se esperaba un objeto JSON"
        })

    estado = datos.get("estado")

    if not isinstance(estado, str) or estado not in ESTADOS_PERMITIDOS:
        return response(400, {
            "message": "Estado debe ser APROBADO o RECHAZADO"
        })

    # 4. Buscar establecimiento
    tabla = get_table()

    clave = {
        "PK": f"EST#{establecimiento_id}",
        "SK": "META"
    }

    resultado = tabla.get_item(
        Key=clave,
        ConsistentRead=True
    )

    establecimiento = resultado.get("Item")

    if not establecimiento:
        return response(404, {
            "message": "Establecimiento no encontrado"
        })

    if establecimiento.get("estado") != "PENDIENTE":
        return response(409, {
            "message": "El establecimiento ya fue revisado"
        })

    # 5. Preparar nuevo estado
    ciudad = establecimiento["ciudad"].strip().upper()
    fecha = datetime.now(timezone.utc).isoformat()

    # 6. Actualizar de manera condicionada
    try:
        tabla.update_item(
            Key=clave,
            UpdateExpression=(
                "SET #estado = :nuevo, "
                "GSI1PK = :indice, "
                "actualizado_en = :fecha, "
                "revisado_por = :admin"
            ),
            ConditionExpression=(
                "attribute_exists(PK) AND "
                "#estado = :pendiente AND "
                "GSI1PK = :indice_anterior"
            ),
            ExpressionAttributeNames={
                "#estado": "estado"
            },
            ExpressionAttributeValues={
                ":nuevo": estado,
                ":pendiente": "PENDIENTE",
                ":indice": f"CIUDAD#{ciudad}#{estado}",
                ":indice_anterior": (
                    f"CIUDAD#{ciudad}#PENDIENTE"
                ),
                ":fecha": fecha,
                ":admin": user_id
            }
        )
    except Exception as error:
        codigo = (
            getattr(error, "response", {})
            .get("Error", {})
            .get("Code", "")
        )

        if codigo == "ConditionalCheckFailedException":
            return response(409, {
                "message": (
                    "Otro administrador ya modifico "
                    "este establecimiento"
                )
            })

        raise

    return response(200, {
        "message": "Establecimiento revisado",
        "establecimiento_id": establecimiento_id,
        "estado": estado,
        "revisado_por": user_id
    })


def lambda_handler(event, context):
    metodo = (
        event.get("requestContext", {})
        .get("http", {})
        .get("method", "")
    )

    if metodo != "PATCH":
        return response(405, {
            "message": "Metodo no permitido"
        })

    try:
        return revisar_establecimiento(event)

    except Exception:
        logger.exception(
            "Error al revisar establecimiento"
        )
        return response(503, {
            "message": "Servicio temporalmente no disponible"
        })


import json
import unittest
import uuid
from unittest.mock import patch

from backend.functions.admin_establecimientos import (
    lambda_handler
)


ID_ESTABLECIMIENTO = str(uuid.uuid4())


class ErrorCondicional(Exception):
    response = {
        "Error": {
            "Code": "ConditionalCheckFailedException"
        }
    }


class TablaSimulada:
    def __init__(self):
        self.item = {
            "PK": f"EST#{ID_ESTABLECIMIENTO}",
            "SK": "META",
            "establecimiento_id": ID_ESTABLECIMIENTO,
            "nombre": "Complejo Deportivo Norte",
            "ciudad": "Trujillo",
            "estado": "PENDIENTE",
            "GSI1PK": "CIUDAD#TRUJILLO#PENDIENTE"
        }

        self.simular_conflicto = False

    def get_item(self, **kwargs):
        if self.item is None:
            return {}

        if kwargs["Key"]["PK"] != self.item["PK"]:
            return {}

        return {"Item": self.item.copy()}

    def update_item(self, **kwargs):
        if self.simular_conflicto:
            raise ErrorCondicional()

        valores = kwargs["ExpressionAttributeValues"]

        if self.item["estado"] != "PENDIENTE":
            raise ErrorCondicional()

        if self.item["GSI1PK"] != valores[":indice_anterior"]:
            raise ErrorCondicional()

        self.item["estado"] = valores[":nuevo"]
        self.item["GSI1PK"] = valores[":indice"]
        self.item["revisado_por"] = valores[":admin"]
        self.item["actualizado_en"] = valores[":fecha"]


class TestAdminEstablecimientos(unittest.TestCase):

    def setUp(self):
        self.tabla = TablaSimulada()

        parche = patch(
            "backend.functions.admin_establecimientos.get_table",
            return_value=self.tabla
        )

        parche.start()
        self.addCleanup(parche.stop)

    def evento(
        self,
        estado="APROBADO",
        grupos=None,
        autenticado=True
    ):
        if grupos is None:
            grupos = ["administrador"]

        evento = {
            "requestContext": {
                "http": {"method": "PATCH"}
            },
            "pathParameters": {
                "id": ID_ESTABLECIMIENTO
            },
            "body": json.dumps({
                "estado": estado
            })
        }

        if autenticado:
            evento["requestContext"]["authorizer"] = {
                "jwt": {
                    "claims": {
                        "sub": "admin-001",
                        "cognito:groups": grupos
                    }
                }
            }

        return evento

    def test_aprobar_establecimiento(self):
        resultado = lambda_handler(
            self.evento("APROBADO"), None
        )

        cuerpo = json.loads(resultado["body"])

        self.assertEqual(resultado["statusCode"], 200)
        self.assertEqual(cuerpo["estado"], "APROBADO")
        self.assertEqual(
            self.tabla.item["GSI1PK"],
            "CIUDAD#TRUJILLO#APROBADO"
        )

    def test_rechazar_establecimiento(self):
        resultado = lambda_handler(
            self.evento("RECHAZADO"), None
        )

        self.assertEqual(resultado["statusCode"], 200)
        self.assertEqual(
            self.tabla.item["estado"],
            "RECHAZADO"
        )

    def test_usuario_no_autenticado(self):
        resultado = lambda_handler(
            self.evento(autenticado=False), None
        )

        self.assertEqual(resultado["statusCode"], 401)

    def test_propietario_no_puede_aprobar(self):
        resultado = lambda_handler(
            self.evento(grupos=["propietario"]), None
        )

        self.assertEqual(resultado["statusCode"], 403)

    def test_estado_invalido(self):
        resultado = lambda_handler(
            self.evento("ELIMINADO"), None
        )

        self.assertEqual(resultado["statusCode"], 400)

    def test_establecimiento_inexistente(self):
        self.tabla.item = None

        resultado = lambda_handler(
            self.evento(), None
        )

        self.assertEqual(resultado["statusCode"], 404)

    def test_no_revisar_dos_veces(self):
        self.tabla.item["estado"] = "APROBADO"

        resultado = lambda_handler(
            self.evento(), None
        )

        self.assertEqual(resultado["statusCode"], 409)

    def test_conflicto_concurrente(self):
        self.tabla.simular_conflicto = True

        resultado = lambda_handler(
            self.evento(), None
        )

        self.assertEqual(resultado["statusCode"], 409)

    def test_metodo_no_permitido(self):
        evento = self.evento()
        evento["requestContext"]["http"]["method"] = "DELETE"

        resultado = lambda_handler(evento, None)

        self.assertEqual(resultado["statusCode"], 405)

    def test_identificador_invalido(self):
        evento = self.evento()
        evento["pathParameters"]["id"] = "abc"

        resultado = lambda_handler(evento, None)

        self.assertEqual(resultado["statusCode"], 400)


if __name__ == "__main__":
    unittest.main()

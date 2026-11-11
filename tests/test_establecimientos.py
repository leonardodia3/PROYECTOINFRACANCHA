
import json
import unittest
from unittest.mock import patch

from backend.functions.establecimientos import lambda_handler


class TablaSimulada:
    def __init__(self):
        self.registros = []
        self.consulta = None

    def put_item(self, **kwargs):
        self.registros.append(kwargs["Item"])

    def query(self, **kwargs):
        self.consulta = kwargs

        return {
            "Items": [
                {
                    "establecimiento_id": "est-001",
                    "nombre": "Complejo Deportivo Norte",
                    "ciudad": "Trujillo",
                    "direccion": "Av. Principal 123"
                }
            ]
        }


class TestEstablecimientos(unittest.TestCase):

    def setUp(self):
        self.tabla = TablaSimulada()

        parche = patch(
            "backend.functions.establecimientos.get_table",
            return_value=self.tabla
        )

        parche.start()
        self.addCleanup(parche.stop)

    def evento(self, metodo, data=None, autenticado=True):
        evento = {
            "requestContext": {
                "http": {
                    "method": metodo
                }
            },
            "queryStringParameters": {}
        }

        if autenticado:
            evento["requestContext"]["authorizer"] = {
                "jwt": {
                    "claims": {
                        "sub": "usuario-123",
                        "cognito:groups": ["propietario"]
                    }
                }
            }

        if data is not None:
            evento["body"] = json.dumps(data)

        return evento

    def test_crear_establecimiento(self):
        evento = self.evento("POST", {
            "nombre": "Cancha Los Campeones",
            "ciudad": "Trujillo",
            "direccion": "Av. América 500"
        })

        resultado = lambda_handler(evento, None)
        cuerpo = json.loads(resultado["body"])

        self.assertEqual(resultado["statusCode"], 201)
        self.assertEqual(cuerpo["estado"], "PENDIENTE")
        self.assertEqual(len(self.tabla.registros), 1)

        registro = self.tabla.registros[0]
        self.assertEqual(
            registro["propietario_id"],
            "usuario-123"
        )

    def test_campos_obligatorios(self):
        evento = self.evento("POST", {
            "nombre": "",
            "ciudad": "Trujillo",
            "direccion": ""
        })

        resultado = lambda_handler(evento, None)

        self.assertEqual(resultado["statusCode"], 400)
        self.assertEqual(len(self.tabla.registros), 0)

    def test_sin_autenticacion(self):
        evento = self.evento(
            "POST",
            {
                "nombre": "Cancha A",
                "ciudad": "Lima",
                "direccion": "Calle 123"
            },
            autenticado=False
        )

        resultado = lambda_handler(evento, None)

        self.assertEqual(resultado["statusCode"], 401)

    def test_cliente_no_puede_registrar(self):
        evento = self.evento("POST", {
            "nombre": "Cancha A",
            "ciudad": "Lima",
            "direccion": "Calle 123"
        })

        claims = evento["requestContext"]["authorizer"]["jwt"]["claims"]
        claims["cognito:groups"] = ["cliente"]

        resultado = lambda_handler(evento, None)

        self.assertEqual(resultado["statusCode"], 403)

    def test_listar_establecimientos(self):
        evento = self.evento("GET")
        evento["queryStringParameters"] = {
            "ciudad": "Trujillo"
        }

        resultado = lambda_handler(evento, None)
        cuerpo = json.loads(resultado["body"])

        self.assertEqual(resultado["statusCode"], 200)
        self.assertEqual(cuerpo["total_pagina"], 1)
        self.assertEqual(
            self.tabla.consulta["IndexName"],
            "BusquedaPorCiudad"
        )
        self.assertEqual(
            self.tabla.consulta["Limit"],
            20
        )

        self.assertEqual(
            self.tabla.consulta["ExpressionAttributeValues"][":ciudad"],
            "CIUDAD#TRUJILLO#APROBADO"
        )

    def test_ciudad_obligatoria(self):
        evento = self.evento("GET")

        resultado = lambda_handler(evento, None)

        self.assertEqual(resultado["statusCode"], 400)


if __name__ == "__main__":
    unittest.main()

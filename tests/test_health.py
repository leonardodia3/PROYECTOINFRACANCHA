
import json
import unittest

from backend.functions.health import lambda_handler


class TestHealthLambda(unittest.TestCase):

    def test_status_code(self):
        response = lambda_handler({}, None)

        self.assertEqual(
            response["statusCode"],
            200
        )

    def test_response_body(self):
        response = lambda_handler({}, None)

        body = json.loads(response["body"])

        self.assertEqual(
            body["status"],
            "ok"
        )

        self.assertEqual(
            body["service"],
            "cancha-go-backend"
        )

        self.assertEqual(
            body["environment"],
            "staging"
        )

    def test_content_type(self):
        response = lambda_handler({}, None)

        self.assertEqual(
            response["headers"]["Content-Type"],
            "application/json"
        )


if __name__ == "__main__":
    unittest.main()

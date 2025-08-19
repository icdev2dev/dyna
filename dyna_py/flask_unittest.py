import unittest
import requests

class APITestCase(unittest.TestCase):
    def test_hello(self): 
        url = "http://127.0.0.1:5000/schemas"

        payload = {
            "schema_name": "TestSchema",
            "is_top_level": True,
            "description": "Example made using requests"
        }

        response = requests.post(url, json=payload)
        assert response.status_code == 201
        print(response.status_code)   # Should print 201
        print(response.json())        # Should print "nice"

unittest.main()


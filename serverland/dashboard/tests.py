from django.test.testcases import TestCase

class CheckErrorHandlers(TestCase):
    """
    UnitTest checking that HTTP 404 and 500 error pages render.
    """
    def test_http_404_page_not_found(self):
        from django.test.client import Client
        c = Client()
        response = c.get('/some/non-existing/view/')
        self.assertEqual(response.status_code, 404)


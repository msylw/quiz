from django.test import TestCase

from django.test.utils import setup_test_environment
setup_test_environment()

from django.test import Client

from quiz.models import User

# Pylint false positive:
#pylint: disable=maybe-no-member,no-member


class StartView(TestCase):
    fixtures = ['quiz/dbdump.json']
    user_agent = 'Mozilla/5.0'
    language = 'LANGUAGE'

    def setUp(self):  # pylint: disable=invalid-name
        pass

    def test_start_redirect(self):
        client = Client(
            HTTP_USER_AGENT=self.user_agent,
            HTTP_ACCEPT_LANGUAGE=self.language)

        response = client.get('/start/1//')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.has_header("location"))

        #print response["location"]
        response = client.get(response["location"])
        self.assertEqual(response.status_code, 200)

        self.assertTrue("uuid" in response.context)

        uuid = response.context["uuid"]
        # 'http://testserver/start/1/451a9c1d-9c91-4e52-9998-603997c74b80/'
        user = User.objects.get(uuid=uuid)

        self.assertIsNotNone(user.created)

        self.assertEqual(user.user_agent, self.user_agent)
        self.assertEqual(user.language, self.language)

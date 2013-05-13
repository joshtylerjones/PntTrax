"""
Setting up basic test cases.
Called using manage.py and specifying the test.py settings extension.
(virtualenv)$ python manage.py test GPSTracker

Using coverage.py
(virtualenv)$ coverage run manage.py test GPSTracker # Execute Tests
(virtualenv)$ coverage run manage.py test GPSTracker --settings=PntTrax.settings.tests
(virtualenv)$ coverage run manage.py test GPSTracker --settings=PntTrax.settings.tests --verbosity 2
(virtualenv)$ coverage html --include="/Users/matt/PycharmProjects/PntTrax/GPSTracker*" --omit="admin.py" # Gen HTML

For a list of assertions, see:
https://docs.djangoproject.com/en/dev/topics/testing/overview/#assertions
"""

import os
from django.test import TestCase, Client
from GPSTracker.models import Line


class GetPages(TestCase):
    fixtures = ['test_data.json', ]

    def setUp(self):
        """
        Create a client
        """
        self.client = Client()
        self.client.login(username='matt', password='test')

    def test_response(self):
        # Issue a GET request.
        APP_ROOT = '/gpstracker'
        URLS = ['about','clients','groups/1','groups/detail/1']
        for url in URLS:
            response = self.client.get(os.path.join(APP_ROOT, url + '/'))
            # Check that the response is 200 OK.
            self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 200)

class testAuthorization(TestCase):
    """
    # Non-logged in users shouldn't see anything.
    # City of Yakima users should only see CoY data.
    # City of Bainbridge users should only see CoB data.
    # Ridolfi staff should see both.
    """
    fixtures = ['test_data.json']

    def setUp(self):
        """
        Create a client.
        """
        self.client = Client()
        self.APP_ROOT = '/gpstracker'

    def test_no_login(self):
        response = self.client.get(os.path.join(self.APP_ROOT, 'clients/'), follow=True)
        self.assertTemplateUsed(response, '../templates/registration/login.html')

    def test_staff(self):
        self.client.login(username='matt', password='test')
        response = self.client.get(os.path.join(self.APP_ROOT, 'clients/'), follow=True)
        self.assertEqual(len(response.context['client_list']),2)
        self.client.logout()

    def test_client(self):
        self.client.login(username='yakima', password='test')
        response = self.client.get(os.path.join(self.APP_ROOT, 'clients/'), follow=True)
        self.assertEqual(len(response.context['client_list']),1)
        self.client.logout()

class testGeomExport(TestCase):
    """
    Check various export formats for geometries:
    KML, SHP, GeoJSON.
    Should Check Content-Type headers.
    """
    fixtures = ['test_data.json']

    def setUp(self):
        """
        Create a client.
        """
        self.client = Client()
        self.APP_ROOT = '/gpstracker'

    def test_GeoJSON(self):
        self.client.login(username='matt', password='test')
        response = self.client.get(os.path.join(self.APP_ROOT, 'geojson/point/group/7/'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'text/plain')

    def test_KML(self):
        self.client.login(username='matt', password='test')
        response = self.client.get(os.path.join(self.APP_ROOT, 'kml/point/group/7/'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/vnd.google-earth.kml+xml')

    def test_SHP(self):
        self.client.login(username='matt', password='test')
        response = self.client.get(os.path.join(self.APP_ROOT, 'shp/point/group/7/'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/zip')

class test_fileUpload(TestCase):
    """
    Test a file upload.
    In this test, a shapefile containing two line features is
    loaded into the group with PK 7.
    Get count of features in group pre-upload
    Assert that count after upload = pre+two.
    Assert upload_success.html template is rendered.
    """
    fixtures = ['test_data.json']

    def setUp(self):
        """
        Create a client.
        """
        self.client = Client()
        self.APP_ROOT = '/gpstracker'

    def test_upload(self):
        """
        Test file upload works.
        """
        self.client.login(username='matt', password='test')
        testSHPPath = os.path.join(os.path.dirname(__file__), 'fixtures/QGIS_Lines.zip')
        with open(testSHPPath) as goodSHP:
            self.client.post('/gpstracker/uploadfile/', {'file': goodSHP})

        shpFieldMappings =  {
            'type': u'',
            'collectDates': u'GPS_Date',
            'comment': u'comment',
            'group': u'7',
            'method': u'',
            'name': u'Feat_Name'
        }

        # Get count of line features in group prior to upload.
        pre_feat_count = len(Line.objects.filter(group__pk=7))

        response = self.client.post(os.path.join(self.APP_ROOT, 'uploadfile/2'), shpFieldMappings, follow=True)

        self.assertEqual(len(Line.objects.filter(group__pk=7)), pre_feat_count + 2)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gpstracker/upload_success.html')

import unittest
import random
import datetime
import pickle
import mock
from tables.models import Table, Camera
from mockredis import mock_redis_client
from tables.camera_client import CameraClient


class TestTableOperations(unittest.TestCase):

    @mock.patch('tables.models.datetime')
    def test_claiming_table(self, m_datetime):
        m_datetime.now = lambda: 12
        user_id = "user-1"
        table_id = "test-1"

        table = Table(table_id)
        table.redis_client = self.mock_redis
        table.claim(user_id)

        table_status = table.check()[0]
        desired_output = {
            'action': 'claim',
            'user_id': 'user-1',
            'how_long': datetime.timedelta(0, 1800),
            'created': 12
        }

        self.assertEqual(table_status, desired_output)
        self.assertTrue(table.is_used_now())

    def test_showing_tables(self):
        pass

    def test_freeing_table(self):
        user_id = "user-1"
        table_id = "test-1"

        table = Table(table_id)
        table.redis_client = self.mock_redis
        table.claim(user_id)

        self.assertTrue(table.is_used_now())
        table.free(user_id)
        self.assertFalse(table.is_used_now())
        self.assertEqual(len(table.check()), 2)

    def setUp(self):
        self.mock_redis = mock_redis_client()


class CameraClientTest(unittest.TestCase):
    def setUp(self):
        self.sample_size = 4
        tables = ['table-%s' % x for x in xrange(self.sample_size)]
        self.camera = Camera('camera')
        self.mock_redis = mock_redis_client()
        self.camera.redis_client = self.mock_redis

    def test_pushing_image(self):
        image_path = 'tests_data/kitten.jpg'
        self.camera.push_image(
            image_path
        )
        images = self.camera.get_images()
        image = images[0]
        self.assertEqual(image.size, (200, 300))

    def test_pushing_chaos_data(self):
        sample_size = 19
        table_id_1 = 'table_id_1'
        table_id_2 = 'table_id_2'
        chaos_levels = [{
            table_id_1: random.randint(0, 100),
            table_id_2: random.randint(0, 100),
        } for x in xrange(sample_size)]

        for chaos_level in chaos_levels:
            self.camera.push_chaos_levels(chaos_level)

        self.assertEqual(
            len(self.camera.get_chaos_levels(table_id_1, 100)),
            sample_size
        )

if __name__ == '__main__':
    unittest.main()

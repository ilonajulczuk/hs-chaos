import unittest
import random
import datetime
import pickle
import mock
from mockredis import mock_redis_client
from tables.manager import TableManager
from tables.reporter import ChaosReporter
from tables.camera_client import CameraClient


class TestTableOperations(unittest.TestCase):

    @mock.patch('tables.manager.datetime')
    def test_claiming_table(self, m_datetime):
        m_datetime.now = lambda: 12
        user_id = "user-1"
        table_id = "test-1"

        self.manager.claim_table(table_id, user_id)

        table_status = self.manager.check_table(table_id)[0]
        desired_output = {
            'action': 'claim',
            'user_id': 'user-1',
            'how_long': datetime.timedelta(0, 1800),
            'created': 12
        }

        self.assertEqual(table_status, desired_output)
        self.assertTrue(self.manager.is_table_used_now(table_id))

    def test_showing_tables(self):
        camera_id = 'camera-1'
        sample_size = 4
        users = ['user-%s' % x for x in xrange(sample_size)]
        tables = ['table-%s' % x for x in range(sample_size)]

        for table in tables:
            self.manager.register_table(table, camera_id)

        for n, (user, table) in enumerate(zip(users, tables)):
            for x in xrange(n):
                if (n + 1) % 2:
                    self.manager.claim_table(table, user)
                else:
                    self.manager.free_table(table, user)

        statuses = self.manager.show_tables_statuses()
        self.assertEqual(len(statuses), sample_size)

        for x in xrange(sample_size):
            self.assertEqual(len(statuses[x]), x)

    def test_freeing_table(self):
        user_id = "user-1"
        table_id = "test-1"
        self.manager.claim_table(table_id, user_id)

        self.assertTrue(self.manager.is_table_used_now(table_id))
        self.manager.free_table(table_id, user_id)
        self.assertFalse(self.manager.is_table_used_now(table_id))
        self.assertEqual(len(self.manager.check_table(table_id)), 2)

    def test_registering_tables(self):
        cameras = [
            {
                "camera_id": 1,
                "tables": [
                    "1", "2", "3"
                ]
            },
            {
                "camera_id": 2,
                "tables": [
                    "4", "5", "6"
                ]
            }
        ]
        for camera in cameras:
            camera_id = camera['camera_id']
            for table_id in camera['tables']:
                self.manager.register_table(table_id, camera_id)

        keys_from_db = self.manager.get_tables_ids()
        keys_from_db.sort()
        self.assertEqual(
            keys_from_db,
            [str(x) for x in xrange(1, 7)]
        )

    def setUp(self):
        self.manager = TableManager()
        self.mock_redis = mock_redis_client()
        self.manager.redis_client = self.mock_redis


class CameraClientTest(unittest.TestCase):
    def setUp(self):
        self.sample_size = 4
        tables = ['table-%s' % x for x in xrange(self.sample_size)]
        self.client = CameraClient('camera', tables)
        self.client.register()
        self.mock_redis = mock_redis_client()
        self.client.redis_client = self.mock_redis

    def test_pushing_image(self):
        image_path = 'tests_data/kitten.jpg'
        self.client.push_image(
            image_path
        )
        self.client.register()
        reporter = ChaosReporter()
        reporter.redis_client = self.mock_redis
        images = reporter.get_images_for_all_cams()
        image = images[0][0]
        self.assertEqual(image.size, (200, 300))

    def test_pushing_chaos_data(self):
        sample_size = 19
        table_id_1 = 'table_id_1'
        table_id_2 = 'table_id_2'
        chaos_levels = [{
            table_id_1: random.randint(0, 100),
            table_id_2: random.randint(0, 100),
        } for x in xrange(sample_size)]
        self.client.register()

        reporter = ChaosReporter()
        reporter.redis_client = self.mock_redis
        for chaos_level in chaos_levels:
            self.client.push_chaos_levels(chaos_level)

        self.assertEqual(
            len(reporter.get_last_chaos_levels(table_id_1)),
            self.client.LIST_LIMIT
        )

if __name__ == '__main__':
    unittest.main()

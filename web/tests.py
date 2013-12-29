import unittest
import datetime
import pickle
import mock
from mockredis import mock_redis_client
from tables.manager import TableManager


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

if __name__ == '__main__':
    unittest.main()

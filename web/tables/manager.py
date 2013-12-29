import redis
import pickle
from datetime import timedelta, datetime


class TableManager(object):
    table_statuses = 'table-{table_id}-status'
    table_index = 'tables'
    LIST_LIMIT = 10
    table_users = 'table-{table_id}-users'
    table_busy = 'table-{table_id}-busy'

    table_actions = {
        'claim': 'busy',
        'free': 'free'
    }


    def __init__(self, **redis_credentials):
        self.redis_client = redis.Redis(**redis_credentials)

    def update_table_current_usage(self, table_id, action, how_long):
        table_key = self.table_busy.format(table_id=table_id)
        if action == 'claim':
            self.redis_client.setex(
                table_key,
                'busy',
                how_long.seconds,
            )
        elif action == 'free':
            self.redis_client.delete(table_key)

    def is_table_used_now(self, table_id):
        return self.redis_client.exists(
            self.table_busy.format(table_id=table_id)
        )

    def update_table(self, table_id, user_id,
                     how_long,
                     action):

        table_status_key = self.table_statuses.format(
            table_id=table_id
        )

        status_data = pickle.dumps({
            'action': action,
            'user_id': user_id,
            'how_long': how_long,
            'created': datetime.now()
        })

        self.redis_client.lpush(
            table_status_key,
            status_data
        )

        # contrain list length to LIST_LIMIT
        self.redis_client.ltrim(
            table_status_key,
            0,
            self.LIST_LIMIT
        )
        self.update_table_current_usage(table_id, action, how_long)

    def claim_table(self, table_id, user_id,
                    how_long=timedelta(minutes=30)):
        """save in redis new status and new user for this table"""

        self.update_table(table_id, user_id, how_long, action='claim')

    def free_table(self, table_id, user_id):
        self.update_table(
            table_id,
            user_id,
            action='free',
            how_long=timedelta(0)
        )

    def register_table(self, table_id, camera_id):
        table_data = pickle.dumps({
            "camera_id": camera_id,
            "registered": datetime.now()
        })

        self.redis_client.hset(
            self.table_index,
            table_id,
            table_data
        )

    def get_tables_ids(self):
        return self.redis_client.hkeys(self.table_index)

    def show_tables_statuses(self):
        tables = self.get_tables_ids()
        return [self.check_table(table_id) for table_id in tables]

    def check_table(self, table_id):
        raw_table_statuses = self.redis_client.lrange(
            TableManager.table_statuses.format(table_id=table_id),
            0,
            self.LIST_LIMIT
        )

        return [pickle.loads(status) for status in raw_table_statuses]


import redis
import StringIO
import pickle
from PIL import Image
import datetime
from datetime import timedelta, datetime
from settings import redis_defaults


app_namespace = "junk_vision"

cameras_namespace = "cameras"

camera_keys = {
    "chaos_levels": "table:{table_id}:messiness",
    "movement": "table:{table_id}:movement",
    "images": "images",
    "tables": "tables"
}

CAMERA_KEYS = {
    key: app_namespace + ":" +  cameras_namespace + ":{camera_id}:" + value
    for key, value in camera_keys.iteritems()
}

table_namespaces = "table_management"

table_keys = {
    "actions": "table:{table_id}:actions",
    "status": "table:{table_id}:status"
}

TABLE_KEYS = {
    key: app_namespace + ":" + value
    for key, value in table_keys.iteritems()
}


class CameraManager(object):

    def __init__(self, redis_credentials=redis_defaults):
        self.redis_client = redis.Redis(**redis_credentials)

    def get_cameras_ids(self):
        status_keys = self.redis_client.keys(
            CAMERA_KEYS['chaos_levels'].format(camera_id="*", table_id="*")
        )
        ids = [key.split(":")[2] for key in status_keys]
        return list(set(ids))

    def get_all_cameras(self):
        return [Camera(id) for id in self.get_cameras_ids()]


class Camera(object):
    LIST_LIMIT = 100

    def __init__(self, camera_id, redis_credentials=redis_defaults):
        self.camera_id = camera_id
        self.redis_client = redis.Redis(**redis_credentials)

    def push_chaos_levels(self, chaos_levels):
        for table_id, chaos_level in chaos_levels.items():
            table_key = CAMERA_KEYS['chaos_levels'].format(
                camera_id=self.camera_id,
                table_id=table_id
            )
            self.redis_client.lpush(
                table_key,
                chaos_level
            )

            self.redis_client.ltrim(
                table_key,
                0,
                self.LIST_LIMIT - 1
            )

    def push_image(self, image_path):
        output = StringIO.StringIO()
        im = Image.open(image_path)
        im.save(output, format=im.format)

        key = CAMERA_KEYS['images'].format(
            camera_id=self.camera_id
        )

        self.redis_client.lpush(
            key,
            output.getvalue()
        )

        output.close()

        self.redis_client.ltrim(
            key,
            0,
            self.LIST_LIMIT
        )

    def get_chaos_levels(self, table_id, n=1):
        table_key = CAMERA_KEYS['chaos_levels'].format(
            camera_id=self.camera_id,
            table_id=table_id
        )

        return self.redis_client.lrange(
            table_key,
            0,
            10000
        )[:n]

    def get_images(self, n=1):
        key = CAMERA_KEYS['images'].format(
            camera_id=self.camera_id
        )
        raw_images = self.redis_client.lrange(
            key,
            0,
            1000
        )
        return [Image.open(StringIO.StringIO(raw)) for raw in raw_images]


class TableManager(object):

    def __init__(self, redis_credentials=redis_defaults):
        self.redis_client = redis.Redis(**redis_credentials)

    def get_tables_ids(self, camera_id):
        status_keys = self.redis_client.keys(
            CAMERA_KEYS['chaos_levels'].format(camera_id=camera_id, table_id="*")
        )
        ids = [key.split(":")[-2] for key in status_keys]
        return ids

    def get_all_tables(self, camera_id):
        return [Table(id) for id in self.get_tables_ids(camera_id)]


class Table(object):
    table_actions = {
        'claim': 'busy',
        'free': 'free'
    }

    LIST_LIMIT = 10

    def __init__(self, id, redis_credentials=redis_defaults):
        self.id = id
        self.name = id.split('-')[-2]
        self.color = id.split('-')[-1]
        self.redis_client = redis.Redis(**redis_credentials)

    def is_used_now(self):
        key = TABLE_KEYS['status'].format(table_id=self.id)
        return self.redis_client.exists(
            key
        )

    def free(self, user_id):
        self.update(
            user_id,
            action='free',
            how_long=timedelta(0)
        )

    def claim(self, user_id,
                    how_long=timedelta(minutes=30)):
        """save in redis new status and new user for this table"""

        self.update(user_id, how_long, action='claim')

    def update(self, user_id, how_long, action):
        key = TABLE_KEYS['actions'].format(
            table_id=self.id
        )

        status_data = pickle.dumps({
            'action': action,
            'user_id': user_id,
            'how_long': how_long,
            'created': datetime.now()
        })

        self.redis_client.lpush(
            key,
            status_data
        )

        # constrain list length to LIST_LIMIT
        self.redis_client.ltrim(
            key,
            0,
            self.LIST_LIMIT
        )
        self.update_current_usage(action, how_long)

    def update_current_usage(self, action, how_long):
        key = TABLE_KEYS['status'].format(table_id=self.id)
        if action == 'claim':
            self.redis_client.setex(
                key,
                'busy',
                how_long.seconds,
            )

        elif action == 'free':
            self.redis_client.delete(key)

    def check(self):
        key = TABLE_KEYS['actions'].format(
            table_id=self.id
        )
        raw_actions = self.redis_client.lrange(
            key,
            0,
            self.LIST_LIMIT
        )

        return [pickle.loads(action) for action in raw_actions]

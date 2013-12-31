import redis
from PIL import Image
import pickle
import StringIO
from datetime import timedelta, datetime


class CameraClient(object):
    def __init__(self, camera_id, tables, redis_credentials={}):
        """Camera should have an unique id and clearly define
        it's tables"""

        self.LIST_LIMIT = 10
        self.camera_id = camera_id
        self.tables = tables
        self.table_index = 'tables'
        self.camera_image_list = '%s-image' % camera_id
        self.redis_client = redis.Redis(**redis_credentials)
        self.table_chaos = 'table-chaos-{table_id}'

    def register(self):
        self.redis_client.sadd('cameras', self.camera_id)
        self.redis_client.sadd(self.camera_id, *self.tables)

        for table_id in self.tables:
            self.register_table(table_id, self.camera_id)

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

    def push_data(self, image_path, chaos_levels):
        self.push_image(image)
        self.push_chaos_levels(chaos_levels)

    def push_chaos_levels(self, chaos_levels):
        for table_id, chaos_level in chaos_levels.iteritems():
            table_key = self.table_chaos.format(table_id=table_id)
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

        key = '%s-image' % self.camera_id
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

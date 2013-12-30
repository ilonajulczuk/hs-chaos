import redis
import StringIO
from PIL import Image


class ChaosReporter(object):
    table_index = 'tables'
    table_chaos = 'table-chaos-{table_id}'

    def __init__(self, redis_credentials={}):
        self.redis_client = redis.Redis(**redis_credentials)

    def get_all_cameras(self):
        return self.redis_client.smembers('cameras')

    def get_all_tables(self):
        return self.redis_client.hkeys(self.table_index)

    def get_last_images(self, camera_id):
        camera_image_list = '%s-image' % camera_id
        raw_images = self.redis_client.lrange(
            camera_image_list,
            0,
            1000
        )
        return [Image.open(StringIO.StringIO(raw)) for raw in raw_images]

    def get_last_chaos_levels(self, table_id):
        table_key = self.table_chaos.format(table_id=table_id)

        return self.redis_client.lrange(
            table_key,
            0,
            10000
        )

    def get_images_for_all_cams(self):
        cameras = self.get_all_cameras()
        return [self.get_last_images(camera) for camera in cameras]

    def get_chaos_levels_for_all_tables(self):
        tables = get_all_tables()
        return [self.get_last_chaos_levels(table) for table in tables]

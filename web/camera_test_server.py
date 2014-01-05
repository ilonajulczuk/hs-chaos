import time
import random

from tables.models import Camera
from tables.camera_client import CameraClient
from tables.reporter import ChaosReporter


class FakeCamera(object):
    def __init__(self):
        self.sample_size = 4
        tables  = ['table_id_1', 'table_id_2']
        self.camera = Camera('camera')

    def push_image(self):
        image_path = 'tests_data/kitten.jpg'
        self.camera.push_image(
            image_path
        )

    def push_chaos_data(self):
        sample_size = 19
        table_id_1 = 'table_id_1'
        table_id_2 = 'table_id_2'
        chaos_levels = {
            table_id_1: random.randint(0, 100),
            table_id_2: random.randint(0, 100),
        }

        self.camera.push_chaos_levels(chaos_levels)

def main():
    camera = FakeCamera()
    while True:
        camera.push_image()
        camera.push_chaos_data()
        time.sleep(5)

if __name__ == '__main__':
    main()

import functools
from tables.models import TableManager, CameraManager


def login_required(fn):
    @functools.wraps
    def inner(*args, **kwargs):
        if not session['username']:
            return "404"
        else:
            return fn(*args, **kwargs)
    return inner

def store_image(image, camera_id):
    path = camera_id + "camera_current.jpg"
    image.save('static' + '/' + path)
    return path


def table_statuses():
    manager = TableManager()
    cameras = CameraManager().get_all_cameras()
    data_per_camera = {}
    for camera in cameras:
        tables = manager.get_all_tables(camera.camera_id)
        table_statuses = []
        for table in tables:
            chaos_level = camera.get_chaos_levels(table.id)[0]
            occupancy_data = table.check()
            occupied = table.is_used_now()
            table_status = {
                'id': table.id,
                'name': table.name,
                'color': table.color,
                'chaos_percentage': chaos_level,
                'actions': occupancy_data,
                'occupied': occupied
            }

            if float(chaos_level) > 50 and not occupied:
                table_status['message'] = 'Oh snap! There\'s a mess and there is nobody near!'
            table_statuses.append(table_status)
            data_per_camera[camera.camera_id] = table_statuses

    return data_per_camera


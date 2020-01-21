from server import celery_app

class MiscTasker(object):
    @staticmethod
    def set_ip_location(ip_address_id, ip):
        task = {'ip_address_id': ip_address_id, 'ip': ip}
        ip_location_task = celery_app.signature('worker.celery_tasks.ip_location', args=(task,))
        ip_location_task.delay()

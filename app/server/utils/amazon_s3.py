import os
import requests
import datetime
from flask import g, current_app
from botocore.exceptions import ClientError
from server import s3
import base64

class LoadFileException(Exception):
    pass

def get_bucket_name():
    return 'sempoctp-' + str(current_app.config['DEPLOYMENT_NAME'].lower())

def upload_local_file_to_s3(local_file_path, filename):
    # generate bucket name unique to this deployment
    bucket_name = get_bucket_name()

    # Call S3 to list current buckets
    response = s3.list_buckets()

    # check for a bucket for this deployment, create bucket if none exists
    buckets = [bucket['Name'] for bucket in response['Buckets']]

    if bucket_name not in buckets:
        try:
            s3.create_bucket(Bucket=bucket_name)
            print('Created Bucket: ', bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyExists':
                print("Bucket already exists")
            else:
                print("Unexpected error: %s" % e)

    s3.upload_file(local_file_path, bucket_name, filename)

    file_url = s3.generate_presigned_url('get_object',
                                         Params={'Bucket': bucket_name, 'Key': filename}, ExpiresIn=3600 * 24 * 7)

    return file_url


def get_file_url(filename):

    # generate bucket name unique to this deployment
    bucket_name = get_bucket_name()

    file_url = s3.generate_presigned_url('get_object',
                                         Params={'Bucket': bucket_name, 'Key': filename}, ExpiresIn=3600 * 24 * 7)

    return file_url


def generate_new_filename(original_filename, file_type = 'UnknownType', user_id = None):

    if user_id is None:
        if g.user:
            user_id = g.user.id
        else:
            user_id = 'UnknownID'

    extension = original_filename.split('.')[-1]

    export_time = datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y%m%dT%H%M%SM%f")

    return file_type.lower() + '-user_' + str(user_id) + '-' + export_time + '.' + extension

def make_sure_path_exists(path):
    if not os.path.exists(path):
        os.mkdir(path)

def get_local_save_path(new_filename):
    local_save_directory = os.path.join(current_app.config['BASEDIR'], "tmp/")
    make_sure_path_exists(local_save_directory)
    return os.path.join(local_save_directory, new_filename)

def save_to_s3_from_url(external_url, new_filename):

    local_save_path = get_local_save_path(new_filename)

    response = requests.get(external_url, stream=True)

    if response.status_code == 200:
        with open(local_save_path, 'wb') as f:
            f.write(response.content)

    else:
        raise LoadFileException("File Could not be loaded")

    s3_url = upload_local_file_to_s3(local_save_path, new_filename)

    os.remove(local_save_path)

    return s3_url


def save_to_s3_from_image_base64(image_base64, new_filename):
    if image_base64 is None:
        return
    local_save_path = get_local_save_path(new_filename)

    imgdata = base64.b64decode(image_base64)

    with open(local_save_path, 'wb') as f:
        f.write(imgdata)

    s3_url = upload_local_file_to_s3(local_save_path, new_filename)

    os.remove(local_save_path)

    return s3_url


def save_to_s3_from_image_object(image_object, new_filename):

    local_save_path = get_local_save_path(new_filename)

    image_object.save(local_save_path)

    url = upload_local_file_to_s3(local_save_path, new_filename)

    os.remove(local_save_path)

    return url


def save_to_s3_from_document(document, new_filename):

    local_save_path = get_local_save_path(new_filename)

    document.save(local_save_path)

    url = upload_local_file_to_s3(local_save_path, new_filename)

    os.remove(local_save_path)

    return url

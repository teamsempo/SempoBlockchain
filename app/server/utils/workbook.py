import os
from flask import g, current_app
from server.utils.amazon_s3 import upload_local_file_to_s3, get_local_save_path
from server.utils.amazon_ses import send_export_email


def save_local_file_and_upload_to_s3(wb, workbook_filename, email=None):
    file_url = ''
    if not current_app.config['IS_TEST']:
        # Save locally
        local_save_path = get_local_save_path(workbook_filename)
        wb.save(filename=local_save_path)

        # upload to s3
        file_url = upload_local_file_to_s3(local_save_path, workbook_filename)

        if email:
            send_export_email(file_url, email)

        else:
            if g.user.email is not None:
                send_export_email(file_url, g.user.email)

        # remove local file path
        os.remove(local_save_path)

    return file_url

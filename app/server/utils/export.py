import os

from flask import render_template, current_app, g
from weasyprint import HTML

from server.schemas import pdf_users_schema
from server.utils.amazon_s3 import upload_local_file_to_s3, get_local_save_path
from server.utils.amazon_ses import send_export_email
from pdfrw import PdfReader, PdfWriter

def generate_pdf_export(users, pdf_filename):
    users = list(users)
    serialised_users = pdf_users_schema.dump(users).data

    serialised_users.sort(key=lambda u: f'{u.get("last_name")} {u.get("first_name")}')

    html = render_template(
        'user_export.html',
        title='export',
        users=serialised_users
    )

    return export_pdf_via_s3(html, pdf_filename)


def export_pdf_via_s3(html, filename, email=None):

    def pdf_save_meth(path):
        HTML(string=html).write_pdf(path)
        # Strip producer PDF metadata
        pdf = PdfReader(path)
        pdf.Info.Producer = ''
        PdfWriter(path, trailer=pdf).write()
    return _export_via_s3(pdf_save_meth, filename, email)


def export_workbook_via_s3(wb, filename, email=None):

    def wb_save_method(path):
        wb.save(path)

    return _export_via_s3(wb_save_method, filename, email)


def _export_via_s3(save_method, filename, email=None):
    file_url = ''
    if not current_app.config['IS_TEST']:
        # Save locally
        local_save_path = get_local_save_path(filename)

        save_method(local_save_path)

        # upload to s3
        file_url = upload_local_file_to_s3(local_save_path, filename)

        if email:
            send_export_email(file_url, email)

        else:
            if g.user.email is not None:
                send_export_email(file_url, g.user.email)

        # remove local file path
        os.remove(local_save_path)

    return file_url

WINDOW_SIZE = 250
def partition_query(query):
    start = 0
    while True:
        stop = start + WINDOW_SIZE
        things = query.slice(start, stop).all()
        if len(things) == 0:
            break
        for thing in things:
            yield thing
        start += WINDOW_SIZE

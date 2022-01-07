from sqlalchemy.ext.hybrid import hybrid_property
from server.utils.amazon_s3 import get_file_url

from server import db
from server.models.utils import ModelBase


class UploadedResource(ModelBase):
    """
    UploadedResource model handles documents, files and photos uploaded to Amazon S3.
    """
    __tablename__               = 'uploaded_resource'

    filename                    = db.Column(db.String)
    file_type                   = db.Column(db.String)
    user_filename               = db.Column(db.String)
    reference                   = db.Column(db.String)

    credit_transfer_id          = db.Column(db.Integer, db.ForeignKey("credit_transfer.id"), index=True)
    user_id                     = db.Column(db.Integer, db.ForeignKey("user.id"))
    kyc_application_id          = db.Column(db.Integer, db.ForeignKey('kyc_application.id'))

    @hybrid_property
    def file_url(self):
        return get_file_url(self.filename)


from sqlalchemy.ext.hybrid import hybrid_property
from server.utils.amazon_s3 import get_file_url

from server import db
from server.models.utils import ModelBase

class UploadedImage(ModelBase):
    __tablename__ = 'uploaded_image'

    filename = db.Column(db.String)
    image_type = db.Column(db.String)
    credit_transfer_id = db.Column(db.Integer, db.ForeignKey("credit_transfer.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    @hybrid_property
    def image_url(self):
        return get_file_url(self.filename)

class UploadedDocument(ModelBase):
    __tablename__               = 'uploaded_document'

    kyc_application_id = db.Column(db.Integer, db.ForeignKey('kyc_application.id'))

    filename                    = db.Column(db.String)
    file_type                   = db.Column(db.String)
    user_filename               = db.Column(db.String)
    reference                   = db.Column(db.String)

    @hybrid_property
    def file_url(self):
        return get_file_url(self.filename)

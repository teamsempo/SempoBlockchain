from server import db
from server.models.utils import ModelBase
from server.utils.custom_attribute import clean_value
from sqlalchemy.dialects.postgresql import JSONB

class CustomAttribute(ModelBase):
    __tablename__ = 'custom_attribute'

    name            = db.Column(db.String)
    attributes      = db.relationship("CustomAttributeUserStorage", back_populates="custom_attribute")
    cleaning_steps  = db.Column(JSONB, default=None) # E.x. [ { "replace": ["this", "that"] }, { "lower": null } ]
    options         = db.Column(JSONB, default=None) # E.x. ["male", "female", "other"]

    def clean_and_validate_custom_attribute(self, value):
        if self.cleaning_steps:
            value = clean_value(self.cleaning_steps, value)
        if self.options:
            if value not in self.options:
                raise Exception(f'{value} not a valid option for {self.name}! Please choose one of {self.options}')
        return value

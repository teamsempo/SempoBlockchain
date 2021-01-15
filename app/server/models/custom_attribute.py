from server import db
from server.models.utils import ModelBase
from server.models.custom_attribute_user_storage import CustomAttributeUserStorage
from server.utils.custom_attribute import clean_value
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
import enum

class MetricsVisibility(enum.Enum):
    SENDER = 'SENDER' 
    RECIPIENT = 'RECIPIENT'
    SENDER_AND_RECIPIENT = 'SENDER_AND_RECIPIENT'
    HIDDEN = 'HIDDEN' # Usable, but not visible surfaced in API


class CustomAttribute(ModelBase):
    __tablename__ = 'custom_attribute'

    name            = db.Column(db.String, index=True)
    attributes      = db.relationship("CustomAttributeUserStorage", back_populates="custom_attribute")
    cleaning_steps  = db.Column(JSONB, default=None) # E.x. [ { "replace": ["this", "that"] }, { "lower": null } ]
    options         = db.Column(JSONB, default=None) # E.x. ["male", "female", "other"]

    filter_visibility = db.Column(db.Enum(MetricsVisibility), default=MetricsVisibility.SENDER_AND_RECIPIENT, index=True)
    group_visibility = db.Column(db.Enum(MetricsVisibility), default=MetricsVisibility.SENDER_AND_RECIPIENT, index=True)

    # Different from just "options", becuase it checks what is being used in 
    # CustomAttributeUserStorage, as opposed to being a list to check against for
    # validation
    @hybrid_property
    def existing_options(self):
        options = db.session.query(CustomAttributeUserStorage.value)\
            .filter(CustomAttributeUserStorage.custom_attribute_id == self.id)\
            .distinct()\
            .all()
        return [o[0] for o in options]

    def clean_and_validate_custom_attribute(self, value):
        if self.cleaning_steps:
            value = clean_value(self.cleaning_steps, value)
        if self.options:
            if value not in self.options:
                raise Exception(f'{value} not a valid option for {self.name}! Please choose one of {self.options}')
        return value

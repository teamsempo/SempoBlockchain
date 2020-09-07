from server import db
from server.models.utils import OneOrgBase, ModelBase

class AttributeMap(OneOrgBase, ModelBase):
    __tablename__ = 'attribute_map'

    input_name = db.Column(db.String(), nullable=False)
    output_name = db.Column(db.String(), nullable=False)

    def __init__(self, input_name, output_name, organisation):
        self.input_name = input_name
        self.output_name = output_name
        self.organisation = organisation
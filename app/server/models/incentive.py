from server.models.utils import ModelBase
from sqlalchemy.dialects.postgresql import JSON
from server.models.organisation import Organisation
from server import db

class Incentive(ModelBase):
    """
    Incentives applied to transacitons at an orgnisation-level 
    """
    __tablename__       = 'incentive'
    incentive_rules = db.Column(JSON)
    organisation_id = db.Column(db.Integer, db.ForeignKey(Organisation.id))

    def handle_incentive(self):
        print('ayy')
        print(self.incentive_rules)

    def __init__(self, **kwargs):
        super(Incentive, self).__init__(**kwargs)
        if 'transfer_method' not in self.incentive_rules:
            raise Exception ('No transfer method provided')


"""
{
    transfer_method: [uuid, qr_data, nfc_serial_number] (one of)
    incentive_type: [percentage, fixed_amount]
    incentive_amount: 10
    incentive_recipient: [sender, recipient]
    restrictions:[
        {
            style: 'time_window'
            days: 7
            transactions: 15 
        }
        {
            style: currency
            days: 7
            limit: 100
        }
        ]
}

"""
from server import db
from server.models.utils import ModelBase


class TargetingSurvey(ModelBase):
    __tablename__ = 'targeting_survey'

    number_people_household = db.Column(db.Integer)
    number_below_adult_age_household = db.Column(db.Integer)
    number_people_women_household = db.Column(db.Integer)
    number_people_men_household = db.Column(db.Integer)
    number_people_work_household = db.Column(db.Integer)
    disabilities_household = db.Column(db.String)
    long_term_illnesses_household = db.Column(db.String)

    user = db.relationship(
        'User', backref='targeting_survey', lazy=True, uselist=False)

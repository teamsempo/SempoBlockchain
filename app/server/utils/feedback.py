from flask import current_app
from sqlalchemy import or_, and_
from server.models.transfer import TransferAccount, CreditTransfer
from server.models.feedback import Feedback
from server.models.user import User

def request_feedback_questions(user):
    questions = current_app.config['DEFAULT_FEEDBACK_QUESTIONS']
    balance_below_trigger = current_app.config['FEEDBACK_TRIGGERED_WHEN_BALANCE_BELOW']
    transfer_count_above_trigger = current_app.config['FEEDBACK_TRIGGERED_WHEN_TRANSFER_COUNT_ABOVE']
    if transfer_count_above_trigger == -1:
        # Makes it easy to disable the transfer count trigger by setting it to -1
        transfer_count_above_trigger = 999999999999

    user_transfer_accounts = TransferAccount.query.execution_options(show_all=True).filter(
        TransferAccount.users.any(User.id.in_([user.id]))).all()

    if user.has_beneficiary_role and (len(user_transfer_accounts) > 0):
        # todo: this will raise an error No 'user.transfer_account_id'. fix.
        # transfer_account = TransferAccount.query.get(user.transfer_account_id)
        transfer_account = user_transfer_accounts[0]  # get the first transfer account. todo: fix this for many-to-many

        transfer_number = CreditTransfer.query.filter(or_(
            CreditTransfer.recipient_user == user,
            CreditTransfer.sender_user == user
        )).count()

        feedback = Feedback.query.filter(and_(Feedback.user == user,
                                              Feedback.question.in_(questions))).first()

        if feedback is None and transfer_account.is_approved:

            if transfer_account.balance < balance_below_trigger or transfer_number > transfer_count_above_trigger:
                return questions

    return []

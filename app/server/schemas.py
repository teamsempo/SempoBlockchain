from flask import g
from marshmallow import Schema, fields, ValidationError, pre_load, post_dump, pre_dump
from server.utils.amazon_s3 import get_file_url
from server import models

class UserSchema(Schema):

    id      = fields.Int(dump_only=True)
    created = fields.DateTime(dump_only=True)

    first_name              = fields.Str()
    last_name               = fields.Str()

    email                   = fields.Str()
    phone                   = fields.Str()

    public_serial_number    = fields.Str()
    nfc_serial_number       = fields.Str()

    location                = fields.Str()
    lat                     = fields.Float()
    lng                     = fields.Float()

    one_time_code           = fields.Str()

    is_activated            = fields.Boolean()
    is_disabled             = fields.Boolean()

    is_beneficiary          = fields.Boolean(attribute='has_beneficiary_role')
    is_vendor               = fields.Boolean(attribute='has_vendor_role')
    is_any_admin            = fields.Boolean(attribute='is_any_admin')

    ap_user_id              = fields.Str()
    ap_bank_id              = fields.Str()
    ap_paypal_id            = fields.Str()
    kyc_state               = fields.Str()

    custom_attributes        = fields.Method("get_json_data")
    matched_profile_pictures = fields.Method("get_profile_url")

    transfer_account        = fields.Nested('server.schemas.TransferAccountSchema', exclude=('user',))

    def get_json_data(self, obj):
        
        allowed_custom_attributes_objs = models.CustomAttribute.query.all()
        allowed_custom_attributes = []

        for attribute in allowed_custom_attributes_objs:
            allowed_custom_attributes.append(attribute.name)

        custom_attributes = obj.custom_attributes

        if custom_attributes is None:
            return {}

        keys_to_pop = []
        for attribute_key in custom_attributes.keys():
            try:
                if 'uploaded_image_id' in custom_attributes[attribute_key]:
                    custom_attributes[attribute_key]['url'] = get_file_url(
                        custom_attributes[attribute_key]['value']
                    )
            except TypeError:
                pass

            if len(allowed_custom_attributes) > 0 and attribute_key not in allowed_custom_attributes:
                keys_to_pop.append(attribute_key)

        for key in keys_to_pop:
            custom_attributes.pop(key)

        return custom_attributes

    def get_profile_url(self, obj):
        processed_profile_pictures = []
        if obj.matched_profile_pictures:
            for profile in obj.matched_profile_pictures:
                profile['url'] = get_file_url(profile['value'])

                processed_profile_pictures.append(profile)
        return processed_profile_pictures


class UploadedImageSchema(Schema):
    id                      = fields.Int(dump_only=True)
    filename                = fields.Str()
    image_url               = fields.Function(lambda obj: obj.image_url)
    credit_transfer_id      = fields.Int()

class BlockchainAddressSchema(Schema):
    id = fields.Int(dump_only=True)
    created = fields.DateTime(dump_only=True)
    address = fields.Str()
    has_private_key = fields.Function(lambda obj: bool(obj.encoded_private_key))

class CreditTransferSchema(Schema):

    id      = fields.Int(dump_only=True)
    # created = fields.DateTime(dump_only=True)
    created = fields.DateTime(dump_only= True, attribute='resolved_date')
    authorising_user_email  = fields.Method('get_authorising_user_email')

    uuid = fields.String()

    @post_dump(pass_many=True)
    def filter_rejected(self, data, many):
        if not self.context.get('filter_rejected'):
            return data
        if many:
            return list(filter(lambda x: x['transfer_status'] != 'REJECTED', data))
        elif ['transfer_status'] == 'REJECTED':
            return None

    resolved                = fields.DateTime(attribute='resolved_date')
    transfer_amount         = fields.Int()
    transfer_type           = fields.Function(lambda obj: obj.transfer_type.value)
    transfer_mode           = fields.Function(lambda obj: obj.transfer_mode.value)
    transfer_status         = fields.Function(lambda obj: obj.transfer_status.value)

    transfer_use            = fields.Function(lambda obj: obj.transfer_use)


    sender_user             = fields.Nested(UserSchema, attribute='sender_user', only=("id", "first_name", "last_name"))
    recipient_user          = fields.Nested(UserSchema, attribute='recipient_user', only=("id", "first_name", "last_name"))

    sender_transfer_account    = fields.Nested("server.schemas.TransferAccountSchema", only=("id", "balance"))
    recipient_transfer_account = fields.Nested("server.schemas.TransferAccountSchema", only=("id", "balance"))

    sender_blockchain_address    = fields.Nested(BlockchainAddressSchema)
    recipient_blockchain_address = fields.Nested(BlockchainAddressSchema)

    attached_images         = fields.Nested(UploadedImageSchema, many=True)

    lat               = fields.Function(lambda obj: obj.recipient_transfer_account.primary_user.lat)
    lng               = fields.Function(lambda obj: obj.recipient_transfer_account.primary_user.lng)

    is_sender               = fields.Function(lambda obj: obj.sender_transfer_account_id == g.user.transfer_account_id)

    blockchain_status = fields.Function(lambda obj: obj.blockchain_status)
    blockchain_status_breakdown = fields.Function(lambda obj: obj.blockchain_status_breakdown)
    uncompleted_blockchain_tasks = fields.Function(lambda obj: list(obj.uncompleted_blockchain_tasks))

    def get_authorising_user_email(self, obj):
        authorising_user_id = obj.authorising_user_id
        if authorising_user_id is None:
            return None

        authorising_user = models.User.query.get(obj.authorising_user_id)
        if authorising_user is None:
            return None

        return authorising_user.email



class TransferAccountSchema(Schema):

    id      = fields.Int(dump_only=True)
    created = fields.DateTime(dump_only=True)

    is_approved             = fields.Boolean()
    # balance                 = fields.Int()

    balance                 = fields.Function(lambda obj: obj.balance)

    primary_user_id         = fields.Int()

    transfer_account_name   = fields.Str()
    is_vendor               = fields.Boolean()

    payable_period_type     = fields.Str()
    payable_period_length   = fields.Int()
    payable_epoch           = fields.Str()
    payable_period_epoch    = fields.DateTime()

    blockchain_address = fields.Nested(BlockchainAddressSchema)

    #TODO: Make this plural because it's stupid
    users                   = fields.Nested(UserSchema, attribute='users', many = True, exclude=('transfer_account',))

    credit_sends            = fields.Nested(CreditTransferSchema, many=True)
    credit_receives         = fields.Nested(CreditTransferSchema, many=True)

    def get_primary_user_id(self, obj):
        users = obj.user
        print(obj)
        return sorted(users, key=lambda user: user.created)[0].id

class TransferCardSchema(Schema):
    id = fields.Int(dump_only=True)
    created = fields.DateTime(dump_only=True)

    public_serial_number = fields.Str()
    nfc_serial_number = fields.Function(lambda obj: obj.nfc_serial_number.upper())

    amount_loaded = fields.Function(lambda obj: obj._amount_loaded)
    amount_loaded_signature = fields.Str()

    user = fields.Nested(UserSchema, only=('first_name', 'last_name'))


class ReferralSchema(Schema):

    id      = fields.Int(dump_only=True)
    created = fields.DateTime(dump_only=True)

    first_name = fields.Str()
    last_name = fields.Str()
    reason = fields.Str()
    phone = fields.Str()


class SavedFilterSchema(Schema):
    id      = fields.Int(dump_only=True)
    created = fields.DateTime(dump_only=True)

    name    = fields.Str()
    filter  = fields.Method('get_filter_json')

    def get_filter_json(self, obj):
        return obj.filter


class BankAccountSchema(Schema):
    id              = fields.Int(dump_only=True)
    created         = fields.DateTime(dump_only=True)

    wyre_id                  = fields.Str()
    kyc_application_id = fields.Int()

    bank_country    = fields.Str()
    routing_number  = fields.Str()
    account_number  = fields.Str()
    currency        = fields.Str()


class UploadedDocumentSchema(Schema):
    id              = fields.Int(dump_only=True)
    created         = fields.DateTime(dump_only=True)

    kyc_application_id = fields.Int()

    filename        = fields.Str()
    file_type       = fields.Str()
    reference       = fields.Str()
    user_filename   = fields.Str()
    file_url        = fields.Function(lambda obj: obj.file_url)


class KycApplicationSchema(Schema):
    id                  = fields.Int(dump_only=True)
    created             = fields.DateTime(dump_only=True)

    type                = fields.Str()

    trulioo_id          = fields.Str()
    wyre_id             = fields.Str()
    kyc_status          = fields.Str()
    kyc_actions         = fields.Method('get_kyc_actions_json')

    first_name          = fields.Str()
    last_name           = fields.Str()
    phone               = fields.Str()
    dob                 = fields.Str()
    business_legal_name = fields.Str()
    business_type       = fields.Str()
    tax_id              = fields.Str()
    website             = fields.Str()
    date_established    = fields.Str()
    country             = fields.Str()
    street_address      = fields.Str()
    street_address_2    = fields.Str()
    city                = fields.Str()
    region              = fields.Str()
    postal_code         = fields.Int()
    beneficial_owners   = fields.Method('get_beneficial_owners_json')

    bank_accounts       = fields.Nested('server.schemas.BankAccountSchema', many=True, exclude=('kyc_application_id',))
    uploaded_documents  = fields.Nested('server.schemas.UploadedDocumentSchema', many=True, exclude=('kyc_application_id',))

    def get_beneficial_owners_json(self, obj):
        return obj.beneficial_owners

    def get_kyc_actions_json(self, obj):
        return obj.kyc_actions


class OrganisationSchema(Schema):
    id                  = fields.Int(dump_only=True)
    created             = fields.DateTime(dump_only=True)

    name                = fields.Str()

    users               = fields.Nested('server.schemas.UserSchema', many=True)
    transfer_accounts   = fields.Nested('server.schemas.TransferAccountSchema', many=True)
    credit_transfers    = fields.Nested('server.schemas.CreditTransferSchema', many=True)


old_user_schema = UserSchema(exclude=("transfer_account.users",))
user_schema = UserSchema(exclude=("transfer_account.users",
                                  "transfer_account.credit_sends",
                                  "transfer_account.credit_receives"))

users_schema = UserSchema(many=True, exclude=("transfer_account.users",))

blockchain_address_schema = BlockchainAddressSchema(many=True)

transfer_account_schema = TransferAccountSchema(
    exclude=(
        "credit_sends.sender_transfer_account",
        "credit_sends.recipient_transfer_account",
        # "credit_sends.sender_user",
        # "credit_sends.recipient_user",
        "credit_receives.sender_transfer_account",
         "credit_receives.recipient_transfer_account",
        #  "credit_receives.sender_user",
        #  "credit_receives.recipient_user"
    ))
transfer_accounts_schema = TransferAccountSchema(many=True, exclude=("credit_sends", "credit_receives"))

view_transfer_account_schema = TransferAccountSchema(
    exclude=(
        "credit_sends.sender_transfer_account",
        "credit_sends.recipient_transfer_account",
        "credit_sends.recipient_user",
        "credit_sends.sender_user",
        "credit_receives.sender_transfer_account",
        "credit_receives.recipient_transfer_account",
        "credit_receives.recipient_user",
        "credit_receives.sender_user",
        "users"
    ))
view_transfer_accounts_schema = TransferAccountSchema(many=True, exclude=("credit_sends", "credit_receives", "users"))

credit_transfer_schema = CreditTransferSchema()
credit_transfers_schema = CreditTransferSchema(many=True)

view_credit_transfers_schema = CreditTransferSchema(many=True, exclude=("sender_user", "recipient_user", "lat", "lng", "attached_images"))

me_credit_transfer_schema = CreditTransferSchema(exclude=("sender_transfer_account",
                                                          "recipient_transfer_account",
                                                          "sender_user",
                                                          "recipient_user",
                                                          ),
                                                 context={'filter_rejected': True})

me_credit_transfers_schema = CreditTransferSchema(many=True, exclude=("sender_transfer_account",
                                                                      "recipient_transfer_account",
                                                                      "sender_user",
                                                                      "recipient_user",
                                                                      ),
                                                  context={'filter_rejected': True})

transfer_cards_schema = TransferCardSchema(many=True, exclude=("id", "created"))

uploaded_image_schema = UploadedImageSchema()

referral_schema = ReferralSchema()
referrals_schema = ReferralSchema(many=True)

filter_schema = SavedFilterSchema()
filters_schema = SavedFilterSchema(many=True)

kyc_application_schema = KycApplicationSchema()
kyc_application_state_schema = KycApplicationSchema(exclude=("trulioo_id","wyre_id", "first_name", "last_name", "phone",
                                                                         "business_legal_name", "business_type",
                                                                         "tax_id", "website", "date_established",
                                                                         "country", "street_address", "street_address_2"
                                                                         "city", "region", "postal_code",
                                                                         "beneficial_owners", "bank_accounts",
                                                                         "documents", "dob"
                                                                         ))
organisation_schema = OrganisationSchema()
organisations_schema = OrganisationSchema(many=True, exclude=("users", "transfer_accounts", "credit_transfers"))

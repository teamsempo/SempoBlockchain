from flask import g
from marshmallow import Schema, fields, post_dump

from server.models.custom_attribute import CustomAttribute
from server.utils.amazon_s3 import get_file_url
from server.models.user import User


class LowerCase(fields.Field):
    """Field that deserializes to a lower case string.
    """

    def _deserialize(self, value, attr, data, **kwargs):
        return value.lower()


class SchemaBase(Schema):
    id = fields.Int(dump_only=True)
    created = fields.DateTime(dump_only=True)
    updated = fields.DateTime(dump_only=True)

class BlockchainTaskableSchemaBase(SchemaBase):

    blockchain_task_id  = fields.Int(dump_only=True)
    blockchain_status   = fields.Function(lambda obj: obj.blockchain_status)

class UserSchema(SchemaBase):
    first_name              = fields.Str()
    last_name               = fields.Str()
    preferred_language      = fields.Str()

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

    business_usage_id = fields.Int()

    failed_pin_attempts = fields.Int()

    custom_attributes        = fields.Method("get_json_data")
    matched_profile_pictures = fields.Method("get_profile_url")

    transfer_accounts        = fields.Nested('TransferAccountSchema',
                                             many=True,
                                             exclude=('users','credit_sends','credit_receives'))

    def get_json_data(self, obj):

        allowed_custom_attributes_objs = CustomAttribute.query.all()
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


class UploadedResourceSchema(SchemaBase):

    kyc_application_id = fields.Int()
    credit_transfer_id = fields.Int()

    filename = fields.Str()
    file_type = fields.Str()
    reference = fields.Str()
    user_filename = fields.Str()

    file_url = fields.Function(lambda obj: obj.file_url)

class TokenSchema(SchemaBase):
    address             = fields.Str()
    symbol              = fields.Str()
    name                = fields.Str()
    # exchange_contracts  = fields.Nested("server.schemas.ExchangeContractSchema", many=True)

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
    transfer_amount         = fields.Function(lambda obj: int(obj.transfer_amount))
    transfer_type           = fields.Function(lambda obj: obj.transfer_type.value)
    transfer_subtype        = fields.Function(lambda obj: obj.transfer_subtype.value)
    transfer_mode           = fields.Function(lambda obj: obj.transfer_mode.value)
    transfer_status         = fields.Function(lambda obj: obj.transfer_status.value)

    transfer_use            = fields.Function(lambda obj: obj.transfer_use)

    transfer_metadata       = fields.Function(lambda obj: obj.transfer_metadata)

    sender_transfer_account_id      = fields.Int()
    recipient_transfer_account_id   = fields.Int()

    sender_user             = fields.Nested(UserSchema, attribute='sender_user', only=("id", "first_name", "last_name"))
    recipient_user          = fields.Nested(UserSchema, attribute='recipient_user', only=("id", "first_name", "last_name"))

    sender_transfer_account    = fields.Nested("server.schemas.TransferAccountSchema", only=("id", "balance", "token"))
    recipient_transfer_account = fields.Nested("server.schemas.TransferAccountSchema", only=("id", "balance", "token"))

    from_exchange_to_transfer_id = fields.Function(lambda obj: obj.from_exchange.to_transfer.id)

    attached_images         = fields.Nested(UploadedResourceSchema, many=True)

    lat                     = fields.Function(lambda obj: obj.recipient_transfer_account.primary_user.lat)
    lng                     = fields.Function(lambda obj: obj.recipient_transfer_account.primary_user.lng)

    is_sender               = fields.Function(lambda obj: obj.sender_transfer_account in g.user.transfer_accounts)

    def get_authorising_user_email(self, obj):
        authorising_user_id = obj.authorising_user_id
        if authorising_user_id is None:
            return None

        authorising_user = User.query.get(obj.authorising_user_id)
        if authorising_user is None:
            return None

        return authorising_user.email


class ExchangeContractSchema(SchemaBase):

    blockchain_address = fields.String()
    contract_registry_blockchain_address = fields.String()
    subexchange_address_mapping = fields.Function(lambda obj: obj.subexchange_address_mapping)

    reserve_token = fields.Nested(TokenSchema)

    exchangeable_tokens = fields.Nested(TokenSchema, many=True)

class ExchangeSchema(BlockchainTaskableSchemaBase):

    to_desired_amount   = fields.Int()
    user                = fields.Nested(UserSchema)

    from_token          = fields.Nested(TokenSchema)
    to_token            = fields.Nested(TokenSchema)

    from_transfer       = fields.Nested(CreditTransferSchema)
    to_transfer         = fields.Nested(CreditTransferSchema)


class TransferAccountSchema(SchemaBase):
    is_approved             = fields.Boolean()
    # balance                 = fields.Int()

    balance                 = fields.Function(lambda obj: int(obj.balance))

    primary_user_id         = fields.Int()

    transfer_account_name   = fields.Str()
    is_vendor               = fields.Boolean()

    payable_period_type     = fields.Str()
    payable_period_length   = fields.Int()
    payable_epoch           = fields.Str()
    payable_period_epoch    = fields.DateTime()

    blockchain_address      = fields.Str()

    users                   = fields.Nested(UserSchema, attribute='users', many=True, exclude=('transfer_account',))

    credit_sends            = fields.Nested(CreditTransferSchema, many=True)
    credit_receives         = fields.Nested(CreditTransferSchema, many=True)

    token                   = fields.Nested(TokenSchema)

    def get_primary_user_id(self, obj):
        users = obj.user
        print(obj)
        return sorted(users, key=lambda user: user.created)[0].id


class TransferCardSchema(SchemaBase):
    public_serial_number    = fields.Str()
    nfc_serial_number       = fields.Function(lambda obj: obj.nfc_serial_number.upper())

    symbol                  = fields.Method('get_symbol')

    amount_loaded           = fields.Function(lambda obj: obj._amount_loaded)
    amount_loaded_signature = fields.Str()

    user                    = fields.Nested(UserSchema, only=('first_name', 'last_name'))

    def get_symbol(self, obj):
        try:
            return obj.transfer_account.token.symbol
        except Exception as e:
            return None


class ReferralSchema(SchemaBase):
    first_name      = fields.Str()
    last_name       = fields.Str()
    reason          = fields.Str()
    phone           = fields.Str()


class SavedFilterSchema(SchemaBase):
    name            = fields.Str()
    filter          = fields.Method('get_filter_json')

    def get_filter_json(self, obj):
        return obj.filter


class BankAccountSchema(SchemaBase):
    wyre_id             = fields.Str()
    kyc_application_id  = fields.Int()

    bank_country        = fields.Str()
    routing_number      = fields.Str()
    account_number      = fields.Str()
    currency            = fields.Str()


class UploadedDocumentSchema(SchemaBase):
    kyc_application_id = fields.Int()

    filename        = fields.Str()
    file_type       = fields.Str()
    reference       = fields.Str()
    user_filename   = fields.Str()
    file_url        = fields.Function(lambda obj: obj.file_url)


class KycApplicationSchema(SchemaBase):
    type                = fields.Str()
    account_type        = LowerCase(attribute="type")

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


class OrganisationSchema(SchemaBase):
    name                = fields.Str()
    primary_blockchain_address = fields.Str()

    token               = fields.Nested('server.schemas.TokenSchema')

    users               = fields.Nested('server.schemas.UserSchema', many=True)
    transfer_accounts   = fields.Nested('server.schemas.TransferAccountSchema', many=True)
    credit_transfers    = fields.Nested('server.schemas.CreditTransferSchema', many=True)


class TransferUsageSchema(Schema):
    id                  = fields.Int(dump_only=True)

    name                = fields.Str()
    default             = fields.Boolean()

user_schema = UserSchema(exclude=("transfer_accounts.credit_sends",
                                  "transfer_accounts.credit_receives"))

users_schema = UserSchema(many=True, exclude=("transfer_accounts.credit_sends",
                                              "transfer_accounts.credit_receives"))

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

view_credit_transfers_schema = CreditTransferSchema(many=True, exclude=(
"sender_user", "recipient_user", "lat", "lng", "attached_images"))

transfer_cards_schema = TransferCardSchema(many=True, exclude=("id", "created"))

uploaded_resource_schema = UploadedResourceSchema()

referral_schema = ReferralSchema()
referrals_schema = ReferralSchema(many=True)

filter_schema = SavedFilterSchema()
filters_schema = SavedFilterSchema(many=True)

kyc_application_schema = KycApplicationSchema()
kyc_application_state_schema = KycApplicationSchema(
    exclude=("trulioo_id", "wyre_id", "first_name", "last_name", "phone",
             "business_legal_name", "business_type",
             "tax_id", "website", "date_established",
             "country", "street_address", "street_address_2"
                                          "city", "region", "postal_code",
             "beneficial_owners", "bank_accounts",
             "documents", "dob"
             ))
me_organisation_schema = OrganisationSchema(exclude=("users", "transfer_accounts", "credit_transfers"))
organisation_schema = OrganisationSchema()
organisations_schema = OrganisationSchema(many=True, exclude=("users", "transfer_accounts", "credit_transfers"))

token_schema = TokenSchema()
tokens_schema = TokenSchema(many=True)

transfer_usages_schema = TransferUsageSchema(many=True)

exchange_contract_schema = ExchangeContractSchema()
exchange_contracts_schema = ExchangeContractSchema(many=True)


# Me Schemas

me_transfer_accounts_schema = TransferAccountSchema(many=True,
                                                    exclude=("credit_sends",
                                                             "credit_receives",
                                                             "users"))

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

me_exchange_schema = ExchangeSchema()
me_exchanges_schema = ExchangeSchema(many=True)


import base64
from io import BytesIO
from flask import g
from marshmallow import Schema, fields, post_dump
import toastedmarshmallow
import qrcode

from server.models.custom_attribute import CustomAttribute
from server.utils.amazon_s3 import get_file_url
from server.models.user import User
from server.models.exchange import Exchange
from server.exceptions import SubexchangeNotFound


def gen_qr(data):
    out = BytesIO()
    img = qrcode.make(data)
    img.save(out, "PNG")
    out.seek(0)

    return u"data:image/png;base64," + base64.b64encode(out.getvalue()).decode("ascii")

class LowerCase(fields.Field):
    """Field that deserializes to a lower case string.
    """

    def _deserialize(self, value, attr, data, **kwargs):
        return value.lower()

class QR(fields.Field):
    """
    Field that serializes to a QR code
    """

    def _serialize(self, value, attr, obj):
        return gen_qr(value)

class SchemaBase(Schema):
    class Meta:
        jit = toastedmarshmallow.Jit

    id = fields.Int(dump_only=True)
    created = fields.DateTime(dump_only=True)
    updated = fields.DateTime(dump_only=True)

class BlockchainTaskableSchemaBase(SchemaBase):

    blockchain_task_uuid  = fields.Str(dump_only=True)
    blockchain_status   = fields.Function(lambda obj: obj.blockchain_status.name)

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

    roles                   = fields.Dict(keys=fields.Str(), values=fields.Str())
    is_beneficiary          = fields.Boolean(attribute='has_beneficiary_role')
    is_vendor               = fields.Boolean(attribute='has_vendor_role')
    is_tokenagent           = fields.Boolean(attribute='has_token_agent_role')
    is_groupaccount         = fields.Boolean(attribute='has_group_account_role')
    is_any_admin            = fields.Boolean(attribute='is_any_admin')

    business_usage_id = fields.Int()

    failed_pin_attempts = fields.Int()

    default_transfer_account_id = fields.Int()

    custom_attributes        = fields.Method("get_json_data")
    matched_profile_pictures = fields.Method("get_profile_url")
    referred_by              = fields.Method("get_referrer_phone")
    qr                       = fields.Method("get_qr_code")

    transfer_accounts        = fields.Nested('TransferAccountSchema',
                                             many=True,
                                             exclude=('users', 'credit_sends', 'credit_receives'))

    transfer_card = fields.Nested('TransferCardSchema', only=('is_disabled', 'public_serial_number'))

    def get_qr_code(self, obj):
        return gen_qr(f'{obj.id}: {obj.first_name} {obj.last_name}')

    def get_json_data(self, obj):

        custom_attributes = obj.custom_attributes

        parsed_dict = {}

        for attribute in custom_attributes:
            parsed_dict[attribute.key] = attribute.value

        return parsed_dict

    def get_profile_url(self, obj):
        processed_profile_pictures = []
        if obj.matched_profile_pictures:
            for profile in obj.matched_profile_pictures:
                profile['url'] = get_file_url(profile['value'])

                processed_profile_pictures.append(profile)
        return processed_profile_pictures

    def get_referrer_phone(self, obj):
        if obj.referred_by:
            referrer = obj.referred_by[0]
            if referrer.phone:
                return referrer.phone
            if referrer.public_serial_number:
                return referrer.public_serial_number
            if referrer.email:
                return referrer.email


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

    def get_exchange_rates(self, obj):
        rates = {}
        for to_token in self.context.get('exchange_pairs', []):
            if to_token != obj:
                try:
                    rate = Exchange.get_exchange_rate(obj, to_token)
                    rates[to_token.symbol] = rate

                except SubexchangeNotFound:
                    pass

        return rates

    exchange_rates = fields.Method("get_exchange_rates")

    # exchange_contracts  = fields.Nested("server.schemas.ExchangeContractSchema", many=True)

class CreditTransferSchema(BlockchainTaskableSchemaBase):

    id      = fields.Int(dump_only=True)
    created = fields.DateTime(dump_only=True)
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

    transfer_metadata = fields.Function(lambda obj: obj.transfer_metadata)
    token = fields.Nested(TokenSchema, only=('id', 'symbol'))

    sender_transfer_account_id = fields.Int()
    recipient_transfer_account_id = fields.Int()

    sender_user = fields.Nested(UserSchema, attribute='sender_user', only=("id", "first_name", "last_name"))
    recipient_user = fields.Nested(UserSchema, attribute='recipient_user', only=("id", "first_name", "last_name"))

    sender_transfer_account = fields.Nested("server.schemas.TransferAccountSchema",
                                            only=("id", "balance", "token", "blockchain_address", "is_vendor"))
    recipient_transfer_account = fields.Nested("server.schemas.TransferAccountSchema",
                                               only=("id", "balance", "token", "blockchain_address", "is_vendor"))

    sender_transfer_card_id = fields.Int()

    from_exchange_to_transfer_id = fields.Function(lambda obj: obj.from_exchange.to_transfer.id)

    attached_images = fields.Nested(UploadedResourceSchema, many=True)

    lat = fields.Function(lambda obj: obj.recipient_transfer_account.primary_user.lat)
    lng = fields.Function(lambda obj: obj.recipient_transfer_account.primary_user.lng)
    is_sender = fields.Function(lambda obj: obj.sender_transfer_account in g.user.transfer_accounts)

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

class MiniTaSchema(SchemaBase):
    is_approved = fields.Boolean()
    # balance                 = fields.Int()
    #
    balance = fields.Function(lambda obj: int(obj.balance))

    # primary_user_id = fields.Int()

    transfer_account_name = fields.Str()
    is_vendor = fields.Boolean()

    payable_period_type = fields.Str()
    payable_period_length = fields.Int()
    payable_epoch = fields.Str()
    payable_period_epoch = fields.DateTime()
    #
    blockchain_address = fields.Str()

    # users = fields.Nested(UserSchema, attribute='users', many=True, exclude=('transfer_account',))

    credit_sends = fields.Nested(CreditTransferSchema, many=True)
    credit_receives = fields.Nested(CreditTransferSchema, many=True)

    # token = fields.Nested(TokenSchema)
    #
    # def get_primary_user_id(self, obj):
    #     users = obj.user
    #     print(obj)
    #     return sorted(users, key=lambda user: user.created)[0].id


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
    notes                   = fields.Str()
    payable_period_epoch    = fields.DateTime()

    blockchain_address      = fields.Str()

    users                   = fields.Nested(
        UserSchema,
        attribute='users',
        many=True,
        only=(
            "first_name",
            "created",
            "id",
            "is_beneficiary",
            "is_disabled",
            "is_groupaccount",
            "is_tokenagent",
            "is_vendor",
            "last_name",
            "lat",
            "lng",
            "location",
            "phone",
            "public_serial_number",
            "custom_attributes",
            "default_transfer_account_id"
        ),
        exclude=(
            'transfer_accounts',
            'transfer_accounts'))

    credit_sends            = fields.Nested(CreditTransferSchema, many=True)
    credit_receives         = fields.Nested(CreditTransferSchema, many=True)

    token                   = fields.Nested(TokenSchema, only=('id', 'symbol'))

    def get_primary_user_id(self, obj):
        users = obj.user
        print(obj)
        return sorted(users, key=lambda user: user.created)[0].id


class TransferCardSchema(SchemaBase):
    public_serial_number    = fields.Str()
    nfc_serial_number       = fields.Function(lambda obj: obj.nfc_serial_number.upper())
    is_disabled             = fields.Boolean()


    symbol                  = fields.Method('get_symbol')

    amount_loaded           = fields.Function(lambda obj: obj._amount_loaded)
    amount_loaded_signature = fields.Str()

    user                    = fields.Nested(UserSchema, only=('first_name', 'last_name'))

    def get_symbol(self, obj):
        try:
            return obj.transfer_account.token.symbol
        except Exception as e:
            return None


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

    default_lat = fields.Float()
    default_lng = fields.Float()

    card_shard_distance = fields.Int() # Kilometers

    valid_roles = fields.Raw()

    master_wallet_balance = fields.Function(lambda obj: obj.queried_org_level_transfer_account.balance)

    require_transfer_card = fields.Boolean(default=False)
    default_disbursement = fields.Function(lambda obj: int(obj.default_disbursement))
    minimum_vendor_payout_withdrawal = fields.Function(lambda obj: int(obj.minimum_vendor_payout_withdrawal))
    country_code = fields.Function(lambda obj: str(obj.country_code))
    timezone = fields.Function(lambda obj: str(obj.timezone))

    token               = fields.Nested('server.schemas.TokenSchema')

    #users               = fields.Nested('server.schemas.UserSchema', many=True)
    #transfer_accounts   = fields.Nested('server.schemas.TransferAccountSchema', many=True)
    #credit_transfers    = fields.Nested('server.schemas.CreditTransferSchema', many=True)


class TransferUsageSchema(Schema):
    id                  = fields.Int(dump_only=True)
    name                = fields.Str()
    default             = fields.Boolean()

class SynchronizationFilterSchema(Schema):
    id                          = fields.Int(dump_only=True)
    contract_address            = fields.Str()
    contract_type               = fields.Str()
    filter_parameters           = fields.Str()
    filter_type                 = fields.Str()
    created                     = fields.DateTime(dump_only=True)
    updated                     = fields.DateTime(dump_only=True)

class AttributeMapSchema(Schema):
    input_name                  = fields.Str()
    output_name                 = fields.Str()


class DisbursementSchema(SchemaBase):
    search_string               = fields.Str()
    search_filter_params        = fields.Str()
    notes                       = fields.Str()
    errors                      = fields.List(fields.Str())
    include_accounts            = fields.List(fields.Int())
    exclude_accounts            = fields.List(fields.Int())

    recipient_count             = fields.Int()
    total_disbursement_amount   = fields.Int()
    label                       = fields.Str()
    state                       = fields.Str()
    transfer_type               = fields.Str()
    disbursement_amount         = fields.Int()
    creator_user = fields.Nested(UserSchema, attribute='creator_user', only=("id", "first_name", "last_name", "email"))
    approvers = fields.Nested(UserSchema, attribute='approvers', many=True, only=("id", "first_name", "last_name", "email"))
    approval_times              = fields.List(fields.DateTime(dump_only=True))

class AuditHistorySchema(Schema):
    column_name                  = fields.Str()
    old_value                    = fields.Str()
    new_value                    = fields.Str()
    change_by                    = fields.Nested(UserSchema, attribute='change_by', only=("id", "first_name", "last_name", "email"))
    created                      = fields.DateTime(dump_only=True)

pdf_users_schema = UserSchema(many=True, only=("id", "qr", "first_name", "last_name"))

user_schema = UserSchema(exclude=("qr",
                                  "transfer_accounts.credit_sends",
                                  "transfer_accounts.credit_receives"))

users_schema = UserSchema(many=True, exclude=("qr",
                                              "transfer_accounts.credit_sends",
                                              "transfer_accounts.credit_receives"))

transfer_account_schema = TransferAccountSchema(
    exclude=(
        "credit_sends.sender_transfer_account",
        "credit_sends.recipient_transfer_account",
        "credit_receives.sender_transfer_account",
        "credit_receives.recipient_transfer_account",
        "credit_sends",
        "credit_receives",
    ))

transfer_accounts_schema = TransferAccountSchema(
    many=True,
    only=('balance', 'created', 'id', 'users', 'token', 'primary_user_id', 'blockchain_address', 'is_approved')
)

# transfer_accounts_schema = MiniTaSchema(many=True)


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

synchronization_filter_schema = SynchronizationFilterSchema()

view_credit_transfer_schema = CreditTransferSchema(exclude=(
"sender_user", "recipient_user", "lat", "lng", "attached_images"))
view_credit_transfers_schema = CreditTransferSchema(many=True, exclude=(
"sender_user", "recipient_user", "lat", "lng", "attached_images"))
view_credit_transfer_schema = CreditTransferSchema(exclude=(
"sender_user", "recipient_user", "lat", "lng", "attached_images"))

transfer_cards_schema = TransferCardSchema(many=True, exclude=("id", "created"))
transfer_card_schema = TransferCardSchema(exclude=("id", "created"))


uploaded_resource_schema = UploadedResourceSchema()

filter_schema = SavedFilterSchema()
filters_schema = SavedFilterSchema(many=True)

kyc_application_schema = KycApplicationSchema()
kyc_application_state_schema = KycApplicationSchema(
    exclude=("trulioo_id", "wyre_id", "first_name", "last_name", "phone",
             "business_legal_name", "business_type",
             "tax_id", "website", "date_established",
             "country", "street_address", "street_address_2", "city", "region", "postal_code",
             "beneficial_owners", "bank_accounts",
             "uploaded_documents", "dob"
             ))
me_organisation_schema = OrganisationSchema(exclude=("users", "transfer_accounts", "credit_transfers"))
organisation_schema = OrganisationSchema()
organisations_schema = OrganisationSchema(many=True, exclude=("users", "transfer_accounts", "credit_transfers"))

attribute_map_schema = AttributeMapSchema()
attribute_maps_schema = AttributeMapSchema(many=True)


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


disbursement_schema = DisbursementSchema()
disbursements_schema = DisbursementSchema(many=True)

audit_history_schema = AuditHistorySchema()
audit_histories_schema = AuditHistorySchema(many=True)

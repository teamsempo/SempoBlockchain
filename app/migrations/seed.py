import sys
import os
from sqlalchemy import func

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))

from server import db, create_app
from server.models.ussd import UssdMenu
from server.models.user import User
from server.models.transfer_usage import TransferUsage
from server.models.transfer_account import TransferAccount, TransferAccountType
from server.models.organisation import Organisation
from server.models.token import Token, TokenType
from server.exceptions import TransferUsageNameDuplicateException

from server.utils.location import _set_user_gps_from_location

def print_section_title(text):
    print(text)
    print('**********************************************************************')


def print_section_conclusion(text):
    print(text)
    print('------------------------------------------------------------')


def update_or_create_menu(name, description, parent_id=None):
    instance = UssdMenu.query.filter_by(name=name).first()
    if instance:
        instance.name = name
        instance.description = description
        instance.display_key = "ussd.kenya.{}".format(name)
        instance.parent_id = parent_id
    else:
        instance = UssdMenu(
            name=name,
            description=description,
            display_key="ussd.kenya.{}".format(name),
            parent_id=parent_id
        )
        db.session.add(instance)

    db.session.commit()
    return instance


def create_ussd_menus():
    print_section_title('Creating Sarafu Network USSD Menu')
    print('Creating Initial Language Selection menu')

    initial_lang_setup_menu = update_or_create_menu(
        name="initial_language_selection",
        description="Start menu. This is the entry point for users to select their preferred language",
    )
    initial_pin_menu = update_or_create_menu(
        name='initial_pin_entry',
        description='PIN setup entry menu',
        parent_id=initial_lang_setup_menu.id
    )
    update_or_create_menu(
        name='initial_pin_confirmation',
        description='Confirm new PIN menu',
        parent_id=initial_pin_menu.id
    )

    # ****************************** Start Menu ****************************************************

    print('Creating Start menu...')
    start_menu = update_or_create_menu(
        name='start',
        description='Start menu. This is the entry point for activated users',
    )

    print('Creating send token menu...')
    update_or_create_menu(
        name='send_enter_recipient',
        description='Send Token recipient entry',
        parent_id=start_menu.id
    )
    update_or_create_menu(
        name='send_token_amount',
        description='Send Token amount prompt menu',
        parent_id=start_menu.id
    )
    update_or_create_menu(
        name='send_token_reason',
        description='Send Token reason prompt menu',
        parent_id=start_menu.id
    )
    update_or_create_menu(
        name='send_token_reason_other',
        description='Send Token other reason prompt menu',
        parent_id=start_menu.id
    )
    update_or_create_menu(
        name='send_token_pin_authorization',
        description='PIN entry for authorization to send token',
        parent_id=start_menu.id
    )
    update_or_create_menu(
        name='send_token_confirmation',
        description='Send Token confirmation menu',
        parent_id=start_menu.id
    )
    update_or_create_menu(
        name='directory_listing',
        description='Listing of Market place categories for a user to choose',
        parent_id=start_menu.id
    )
    update_or_create_menu(
        name='directory_listing_other',
        description='Listing of Market place other categories for a user to choose',
        parent_id=start_menu.id
    )
    update_or_create_menu(
        name='complete',
        description='Complete menu. Last step of any menu',
    )

    print('****** Manage Account ******')
    account_management_menu = update_or_create_menu(
        name='account_management',
        description='Manage account menu',
        parent_id=start_menu.id
    )
    update_or_create_menu(
        name='my_business',
        description='Manage business directory info',
        parent_id=account_management_menu.id
    )
    update_or_create_menu(
        name='about_my_business',
        description='About business directory info',
        parent_id=account_management_menu.id
    )
    update_or_create_menu(
        name='change_my_business_prompt',
        description='Change business directory info',
        parent_id=account_management_menu.id
    )
    update_or_create_menu(
        name='balance_inquiry_pin_authorization',
        description='PIN authorization before Balance enquiry',
        parent_id=account_management_menu.id
    )
    update_or_create_menu(
        name='choose_language',
        description='Choose default language',
        parent_id=account_management_menu.id
    )
    update_or_create_menu(
        name='opt_out_of_market_place_pin_authorization',
        description='PIN authorization opting out of market',
        parent_id=account_management_menu.id
    )

    print('******** Change PIN Menu ********************')
    update_or_create_menu(
        name='current_pin',
        description='Change PIN enter current PIN menu',
        parent_id=account_management_menu.id
    )
    update_or_create_menu(
        name='new_pin',
        description='New PIN entry menu',
        parent_id=account_management_menu.id
    )
    update_or_create_menu(
        name='new_pin_confirmation',
        description='Confirm new PIN menu',
        parent_id=account_management_menu.id
    )

    print('***** Help Menu *********')
    update_or_create_menu(
        name='help',
        description='Help menu',
        parent_id=start_menu.id
    )

    print('***** Exchange Rate Menu ******')
    exchange_token_menu = update_or_create_menu(
        name='exchange_token',
        description='Menu for exchanging tokens from agents',
        parent_id=start_menu.id
    )
    update_or_create_menu(
        name='exchange_rate_pin_authorization',
        description='PIN entry for authorization to access exchange rate',
        parent_id=exchange_token_menu.id
    )
    update_or_create_menu(
        name='request_exchange_rate',
        description='Exchange menu',
        parent_id=exchange_token_menu.id
    )
    update_or_create_menu(
        name='exchange_token_agent_number_entry',
        description='Exchange Token agent number entry',
        parent_id=exchange_token_menu.id
    )
    update_or_create_menu(
        name='exchange_token_amount_entry',
        description='Exchange Token amount prompt menu',
        parent_id=exchange_token_menu.id
    )
    update_or_create_menu(
        name='exchange_token_pin_authorization',
        description='PIN entry for authorization to convert token',
        parent_id=exchange_token_menu.id
    )
    update_or_create_menu(
        name='exchange_token_confirmation',
        description='Exchange Token confirmation menu',
        parent_id=exchange_token_menu.id
    )

    # Exit codes
    update_or_create_menu(
        name='exit',
        description='Exit menu',
    )
    update_or_create_menu(
        name='exit_invalid_menu_option',
        description='Invalid menu option',
    )
    update_or_create_menu(
        name='exit_invalid_pin',
        description='PIN policy violation',
    )
    update_or_create_menu(
        name='exit_pin_mismatch',
        description='PIN mismatch. New PIN and the new PIN confirmation do not match',
    )
    update_or_create_menu(
        name='exit_pin_blocked',
        description='Ussd PIN Blocked Menu',
    )
    update_or_create_menu(
        name='exit_invalid_request',
        description='Key params missing in request',
    )
    update_or_create_menu(
        name='exit_invalid_input',
        description='The user did not select a choice',
    )
    update_or_create_menu(
        name='exit_recipient_not_found',
        description='The recipient does not exist.',
    )
    update_or_create_menu(
        name='exit_invalid_recipient',
        description='Invalid recipient',
    )
    update_or_create_menu(
        name='exit_use_exchange_menu',
        description='Recipient is token agent, use exchange menu',
    )
    update_or_create_menu(
        name='exit_invalid_token_agent',
        description='Invalid token agent',
    )
    update_or_create_menu(
        name='exit_not_registered',
        description='The phone is not registered on Sarafu or has been deactivated.',
    )
    update_or_create_menu(
        name='exit_invalid_exchange_amount',
        description='The token exchange amount is insufficient',
    )

    print_section_conclusion('Done creating USSD Menus')


def create_business_categories(only_if_none_exist=True):

    if only_if_none_exist:
        usages = db.session.query(TransferUsage).all()
        if len(usages) > 0:
            print("Business Categories already exist! Skipping.")
            return

    print_section_title('Creating Business Categories')
    business_categories = [
        {'name': 'Fresh Food', 'icon': 'food-apple', 'translations': {
            'en': 'Fresh Food'}},
        {'name': 'Long Life Food', 'icon': 'food-variant', 'translations': {
            'en': 'Long Life Food'}},
        {'name': 'Water/Sanitation/Hygiene', 'icon': 'water', 'translations': {
            'en': 'Water/Sanitation/Hygiene'}},
        {'name': 'Health/Medicine', 'icon': 'medical-bag', 'translations': {
            'en': 'Health/Medicine'}},
        {'name': 'Clothing', 'icon': 'tshirt-crew', 'translations': {
            'en': 'Clothing'}},
        {'name': 'Household Items', 'icon': 'home', 'translations': {
            'en': 'Household Items'}},
        {'name': 'Other', 'icon': 'star', 'translations': {
            'en': 'Other'}}
    ]
    for index, business_category in enumerate(business_categories):
        name = business_category['name']
        usage = db.session.query(TransferUsage).filter(
            func.lower(TransferUsage.name) == func.lower(name)).first()
        if usage is None:
            usage = TransferUsage(name=name)
            db.session.add(usage)
        usage.priority = index + 1
        usage.default = True
        usage.icon = business_category['icon']
        usage.translations = business_category['translations']

    db.session.commit()

    print_section_conclusion('Done creating Business Categories')


def create_reserve_token(app):

    print_section_title("Setting up Reserve Token")

    chain_config = app.config['CHAINS'][app.config['DEFAULT_CHAIN']]

    reserve_token_address = chain_config.get('RESERVE_TOKEN_ADDRESS')
    reserve_token_name = chain_config.get('RESERVE_TOKEN_NAME')
    reserve_token_symbol = chain_config.get('RESERVE_TOKEN_SYMBOL')
    # reserve_token_decimals = app.config.get('RESERVE_TOKEN_DECIMALS')

    if reserve_token_address:
        reserve_token = Token.query.filter_by(address=reserve_token_address).first()

        print('Existing token not found, creating')

        if not reserve_token:
            reserve_token = Token(
                address=reserve_token_address,
                name=reserve_token_name,
                symbol=reserve_token_symbol,
                token_type=TokenType.RESERVE,
                chain=app.config['DEFAULT_CHAIN']
            )

            reserve_token.decimals = 18

            db.session.add(reserve_token)
            db.session.commit()

        print(f'Reserve token: {reserve_token}')

        return reserve_token

    print('No token address, skipping')

    return None


def create_master_organisation(app, reserve_token):

    print_section_title('Creating/Updating Master Organisation')

    master_organisation = Organisation.master_organisation()
    if master_organisation is None:
        print('Creating master organisation')
        if reserve_token:
            print('Binding to reserve token')
        master_organisation = Organisation(
            name='Reserve', is_master=True,
            token=reserve_token, country_code=app.config.get('DEFAULT_COUNTRY', 'AU'),
            timezone='UTC'
        )
        db.session.add(master_organisation)

        db.session.commit()

    print_section_conclusion('Done creating master organisation')

# Creates float transfer accounts for any transfer account that doesn't have one already
def create_float_transfer_account(app):
    print_section_title('Creating/Updating Float Transfer Accounts')
    tokens = db.session.query(Token).execution_options(show_all=True)
    for t in tokens:
        if t.float_account is None:
            print(f'Creating Float Account for {t.name}')
            chain_config = app.config['CHAINS'][app.config['DEFAULT_CHAIN']]

            float_transfer_account = TransferAccount(
                private_key=chain_config['FLOAT_PRIVATE_KEY'],
                account_type=TransferAccountType.FLOAT,
                token=t,
                is_approved=True
            )
            db.session.add(float_transfer_account)
            db.session.flush()
            t.float_account = float_transfer_account
        t.float_account.is_public = True
        db.session.commit()
    print_section_conclusion('Done Creating/Updating Float Wallet')
        

# from app folder: python ./migations/seed.py
if __name__ == '__main__':
    current_app = create_app(skip_create_filters=True)
    ctx = current_app.app_context()
    ctx.push()

    create_ussd_menus()
    create_business_categories()

    reserve_token = create_reserve_token(current_app)
    create_master_organisation(current_app, reserve_token)

    create_float_transfer_account(current_app)

    ctx.pop()

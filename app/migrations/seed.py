import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))

from server import db, create_app
from server.models.ussd import UssdMenu
from server.models.transfer_usage import TransferUsage
from server.models.transfer_account import TransferAccount, TransferAccountType
from server.models.organisation import Organisation
from server.models.token import Token, TokenType
from server.exceptions import TransferUsageNameDuplicateException


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


def create_business_categories():

    print_section_title('Creating Business Categories')
    business_categories = [
        {'name': 'Food', 'icon': 'message', 'translations': {
            'en': 'Food', 'sw': 'Chakula'}},
        {'name': 'Water', 'icon': 'message',
         'translations': {'en': 'Water', 'sw': 'Maji'}},
        {'name': 'Energy', 'icon': 'message', 'translations': {
            'en': 'Energy', 'sw': 'Kuni/makaa/mafuta/stima'}},
        {'name': 'Education', 'icon': 'message',
         'translations': {'en': 'Education', 'sw': 'Elimu'}},
        {'name': 'Health', 'icon': 'message',
         'translations': {'en': 'Health', 'sw': 'Afya'}},
        {'name': 'General shop', 'icon': 'message', 'translations': {
            'en': 'General shop', 'sw': 'Duka la jumla'}},
        {'name': 'Environment', 'icon': 'message', 'translations': {
            'en': 'Environment', 'sw': 'Mazingira'}},
        {'name': 'Transport', 'icon': 'message', 'translations': {
            'en': 'Transport', 'sw': 'Usafiri'}},
        {'name': 'Labour', 'icon': 'message', 'translations': {
            'en': 'Labour', 'sw': 'Mfanyakazi'}},
    ]
    for business_category in business_categories:
        usage = TransferUsage.find_or_create(business_category['name'])
        if usage is not None:
            usage.icon = business_category['icon']
            usage.translations = business_category['translations']
        else:
            try:
                usage = TransferUsage(name=business_category['name'], icon=business_category['icon'],
                                      priority=1, default=True, translations=business_category['translations'])
            except TransferUsageNameDuplicateException as e:
                print(e)
        db.session.add(usage)

    db.session.commit()

    print_section_conclusion('Done creating Business Categories')


def create_reserve_token(app):

    print_section_title("Setting up Reserve Token")

    reserve_token_address = app.config.get('RESERVE_TOKEN_ADDRESS')
    reserve_token_name = app.config.get('RESERVE_TOKEN_NAME')
    reserve_token_symbol = app.config.get('RESERVE_TOKEN_SYMBOL')
    # reserve_token_decimals = app.config.get('RESERVE_TOKEN_DECIMALS')

    if reserve_token_address:
        reserve_token = Token.query.filter_by(address=reserve_token_address).first()

        print('Existing token not found, creating')

        if not reserve_token:
            reserve_token = Token(
                address=reserve_token_address,
                name=reserve_token_name,
                symbol=reserve_token_symbol,
                token_type=TokenType.RESERVE
            )

            db.session.add(reserve_token)
            db.session.commit()

        print(f'Reserve token: {reserve_token}')

        return reserve_token

    print('No token address, skipping')

    return None


def create_master_organisation(reserve_token):

    print_section_title('Creating/Updating Master Organisation')

    master_organisation = Organisation.master_organisation()
    if master_organisation is None:
        print('Creating master organisation')
        if reserve_token:
            print('Binding to reserve token')
        master_organisation = Organisation(is_master=True, token=reserve_token)
        db.session.add(master_organisation)

        db.session.commit()

    print_section_conclusion('Done creating master organisation')

def create_float_wallet(app):
    print_section_title('Creating/Updating Float Wallet')
    float_wallet = TransferAccount.query.execution_options(show_all=True).filter(
        TransferAccount.account_type == TransferAccountType.FLOAT
    ).first()

    if float_wallet is None:
        print('Creating Float Wallet')
        float_wallet = TransferAccount(
            private_key=app.config['ETH_FLOAT_PRIVATE_KEY'],
            account_type=TransferAccountType.FLOAT,
            is_approved=True
        )
        db.session.add(float_wallet)

        db.session.commit()

# from app folder: python ./migations/seed.py
if __name__ == '__main__':
    current_app = create_app()
    ctx = current_app.app_context()
    ctx.push()

    create_ussd_menus()
    create_business_categories()

    reserve_token = create_reserve_token(current_app)
    create_master_organisation(reserve_token)

    create_float_wallet(current_app)

    ctx.pop()
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))

from server import db, create_app
from server.models.ussd import UssdMenu


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


# from app folder: python ./migations/seed.py
if __name__ == '__main__':
    app = create_app()
    ctx = app.app_context()
    ctx.push()

    print('Creating Sarafu Network USSD Menu')
    print('**********************************************************************')
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

    print('------------------------------------------------------------')
    print('Done creating USSD Menus')

    ctx.pop()

"""
print('Creating Business Categories')
print('**********************************************************************')

business_categories = {
  '1001' => 'Food',
  '1002' => 'Water',
  '1003' => 'Energy',
  '1004' => 'Education',
  '1005' => 'Health',
  '1006' => 'General shop',
  '1007' => 'Environment',
  '1008' => 'Transport',
  '1009' => 'Labour',
  '1010' => 'Other'
}

business_categories.each do |code, type|
  BusinessCategory.where(classification_code: code).first_or_create! do |bc|
    bc.classification_code = code
    bc.business_type = type
  end
end

print('------------------------------------------------------------')
print('Done creating Business Categories')
"""

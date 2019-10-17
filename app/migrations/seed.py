import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))

from server import db, create_app
from server.models.ussd import UssdMenu


def get_or_create_menu(name, **kwargs):
    instance = UssdMenu.query.filter_by(name=name).first()
    if instance:
        return instance
    else:
        instance = UssdMenu(name=name)
        db.session.add(instance)

        for key, value in kwargs.items():
            setattr(instance, key, value)

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

    initial_lang_setup_menu = get_or_create_menu(
        "initial_language_selection",
        description="Start menu. This is the entry point for users to select their preferred language",
        display_text_en="""CON Welcome to Sarafu 
1. English
2. Kiswahili
3. Help""",
        display_text_sw="""CON Welcome to Sarafu
1. English
2. Kiswahili
3. Help"""
    )
    initial_pin_menu = get_or_create_menu(
        'initial_pin_entry',
        description='PIN setup entry menu',
        display_text_en="""CON Please enter a PIN to manage your account.
0. Back""",
        display_text_sw="""CON Tafadhali weka PIN ili kudhibiti akaunti yako.
0. Nyuma""",
        parent_id=initial_lang_setup_menu.id
    )
    get_or_create_menu(
        'initial_pin_confirmation',
        description='Confirm new PIN menu',
        display_text_en="""CON Enter your PIN again
0. Back""",
        display_text_sw="""CON Weka PIN yako tena
0. Nyuma""",
        parent_id=initial_pin_menu.id
    )

    # ****************************** Start Menu ****************************************************

    print('Creating Start menu...')
    get_or_create_menu(
        'initial_pin_confirmation',
        description='Confirm new PIN menu',
        display_text_en="""CON Enter your PIN again
0. Back""",
        display_text_sw="""CON Weka PIN yako tena
0. Nyuma""",
        parent_id=initial_pin_menu.id
    )

    # ****************************** Start Menu ****************************************************

    print('Creating Start menu...')
    start_menu = get_or_create_menu(
        'start',
        description='Start menu. This is the entry point for activated users',
        display_text_en="""CON Welcome to Sarafu
1. Send
2. My Account
3. Market Place
4. Exchange
5. Help""",
        display_text_sw="""CON Karibu Sarafu
1. Tuma
2. Akaunti Yangu
3. Sokoni
4. Badilisha
5. Usaidizi"""
    )

    print('Creating send token menu...')
    get_or_create_menu(
        'send_enter_recipient',
        description='Send Token recipient entry',
        display_text_en="""CON Enter Phone Number
0. Back""",
        display_text_sw="""CON Weka nambari ya simu
0. Nyuma""",
        parent_id=start_menu.id
    )
    get_or_create_menu(
        'send_token_amount',
        description='Send Token amount prompt menu',
        display_text_en="""CON Enter Amount
0. Back""",
        display_text_sw="""CON Weka kiwango
0. Nyuma""",
        parent_id=start_menu.id
    )
    get_or_create_menu(
        'send_token_reason',
        description='Send Token reason prompt menu',
        display_text_en="""CON Select Transfer reason
1. Food
2. Water
3. Energy
4. Education
5. Health
6. General shop
7. Environment
8. Transport
9. Labour
10. Other
0. Back""",
        display_text_sw="""CON Chagua kusudi la malipo
1. Chakula
2. Maji
3. Kuni/makaa/mafuta/stima
4. Elimu
5. Afya
6. Uchuuzi
7. Mazingira
8. Usafiri
9. Mfanyakazi
10. Nyingine
0. Nyuma""",
        parent_id=start_menu.id
    )
    get_or_create_menu(
        'send_token_reason_other',
        description='Send Token other reason prompt menu',
        display_text_en="""CON Please specify
0. Back""",
        display_text_sw="""CON Fafanua kusudi zaidi
0. Nyuma""",
        parent_id=start_menu.id
    )
    get_or_create_menu(
        'send_token_pin_authorization',
        description='PIN entry for authorization to send token',
        display_text_en="""CON Please enter your PIN. %remaining_attempts%
0. Back""",
        display_text_sw="""CON Weka nambari ya siri. %remaining_attempts%
0. Nyuma""",
        parent_id=start_menu.id
    )
    get_or_create_menu(
        'send_token_confirmation',
        description='Send Token confirmation menu',
        display_text_en="""CON Send %transaction_amount% %token_name% to %recipient_phone% for %transaction_reason%
1. Confirm
2. Cancel
0. Back""",
        display_text_sw="""CON Tuma %transaction_amount% %token_name% kwa %recipient_phone%
1. Thibitisha
2. Futa
0. Nyuma""",
        parent_id=start_menu.id
    )
    get_or_create_menu(
        'directory_listing',
        description='Listing of Market place categories for a user to choose',
        display_text_en="""CON Choose Market Category
1. Food
2. Water
3. Energy
4. Education
5. Health
6. General shop
7. Environment
8. Transport
9. Labour""",
        display_text_sw="""CON Chagua unachotaka Sokoni
1. Chakula
2. Maji
3. Kuni/makaa/mafuta/stima
4. Elimu
5. Afya
6. Duka la jumla
7. Mazingira
8. Usafiri
9. Mfanyakazi""",
        parent_id=start_menu.id
    )
    get_or_create_menu(
        'complete',
        description='Complete menu. Last step of any menu',
        display_text_en="""END Your request has been sent. You will receive an SMS shortly.""",
        display_text_sw="""END Ombi lako limetumwa. Utapokea uthibitishaji wa SMS kwa muda mfupi."""
    )

    print('****** Manage Account ******')
    account_management_menu = get_or_create_menu(
        'account_management',
        description='Manage account menu',
        display_text_en="""CON My account
1. My Business
2. Change language
3. Check Balances
4. Change PIN
5. Opt Out of Market Place
0. Back""",
        display_text_sw="""CON Akaunti yangu
1. Biashara Yangu
2. Chagua lugha utakayotumia
3. Angalia salio
4. Badilisha nambari ya siri
5. Ondoka Sokoni
0. Nyuma""",
        parent_id=start_menu.id
    )
    get_or_create_menu(
        'my_business',
        description='Manage business directory info',
        display_text_en="""CON My Business
1. See my business
2. Change my business
0. Back""",
        display_text_sw="""CON Biashara Yangu
1. Angalia biashara
2. Badilisha biashara
0. Nyuma""",
        parent_id=account_management_menu.id
    )
    get_or_create_menu(
        'about_my_business',
        description='About business directory info',
        display_text_en="""END %user_bio%""",
        display_text_sw="""END %user_bio%""",
        parent_id=account_management_menu.id
    )
    get_or_create_menu(
        'change_my_business_prompt',
        description='Change business directory info',
        display_text_en="""CON Please enter a product or service you offer
0. Back""",
        display_text_sw="""CON Tafadhali weka bidhaa ama huduma unauza
0. Nyuma""",
        parent_id=account_management_menu.id
    )
    get_or_create_menu(
        'balance_inquiry_pin_authorization',
        description='PIN authorization before Balance enquiry',
        display_text_en="""CON Please enter your PIN. %remaining_attempts%
0. Back""",
        display_text_sw="""CON Tafadhali ingiza PIN yako. %remaining_attempts%
0. Nyuma""",
        parent_id=account_management_menu.id
    )
    get_or_create_menu(
        'choose_language',
        description='Choose default language',
        display_text_en="""CON Choose language
1. English
2. Kiswahili
0. Back""",
        display_text_sw="""CON Chagua lugha
1. Kingereza
2. Kiswahili
0. Nyuma""",
        parent_id=account_management_menu.id
    )
    get_or_create_menu(
        'opt_out_of_market_place_pin_authorization',
        description='PIN authorization opting out of market',
        display_text_en="""CON Please enter your PIN. %remaining_attempts%
0. Back""",
        display_text_sw="""CON Tafadhali weka PIN yako. %remaining_attempts%
0. Nyuma""",
        parent_id=account_management_menu.id
    )

    print('******** Change PIN Menu ********************')
    get_or_create_menu(
        'current_pin',
        description='Change PIN enter current PIN menu',
        display_text_en="""CON Enter current PIN. %remaining_attempts%""",
        display_text_sw="""CON Weka nambari ya siri. %remaining_attempts%""",
        parent_id=account_management_menu.id
    )
    get_or_create_menu(
        'new_pin',
        description='New PIN entry menu',
        display_text_en="""CON Enter new PIN
0. Back""",
        display_text_sw="""CON Weka nambari ya siri mpya
0. Nyuma""",
        parent_id=account_management_menu.id
    )
    get_or_create_menu(
        'new_pin_confirmation',
        description='Confirm new PIN menu',
        display_text_en="""CON Enter new PIN again
0. Back""",
        display_text_sw="""CON Rejelea nambari ya siri mpya
0. Nyuma""",
        parent_id=account_management_menu.id
    )

    print('***** Help Menu *********')
    get_or_create_menu(
        'help',
        description='Help menu',
        display_text_en="""END For assistance call %support_phone%""",
        display_text_sw="""END Kwa usaidizi piga simu %support_phone%""",
        parent_id=start_menu.id
    )

    print('***** Exchange Rate Menu ******')
    exchange_token_menu = get_or_create_menu(
        'exchange_token',
        description='Menu for exchanging tokens from agents',
        display_text_en="""CON Exchange
1. Check Exchange Rate
2. Exchange
0. Back""",
        display_text_sw="""CON Badilisha
1. Kiwango cha ubadilishaji
2. Badilisha
0. Nyuma""",
        parent_id=start_menu.id
    )
    get_or_create_menu(
        'exchange_rate_pin_authorization',
        description='PIN entry for authorization to access exchange rate',
        display_text_en="""CON Please enter your PIN. %remaining_attempts%
0. Back""",
        display_text_sw="""CON Tafadhali ingiza PIN yako. %remaining_attempts%
0. Nyuma""",
        parent_id=exchange_token_menu.id
    )
    get_or_create_menu(
        'request_exchange_rate',
        description='Exchange menu',
        display_text_en="""END We are processing your request for your exchange rate. You will receive an SMS shortly.""",
        display_text_sw="""END Ombi lako la kiwango cha ubadilishaji, linashughulikiwa. Utapokea ujumbe wa SMS kwa muda mfupi.""",
        parent_id=exchange_token_menu.id
    )
    get_or_create_menu(
        'exchange_token_agent_number_entry',
        description='Exchange Token agent number entry',
        display_text_en="""CON Enter Agent Phone Number
0. Back""",
        display_text_sw="""CON Weka nambari ya simu ya Agent
0. Nyuma""",
        parent_id=exchange_token_menu.id
    )
    get_or_create_menu(
        'exchange_token_amount_entry',
        description='Exchange Token amount prompt menu',
        display_text_en="""CON Enter Amount (40 or more)
0. Back""",
        display_text_sw="""CON Weka kiwango (40 au zaidi)
0. Nyuma""",
        parent_id=exchange_token_menu.id
    )
    get_or_create_menu(
        'exchange_token_pin_authorization',
        description='PIN entry for authorization to convert token',
        display_text_en="""CON Please enter your PIN. %remaining_attempts%
0. Back""",
        display_text_sw="""CON Weka nambari ya siri. %remaining_attempts%
0. Nyuma""",
        parent_id=exchange_token_menu.id
    )
    get_or_create_menu(
        'exchange_token_confirmation',
        description='Exchange Token confirmation menu',
        display_text_en="""CON Exchange %exchange_amount% %token_name% from Agent %agent_phone%
1. Confirm
2. Cancel
0. Back""",
        display_text_sw="""CON Badilisha %exchange_amount% %token_name% kutoka kwa Agent %agent_phone%
1. Thibitisha
2. Futa
0. Nyuma""",
        parent_id=exchange_token_menu.id
    )

    # Exit codes
    get_or_create_menu(
        'exit',
        description='Exit menu',
        display_text_en="""END Thank you for using the service.""",
        display_text_sw="""END Asante kwa kutumia huduma."""
    )
    get_or_create_menu(
        'exit_invalid_menu_option',
        description='Invalid menu option',
        display_text_en="""END Invalid menu option. For help, call %support_phone%""",
        display_text_sw="""END Chaguo lako sio sahihi. Kwa usaidizi piga simu %support_phone%"""
    )
    get_or_create_menu(
        'exit_invalid_pin',
        description='PIN policy violation',
        display_text_en="""END The PIN you have entered is Invalid. PIN must consist of 4 digits and must be different from your current PIN. For help, call %support_phone%""",
        display_text_sw="""END PIN uliobonyeza sio sahihi. PIN lazima iwe na nambari nne na lazima iwe tofauti na pin yako ya sasa. Kwa usaidizi piga simu %support_phone%"""
    )
    get_or_create_menu(
        'exit_pin_mismatch',
        description='PIN mismatch. New PIN and the new PIN confirmation do not match',
        display_text_en="""END The new PIN and the new PIN confirmation do not match. Please try again. For help, call %support_phone%""",
        display_text_sw="""END PIN mpya na udhibitisho wa pin mpya hailingani. Tafadhali jaribu tena. Kwa usaidizi piga simu %support_phone%"""
    )
    get_or_create_menu(
        'exit_pin_blocked',
        description='Ussd PIN Blocked Menu',
        display_text_en="""END Your PIN has been blocked. For help, please call %support_phone%""",
        display_text_sw="""END PIN yako imefungwa. Kwa usaidizi tafadhali piga simu %support_phone%"""
    )
    get_or_create_menu(
        'exit_invalid_request',
        description='Key params missing in request',
        display_text_en="""END Invalid request""",
        display_text_sw="""END Chaguo si sahihi"""
    )
    get_or_create_menu(
        'exit_invalid_input',
        description='The user did not select a choice',
        display_text_en="""END Invalid input. Nothing selected""",
        display_text_sw="""END Chaguo lako halipatikani. Hakuna kilichochaguliwa"""
    )
    get_or_create_menu(
        'exit_recipient_not_found',
        description='The recipient does not exist.',
        display_text_en="""END Recipient not found""",
        display_text_sw="""END Mpokeaji hakupatikana"""
    )
    get_or_create_menu(
        'exit_invalid_recipient',
        description='Invalid recipient',
        display_text_en="""END Recipient phone number is incorrect""",
        display_text_sw="""END Mpokeaji wa nambari hapatikani au sio sahihi"""
    )
    get_or_create_menu(
        'exit_use_exchange_menu',
        description='Recipient is token agent, use exchange menu',
        display_text_en="""END Recipient phone number is an agent. To exchange, use exchange menu""",
        display_text_sw="""END Mpoekeaji wa nambari ni agent. Ili kubadilisha, tumia ubadilishaji"""
    )
    get_or_create_menu(
        'exit_invalid_token_agent',
        description='Invalid token agent',
        display_text_en="""END Agent phone number is incorrect""",
        display_text_sw="""END Agent wa nambari hapatikani au sio sahihi"""
    )
    get_or_create_menu(
        'exit_not_registered',
        description='The phone is not registered on Sarafu or has been deactivated.',
        display_text_en="""END END Haujasajiliwa kwa hii huduma. Kusajili tuma: jina, nambari ya simu, kitambulisho, eneo, na biashara yako. Kwa 0757628885""",
        display_text_sw="""END END Haujasajiliwa kwa hii huduma. Kusajili tuma: jina, nambari ya simu, kitambulisho, eneo, na biashara yako. Kwa 0757628885"""
    )
    get_or_create_menu(
        'exit_invalid_exchange_amount',
        description='The token exchange amount is insufficient',
        display_text_en="""END The amount entered is insufficient. Please provide an amount of 40 or more.""",
        display_text_sw="""END Kiwango ulichoweka hakitoshi. Tafadhali weka kiwango cha 40 au zaidi."""
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

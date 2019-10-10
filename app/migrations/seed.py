"""
Migration code from GE - need to translate to Python

CommunityToken.where(name: 'Gatina').first_or_create! do |c|
  c.name = 'Gatina'
  c.token_alias = 'GATINA'
  c.token_identifier = '5b9ccc1a81df57e455340a3f'
  c.contract_address = '0x826a4205b829d1907930b1632f9ce227072e59ca'
end

CommunityToken.where(name: 'Bangla').first_or_create! do |c|
  c.name = 'Bangla'
  c.token_alias = 'BANGLA'
  c.token_identifier = '5b9ccb1c81df57e4553402e8'
  c.contract_address = '0x59c7eec63b7ccd438a6dc428848973f11d894b7d'
end

CommunityToken.where(name: 'Lindi').first_or_create! do |c|
  c.name = 'Lindi'
  c.token_alias = 'LINDI'
  c.token_identifier = '5b9ccdbb81df57e455341650'
  c.contract_address = '0x8a890d89cd3585b06a48a174dd847d7818d3074f'
end

CommunityToken.where(name: 'Kangemi').first_or_create! do |c|
  c.name = 'Kangemi'
  c.token_alias = 'KANG'
  c.token_identifier = '5b9cccbc81df57e455340ee8'
  c.contract_address = '0x22e9839aeff9818a8b3617586167e8b92f2ed3c4'
end

CommunityToken.where(name: "Ng'ombeni").first_or_create! do |c|
  c.name = "Ng'ombeni"
  c.token_alias = 'NGOP'
  c.token_identifier = '5b9ccb9a81df57e45534067d'
end

CommunityToken.where(name: 'Miyani').first_or_create! do |c|
  c.name = 'Miyani'
  c.token_alias = 'MIYANI'
  c.token_identifier = '5c4a78f6522a6fb3bec1936c'
  c.contract_address = '0x6bdd2ddc6044cafc7de6d0d7b05ed8b3271c424e'
end

CommunityToken.where(name: 'Grassroots').first_or_create! do |c|
  c.name = 'Grassroots'
  c.token_alias = 'GEP'
  c.token_identifier = '5b9cce4c81df57e455341a7f'
  c.contract_address = '0xcbe421e457989791c0079ba1d5f45272f917f70b'
end

CommunityToken.where(name: 'Mombasa').first_or_create! do |c|
  c.name = 'Mombasa'
  c.token_alias = 'MSA'
  c.token_identifier = '5b9cc95d81df57e45533f5fc'
  c.contract_address = '0xe1f32c0ac661300e1ae6046a12505e4e4f167fa7'
end

CommunityToken.where(name: 'Olympic').first_or_create! do |c|
  c.name = 'Olympic'
  c.token_alias = 'OLYMPIC'
  c.token_identifier = '5c4a7896522a6f9a73c192ab'
  c.contract_address = '0x59f45d4a9beede88458d74a4f08e73cd9de5ef56'
end

CommunityToken.where(name: 'Takaungu').first_or_create! do |c|
  c.name = 'Takaungu'
  c.token_alias = 'TUNGU'
  c.token_identifier = '5c4a782f522a6f6c93c191da'
  c.contract_address = '0x859db7784dc79e6595cd30d13a32a6d440d34153'
end

CommunityToken.where(name: 'Congo').first_or_create! do |c|
  c.name = 'Congo'
  c.token_alias = 'CONGO'
  c.token_identifier = '5c4a7772522a6f733ec19061'
  c.contract_address = '0xd90da2fa2865af5895f4ef592bf4882fb08b3429'
end

CommunityToken.where(name: 'Sarafu').first_or_create! do |c|
  c.name = 'Sarafu'
  c.token_alias = 'SARAFU'
  c.token_identifier = '5b9cc8c581df57e45533f17a'
  c.contract_address = '0xeef28e529146e43e7beccb592f0d2d494b7ccbd6'
end

CommunityToken.where(name: 'Nairobi').first_or_create! do |c|
  c.name = 'Nairobi'
  c.token_alias = 'NAI'
  c.token_identifier = '5b9cca1b81df57e45533fb7c'
  c.contract_address = '0x62e167dfaab37ecaae88b052b1668ce3f10c22fd'
end

puts 'Creating Sarafu Network USSD Menu'
puts '**********************************************************************'
puts 'Creating Initial Language Selection menu'
UssdMenu.where(name: 'initial_language_selection').first_or_create! do |u|
  u.name = 'initial_language_selection'
  u.description = 'Start menu. This is the entry point for users to select their preferred language'
  u.display_text_en = "CON Welcome to Sarafu
1. English
2. Kiswahili
3. Help"
  u.display_text_sw = "CON Welcome to Sarafu
1. English
2. Kiswahili
3. Help"
end

initial_lang_setup_menu = UssdMenu.find_by(name: 'initial_language_selection')
UssdMenu.where(name: 'initial_pin_entry').first_or_create! do |u|
  u.name = 'initial_pin_entry'
  u.description = 'PIN setup entry menu'
  u.display_text_en = 'CON Please enter a PIN to manage your account.
0. Back'
  u.display_text_sw = 'CON Tafadhali weka PIN ili kudhibiti akaunti yako.
0. Nyuma'
  u.parent_id = initial_lang_setup_menu.id
end

initial_pin_menu = UssdMenu.find_by(name: 'initial_pin_entry')
UssdMenu.where(name: 'initial_pin_confirmation').first_or_create! do |u|
  u.name = 'initial_pin_confirmation'
  u.description = 'Confirm new PIN menu'
  u.display_text_en = 'CON Enter your PIN again
0. Back'
    u.display_text_sw = 'CON Weka PIN yako tena
0. Nyuma'
  u.parent_id = initial_pin_menu.id
end


# ****************************** Start Menu ****************************************************

puts 'Creating Start menu...'
UssdMenu.where(name: 'start').first_or_create! do |u|
  u.name = 'start'
  u.description = 'Start menu. This is the entry point for activated users'
  u.display_text_en = "CON Welcome to Sarafu
1. Send
2. My Account
3. Market Place
4. Exchange
5. Help"
  u.display_text_sw = "CON Karibu Sarafu
1. Tuma
2. Akaunti Yangu
3. Sokoni
4. Badilisha
5. Usaidizi"
end

start_menu = UssdMenu.find_by(name: 'start')

puts 'Creating send token menu...'
UssdMenu.where(name: 'send_enter_recipient').first_or_create! do |u|
  u.name = 'send_enter_recipient'
  u.description = 'Send Token recipient entry'
  u.display_text_en = 'CON Enter Phone Number
0. Back'
  u.display_text_sw = 'CON Weka nambari ya simu
0. Nyuma'
  u.parent_id = start_menu.id
end

UssdMenu.where(name: 'send_token_amount').first_or_create! do |u|
  u.name = 'send_token_amount'
  u.description = 'Send Token amount prompt menu'
  u.display_text_en = 'CON Enter Amount
0. Back'
  u.display_text_sw = 'CON Weka kiwango
0. Nyuma'
  u.parent_id = start_menu.id
end

UssdMenu.where(name: 'send_token_reason').first_or_create! do |u|
  u.name = 'send_token_reason'
  u.description = 'Send Token reason prompt menu'
  u.display_text_en = "CON Select Transfer reason
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
0. Back"
  u.display_text_sw = "CON Chagua kusudi la malipo
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
0. Nyuma"
  u.parent_id = start_menu.id
end

UssdMenu.where(name: 'send_token_reason_other').first_or_create! do |u|
  u.name = 'send_token_reason_other'
  u.description = 'Send Token other reason prompt menu'
  u.display_text_en = 'CON Please specify
0. Back'
  u.display_text_sw = 'CON Fafanua kusudi zaidi
0. Nyuma'
  u.parent_id = start_menu.id
end

UssdMenu.where(name: 'send_token_pin_authorization').first_or_create! do |u|
  u.name = 'send_token_pin_authorization'
  u.description = 'PIN entry for authorization to send token'
  u.display_text_en = 'CON Please enter your PIN. %remaining_attempts%
0. Back'
  u.display_text_sw = 'CON Weka nambari ya siri. %remaining_attempts%
0. Nyuma'
  u.parent_id = start_menu.id
end

UssdMenu.where(name: 'send_token_confirmation').first_or_create! do |u|
  u.name = 'send_token_confirmation'
  u.description = 'Send Token confirmation menu'
  u.display_text_en = 'CON Send %transaction_amount% %token_name% to %recipient_phone% for %transaction_reason%
1. Confirm
2. Cancel
0. Back'
  u.display_text_sw = 'CON Tuma %transaction_amount% %token_name% kwa %recipient_phone%
1. Thibitisha
2. Futa
0. Nyuma'
  u.parent_id = start_menu.id
end

UssdMenu.where(name: 'directory_listing').first_or_create! do |u|
  u.name = 'directory_listing'
  u.description = 'Listing of Market place categories for a user to choose'
  u.display_text_en = 'CON Choose Market Category
1. Food
2. Water
3. Energy
4. Education
5. Health
6. General shop
7. Environment
8. Transport
9. Labour'
  u.display_text_sw = 'CON Chagua unachotaka Sokoni
1. Chakula
2. Maji
3. Kuni/makaa/mafuta/stima
4. Elimu
5. Afya
6. Duka la jumla
7. Mazingira
8. Usafiri
9. Mfanyakazi'
  u.parent_id = start_menu.id
end

UssdMenu.where(name: 'complete').first_or_create! do |u|
  u.name = 'complete'
  u.description = 'Complete menu. Last step of any menu'
  u.display_text_en = 'END Your request has been sent. You will receive an SMS shortly.'
  u.display_text_sw = 'END Ombi lako limetumwa. Utapokea uthibitishaji wa SMS kwa muda mfupi.'
end

puts '****** Manage Account ******'
UssdMenu.where(name: 'account_management').first_or_create! do |u|
  u.name = 'account_management'
  u.description = 'Manage account menu'
  u.display_text_en = 'CON My account
1. My Business
2. Change language
3. Check Balances
4. Change PIN
5. Opt Out of Market Place
0. Back'
  u.display_text_sw = 'CON Akaunti yangu
1. Biashara Yangu
2. Chagua lugha utakayotumia
3. Angalia salio
4. Badilisha nambari ya siri
5. Ondoka Sokoni
0. Nyuma'
  u.parent_id = start_menu.id
end

account_management_menu = UssdMenu.find_by(name: 'account_management')

UssdMenu.where(name: 'my_business').first_or_create! do |u|
  u.name = 'my_business'
  u.description = 'Manage business directory info'
  u.display_text_en = 'CON My Business
1. See my business
2. Change my business
0. Back'
  u.display_text_sw = 'CON Biashara Yangu
1. Angalia biashara
2. Badilisha biashara
0. Nyuma'
  u.parent_id = account_management_menu.id
end

UssdMenu.where(name: 'about_my_business').first_or_create! do |u|
  u.name = 'about_my_business'
  u.description = 'About business directory info'
  u.display_text_en = 'END %user_bio%'
  u.display_text_sw = 'END %user_bio%'
  u.parent_id = account_management_menu.id
end

UssdMenu.where(name: 'change_my_business_prompt').first_or_create! do |u|
  u.name = 'change_my_business_prompt'
  u.description = 'Change business directory info'
  u.display_text_en = 'CON Please enter a product or service you offer
0. Back'
  u.display_text_sw = 'CON Tafadhali weka bidhaa ama huduma unauza
0. Nyuma'
  u.parent_id = account_management_menu.id
end

UssdMenu.where(name: 'balance_inquiry_pin_authorization').first_or_create! do |u|
  u.name = 'balance_inquiry_pin_authorization'
  u.description = 'PIN authorization before Balance enquiry'
  u.display_text_en = 'CON Please enter your PIN. %remaining_attempts%
0. Back'
  u.display_text_sw = 'CON Tafadhali ingiza PIN yako. %remaining_attempts%
0. Nyuma'
  u.parent_id = account_management_menu.id
end

UssdMenu.where(name: 'choose_language').first_or_create! do |u|
  u.name = 'choose_language'
  u.description = 'Choose default language'
  u.display_text_en = 'CON Choose language
1. English
2. Kiswahili
0. Back'
  u.display_text_sw = 'CON Chagua lugha
1. Kingereza
2. Kiswahili
0. Nyuma'
  u.parent_id = account_management_menu.id
end

UssdMenu.where(name: 'opt_out_of_market_place_pin_authorization').first_or_create! do |u|
  u.name = 'opt_out_of_market_place_pin_authorization'
  u.description = 'PIN authorization opting out of market'
  u.display_text_en = 'CON Please enter your PIN. %remaining_attempts%
0. Back'
  u.display_text_sw = 'CON Tafadhali weka PIN yako. %remaining_attempts%
0. Nyuma'
  u.parent_id = account_management_menu.id
end

puts '******** Change PIN Menu ********************'

UssdMenu.where(name: 'current_pin').first_or_create! do |u|
  u.name = 'current_pin'
  u.description = 'Change PIN enter current PIN menu'
  u.display_text_en = 'CON Enter current PIN. %remaining_attempts%'
  u.display_text_sw = 'CON Weka nambari ya siri. %remaining_attempts%'
  u.parent_id = account_management_menu.id
end

UssdMenu.where(name: 'new_pin').first_or_create! do |u|
  u.name = 'new_pin'
  u.description = 'New PIN entry menu'
  u.display_text_en = 'CON Enter new PIN
0. Back'
  u.display_text_sw = 'CON Weka nambari ya siri mpya
0. Nyuma'
  u.parent_id = account_management_menu.id
end

UssdMenu.where(name: 'new_pin_confirmation').first_or_create! do |u|
  u.name = 'new_pin_confirmation'
  u.description = 'Confirm new PIN menu'
  u.display_text_en = 'CON Enter new PIN again
0. Back'
  u.display_text_sw = 'CON Rejelea nambari ya siri mpya
0. Nyuma'
  u.parent_id = account_management_menu.id
end

puts '***** Help Menu *********'
UssdMenu.where(name: 'help').first_or_create! do |u|
  u.name = 'help'
  u.description = 'Help menu'
  u.display_text_en = 'END For assistance call %support_phone%'
  u.display_text_sw = 'END Kwa usaidizi piga simu %support_phone%'
  u.parent_id = start_menu.id
end

puts '***** Exchange Rate Menu ******'

UssdMenu.where(name: 'exchange_token').first_or_create! do |u|
  u.name = 'exchange_token'
  u.description = 'Menu for exchanging tokens from agents'
  u.display_text_en = 'CON Exchange
1. Check Exchange Rate
2. Exchange
0. Back'
    u.display_text_sw = 'CON Badilisha
1. Kiwango cha ubadilishaji
2. Badilisha
0. Nyuma'
  u.parent_id = start_menu.id
end

exchange_token_menu = UssdMenu.find_by(name: 'exchange_token')

UssdMenu.where(name: 'exchange_rate_pin_authorization').first_or_create! do |u|
  u.name = 'exchange_rate_pin_authorization'
  u.description = 'PIN entry for authorization to access exchange rate'
  u.display_text_en = 'CON Please enter your PIN. %remaining_attempts%
0. Back'
  u.display_text_sw = 'CON Tafadhali ingiza PIN yako. %remaining_attempts%
0. Nyuma'
  u.parent_id = exchange_token_menu.id
end

UssdMenu.where(name: 'request_exchange_rate').first_or_create! do |u|
  u.name = 'request_exchange_rate'
  u.description = 'Exchange menu'
  u.display_text_en = 'END We are processing your request for your exchange rate. You will receive an SMS shortly.'
  u.display_text_sw = 'END Ombi lako la kiwango cha ubadilishaji, linashughulikiwa. Utapokea ujumbe wa SMS kwa muda mfupi.'
  u.parent_id = exchange_token_menu.id
end

UssdMenu.where(name: 'exchange_token_agent_number_entry').first_or_create! do |u|
  u.name = 'exchange_token_agent_number_entry'
  u.description = 'Exchange Token agent number entry'
  u.display_text_en = 'CON Enter Agent Phone Number
0. Back'
  u.display_text_sw = 'CON Weka nambari ya simu ya Agent
0. Nyuma'
  u.parent_id = exchange_token_menu.id
end


UssdMenu.where(name: 'exchange_token_amount_entry').first_or_create! do |u|
  u.name = 'exchange_token_amount_entry'
  u.description = 'Exchange Token amount prompt menu'
  u.display_text_en = 'CON Enter Amount (40 or more)
0. Back'
  u.display_text_sw = 'CON Weka kiwango (40 au zaidi)
0. Nyuma'
  u.parent_id = exchange_token_menu.id
end

UssdMenu.where(name: 'exchange_token_pin_authorization').first_or_create! do |u|
  u.name = 'exchange_token_pin_authorization'
  u.description = 'PIN entry for authorization to convert token'
  u.display_text_en = 'CON Please enter your PIN. %remaining_attempts%
0. Back'
  u.display_text_sw = 'CON Weka nambari ya siri. %remaining_attempts%
0. Nyuma'
  u.parent_id = exchange_token_menu.id
end

UssdMenu.where(name: 'exchange_token_confirmation').first_or_create! do |u|
  u.name = 'exchange_token_confirmation'
  u.description = 'Exchange Token confirmation menu'
  u.display_text_en = 'CON Exchange %exchange_amount% %token_name% from Agent %agent_phone%
1. Confirm
2. Cancel
0. Back'
  u.display_text_sw = 'CON Badilisha %exchange_amount% %token_name% kutoka kwa Agent %agent_phone%
1. Thibitisha
2. Futa
0. Nyuma'
  u.parent_id = exchange_token_menu.id
end

# Exit codes
UssdMenu.where(name: 'exit').first_or_create! do |u|
  u.name = 'exit'
  u.description = 'Exit menu'
  u.display_text_en = 'END Thank you for using the service.'
  u.display_text_sw = 'END Asante kwa kutumia huduma.'
end

UssdMenu.where(name: 'exit_invalid_menu_option').first_or_create! do |u|
  u.name = 'exit_invalid_menu_option'
  u.description = 'Invalid menu option'
  u.display_text_en = 'END Invalid menu option. For help, call %support_phone%'
  u.display_text_sw = 'END Chaguo lako sio sahihi. Kwa usaidizi piga simu %support_phone%'
end

UssdMenu.where(name: 'exit_invalid_pin').first_or_create! do |u|
  u.name = 'exit_invalid_pin'
  u.description = 'PIN policy violation'
  u.display_text_en = 'END The PIN you have entered is Invalid. PIN must consist of 4 digits and must be different from your current PIN. For help, call %support_phone%'
  u.display_text_sw = 'END PIN uliobonyeza sio sahihi. PIN lazima iwe na nambari nne na lazima iwe tofauti na pin yako ya sasa. Kwa usaidizi piga simu %support_phone%'
end

UssdMenu.where(name: 'exit_pin_mismatch').first_or_create! do |u|
  u.name = 'exit_pin_mismatch'
  u.description = 'PIN mismatch. New PIN and the new PIN confirmation do not match'
  u.display_text_en = 'END The new PIN and the new PIN confirmation do not match. Please try again. For help, call %support_phone%'
  u.display_text_sw = 'END PIN mpya na udhibitisho wa pin mpya hailingani. Tafadhali jaribu tena. Kwa usaidizi piga simu %support_phone%'
end

UssdMenu.where(name: 'exit_pin_blocked').first_or_create! do |u|
  u.name = 'exit_pin_blocked'
  u.description = 'Ussd PIN Blocked Menu'
  u.display_text_en = 'END Your PIN has been blocked. For help, please call %support_phone%'
  u.display_text_sw = 'END PIN yako imefungwa. Kwa usaidizi tafadhali piga simu %support_phone%'
end

UssdMenu.where(name: 'exit_invalid_request').first_or_create! do |u|
  u.name = 'exit_invalid_request'
  u.description = 'Key params missing in request'
  u.display_text_en = 'END Invalid request'
  u.display_text_sw = 'END Chaguo si sahihi'
end

UssdMenu.where(name: 'exit_invalid_input').first_or_create! do |u|
  u.name = 'exit_invalid_input'
  u.description = 'The user did not select a choice'
  u.display_text_en = 'END Invalid input. Nothing selected'
  u.display_text_sw = 'END Chaguo lako halipatikani. Hakuna kilichochaguliwa'
end

UssdMenu.where(name: 'exit_recipient_not_found').first_or_create! do |u|
  u.name = 'exit_recipient_not_found'
  u.description = 'The recipient does not exist.'
  u.display_text_en = 'END Recipient not found'
  u.display_text_sw = 'END Mpokeaji hakupatikana'
end

UssdMenu.where(name: 'exit_invalid_recipient').first_or_create! do |u|
  u.name = 'exit_invalid_recipient'
  u.description = 'Invalid recipient'
  u.display_text_en = 'END Recipient phone number is incorrect'
  u.display_text_sw = 'END Mpokeaji wa nambari hapatikani au sio sahihi'
end

UssdMenu.where(name: 'exit_use_exchange_menu').first_or_create! do |u|
  u.name = 'exit_use_exchange_menu'
  u.description = 'Recipient is token agent, use exchange menu'
  u.display_text_en = 'END Recipient phone number is an agent. To exchange, use exchange menu'
  u.display_text_sw = 'END Mpoekeaji wa nambari ni agent. Ili kubadilisha, tumia ubadilishaji'

end

UssdMenu.where(name: 'exit_invalid_token_agent').first_or_create! do |u|
  u.name = 'exit_invalid_token_agent'
  u.description = 'Invalid token agent'
  u.display_text_en = 'END Agent phone number is incorrect'
  u.display_text_sw = 'END Agent wa nambari hapatikani au sio sahihi'
end

UssdMenu.where(name: 'exit_not_registered').first_or_create! do |u|
  u.name = 'exit_not_registered'
  u.description = 'The phone is not registered on Sarafu or has been deactivated.'
  u.display_text_en = 'END END Haujasajiliwa kwa hii huduma. Kusajili tuma: jina, nambari ya simu, kitambulisho, eneo, na biashara yako. Kwa 0757628885'
  u.display_text_sw = 'END END Haujasajiliwa kwa hii huduma. Kusajili tuma: jina, nambari ya simu, kitambulisho, eneo, na biashara yako. Kwa 0757628885'
end

UssdMenu.where(name: 'exit_invalid_exchange_amount').first_or_create do |u|
  u.name = 'exit_invalid_exchange_amount'
  u.description = 'The token exchange amount is insufficient'
  u.display_text_en = 'END The amount entered is insufficient. Please provide an amount of 40 or more.'
  u.display_text_sw = 'END Kiwango ulichoweka hakitoshi. Tafadhali weka kiwango cha 40 au zaidi.'
end

puts '------------------------------------------------------------'
puts 'Done creating USSD Menus'


puts 'Creating Business Categories'
puts '**********************************************************************'

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

puts '------------------------------------------------------------'
puts 'Done creating Business Categories'
"""
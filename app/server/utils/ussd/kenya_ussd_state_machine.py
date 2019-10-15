"""
    TODO(ussd): state machine code from GE - need to translate to python

    state :initial_language_selection, initial: true
    state :initial_pin_entry, initial: true
    state :initial_pin_confirmation

    state :start, initial: true
    state :send_enter_recipient
    state :send_token_amount
    state :send_token_reason
    state :send_token_reason_other
    state :send_token_pin_authorization
    state :send_token_confirmation
    state :account_management
    state :balance_inquiry_pin_authorization
    state :choose_language
    state :pin_change
    state :current_pin
    state :new_pin
    state :new_pin_confirmation
    state :directory_listing
    state :exchange_token

    state :exchange_rate_pin_authorization
    state :exchange_token_agent_number_entry
    state :exchange_token_amount_entry
    state :exchange_token_pin_authorization
    state :exchange_token_confirmation
    state :help
    state :my_business
    state :about_my_business
    state :change_my_business_prompt
    state :opt_out_of_market_place_pin_authorization

    state :exit
    state :exit_not_registered
    state :exit_invalid_menu_option
    state :exit_invalid_recipient
    state :exit_use_exchange_menu
    state :exit_wrong_pin
    state :exit_invalid_pin
    state :exit_pin_mismatch
    state :exit_pin_blocked
    state :exit_invalid_token_agent
    state :exit_invalid_exchange_amount
    state :complete

    event :initial_language_selection do
      transitions from: :initial_language_selection, to: :complete, after: :change_preferred_language
      transitions from: :initial_language_selection, to: :help, guard: :menu_three_selected
      transitions from: :initial_language_selection, to: :exit_invalid_menu_option
    end

    event :initial_pin_entry do
      transitions from: :initial_pin_entry, to: :initial_pin_confirmation, guard: :validate_initial_pin
      transitions from: :initial_pin_entry, to: :exit_invalid_pin
    end

    event :initial_pin_confirmation do
      transitions from: :initial_pin_confirmation, to: :complete, guard: :match_new_pins, after: :complete_initial_pin_change
      transitions from: :initial_pin_confirmation, to: :exit_pin_mismatch
    end

    event :start do
      transitions from: :start, to: :send_enter_recipient, guard: :menu_one_selected
      transitions from: :start, to: :account_management, guard: :menu_two_selected
      transitions from: :start, to: :directory_listing, guard: :menu_three_selected
      transitions from: :start, to: :exchange_token, guard: :menu_four_selected
      transitions from: :start, to: :help, guard: :menu_five_selected
      transitions from: :start, to: :exit_invalid_menu_option
    end

    event :send_enter_recipient do
      transitions from: :send_enter_recipient, to: :send_token_amount, guard: :valid_recipient, after: :save_recipient_phone
      transitions from: :send_enter_recipient, to: :exit_use_exchange_menu, guard: :token_agent_exists
      transitions from: :send_enter_recipient, to: :exit_invalid_recipient, after: :upsell_unregistered_recipient
    end

    event :send_token_amount do
      transitions from: :send_token_amount, to: :send_token_reason, after: :save_transaction_amount
    end

    event :send_token_reason do
      transitions from: :send_token_reason, to: :send_token_reason_other, guard: :menu_ten_selected
      transitions from: :send_token_reason, to: :send_token_pin_authorization, after: :save_transaction_reason
    end

    event :send_token_reason_other do
      transitions from: :send_token_reason_other, to: :send_token_pin_authorization, after: :save_transaction_reason_other
    end

    event :send_token_pin_authorization do
      transitions from: :send_token_pin_authorization, to: :send_token_confirmation, guard: :authorize_pin
      transitions from: :send_token_pin_authorization, to: :exit_pin_blocked, guard: :blocked_pin
    end

    event :send_token_confirmation do
      transitions from: :send_token_confirmation, to: :complete, guard: :menu_one_selected, after: :process_send_token_request
      transitions from: :send_token_confirmation, to: :exit, guard: :menu_two_selected
      transitions from: :send_token_confirmation, to: :exit_invalid_menu_option
    end

    event :account_management do
      transitions from: :account_management, to: :my_business, guard: :menu_one_selected
      transitions from: :account_management, to: :choose_language, guard: :menu_two_selected
      transitions from: :account_management, to: :balance_inquiry_pin_authorization, guard: :menu_three_selected
      transitions from: :account_management, to: :current_pin, guard: :menu_four_selected
      transitions from: :account_management, to: :opt_out_of_market_place_pin_authorization, guard: :menu_five_selected
      transitions from: :account_management, to: :exit_invalid_menu_option
    end

    event :balance_inquiry_pin_authorization do
      transitions from: :balance_inquiry_pin_authorization, to: :complete, guard: :authorize_pin, after: :request_balance
      transitions from: :balance_inquiry_pin_authorization, to: :exit_pin_blocked, guard: :blocked_pin
    end

    event :directory_listing do
      transitions from: :directory_listing, to: :complete, after: :send_directory_listing
    end

    event :my_business do
      transitions from: :my_business, to: :about_my_business, guard: :menu_one_selected
      transitions from: :my_business, to: :change_my_business_prompt, guard: :menu_two_selected
    end

    event :change_my_business_prompt do
      transitions from: :change_my_business_prompt, to: :exit, after: :save_business_directory_info
    end

    event :choose_language do
      transitions from: :choose_language, to: :complete, after: :change_preferred_language
    end

    event :current_pin do
      transitions from: :current_pin, to: :new_pin, guard: :authorize_pin
      transitions from: :current_pin, to: :exit_pin_blocked, guard: :blocked_pin
    end

    event :new_pin do
      transitions from: :new_pin, to: :new_pin_confirmation, guard: :validate_new_pin
      transitions from: :new_pin, to: :exit_invalid_pin
    end

    event :new_pin_confirmation do
      transitions from: :new_pin_confirmation, to: :complete, guard: :match_new_pins, after: :complete_pin_change
      transitions from: :new_pin_confirmation, to: :exit_pin_mismatch
    end
    event :opt_out_of_market_place_pin_authorization do
      transitions from: :opt_out_of_market_place_pin_authorization, to: :complete, guard: :authorize_pin, after: :change_opt_in_market_status
      transitions from: :opt_out_of_market_place_pin_authorization, to: :exit_pin_blocked, guard: :blocked_pin
    end

    event :exchange_token do
      transitions from: :exchange_token, to: :exchange_rate_pin_authorization, guard: :menu_one_selected
      transitions from: :exchange_token, to: :exchange_token_agent_number_entry, guard: :menu_two_selected
      transitions from: :exchange_token, to: :exit_invalid_menu_option
    end

    event :exchange_rate_pin_authorization do
      transitions from: :exchange_rate_pin_authorization, to: :complete, guard: :authorize_pin, after: :fetch_user_exchange_rate
      transitions from: :exchange_rate_pin_authorization, to: :exit_pin_blocked, guard: :blocked_pin
    end

    event :exchange_token_agent_number_entry do
      transitions from: :exchange_token_agent_number_entry, to: :exchange_token_amount_entry, guard: :valid_token_agent, after: :save_exchange_agent_phone
      transitions from: :exchange_token_agent_number_entry, to: :exit_invalid_token_agent
    end

    event :exchange_token_amount_entry do
      transitions from: :exchange_token_amount_entry, to: :exchange_token_pin_authorization, guard: :valid_token_exchange_amount, after: :save_exchange_amount
      transitions from: :exchange_token_amount_entry, to: :exit_invalid_exchange_amount
    end

    event :exchange_token_pin_authorization do
      transitions from: :exchange_token_pin_authorization, to: :exchange_token_confirmation, guard: :authorize_pin
      transitions from: :exchange_token_pin_authorization, to: :exit_pin_blocked, guard: :blocked_pin
    end

    event :exchange_token_confirmation do
      transitions from: :exchange_token_confirmation, to: :complete, guard: :menu_one_selected, after: :process_exchange_token_request
      transitions from: :exchange_token_confirmation, to: :exit, guard: :menu_two_selected
      transitions from: :exchange_token_confirmation, to: :exit_invalid_menu_option
    end

    event :help do
      transitions from: :help, to: :complete
    end
"""
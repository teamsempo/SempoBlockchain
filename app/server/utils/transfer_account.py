from server.exceptions import NoTransferAccountError


def find_transfer_accounts_with_matching_token(account_holder, token):
    matching_transfer_accounts = []
    print('account_holder')
    print(account_holder)
    print(account_holder)
    print(account_holder)
    print(account_holder)
    print(account_holder)
    for transfer_account in account_holder.transfer_accounts:
        if transfer_account.token == token:
            matching_transfer_accounts.append(transfer_account)
    if len(matching_transfer_accounts) == 0:
        raise NoTransferAccountError(f"No transfer account for holder {account_holder} and token {token}")
    if len(matching_transfer_accounts) > 1:
        raise Exception(f"User has multiple transfer accounts for token {token}")
    return matching_transfer_accounts[0]

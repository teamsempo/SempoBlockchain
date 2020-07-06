from server.exceptions import NoTransferAccountError


def find_transfer_accounts_with_matching_token(account_holder, token):
    print('zzzzzzzzzzzzzzzzz')
    print(account_holder)
    print(token)
    matching_transfer_accounts = []
    for transfer_account in account_holder.transfer_accounts:
        if transfer_account.token == token:
            matching_transfer_accounts.append(transfer_account)
    if len(matching_transfer_accounts) == 0:
        raise NoTransferAccountError(f"No transfer account for holder {account_holder} and token {token}")
    if len(matching_transfer_accounts) > 1:
        raise Exception(f"User has multiple transfer accounts for token {token}")
    print(matching_transfer_accounts[0])
    print(matching_transfer_accounts[0])
    print(matching_transfer_accounts[0])
    print(matching_transfer_accounts[0])
    print(matching_transfer_accounts[0])
    print(matching_transfer_accounts[0])
    print(matching_transfer_accounts[0])
    print(matching_transfer_accounts[0])
    return matching_transfer_accounts[0]
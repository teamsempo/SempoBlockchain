"""
This file (test_misc.py) contains the unit tests for the misc.py file in utils dir.
"""


def test_encrypt_and_decrypt_string(test_client):
    """
    GIVEN encrypt_string and decrypt_string function
    WHEN a string is encrypted then decrypted
    THEN check equals original string
    :return:
    """
    from server.utils.misc import encrypt_string, decrypt_string

    string = 'PASSWORD1234'
    encrypted_string = encrypt_string(string)
    assert string not in encrypted_string
    assert isinstance(encrypted_string, str)

    decrypted_string = decrypt_string(encrypted_string)
    assert decrypted_string == string

import pytest
from server.utils.user import set_custom_attributes

def test_custom_attribute_cleansing(create_transfer_account_user):
    user = create_transfer_account_user

    # Test a base custom attribute
    attribute_dict = {'custom_attributes': {}}
    attribute_dict['custom_attributes']['gender'] = 'female'

    ca = set_custom_attributes(attribute_dict, user)[0]

    assert user.custom_attributes[0].value == 'female'
    assert user.custom_attributes[0].key == 'gender'
    
    # Test each of the cleaning steps
    attribute_dict['custom_attributes']['gender'] = 'PIZZA'
    # PIZZA -> pizza -> aaba -> aaa -> AAA
    ca.custom_attribute.cleaning_steps = [ ( "lower", ), ( 'replace', ['pizz', 'aa'] ), ( 'upper', ) ]
    ca = set_custom_attributes(attribute_dict, user)[0]
    assert user.custom_attributes[0].value == 'AAA'
    assert user.custom_attributes[0].key == 'gender'

    # Test that when options are set, you can't add things which aren't options
    ca.custom_attribute.cleaning_steps = None
    ca.custom_attribute.options = ['male', 'female', 'other']
    attribute_dict['custom_attributes']['gender'] = 'PIZZA'
    with pytest.raises(Exception):
        set_custom_attributes(attribute_dict, user)[0]
        
    attribute_dict['custom_attributes']['gender'] = 'male'
    set_custom_attributes(attribute_dict, user)[0]
    assert user.custom_attributes[0].value == 'male'

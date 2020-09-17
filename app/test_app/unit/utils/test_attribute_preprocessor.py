import pytest
from server.utils import attribute_preprocessor as ap
from server.utils.auth import show_all


@pytest.fixture(scope='module')
def create_map(create_organisation, init_database):
    from server.models.attribute_map import AttributeMap

    attribute_map = AttributeMap(
        input_name='your_first_name',
        output_name='first_name',
        organisation=create_organisation
    )
    init_database.session.add(attribute_map)
    init_database.session.commit()

    return attribute_map

@pytest.fixture(scope='module')
@show_all
def create_setting(create_organisation, init_database):
    from server.models.settings import Settings

    s = Settings(name='magic_setting', value=42)
    s.organisation = create_organisation

    init_database.session.add(s)
    init_database.session.commit()

@pytest.mark.parametrize('in_data, out_data', [
    ({'is_vendor': True, '_data': {'first_name': 'Alice'}}, {'is_vendor': True, 'first_name': 'Alice'}),
    ({'is_vendor': True, 'first_name': 'Alice'}, {'is_vendor': True, 'first_name': 'Alice'}),
    ({'is_vendor': True, '_data': {'is_vendor': False}}, {'is_vendor': False})
])
def test_unwrap_data(in_data, out_data):
    assert out_data == ap.unwrap_data(in_data)

@pytest.mark.parametrize('in_data, out_data', [
    ({'your_first_name': 'bar'}, {'first_name': 'bar'}),
    ({'foo': 'bar'}, {'foo': 'bar'}),
    ({'bar': 'your_first_name'}, {'bar': 'your_first_name'}),
    ({'your_first_name': 'more_than_foo'}, {'first_name': 'more_than_foo'}),
])
@show_all
def test_map_attribute_keys(create_map, in_data, out_data):
    assert out_data == ap.map_attribute_keys(in_data)


@pytest.mark.parametrize('in_data, out_data', [
    ({'meta/instanceID': 'BAR'}, {}),
    ({'foo': 'meta/instanceID'}, {'foo': 'meta/instanceID'}),
    ({'foo': 'bar'}, {'foo': 'bar'})
])
def test_filter_out_kobo_meta_attributes(in_data, out_data):
    assert out_data == ap.filter_out_kobo_meta_attributes(in_data)


@pytest.mark.parametrize('in_data, out_data', [
    ({'_foo': 'BAR'}, {}),
    ({'foo': 'bar'}, {'foo': 'bar'}),
    ({'foo': '_bar'}, {'foo': '_bar'})
])
def test_filter_out_underscore_prefixed_attributes(in_data, out_data):
    assert out_data == ap.filter_out_underscore_prefixed_attributes(in_data)


@pytest.mark.parametrize('in_data, out_data', [
    ({'my_custom_attribute': 'BAR'}, {'custom_attributes': {'my_custom_attribute': 'BAR'}}),
    ({'first_name': 'WOZ'}, {'first_name': 'WOZ'}),
    ({'custom_attributes': {'my_custom_attribute': 'BAR'}}, {'custom_attributes': {'my_custom_attribute': 'BAR'}}),
    ({'custom_attributes': {'a': '1'}, 'b': '2'}, {'custom_attributes': {'a': '1', 'b': '2'}})
])
def test_convert_unknown_attributes_to_custom_attributes(in_data, out_data):
    assert out_data == ap.convert_unknown_attributes_to_custom_attributes(in_data)


@pytest.mark.parametrize('in_data, out_data', [
    ({'FOO': 'BAR'}, {'foo': 'BAR'}),
])
def test_force_attribute_dict_keys_to_lowercase(in_data, out_data):
    assert out_data == ap.force_attribute_dict_keys_to_lowercase(in_data)


@pytest.mark.parametrize('in_data, out_data', [
    ({'dkdkdd/foo': 'lots_of/_bar'}, {'foo': 'lots_of/_bar'}),
    ({'foo': 'bar'}, {'foo': 'bar'}),
])
def test_strip_preslashes(in_data, out_data):
    assert out_data == ap.strip_preslashes(in_data)


@pytest.mark.parametrize('in_data, out_data', [
    ({'foo': 'bar'}, {'foo': 'bar', 'magic_setting': 42}),
])
def test_insert_settings_from_database(in_data, out_data, create_setting):
    assert out_data == ap.insert_settings_from_database(['magic_setting'], in_data)


@pytest.mark.parametrize('in_data, out_data', [
    ({'f\no\ro\t': '\nba\nr\t house'}, {'foo': 'bar house'}),
    ({'/tfoo': 'lot/n3'}, {'/tfoo': 'lot/n3'}),
    ({'baz': True}, {'baz': True}),
    ({'baz': 122.3}, {'baz': 122.3}),
])
def test_strip_weirdspace_characters(in_data, out_data):
    assert out_data == ap.strip_weirdspace_characters(in_data)


@pytest.mark.parametrize('in_data, out_data', [
    ({'foo': 'YES'}, {'foo': True}),
    ({'foo': 'Yes'}, {'foo': True}),
    ({'foo': True}, {'foo': True}),
    ({'foo': 'NO'}, {'foo': False}),
    ({'foo': 'No'}, {'foo': False}),
    ({'foo': False}, {'foo': False}),
    ({'foo': 1}, {'foo': 1}),
    ({'foo': 0}, {'foo': 0})
])
def test_attempt_to_truthy_values(in_data, out_data):
    assert out_data == ap.attempt_to_truthy_values(in_data)

@show_all
def test_attribute_processor_piping(create_map, create_setting):

    data = {
        'your_first_name': 'WOO',
        'BOO': 'MOO'
    }

    data = ap.standard_user_preprocess(data, ['magic_setting'])

    assert data == {'first_name': 'WOO', 'magic_setting': 42, 'custom_attributes': {'boo': 'MOO'}}


from run import SuperblocksObject

mock_data = SuperblocksObject({"name": "ro", "meta": {"tags": [1,2,3,4, {"obj_name": {"publish": True}, "obj_id": {"publish": False}}], "ssl": {"key": "123", "value": "345"} }})


def test_access_values_using_dot():
    assert mock_data.name == "ro"
    assert mock_data.meta.tags[:-1] == [1,2,3,4]
    assert mock_data.meta.tags[-1] == {'obj_name': {'publish': True}, 'obj_id': {'publish': False}}
    assert mock_data.meta.tags[-1].obj_name.publish == True
    assert mock_data.meta.tags[-1] == {'obj_name': {'publish': True}, 'obj_id': {'publish': False}}
    assert mock_data.meta.tags[-1].obj_name.publish == True
    assert mock_data.meta.ssl == {'key': '123', 'value': '345'}
    assert list(mock_data.meta.ssl.keys()) == ['key', 'value']

def test_access_values_using_dict_syntax():
    assert mock_data['name'] == "ro"
    assert mock_data['meta']['ssl']['key'] == "123"

def test_access_values_using_mixed_syntax():
    assert mock_data.meta["tags"][:-1] == [1,2,3,4]
    assert mock_data.meta.tags[-1]['obj_name'].publish == True
    assert mock_data.meta.tags[-1]['obj_name']['publish'] == True
    assert mock_data.meta.tags[-1].obj_name['publish'] == True
    assert mock_data['meta'].ssl.key == "123"
    assert mock_data['meta']['ssl'].key == "123"

def test_add_attributes():
    mock_data = SuperblocksObject({"name": "tom"})
    mock_data.age = 10

    assert mock_data.age == 10
    assert mock_data['age'] == 10

    mock_data.meta = {
        'key': 'value',
        'tags': [1,2,3,4]
    }

    assert mock_data['meta']['key'] == 'value'
    assert mock_data['meta']['tags'] == [1,2,3,4]

def test_delete_attributes_using_dict_syntax():
    mock_data = SuperblocksObject({"name": "ro", "meta": {"tags": [1,2,3,4, {"obj_name": {"publish": True}, "obj_id": {"publish": False}}], "ssl": {"key": "123", "value": "345"} }})
    del mock_data['name']

    try:
        mock_data.name
        assert False, "expect AttributeError"
    except AttributeError:
        assert True

def test_delete_attributes_using_attr_syntax():
    del mock_data.meta
    try:
        mock_data.meta
        assert False, "expect AttributeError"
    except AttributeError:
        assert True

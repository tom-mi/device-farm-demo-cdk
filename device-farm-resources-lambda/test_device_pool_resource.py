import pytest
from unittest.mock import MagicMock

from src import device_pool_resource

TEST_DEVICE_POOL_NAME = 'device-pool-name'
TEST_RESPONSE_URL = 'http://example.com/response'
TEST_PHYSICAL_RESOURCE_ID = 'arn:aws:devicefarm:us-west-2::devicepool:67890'
TEST_PROJECT_ID = '12345'
TEST_TOP_DEVICES_ARN = 'arn:top-devices'
TEST_PROJECT_ARN = 'arn:aws:devicefarm:us-west-2:account-id:project:12345'
TEST_DEVICE_POOL_RULES = [{
    'attribute': 'REMOTE_ACCESS_ENABLED',
    'operator': 'EQUALS',
    'value': 'True',
}]
TEST_DESCRIPTION = 'This is my new shiny device pool'
TEST_MAX_DEVICES = 42
TEST_VALID_RESOURCE_PROPERTIES = {
    'ProjectArn': TEST_PROJECT_ARN,
    'Name': TEST_DEVICE_POOL_NAME,
    'Rules': TEST_DEVICE_POOL_RULES,
    'Description': TEST_DESCRIPTION,
    'MaxDevices': TEST_MAX_DEVICES,
}


@pytest.fixture
def context():
    mock = MagicMock()
    mock.log_stream_name = 'stream'
    return mock


@pytest.fixture
def device_farm_endpoint(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr('boto3.client', MagicMock(return_value=mock))
    mock.create_device_pool = MagicMock(return_value={
        'devicePool': {
            'arn': TEST_PHYSICAL_RESOURCE_ID,
            'name': TEST_DEVICE_POOL_NAME,
            'description': TEST_DESCRIPTION,
            'type': 'PRIVATE',
            'rules': TEST_DEVICE_POOL_RULES,
            'maxDevices': TEST_MAX_DEVICES
        }
    })
    return mock


@pytest.mark.parametrize('resource_properties,expected_reason', [
    # missing parameters
    ({}, 'Required property ProjectArn not set'),
    ({'Name': TEST_DEVICE_POOL_NAME, 'Rules': TEST_DEVICE_POOL_RULES}, 'Required property ProjectArn not set'),
    ({'ProjectArn': TEST_PROJECT_ARN, 'Rules': TEST_DEVICE_POOL_RULES}, 'Required property Name not set'),
    ({'ProjectArn': TEST_PROJECT_ARN, 'Name': TEST_DEVICE_POOL_NAME}, 'Required property Rules not set'),
    # invalid parameters
    ({'ProjectArn': TEST_PROJECT_ARN, 'Name': TEST_DEVICE_POOL_NAME, 'Rules': TEST_DEVICE_POOL_RULES, 'Foo': 'foo'},
     'Unknown properties found: Foo'),
])
def test_handler_create_missing_or_invalid_parameter(resource_properties, expected_reason, context,
                                                     device_farm_endpoint):
    event = {
        'RequestType': 'Create',
        'LogicalResourceId': 'DeviceFarm',
        'RequestId': '1234',
        'ResponseURL': TEST_RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-2:namespace:stack/stack-name/guid',
        'ResourceProperties': resource_properties,
    }

    with pytest.raises(Exception):
        device_pool_resource.lambda_handler(event, context)

    device_farm_endpoint.create_device_pool.assert_not_called()
    device_farm_endpoint.update_device_pool.assert_not_called()


def test_handler_create(context, device_farm_endpoint):
    event = {
        'RequestType': 'Create',
        'LogicalResourceId': 'DeviceFarm',
        'RequestId': '1234',
        'ResponseURL': TEST_RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-2:namespace:stack/stack-name/guid',
        'ResourceProperties': TEST_VALID_RESOURCE_PROPERTIES,
    }

    result = device_pool_resource.lambda_handler(event, context)

    assert result['PhysicalResourceId'] == TEST_PHYSICAL_RESOURCE_ID
    assert result['Data']['Arn'] == TEST_PHYSICAL_RESOURCE_ID
    device_farm_endpoint.create_device_pool.assert_called_with(
        projectArn=TEST_PROJECT_ARN,
        name=TEST_DEVICE_POOL_NAME,
        description=TEST_DESCRIPTION,
        rules=TEST_DEVICE_POOL_RULES,
        maxDevices=TEST_MAX_DEVICES,
    )
    device_farm_endpoint.update_device_pool.assert_not_called()


def test_handler_create_without_optional_parameters(context, device_farm_endpoint):
    event = {
        'RequestType': 'Create',
        'LogicalResourceId': 'DeviceFarm',
        'RequestId': '1234',
        'ResponseURL': TEST_RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-2:namespace:stack/stack-name/guid',
        'ResourceProperties': {
            'ProjectArn': TEST_PROJECT_ARN,
            'Name': TEST_DEVICE_POOL_NAME,
            'Rules': TEST_DEVICE_POOL_RULES,
        }
    }

    result = device_pool_resource.lambda_handler(event, context)

    assert result['PhysicalResourceId'] == TEST_PHYSICAL_RESOURCE_ID
    assert result['Data']['Arn'] == TEST_PHYSICAL_RESOURCE_ID
    device_farm_endpoint.create_device_pool.assert_called_with(
        projectArn=TEST_PROJECT_ARN,
        name=TEST_DEVICE_POOL_NAME,
        rules=TEST_DEVICE_POOL_RULES,
    )
    device_farm_endpoint.update_device_pool.assert_not_called()


def test_handler_create_fails(context, device_farm_endpoint):
    event = {
        'RequestType': 'Create',
        'LogicalResourceId': 'DeviceFarm',
        'RequestId': '1234',
        'ResponseURL': TEST_RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-2:namespace:stack/stack-name/guid',
        'ResourceProperties': TEST_VALID_RESOURCE_PROPERTIES,
    }
    device_farm_endpoint.create_device_pool = MagicMock(side_effect=Exception('This went wrong'))

    with pytest.raises(Exception):
        device_pool_resource.lambda_handler(event, context)

    device_farm_endpoint.create_device_pool.assert_called_with(
        projectArn=TEST_PROJECT_ARN,
        name=TEST_DEVICE_POOL_NAME,
        description=TEST_DESCRIPTION,
        rules=TEST_DEVICE_POOL_RULES,
        maxDevices=TEST_MAX_DEVICES,
    )
    device_farm_endpoint.update_device_pool.assert_not_called()


def test_handler_update(context, device_farm_endpoint):
    event = {
        'RequestType': 'Update',
        'LogicalResourceId': 'DeviceFarm',
        'PhysicalResourceId': TEST_PHYSICAL_RESOURCE_ID,
        'RequestId': '1234',
        'ResponseURL': TEST_RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-2:namespace:stack/stack-name/guid',
        'ResourceProperties': TEST_VALID_RESOURCE_PROPERTIES,
    }

    result = device_pool_resource.lambda_handler(event, context)

    assert result['PhysicalResourceId'] == TEST_PHYSICAL_RESOURCE_ID
    assert result['Data']['Arn'] == TEST_PHYSICAL_RESOURCE_ID
    device_farm_endpoint.create_device_pool.assert_not_called()
    device_farm_endpoint.update_device_pool.assert_called_with(
        arn=TEST_PHYSICAL_RESOURCE_ID,
        name=TEST_DEVICE_POOL_NAME,
        description=TEST_DESCRIPTION,
        rules=TEST_DEVICE_POOL_RULES,
        maxDevices=TEST_MAX_DEVICES,
    )


def test_handler_update_without_optional_parameters(context, device_farm_endpoint):
    event = {
        'RequestType': 'Update',
        'LogicalResourceId': 'DeviceFarm',
        'PhysicalResourceId': TEST_PHYSICAL_RESOURCE_ID,
        'RequestId': '1234',
        'ResponseURL': TEST_RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-2:namespace:stack/stack-name/guid',
        'ResourceProperties': {
            'ProjectArn': TEST_PROJECT_ARN,
            'Name': TEST_DEVICE_POOL_NAME,
            'Rules': TEST_DEVICE_POOL_RULES,
        }
    }

    result = device_pool_resource.lambda_handler(event, context)

    assert result['PhysicalResourceId'] == TEST_PHYSICAL_RESOURCE_ID
    assert result['Data']['Arn'] == TEST_PHYSICAL_RESOURCE_ID
    device_farm_endpoint.create_device_pool.assert_not_called()
    device_farm_endpoint.update_device_pool.assert_called_with(
        arn=TEST_PHYSICAL_RESOURCE_ID,
        name=TEST_DEVICE_POOL_NAME,
        rules=TEST_DEVICE_POOL_RULES,
        clearMaxDevices=True,
    )


def test_handler_update_clear_max_devices(context, device_farm_endpoint):
    event = {
        'RequestType': 'Update',
        'LogicalResourceId': 'DeviceFarm',
        'PhysicalResourceId': TEST_PHYSICAL_RESOURCE_ID,
        'RequestId': '1234',
        'ResponseURL': TEST_RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-2:namespace:stack/stack-name/guid',
        'ResourceProperties': {
            'ProjectArn': TEST_PROJECT_ARN,
            'Name': TEST_DEVICE_POOL_NAME,
            'Rules': TEST_DEVICE_POOL_RULES,
            'Description': TEST_DESCRIPTION,
        },
    }

    result = device_pool_resource.lambda_handler(event, context)

    assert result['PhysicalResourceId'] == TEST_PHYSICAL_RESOURCE_ID
    assert result['Data']['Arn'] == TEST_PHYSICAL_RESOURCE_ID
    device_farm_endpoint.create_device_pool.assert_not_called()
    device_farm_endpoint.update_device_pool.assert_called_with(
        arn=TEST_PHYSICAL_RESOURCE_ID,
        name=TEST_DEVICE_POOL_NAME,
        description=TEST_DESCRIPTION,
        rules=TEST_DEVICE_POOL_RULES,
        clearMaxDevices=True,
    )


def test_handler_update_fails(context, device_farm_endpoint):
    event = {
        'RequestType': 'Update',
        'LogicalResourceId': 'DeviceFarm',
        'PhysicalResourceId': TEST_PHYSICAL_RESOURCE_ID,
        'RequestId': '1234',
        'ResponseURL': TEST_RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-2:namespace:stack/stack-name/guid',
        'ResourceProperties': TEST_VALID_RESOURCE_PROPERTIES,
    }
    device_farm_endpoint.update_device_pool = MagicMock(side_effect=Exception('This went wrong'))

    with pytest.raises(Exception):
        device_pool_resource.lambda_handler(event, context)

    device_farm_endpoint.create_device_pool.assert_not_called()
    device_farm_endpoint.update_device_pool.assert_called_with(
        arn=TEST_PHYSICAL_RESOURCE_ID,
        name=TEST_DEVICE_POOL_NAME,
        description=TEST_DESCRIPTION,
        rules=TEST_DEVICE_POOL_RULES,
        maxDevices=TEST_MAX_DEVICES,
    )


def test_handler_delete(context, device_farm_endpoint):
    event = {
        'RequestType': 'Delete',
        'LogicalResourceId': 'DeviceFarm',
        'PhysicalResourceId': TEST_PHYSICAL_RESOURCE_ID,
        'RequestId': '1234',
        'ResponseURL': TEST_RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-2:namespace:stack/stack-name/guid',
        'ResourceProperties': TEST_VALID_RESOURCE_PROPERTIES,
    }

    result = device_pool_resource.lambda_handler(event, context)

    assert result['PhysicalResourceId'] == TEST_PHYSICAL_RESOURCE_ID
    device_farm_endpoint.create_device_pool.assert_not_called()
    device_farm_endpoint.update_device_pool.assert_not_called()
    device_farm_endpoint.delete_device_pool.assert_called_with(arn=TEST_PHYSICAL_RESOURCE_ID)


def test_handler_delete_not_created(context, device_farm_endpoint):
    event = {
        'RequestType': 'Delete',
        'LogicalResourceId': 'DeviceFarm',
        'PhysicalResourceId': 'ResourceNotCreated',
        'RequestId': '1234',
        'ResponseURL': TEST_RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-2:namespace:stack/stack-name/guid',
        'ResourceProperties': TEST_VALID_RESOURCE_PROPERTIES,
    }

    result = device_pool_resource.lambda_handler(event, context)

    assert result['PhysicalResourceId'] == 'ResourceNotCreated'
    device_farm_endpoint.create_devic_pool.assert_not_called()
    device_farm_endpoint.update_devic_pool.assert_not_called()
    device_farm_endpoint.delete_devic_pool.assert_not_called()


def test_handler_delete_fails(context, device_farm_endpoint):
    event = {
        'RequestType': 'Delete',
        'LogicalResourceId': 'DeviceFarm',
        'PhysicalResourceId': TEST_PHYSICAL_RESOURCE_ID,
        'RequestId': '1234',
        'ResponseURL': TEST_RESPONSE_URL,
        'StackId': 'arn:aws:cloudformation:us-east-2:namespace:stack/stack-name/guid',
        'ResourceProperties': TEST_VALID_RESOURCE_PROPERTIES,
    }
    device_farm_endpoint.delete_device_pool = MagicMock(side_effect=Exception('This went wrong'))

    with pytest.raises(Exception):
        device_pool_resource.lambda_handler(event, context)

    device_farm_endpoint.create_device_pool.assert_not_called()
    device_farm_endpoint.update_device_pool.assert_not_called()
    device_farm_endpoint.delete_device_pool.assert_called_with(arn=TEST_PHYSICAL_RESOURCE_ID)

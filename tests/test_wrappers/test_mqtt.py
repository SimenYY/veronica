

import pytest
import paho.mqtt.client as mqtt
from veronica.wrappers.mqtt import MqttClientV2

_MQTT_BROKER_HOST = "172.20.61.6"
_MQTT_BROKER_PORT = 1883

@pytest.fixture
def mqtt_client():
    client = MqttClientV2(
        host=_MQTT_BROKER_HOST,
        port=_MQTT_BROKER_PORT
    )
    return client

def test_mqtt_connect_and_disconnect(mqtt_client):
    try:
        result = mqtt_client.connect()
        assert result == mqtt.MQTT_ERR_SUCCESS
        assert mqtt_client.is_connected()
        
    except Exception as e:
        pytest.fail(f"Unexpected error: {e}")
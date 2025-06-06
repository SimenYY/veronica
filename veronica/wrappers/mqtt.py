import uuid
import logging
from typing import Tuple, Any, Optional, Union
from dataclasses import field

try:
    import paho.mqtt.client as mqtt
    from paho.mqtt.client import (
        CallbackOnConnect,
        CallbackOnDisconnect,
        CallbackOnConnectFail,
        CallbackOnMessage,
        CallbackOnPublish,
        CallbackOnSubscribe,
        CallbackOnLog,
    )
    from paho.mqtt.enums import CallbackAPIVersion, MQTTErrorCode
except ImportError:
    raise ImportError("paho-mqtt is not installed., Please install it using pip insall veronica[mqtt]")

from veronica.base.models import DataModel

logger = logging.getLogger(__name__)


__all__ = [
    "MqttClientV2",
]

class MqttClientV2(DataModel):
    """MQTT client wrapper based on Callback API Version 2
    
    Notes:
        Uses MQTT v5.0
        Requires paho-mqtt >= 2.0
    """
    host: str = "localhost"
    port: int = 1883
    client_id: Optional[str] = None
    auth: Optional[Tuple[str, str]] = field(default=None, repr=False)
    user_data: Any = None
    qos: int = 0
    
    
    def __post_init__(self) -> None:
        if self.client_id is None:
            self.client_id = f"mqtt_client_v2_{uuid.uuid4()}"
        
        self._client: mqtt.Client = mqtt.Client(
            CallbackAPIVersion.VERSION2,
            client_id=self.client_id
        )
        
        if self.auth is not None:
            self._client.username_pw_set(*self.auth)
        
        if self.user_data is not None:
            self._client.user_data_set(self.user_data)

        self._client.enable_logger(logger)
            
        self._address: str = f"{self.host}:{self.port}"
        
        self._set_on_log()
        
        
    @property
    def address(self) -> str:
        return self._address


    @property
    def client(self) -> mqtt.Client:
        return self._client
    
    
    def set_on_connect(
        self, 
        connect_callback: Optional[CallbackOnConnect] = None
        ) -> None:
        """set connect callback
        
        Notes:
            connect_callback(client, userdata, flags, reason_code, properties)


        :param Optional[CallbackOnConnect] connect_callback: _description_, defaults to None
        """
        if not isinstance(self._client, mqtt.Client):
            raise RuntimeError("MQTT client is not initialized")
        
        if connect_callback is None:
            def on_connect(client, userdata, flags, reason_code, properties):
                if reason_code.is_failure:
                    logger.error(f'Failed to connect MQTT broker[{self.address}], reason code: {reason_code}.')
                else:
                    logger.info(f'Connected to MQTT Broker[{self.address}], client id: {self.client_id}.')
            self._client.on_connect = on_connect
        else:
            self._client.on_connect = connect_callback  
            
            
    def set_on_connect_fail(
        self, 
        connect_fail_callback: Optional[CallbackOnConnectFail] = None
    ) -> None:
        """set connect fail callback
        
        Notes:
            connect_fail_callback(client, userdata)

        :param Optional[CallbackOnConnectFail] connect_fail_callback: _description_, defaults to None
        """
        if not isinstance(self._client, mqtt.Client):
            raise RuntimeError("MQTT client is not initialized")
        
        if connect_fail_callback is None:
            def on_connect_fail(client, userdata):
                logger.error(f"Failed to connect to MQTT broker[{self.address}]")
            self._client.on_connect_fail = connect_fail_callback
        else:
            self._client.on_connect_fail = connect_fail_callback
            
            
    def set_on_disconnect(
        self, 
        disconnect_callback: Optional[CallbackOnDisconnect] = None
    ) -> None:
        """set disconnect callback
        
        Notes:
            disconnect_callback(client, userdata, reason_code, properties)

        :param Optional[CallbackOnDisconnect] disconnect_callback: _description_, defaults to None
        """
        if not isinstance(self._client, mqtt.Client):
            raise RuntimeError("MQTT client is not initialized")
        
        if disconnect_callback is None:
            def on_disconnect(client, userdata, reason_code, properties):
                logger.info(f'Disconnected from MQTT Broker[{self.address}], client id: {self.client_id}.')
            self._client.on_disconnect = on_disconnect
        else:
            self._client.on_disconnect = disconnect_callback
            

    def set_on_publish(
        self, 
        publish_callback: Optional[CallbackOnPublish] = None,
    ) -> None:
        """set publish callback

        Notes:
            publish_callback(client, userdata, mid, reason_code, properties)
            
        :param Optional[CallbackOnPublish] callback: _description_, defaults to None
        """
        if not isinstance(self._client, mqtt.Client):
            raise RuntimeError("MQTT client is not initialized")
        
        if publish_callback is None:
            def on_publish(client, userdata, mid, reason_code, properties):
                logger.debug(f'mid: {mid}, reason_code: {reason_code}, properties: {properties}')
                
            self._client.on_publish = on_publish
        else:
            self._client.on_publish = publish_callback
            
    
    def set_on_message(
        self,
        message_callback: Optional[CallbackOnMessage] = None,
    ) -> None:
        """set message callback

        Notes:
            message_callback(client, userdata, message)
            
        :param Optional[CallbackOnMessage] message_callback: _description_, defaults to None
        """
        if not isinstance(self._client, mqtt.Client):
            raise RuntimeError("MQTT client is not initialized")
        
        if message_callback is None:
            def on_message(client, userdata, message):
                logger.debug(f"topic:{message.topic}, payload: {str(message.payload)}")
            self._client.on_message = on_message
        else:
            self._client.on_message = message_callback
            
    
    def set_on_subscribe(
        self, 
        subscribe_callback: Optional[CallbackOnSubscribe] = None,
    ) -> None:
        """set subscribe callback
        
        Notes:
            subscribe_callback(client, userdata, mid, reason_code_list, properties)

        :param Optional[CallbackOnSubscribe] subscribe_callback: _description_, defaults to None
        """
        if not isinstance(self._client, mqtt.Client):
            raise RuntimeError("MQTT client is not initialized")
        
        if subscribe_callback is None:
            def on_subscribe(client, userdata, mid, reason_code_list, properties):
                if reason_code_list[0].is_failure:
                        logger.error(f"Broker rejected you subscription: {reason_code_list[0]}")
                else:
                    logger.info(f"Broker granted the following QoS: {reason_code_list[0].value}")
            self._client.on_subscribe = on_subscribe
        else:
            self._client.on_subscribe = subscribe_callback
    
    
    def _set_on_log(
        self, 
        log_callback: Optional[CallbackOnLog] = None
    ) -> None:
        """set log callback

        Notes:
            log_callback(client, userdata, level, buf)
            
        :param Optional[CallbackOnLog] log_callback: _description_, defaults to None
        :raises RuntimeError: _description_
        """
        if not isinstance(self._client, mqtt.Client):
            raise RuntimeError("MQTT client is not initialized")
        
        if log_callback is None:
            
            def on_log(client, userdata, paho_log_level, messages):
                match paho_log_level:
                    case mqtt.MQTT_LOG_DEBUG:
                        logger.debug(messages)
                    case mqtt.MQTT_LOG_INFO:
                        logger.info(messages)
                    case mqtt.MQTT_LOG_WARNING:
                        logger.warning(messages)
                    case mqtt.MQTT_LOG_ERR:
                        logger.error(messages)
                    case _:
                        logger.info(messages)
            self._client.on_log = on_log
        else:
            self._client.on_log = log_callback
        
    
    def connect(self, is_async: bool =False, *args, **kwargs) -> Optional[MQTTErrorCode]:
        if not isinstance(self._client, mqtt.Client):
            raise RuntimeError("MQTT client is not initialized")
        try:
            if is_async:
                return self._client.connect_async(self.host, self.port, *args, **kwargs)
            else:
                return self._client.connect(self.host, self.port, *args, **kwargs)
        except ConnectionRefusedError as e:
            logger.error(f"Failed to connect to MQTT broker {self.address}")
            raise e
        
        
    def disconnect(self) -> MQTTErrorCode:
        if not isinstance(self._client, mqtt.Client):
            raise RuntimeError("MQTT client is not initialized")
        
        return self._client.disconnect()
    
    
    def publish(
        self, 
        topic: str, 
        payload: Optional[str] = None, 
        *args, **kwargs
    ) -> mqtt.MQTTMessageInfo:
        """Publish a message to a topic

        :param str topic: _description_
        :param Optional[str] payload: _description_, defaults to None
        :param bool retain: _description_, defaults to False
        :return mqtt.MQTTMessageInfo: _description_
        """
        if not isinstance(self._client, mqtt.Client):
            raise RuntimeError("MQTT client is not initialized")
        
        if not self._client.is_connected():
            raise RuntimeError("MQTT client is not connected")
        
        return self._client.publish(topic=topic, payload=payload, qos=self.qos, *args, **kwargs)


    def subscribe(
            self,
            topic: Union[str, tuple, list], 
            *args, **kwargs
    ) -> None:
        """Subscribe to one or more topics

        Notess:
            Typically called in on_connect handler
        
        :param str topic: _description_
        :param Optional[Callable[[mqtt.Client, Any, mqtt.MQTTMessage], None]] callback: _description_, defaults to None
        """
        if not isinstance(self._client, mqtt.Client):
            raise RuntimeError("MQTT client is not initialized")
        
        if not self._client.is_connected():
            raise RuntimeError("MQTT client is not connected")
        
        
        
        self._client.subscribe(topic=topic, qos=self.qos, *args, **kwargs)
    
    
    def __enter__(self) -> None:
        if self._client is not None:
            self._client.loop_start()
        else:
            raise RuntimeError("MQTT client is not initialized before entering context.")
        
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client is not None:
            try:
                self._client.loop_stop()
            except Exception as e:
                logger.error(f"Error occurred while stopping MQTT client loop: {e}")
        else:
            logger.error("MQTT client is already closed or uninitialized when exiting context.")

        if exc_type is not None:
            logger.error(f"Exception in context: {exc_val}")
            
            
    def run(self, timeout: float = 1.0, retry_first_connection: bool = True) -> MQTTErrorCode:
        """Blocked running
        
        :param float timeout: _description_, defaults to 1.0
        :param bool retry_first_connection: _description_, defaults to False
        """
        return self._client.loop_forever(timeout, retry_first_connection)
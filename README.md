# Veronica

## 介绍

Veronica是一个用于提升Python开发北向接口效率的工具库。它提供了丰富的封装组件和实用工具，帮助开发者快速构建稳定、高效的网络应用和服务。

该库包含了对常见协议（如MQTT、Kafka）的封装、TCP连接管理、配置管理、日志处理、装饰器工具等，能够显著提高开发效率，减少重复代码。

## 软件架构

Veronica采用模块化设计，主要包含以下几个核心模块：

```
veronica/
├── base/           # 基础模型类
├── core/           # 核心功能模块（日志、配置、应用锁等）
├── encap/          # 第三方库封装（MQTT、Kafka等）
├── transport/      # 网络传输相关组件
└── utils/          # 工具类和装饰器
```

## 功能特性

### 1. 消息队列封装
- **MQTT客户端**: 基于paho-mqtt封装，提供更简洁的API和默认回调处理
- **Kafka生产者**: 基于confluent-kafka封装，支持异步生产和自动轮询

### 2. 网络传输组件
- **TCP客户端协议**: 基于asyncio.Protocol的可扩展TCP协议基类
- **TCP连接器**: 支持自动重连、连接抖动控制的TCP连接管理器

### 3. 核心工具
- **应用锁**: 基于文件锁的应用单实例运行保证
- **配置管理**: 基于pydantic-settings的YAML/JSON配置加载
- **日志系统**: 集成loguru和标准logging的日志处理工具

### 4. 实用工具
- **装饰器集合**: 包含性能计时、线程同步、单例模式、享元模式等装饰器
- **加载器**: 支持JSON、YAML、TOML等格式配置文件的加载链

## 安装教程

### 环境要求
- Python >= 3.11

### 安装方式

```bash
# 克隆项目
git clone <repository-url>
cd veronica

# 安装依赖
pip install -e .
```

或者使用pip安装：

```bash
pip install .
```

## 使用说明

### 1. MQTT客户端使用示例

```python
from veronica.encap.mqtt import MqttClientV2

# 创建MQTT客户端
client = MqttClientV2(
    host="localhost",
    port=1883,
    client_id="my_client"
)

# 连接并使用
with client:
    client.publish("test/topic", "Hello World")
```

### 2. Kafka生产者使用示例

```python
from veronica.encap.kafka import BaseProducer

# 创建Kafka生产者
producer = BaseProducer(bootstrap_servers="localhost:9092")

# 发送消息
producer.produce("my-topic", b"Hello World")

# 关闭生产者
producer.close()
```

### 3. TCP客户端使用示例

```python
import asyncio
from veronica.transport.connector import TCPConnector
from veronica.transport.protocol import TCPClientProtocol

class MyProtocol(TCPClientProtocol):
    def on_data_received(self, data: bytes) -> None:
        print(f"Received: {data}")

async def main():
    # 创建TCP连接
    connector = await TCPConnector.create(
        "127.0.0.1", 
        8888, 
        protocol_class=MyProtocol
    )

if __name__ == "__main__":
    asyncio.run(main())
```

### 4. 配置管理使用示例

```python
from veronica.core.settings import YamlSettings

class Settings(YamlSettings):
    model_config = SettingsConfigDict(
        yaml_file="config.yaml",
        yaml_file_encoding="utf-8",
        env_prefix="VERONICA_"
    )
    
    debug: bool = False
    host: str = "localhost"

# 加载配置
settings = Settings()
```

### 5. 装饰器使用示例

```python
from veronica.utils.decorator import singleton, time_this

@singleton
class MyService:
    pass

@time_this
def slow_function():
    import time
    time.sleep(1)
    return "done"
```

## 项目依赖

- confluent-kafka>=2.11.0: Kafka客户端
- filelock>=3.18.0: 文件锁工具
- loguru>=0.7.3: 日志记录工具
- paho-mqtt>=2.1.0: MQTT客户端
- prometheus-client>=0.22.1: Prometheus监控客户端
- pydantic-settings>=2.10.1: 配置管理
- pytest>=8.4.1: 测试框架
- pytest-asyncio>=1.0.0: 异步测试支持

## 参与贡献

我们欢迎任何形式的贡献！

1. Fork 本仓库
2. 创建您的特性分支 (git checkout -b feature/AmazingFeature)
3. 提交您的更改 (git commit -m 'Add some amazing feature')
4. 推送到分支 (git push origin feature/AmazingFeature)
5. 开启一个 Pull Request

### 开发环境搭建

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest
```

## 许可证

本项目采用 [MIT](LICENSE) 许可证。

## 联系方式

He Yinyu - heyinyu.sensi@foxmail.com

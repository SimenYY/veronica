from pathlib import Path

from pydantic_settings import SettingsConfigDict
from pydantic_settings import (
    BaseSettings,
    YamlConfigSettingsSource,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
)

__all__ = [
    "YamlSettings",
    "JsonSettings",
]


class YamlSettings(BaseSettings):
    """添加Yaml, Json配置源

    Example:
    ... class Settings(YamlSettings):
    ...     model_config = SettingsConfigDict(
    ...         yaml_file="config.yaml",
    ...         yaml_file_encoding="utf-8",
    ...         env_prefix="veronica_"
    ...     )
    """
    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        sources = super().settings_customise_sources(
            settings_cls,
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )
        yaml_settings = YamlConfigSettingsSource(
            cls,
            yaml_file=cls.model_config.get("yaml_file", Path("")),
            yaml_file_encoding=cls.model_config.get("yaml_file_encoding", None)
        )
        return (yaml_settings, ) + sources

    model_config = SettingsConfigDict(
        yaml_file="config.yaml",
        yaml_file_encoding="utf-8",
        env_prefix="v_"
    )

class JsonSettings(BaseSettings):
    """添加Yaml, Json配置源

    Example:
    ... class Settings(JsonSettings):
    ...     model_config = SettingsConfigDict(
    ...         json_file="config.json",
    ...         json_file_encodeing="utf-8",
    ...         env_prefix="veronica_"
    ...     )
    """
    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        sources = super().settings_customise_sources(
            settings_cls,
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )
        json_settings = JsonConfigSettingsSource(
            cls,
            json_file=cls.model_config.get("json_file", Path("")),
            json_file_encoding=cls.model_config.get("json_file_encoding", None)
        )
        return (json_settings, ) + sources
    
    model_config = SettingsConfigDict(
        json_file="config.json",
        json_file_encoding="utf-8",
        env_prefix="v_"
    )
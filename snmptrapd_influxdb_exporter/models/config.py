from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel


class LogLevel(Enum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class AuthProtocol(Enum):
    USM_AUTH_HMAC96_MD5 = "md5"
    USM_AUTH_HMAC96_SHA = "sha"
    USM_AUTH_HMAC128_SHA224 = "sha128"
    USM_AUTH_HMAC192_SHA256 = "sha192"
    USM_AUTH_HMAC256_SHA384 = "sha256"
    USM_AUTH_HMAC384_SHA512 = "sha512"
    USM_AUTH_NONE = "none"


class PrivProtocol(Enum):
    USM_PRIV_CFB128_AES = "aes128"
    USM_PRIV_CFB192_AES = "aes192"
    USM_PRIV_CFB256_AES = "aes256"
    USM_PRIV_CBC56_DES = "des"
    USM_PRIV_CBC168_3DES = "3des"
    USM_PRIV_CFB192_AES_BLUMENTHAL = "aes192Blumenthal"
    USM_PRIV_CFB256_AES_BLUMENTHAL = "aes256Blumenthal"
    USM_PRIV_NONE = "none"


class Server(BaseModel):
    name: str
    url: str
    org: str
    token: str
    bucket: str


class Influxdb(BaseModel):
    server: List[Server]


class Tags(BaseModel):
    host_dns: str
    host_ip: str
    oid: str


class DefaultMapping(BaseModel):
    measurement: str
    tags: Tags
    permit: Optional[List[str]] = None
    deny: Optional[List[str]] = None


class CustomMapping(BaseModel):
    measurement: str
    tags: List[str]
    fields: List[str]


class User(BaseModel):
    user: str
    auth_protocol: AuthProtocol
    auth_key: Optional[str] = None
    priv_protocol: PrivProtocol
    priv_key: Optional[str] = None
    engine_id: Optional[str] = None


class SnmpV3(BaseModel):
    engine_id: str
    users: List[User]


class SnmpV2(BaseModel):
    community: str
    description: str


class Config(BaseModel):
    logging: LogLevel
    influxdb: Influxdb
    default_mapping: DefaultMapping
    custom_mappings: Optional[Dict[str, CustomMapping]]
    mib_list: List[str]
    snmpv2: Optional[List[SnmpV2]]
    snmpv3: Optional[SnmpV3]

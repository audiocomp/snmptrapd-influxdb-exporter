import asyncio

from modules.datapoints import build_datapoints
from modules.load_config import log, snmp_config
from modules.load_mibs import mibViewController
from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.entity import config, engine
from pysnmp.entity.rfc3413 import ntfrcv
from pysnmp.proto.api import v2c
from pysnmp.smi import rfc1902

authProtocol = {
    "USM_AUTH_HMAC96_MD5": config.USM_AUTH_HMAC96_MD5,
    "USM_AUTH_HMAC96_SHA": config.USM_AUTH_HMAC96_SHA,
    "USM_AUTH_HMAC128_SHA224": config.USM_AUTH_HMAC128_SHA224,
    "USM_AUTH_HMAC192_SHA256": config.USM_AUTH_HMAC192_SHA256,
    "USM_AUTH_HMAC256_SHA384": config.USM_AUTH_HMAC256_SHA384,
    "USM_AUTH_HMAC384_SHA512": config.USM_AUTH_HMAC384_SHA512,
    "USM_PRIV_CFB128_AES": config.USM_PRIV_CFB128_AES,
    "USM_PRIV_CFB256_AES": config.USM_PRIV_CFB256_AES,
    "USM_PRIV_CFB192_AES": config.USM_PRIV_CFB192_AES,
    "USM_PRIV_CBC56_DES": config.USM_PRIV_CBC56_DES,
    "USM_PRIV_CBC168_3DES": config.USM_PRIV_CBC168_3DES,
    "USM_PRIV_CFB192_AES_BLUMENTHAL": config.USM_PRIV_CFB192_AES_BLUMENTHAL,
    "USM_PRIV_CFB256_AES_BLUMENTHAL": config.USM_PRIV_CFB256_AES_BLUMENTHAL,
    "USM_AUTH_NONE": config.USM_AUTH_NONE,
    "USM_PRIV_NONE": config.USM_PRIV_NONE,
}


def snmp_engine():
    # Create SNMP engine with autogenernated engineID and pre-bound
    # to socket transport dispatcher
    snmpEngine = engine.SnmpEngine(
        snmpEngineID=v2c.OctetString(hexValue=snmp_config.snmpv3.engine_id)
    )

    # Transport setup
    # UDP over IPv4, first listening interface/port
    config.add_transport(
        snmpEngine,
        udp.DOMAIN_NAME + (1,),
        udp.UdpTransport().open_server_mode(("0.0.0.0", 162)),
    )

    # SNMPv1/2c setup
    # SecurityName <-> CommunityName mapping
    if snmp_config.snmpv2 is not None:
        for entry in snmp_config.snmpv2:
            config.add_v1_system(
                snmpEngine, entry.description, entry.community)

    # SNMP v3 setup
    if snmp_config.snmpv3.users is not None:
        for user in snmp_config.snmpv3.users:
            if user.engine_id is not None:
                user.engine_id = v2c.OctetString(hexValue=user.engine_id)
            config.add_v3_user(
                snmpEngine,
                userName=user.user,
                authKey=user.auth_key,
                privKey=user.priv_key,
                authProtocol=authProtocol.get(
                    user.auth_protocol.name, config.USM_AUTH_NONE
                ),
                privProtocol=authProtocol.get(
                    user.priv_protocol.name, config.USM_PRIV_NONE
                ),
                securityEngineId=user.engine_id,
            )

    # Callback function for receiving notifications
    def cbFun(
        snmpEngine,
        stateReference,
        contextEngineId,
        contextName,
        varBinds,
        cbCtx,
    ):
        _, tAddress = snmpEngine.message_dispatcher.get_transport_info(
            stateReference)
        message = {}
        message["host_dns"] = tAddress[0].strip()
        message["host_ip"] = tAddress[0].strip()
        message["oid"] = None
        message["sysuptime"] = None
        message["varbinds"] = []
        message["varbinds_dict"] = {}
        for oid, val in varBinds:
            varBind = str(
                rfc1902.ObjectType(
                    rfc1902.ObjectIdentity(oid), val
                ).resolve_with_mib(mibViewController)
            )
            if "sysUpTime" in varBind:
                message["uptime"] = varBind.split(" = ")[1].strip()
            elif "snmpTrapOID" in varBind:
                if message["oid"] is None:
                    message["oid"] = varBind.split(" = ")[1].strip()
            else:
                message["varbinds"].append(varBind)
                if len(varBind.split(" = ")) > 1:
                    message["varbinds_dict"][
                        varBind.split(" = ")[0].strip()
                    ] = varBind.split(" = ")[1].strip()
        log.info(
            f"Trap From: {tAddress}, EngineId {contextEngineId.prettyPrint()}"
        )
        log.debug(f"Context Name: {contextName}, cbCtx: {cbCtx}")
        log.debug(f"Trap Detail: {message}")
        asyncio.create_task(build_datapoints(message))

    # Register SNMP Application at the SNMP engine
    ntfrcv.NotificationReceiver(snmpEngine, cbFun)
    snmpEngine.transport_dispatcher.job_started(1)
    try:
        log.error("Trap Receiver started on port 162. Press Ctrl-c to quit.")
        snmpEngine.transport_dispatcher.run_dispatcher()
        ntfrcv.NotificationReceiver(snmpEngine, cbFun)
    except KeyboardInterrupt:
        log.error("Ctrl-c Pressed. Trap Receiver Stopped")
    finally:
        snmpEngine.transport_dispatcher.close_dispatcher()


def main():
    snmp_engine()


if __name__ == "__main__":
    main()

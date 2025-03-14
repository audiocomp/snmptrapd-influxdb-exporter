import os
from typing import List

from modules.load_config import log, snmp_config
from pysnmp.smi import builder, compiler, view
from pysnmp.smi.error import MibNotFoundError

mib_path: str = os.path.join(
    os.path.dirname(os.path.realpath("__file__")), "mibs"
)
mib_list: List[str] = snmp_config.mib_list

mibBuilder = builder.MibBuilder()
compiler.addMibCompiler(
    mibBuilder, sources=[
        f"file://{mib_path}",
        "/usr/share/snmp/mibs"
        ])
if mib_list != []:
    try:
        mibBuilder.loadModules(*mib_list)
    except MibNotFoundError as e:
        log.error(e)
mibViewController = view.MibViewController(mibBuilder)

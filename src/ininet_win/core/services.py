"""Well-known TCP/UDP services and best-effort service identification."""

from __future__ import annotations

import socket

# Common well-known ports. Values are short, widely used service names.
KNOWN_SERVICES: dict[int, str] = {
    20: "ftp-data",
    21: "ftp",
    22: "ssh",
    23: "telnet",
    25: "smtp",
    53: "dns",
    67: "dhcp",
    69: "tftp",
    80: "http",
    88: "kerberos",
    110: "pop3",
    111: "rpcbind",
    123: "ntp",
    135: "msrpc",
    137: "netbios-ns",
    138: "netbios-dgm",
    139: "netbios-ssn",
    143: "imap",
    161: "snmp",
    162: "snmptrap",
    179: "bgp",
    389: "ldap",
    443: "https",
    445: "microsoft-ds",
    465: "smtps",
    500: "isakmp",
    514: "syslog",
    515: "lpd",
    548: "afp",
    587: "smtp",
    631: "ipp",
    636: "ldaps",
    873: "rsync",
    902: "vmware",
    989: "ftps-data",
    990: "ftps",
    993: "imaps",
    995: "pop3s",
    1080: "socks",
    1194: "openvpn",
    1433: "mssql",
    1521: "oracle",
    1723: "pptp",
    1883: "mqtt",
    2049: "nfs",
    2082: "cpanel",
    2083: "cpanel-ssl",
    2181: "zookeeper",
    2375: "docker",
    2376: "docker-ssl",
    3000: "http-alt",
    3128: "squid",
    3260: "iscsi",
    3306: "mysql",
    3389: "rdp",
    4443: "https-alt",
    5000: "upnp",
    5060: "sip",
    5061: "sips",
    5432: "postgresql",
    5672: "amqp",
    5900: "vnc",
    5901: "vnc",
    5984: "couchdb",
    6379: "redis",
    6443: "kubernetes",
    8000: "http-alt",
    8080: "http-proxy",
    8081: "http-alt",
    8443: "https-alt",
    8888: "http-alt",
    9000: "cslistener",
    9090: "websm",
    9100: "jetdirect",
    9200: "elasticsearch",
    9300: "elasticsearch",
    11211: "memcached",
    27017: "mongodb",
    27018: "mongodb",
    50000: "sap",
}


def service_name(port: int) -> str:
    """Best-effort service name for a port number.

    Prefers the built-in table, then falls back to the OS services database.
    """
    name = KNOWN_SERVICES.get(port)
    if name:
        return name
    try:
        return socket.getservbyport(port, "tcp")
    except OSError:
        return ""

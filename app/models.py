"""Request models.

Every string that reaches a template is validated here. Nothing may contain a
newline or other control character, because each value is pasted into IOS
configuration line by line: a newline would let one field inject whole commands.
"""

from ipaddress import IPv4Address, IPv4Network
from typing import Annotated, List, Literal, Optional, Union

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints, model_validator

# --------------------------------------------------------------------------- types

Hostname = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,62}$")]
"""IOS hostname: letters, digits, '.', '_', '-'; max 63 chars."""

InterfaceName = Annotated[str, StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9/.:-]{0,63}$")]
"""e.g. GigabitEthernet0/0, Gi1/0/24, Vlan10, Tunnel0, Port-channel1."""

Description = Annotated[str, StringConstraints(pattern=r"^[^\x00-\x1f\x7f]*$", max_length=200)]
"""Free text on one line (no control characters)."""

ObjectName = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{1,64}$")]
"""ACL and VLAN names: no spaces."""

Secret = Annotated[str, StringConstraints(pattern=r"^[\x21-\x7e]+$")]
"""Printable ASCII without spaces."""

Asn = Annotated[int, Field(ge=1, le=4294967295)]
VlanId = Annotated[int, Field(ge=1, le=4094)]
OspfArea = Annotated[int, Field(ge=0, le=4294967295)]
ProcessId = Annotated[int, Field(ge=1, le=65535)]


def _netmask(value: str) -> str:
    try:
        IPv4Network(f"0.0.0.0/{value}")
    except ValueError as exc:
        raise ValueError(f"'{value}' is not a valid subnet mask") from exc
    if value.count(".") != 3:
        raise ValueError(f"'{value}' must be a dotted-decimal subnet mask")
    return value


def _wildcard(value: str) -> str:
    try:
        inverted = str(IPv4Address(int(IPv4Address("255.255.255.255")) ^ int(IPv4Address(value))))
        IPv4Network(f"0.0.0.0/{inverted}")
    except ValueError as exc:
        raise ValueError(f"'{value}' is not a valid wildcard mask") from exc
    return value


Netmask = Annotated[str, AfterValidator(_netmask)]
Wildcard = Annotated[str, AfterValidator(_wildcard)]


def _acl_address(value: str) -> str:
    """'any', 'host A.B.C.D', or 'A.B.C.D W.W.W.W'."""
    parts = value.split()
    if parts == ["any"]:
        return "any"
    if len(parts) == 2 and parts[0] == "host":
        return f"host {IPv4Address(parts[1])}"
    if len(parts) == 2:
        _wildcard(parts[1])
        return f"{IPv4Address(parts[0])} {parts[1]}"
    raise ValueError("use 'any', 'host A.B.C.D' or 'A.B.C.D <wildcard>'")


AclAddress = Annotated[str, AfterValidator(_acl_address)]
Port = Annotated[str, StringConstraints(pattern=r"^([0-9]{1,5}|[a-z][a-z0-9-]{1,20})$")]
"""Port number or IOS keyword (www, ssh, telnet, domain, ...)."""


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# --------------------------------------------------------------------------- interface


class Interface(Strict):
    name: InterfaceName
    ip: IPv4Address
    mask: Netmask
    description: Description = ""


class InterfaceConfig(Strict):
    hostname: Hostname
    interfaces: List[Interface] = Field(
        default=[Interface(name="GigabitEthernet0/0", ip="10.0.0.1", mask="255.255.255.0", description="Uplink")],
        min_length=1,
    )


# --------------------------------------------------------------------------- OSPF


class OspfNetwork(Strict):
    network: IPv4Address
    wildcard: Wildcard
    area: OspfArea = 0


class OSPFConfig(Strict):
    hostname: Hostname
    router_id: IPv4Address = Field(examples=["10.0.0.1"])
    process_id: ProcessId = 1
    networks: List[OspfNetwork] = Field(default=[OspfNetwork(network="10.0.0.0", wildcard="0.0.0.255", area=0)])
    passive_interfaces: List[InterfaceName] = Field(default=[])
    default_route: bool = False


# --------------------------------------------------------------------------- BGP


class BgpNeighbor(Strict):
    ip: IPv4Address
    remote_asn: Asn
    description: Description = ""


class BGPConfig(Strict):
    hostname: Hostname
    local_asn: Asn = Field(examples=[65001])
    router_id: IPv4Address = Field(examples=["10.0.0.1"])
    neighbors: List[BgpNeighbor] = Field(
        default=[BgpNeighbor(ip="10.0.0.2", remote_asn=65002, description="eBGP Peer")]
    )
    networks: List[IPv4Network] = Field(default=[], description="Prefixes to advertise, CIDR notation")


# --------------------------------------------------------------------------- VLAN


class Vlan(Strict):
    id: VlanId
    name: ObjectName
    ip: IPv4Address
    mask: Netmask


class VLANConfig(Strict):
    hostname: Hostname
    vlans: List[Vlan] = Field(
        default=[
            Vlan(id=10, name="SALES", ip="10.10.10.1", mask="255.255.255.0"),
            Vlan(id=20, name="ENGINEERING", ip="10.10.20.1", mask="255.255.255.0"),
        ],
        min_length=1,
    )
    trunk_ports: List[InterfaceName] = Field(default=["GigabitEthernet0/1"])
    native_vlan: VlanId = 1


# --------------------------------------------------------------------------- DMVPN


class DMVPNConfig(Strict):
    hostname: Hostname
    role: Literal["hub", "spoke"] = "hub"
    tunnel_ip: IPv4Address = Field(examples=["172.16.0.1"])
    tunnel_mask: Netmask = "255.255.255.0"
    tunnel_source: InterfaceName = Field(examples=["GigabitEthernet0/0"])
    nhrp_network_id: Annotated[int, Field(ge=1, le=4294967295)] = 100
    nhrp_key: Annotated[Secret, StringConstraints(max_length=8)] = Field(
        description="NHRP authentication string (IOS allows at most 8 characters)"
    )
    ipsec_psk: Annotated[Secret, StringConstraints(min_length=16, max_length=128)] = Field(
        description="IKEv1 pre-shared key shared by all DMVPN peers (16+ characters)"
    )
    hub_public_ip: Optional[IPv4Address] = Field(default=None, examples=["203.0.113.1"])
    hub_tunnel_ip: Optional[IPv4Address] = Field(default=None, examples=["172.16.0.1"])
    ospf_process: ProcessId = 1

    @model_validator(mode="after")
    def _spoke_needs_hub(self):
        if self.role == "spoke" and (self.hub_public_ip is None or self.hub_tunnel_ip is None):
            raise ValueError("spoke role requires hub_public_ip and hub_tunnel_ip")
        return self

    @property
    def tunnel_network(self) -> IPv4Network:
        return IPv4Network(f"{self.tunnel_ip}/{self.tunnel_mask}", strict=False)


# --------------------------------------------------------------------------- ACL


class AclEntry(Strict):
    action: Literal["permit", "deny"]
    protocol: Literal["ip", "tcp", "udp", "icmp", "gre", "esp", "ahp", "ospf", "eigrp"] = "ip"
    src: AclAddress = "any"
    dst: AclAddress = "any"
    dst_port: Optional[Port] = None
    remark: Description = ""

    @model_validator(mode="after")
    def _port_needs_tcp_udp(self):
        if self.dst_port and self.protocol not in ("tcp", "udp"):
            raise ValueError("dst_port is only valid with protocol tcp or udp")
        return self


class AclRemark(Strict):
    action: Literal["remark"]
    remark: Description
    protocol: Literal[""] = ""
    src: Literal[""] = ""
    dst: Literal[""] = ""
    dst_port: Literal[""] = ""


class ACLConfig(Strict):
    hostname: Hostname
    acl_name: ObjectName = Field(examples=["BLOCK_TELNET"])
    acl_type: Literal["standard", "extended"] = "extended"
    rules: List[Union[AclRemark, AclEntry]] = Field(
        default=[
            AclEntry(action="deny", protocol="tcp", dst_port="23", remark="Block Telnet"),
            AclEntry(action="permit", protocol="ip", remark="Allow all other traffic"),
        ],
        min_length=1,
    )
    apply_to: Optional[Annotated[str, StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9/.:-]{0,63} (in|out)$")]] = Field(
        default=None, examples=["GigabitEthernet0/0 in"]
    )

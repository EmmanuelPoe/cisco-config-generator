from pydantic import BaseModel, Field
from typing import List, Optional


class InterfaceConfig(BaseModel):
    hostname: str
    interfaces: List[dict] = Field(
        default=[{"name": "GigabitEthernet0/0", "ip": "10.0.0.1", "mask": "255.255.255.0", "description": "Uplink"}]
    )


class OSPFConfig(BaseModel):
    hostname: str
    router_id: str = Field(example="10.0.0.1")
    process_id: int = Field(default=1, ge=1, le=65535)
    networks: List[dict] = Field(
        default=[{"network": "10.0.0.0", "wildcard": "0.0.0.255", "area": 0}]
    )
    passive_interfaces: List[str] = Field(default=[])
    default_route: bool = False


class BGPConfig(BaseModel):
    hostname: str
    local_asn: int = Field(example=65001)
    router_id: str = Field(example="10.0.0.1")
    neighbors: List[dict] = Field(
        default=[{"ip": "10.0.0.2", "remote_asn": 65002, "description": "eBGP Peer"}]
    )
    networks: List[str] = Field(default=[])


class VLANConfig(BaseModel):
    hostname: str
    vlans: List[dict] = Field(
        default=[
            {"id": 10, "name": "SALES", "ip": "10.10.10.1", "mask": "255.255.255.0"},
            {"id": 20, "name": "ENGINEERING", "ip": "10.10.20.1", "mask": "255.255.255.0"},
        ]
    )
    trunk_ports: List[str] = Field(default=["GigabitEthernet0/1"])
    native_vlan: int = 1


class DMVPNConfig(BaseModel):
    hostname: str
    role: str = Field(default="hub", pattern="^(hub|spoke)$")
    tunnel_ip: str = Field(example="172.16.0.1")
    tunnel_mask: str = Field(default="255.255.255.0")
    tunnel_source: str = Field(example="GigabitEthernet0/0")
    nhrp_network_id: int = Field(default=100)
    nhrp_key: str = Field(default="cisco123")
    hub_public_ip: Optional[str] = Field(default=None, example="203.0.113.1")
    hub_tunnel_ip: Optional[str] = Field(default=None, example="172.16.0.1")
    ospf_process: int = Field(default=1)


class ACLConfig(BaseModel):
    hostname: str
    acl_name: str = Field(example="BLOCK_TELNET")
    acl_type: str = Field(default="extended", pattern="^(standard|extended)$")
    rules: List[dict] = Field(
        default=[
            {"action": "deny", "protocol": "tcp", "src": "any", "dst": "any", "dst_port": "23", "remark": "Block Telnet"},
            {"action": "permit", "protocol": "ip", "src": "any", "dst": "any", "remark": "Allow all other traffic"},
        ]
    )
    apply_to: Optional[str] = Field(default=None, example="GigabitEthernet0/0 in")

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PSK = "a-long-shared-secret-1"


def post(kind, payload):
    return client.post(f"/generate/{kind}", json=payload)


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200 and "Cisco Config Generator" in r.text


@pytest.mark.parametrize(
    "kind, payload",
    [
        ("interface", {"hostname": "R1"}),
        ("ospf", {"hostname": "R1", "router_id": "10.0.0.1"}),
        ("bgp", {"hostname": "R1", "local_asn": 65001, "router_id": "10.0.0.1"}),
        ("vlan", {"hostname": "SW1"}),
        (
            "dmvpn",
            {
                "hostname": "HUB",
                "tunnel_ip": "172.16.0.1",
                "tunnel_source": "Gi0/0",
                "nhrp_key": "k3y",
                "ipsec_psk": PSK,
            },
        ),
        ("acl", {"hostname": "R1", "acl_name": "EDGE_IN"}),
    ],
)
def test_every_generator_renders_with_defaults(kind, payload):
    r = post(kind, payload)
    assert r.status_code == 200, r.text
    assert r.text.startswith("! ====")
    assert "hostname " in r.text


# ----------------------------------------------------------------- injection & validation


@pytest.mark.parametrize(
    "kind, payload",
    [
        ("ospf", {"hostname": "R1\nusername evil privilege 15 secret x", "router_id": "1.1.1.1"}),
        (
            "interface",
            {
                "hostname": "R1",
                "interfaces": [
                    {"name": "Gi0/0", "ip": "10.0.0.1", "mask": "255.255.255.0", "description": "x\nenable secret 0 y"}
                ],
            },
        ),
        (
            "bgp",
            {
                "hostname": "R1",
                "local_asn": 1,
                "router_id": "1.1.1.1",
                "neighbors": [{"ip": "10.0.0.2", "remote_asn": 2, "description": "a\r\nb"}],
            },
        ),
        ("vlan", {"hostname": "SW1", "vlans": [{"id": 10, "name": "A\nB", "ip": "10.0.0.1", "mask": "255.255.255.0"}]}),
        ("acl", {"hostname": "R1", "acl_name": "X", "rules": [{"action": "remark", "remark": "hi\nusername x"}]}),
        ("acl", {"hostname": "R1", "acl_name": "X", "apply_to": "Gi0/0 in\nline vty 0 4"}),
        ("ospf", {"hostname": "R1", "router_id": "1.1.1.1", "passive_interfaces": ["Gi0/1\nshutdown"]}),
    ],
)
def test_newlines_are_rejected_everywhere(kind, payload):
    assert post(kind, payload).status_code == 422


@pytest.mark.parametrize(
    "kind, payload",
    [
        ("ospf", {"hostname": "R1", "router_id": "not-an-ip"}),
        (
            "ospf",
            {
                "hostname": "R1",
                "router_id": "1.1.1.1",
                "networks": [{"network": "10.0.0.0", "wildcard": "0.255.0.255", "area": 0}],
            },
        ),
        ("interface", {"hostname": "R1", "interfaces": [{"name": "Gi0/0", "ip": "10.0.0.1", "mask": "255.0.255.0"}]}),
        ("bgp", {"hostname": "R1", "local_asn": 0, "router_id": "1.1.1.1"}),
        ("bgp", {"hostname": "R1", "local_asn": 1, "router_id": "1.1.1.1", "networks": ["192.168.0.1/24"]}),
        ("vlan", {"hostname": "SW1", "vlans": [{"id": 4095, "name": "X", "ip": "10.0.0.1", "mask": "255.255.255.0"}]}),
        (
            "dmvpn",
            {
                "hostname": "H",
                "tunnel_ip": "172.16.0.1",
                "tunnel_source": "Gi0/0",
                "nhrp_key": "k",
                "ipsec_psk": "short",
            },
        ),
        (
            "dmvpn",
            {
                "hostname": "H",
                "tunnel_ip": "172.16.0.1",
                "tunnel_source": "Gi0/0",
                "nhrp_key": "toolongkey",
                "ipsec_psk": PSK,
            },
        ),
        (
            "dmvpn",
            {
                "hostname": "S",
                "role": "spoke",
                "tunnel_ip": "172.16.0.2",
                "tunnel_source": "Gi0/0",
                "nhrp_key": "k",
                "ipsec_psk": PSK,
            },
        ),
        ("acl", {"hostname": "R1", "acl_name": "X", "rules": [{"action": "allow", "protocol": "ip"}]}),
        (
            "acl",
            {"hostname": "R1", "acl_name": "X", "rules": [{"action": "permit", "protocol": "ip", "dst_port": "22"}]},
        ),
        ("acl", {"hostname": "R1", "acl_name": "X", "rules": [{"action": "permit", "src": "10.0.0.0/24"}]}),
        ("acl", {"hostname": "R1", "acl_name": "X", "apply_to": "Gi0/0 sideways"}),
        ("acl", {"hostname": "R1", "acl_name": "has space"}),
        ("ospf", {"hostname": "R1", "router_id": "1.1.1.1", "unexpected": "field"}),
    ],
)
def test_invalid_values_are_rejected(kind, payload):
    assert post(kind, payload).status_code == 422


def test_dmvpn_has_no_default_key():
    r = post("dmvpn", {"hostname": "H", "tunnel_ip": "172.16.0.1", "tunnel_source": "Gi0/0"})
    assert r.status_code == 422


# ----------------------------------------------------------------- rendered output


def test_ospf_output():
    r = post(
        "ospf",
        {
            "hostname": "R1",
            "router_id": "10.0.0.1",
            "process_id": 10,
            "networks": [{"network": "10.0.0.0", "wildcard": "0.0.0.255", "area": 0}],
            "passive_interfaces": ["GigabitEthernet0/1"],
            "default_route": True,
        },
    )
    assert "router ospf 10\n router-id 10.0.0.1\n network 10.0.0.0 0.0.0.255 area 0\n" in r.text
    assert " passive-interface GigabitEthernet0/1\n default-information originate always" in r.text


def test_bgp_networks_use_real_masks():
    r = post(
        "bgp",
        {"hostname": "R1", "local_asn": 65001, "router_id": "1.1.1.1", "networks": ["192.168.0.0/24", "10.0.0.0/8"]},
    )
    assert "  network 192.168.0.0 mask 255.255.255.0" in r.text
    assert "  network 10.0.0.0 mask 255.0.0.0" in r.text
    assert "/24" not in r.text


def test_dmvpn_hub_and_spoke():
    hub = post(
        "dmvpn",
        {
            "hostname": "HUB",
            "tunnel_ip": "172.16.0.1",
            "tunnel_mask": "255.255.255.0",
            "tunnel_source": "Gi0/0",
            "nhrp_key": "k3y",
            "ipsec_psk": PSK,
        },
    ).text
    assert "crypto ipsec profile DMVPN-PROFILE" in hub
    assert "\ncrypto profile" not in hub
    assert f"crypto isakmp key {PSK} address 0.0.0.0 0.0.0.0" in hub
    assert " ip nhrp authentication k3y" in hub and " ip nhrp map multicast dynamic" in hub
    assert " ip ospf priority 255" in hub
    assert " network 172.16.0.0 0.0.0.255 area 0" in hub

    spoke = post(
        "dmvpn",
        {
            "hostname": "SPOKE1",
            "role": "spoke",
            "tunnel_ip": "172.16.0.2",
            "tunnel_mask": "255.255.252.0",
            "tunnel_source": "Gi0/0",
            "nhrp_key": "k3y",
            "ipsec_psk": PSK,
            "hub_public_ip": "203.0.113.1",
            "hub_tunnel_ip": "172.16.0.1",
        },
    ).text
    assert " ip nhrp map 172.16.0.1 203.0.113.1" in spoke and " ip nhrp nhs 172.16.0.1" in spoke
    assert " ip ospf priority 0" in spoke
    assert " network 172.16.0.0 0.0.3.255 area 0" in spoke  # wildcard follows the tunnel mask


def test_acl_remarks_and_entries():
    r = post(
        "acl",
        {
            "hostname": "R1",
            "acl_name": "EDGE_IN",
            "apply_to": "GigabitEthernet0/0 in",
            "rules": [
                {"action": "remark", "remark": "Block Telnet"},
                {"action": "deny", "protocol": "tcp", "src": "any", "dst": "host 10.0.0.1", "dst_port": "23"},
                {"action": "permit", "protocol": "ip", "src": "10.1.0.0 0.0.255.255", "dst": "any"},
            ],
        },
    )
    assert r.status_code == 200, r.text
    body = r.text.split("ip access-list extended EDGE_IN\n")[1]
    assert body.startswith(
        " remark Block Telnet\n deny tcp any host 10.0.0.1 eq 23\n permit ip 10.1.0.0 0.0.255.255 any\n!"
    )
    assert "interface GigabitEthernet0/0\n ip access-group EDGE_IN in" in r.text


def test_standard_acl():
    r = post(
        "acl",
        {
            "hostname": "R1",
            "acl_name": "MGMT",
            "acl_type": "standard",
            "rules": [{"action": "permit", "src": "host 192.0.2.10"}],
        },
    )
    assert "ip access-list standard MGMT\n permit host 192.0.2.10\n!" in r.text


def test_vlan_trunk_allowed_list():
    r = post("vlan", {"hostname": "SW1", "native_vlan": 99})
    assert " switchport trunk allowed vlan 10,20\n" in r.text and "native vlan 99" in r.text

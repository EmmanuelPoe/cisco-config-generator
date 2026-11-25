from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.models import ACLConfig, BGPConfig, DMVPNConfig, InterfaceConfig, OSPFConfig, VLANConfig

router = APIRouter(prefix="/generate")
TMPL_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
# autoescape off: output is IOS CLI text, not HTML. Inputs are validated in app/models.py instead.
# StrictUndefined: a typo in a template variable fails loudly instead of rendering blank.
env = Environment(
    loader=FileSystemLoader(str(TMPL_DIR)),
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,
    undefined=StrictUndefined,
)


def render(template_path: str, data: dict) -> str:
    tmpl = env.get_template(template_path)
    return tmpl.render(**data).strip()


@router.post("/interface", response_class=PlainTextResponse)
async def gen_interface(cfg: InterfaceConfig):
    return render("ios/interface.j2", cfg.model_dump())


@router.post("/ospf", response_class=PlainTextResponse)
async def gen_ospf(cfg: OSPFConfig):
    return render("ios/ospf.j2", cfg.model_dump())


@router.post("/bgp", response_class=PlainTextResponse)
async def gen_bgp(cfg: BGPConfig):
    return render("ios/bgp.j2", cfg.model_dump())


@router.post("/vlan", response_class=PlainTextResponse)
async def gen_vlan(cfg: VLANConfig):
    return render("ios/vlan.j2", cfg.model_dump())


@router.post("/dmvpn", response_class=PlainTextResponse)
async def gen_dmvpn(cfg: DMVPNConfig):
    data = cfg.model_dump()
    data["tunnel_network"] = cfg.tunnel_network.network_address
    data["tunnel_wildcard"] = cfg.tunnel_network.hostmask
    return render("ios/dmvpn.j2", data)


@router.post("/acl", response_class=PlainTextResponse)
async def gen_acl(cfg: ACLConfig):
    return render("ios/acl.j2", cfg.model_dump())

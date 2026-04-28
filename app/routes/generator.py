from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from app.models import OSPFConfig, BGPConfig, VLANConfig, DMVPNConfig, ACLConfig, InterfaceConfig

router = APIRouter(prefix="/generate")
TMPL_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
env = Environment(loader=FileSystemLoader(str(TMPL_DIR)), trim_blocks=True, lstrip_blocks=True)


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
    return render("ios/dmvpn.j2", cfg.model_dump())


@router.post("/acl", response_class=PlainTextResponse)
async def gen_acl(cfg: ACLConfig):
    return render("ios/acl.j2", cfg.model_dump())

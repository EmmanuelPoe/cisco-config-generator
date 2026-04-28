'use strict';

function switchTab(name) {
  document.querySelectorAll('.tab-btn').forEach((btn, i) => {
    const names = ['ospf', 'bgp', 'vlan', 'dmvpn', 'acl', 'interface'];
    btn.classList.toggle('active', names[i] === name);
  });
  document.querySelectorAll('.tab-content').forEach(el => {
    el.classList.toggle('active', el.id === 'tab-' + name);
  });
}

function toggleDMVPNRole() {
  const isSpoke = document.getElementById('dmvpn-role').value === 'spoke';
  document.getElementById('dmvpn-spoke-fields').style.display = isSpoke ? '' : 'none';
}

function parseLines(text) {
  return text.trim().split('\n').map(l => l.trim()).filter(Boolean);
}

function buildPayload(type) {
  switch (type) {
    case 'ospf': {
      const networks = parseLines(document.getElementById('ospf-networks').value).map(line => {
        const [network, wildcard, area] = line.split(/\s+/);
        return { network, wildcard, area: parseInt(area) || 0 };
      });
      const passive = parseLines(document.getElementById('ospf-passive').value);
      return {
        hostname: document.getElementById('ospf-hostname').value,
        router_id: document.getElementById('ospf-rid').value,
        process_id: parseInt(document.getElementById('ospf-pid').value),
        networks,
        passive_interfaces: passive,
        default_route: document.getElementById('ospf-default').checked,
      };
    }
    case 'bgp': {
      const neighbors = parseLines(document.getElementById('bgp-neighbors').value).map(line => {
        const parts = line.split(/\s+/);
        return { ip: parts[0], remote_asn: parseInt(parts[1]), description: parts.slice(2).join(' ') };
      });
      const networks = parseLines(document.getElementById('bgp-networks').value);
      return {
        hostname: document.getElementById('bgp-hostname').value,
        local_asn: parseInt(document.getElementById('bgp-asn').value),
        router_id: document.getElementById('bgp-rid').value,
        neighbors,
        networks,
      };
    }
    case 'vlan': {
      const vlans = parseLines(document.getElementById('vlan-vlans').value).map(line => {
        const [id, name, ip, mask] = line.split(/\s+/);
        return { id: parseInt(id), name, ip, mask };
      });
      const trunk_ports = parseLines(document.getElementById('vlan-trunks').value);
      return {
        hostname: document.getElementById('vlan-hostname').value,
        native_vlan: parseInt(document.getElementById('vlan-native').value),
        vlans,
        trunk_ports,
      };
    }
    case 'dmvpn': {
      const role = document.getElementById('dmvpn-role').value;
      const payload = {
        hostname: document.getElementById('dmvpn-hostname').value,
        role,
        tunnel_ip: document.getElementById('dmvpn-tip').value,
        tunnel_mask: document.getElementById('dmvpn-tmask').value,
        tunnel_source: document.getElementById('dmvpn-tsrc').value,
        nhrp_network_id: parseInt(document.getElementById('dmvpn-nid').value),
        nhrp_key: document.getElementById('dmvpn-key').value,
        ospf_process: parseInt(document.getElementById('dmvpn-ospf').value),
      };
      if (role === 'spoke') {
        payload.hub_public_ip = document.getElementById('dmvpn-hub-pub').value;
        payload.hub_tunnel_ip = document.getElementById('dmvpn-hub-tun').value;
      }
      return payload;
    }
    case 'acl': {
      const rules = [];
      parseLines(document.getElementById('acl-rules').value).forEach(line => {
        if (line.startsWith('remark ')) {
          rules.push({ action: 'remark', protocol: '', src: '', dst: '', remark: line.slice(7) });
        } else {
          const parts = line.split(/\s+/);
          const [action, protocol, src, dst, dst_port] = parts;
          rules.push({ action, protocol, src, dst, dst_port: dst_port || '', remark: '' });
        }
      });
      return {
        hostname: document.getElementById('acl-hostname').value,
        acl_name: document.getElementById('acl-name').value,
        acl_type: document.getElementById('acl-type').value,
        apply_to: document.getElementById('acl-apply').value || null,
        rules,
      };
    }
    case 'interface': {
      const interfaces = parseLines(document.getElementById('iface-ifaces').value).map(line => {
        const parts = line.split(/\s+/);
        return { name: parts[0], ip: parts[1], mask: parts[2], description: parts.slice(3).join(' ') };
      });
      return { hostname: document.getElementById('iface-hostname').value, interfaces };
    }
  }
}

async function generate(type) {
  const out = document.getElementById('output');
  out.textContent = '! Generating...';
  try {
    const payload = buildPayload(type);
    const resp = await fetch(`/generate/${type}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) {
      const err = await resp.json();
      out.textContent = '! Error: ' + JSON.stringify(err.detail, null, 2);
      return;
    }
    out.textContent = await resp.text();
  } catch (e) {
    out.textContent = '! Request failed: ' + e.message;
  }
}

function copyOutput() {
  const text = document.getElementById('output').textContent;
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById('copy-btn');
    btn.textContent = 'Copied!';
    setTimeout(() => btn.textContent = 'Copy', 1500);
  });
}

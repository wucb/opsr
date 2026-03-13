const state = {
  assets: [],
  edges: [],
  view: "list",
  filter: "all",
};

const DB_PORTS = { 3306: "mysql", 5432: "postgres", 6379: "redis", 27017: "mongodb" };
const MIDDLEWARE_PORTS = { 9092: "kafka", 5672: "rabbitmq", 80: "nginx", 443: "nginx" };

function hashId(input) {
  let hash = 0;
  for (let i = 0; i < input.length; i += 1) {
    hash = (hash << 5) - hash + input.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash).toString(16).slice(0, 12);
}

function classify(ports) {
  if (ports.some((p) => DB_PORTS[p])) return "database";
  if (ports.some((p) => MIDDLEWARE_PORTS[p])) return "middleware";
  return "server";
}

function expandTargets(raw) {
  const tokens = raw.split(",").map((x) => x.trim()).filter(Boolean);
  const ips = [];
  for (const token of tokens) {
    if (token.includes("/")) {
      const [base, maskRaw] = token.split("/");
      const mask = Number(maskRaw);
      const octets = base.split(".").map(Number);
      if (octets.length !== 4 || Number.isNaN(mask) || mask < 0 || mask > 32) continue;
      const hostBits = 32 - mask;
      const count = Math.min(Math.max(0, (2 ** hostBits) - 2), 256);
      const start = octets[3] & (256 - (2 ** hostBits));
      for (let i = 1; i <= count; i += 1) {
        const host = start + i;
        if (host > 254) break;
        ips.push(`${octets[0]}.${octets[1]}.${octets[2]}.${host}`);
      }
    } else {
      ips.push(token);
    }
  }
  return [...new Set(ips)];
}

function probeHost(ip) {
  const last = Number(ip.split(".").at(-1));
  const ports = [22];
  const procs = ["systemd"];
  if (last % 3 === 0) {
    ports.push(5432);
    procs.push("postgres");
  } else if (last % 3 === 1) {
    ports.push(80);
    procs.push("nginx");
  } else {
    ports.push(6379);
    procs.push("redis");
  }
  const dependencies = last > 1 ? [`${ip.split(".").slice(0, 3).join(".")}.${last - 1}`] : [];
  return { target: ip, open_ports: ports, process_names: procs, dependencies };
}

async function sniffWithWorkers(targets, workers) {
  const queue = [...targets];
  const results = [];

  async function worker() {
    while (queue.length) {
      const ip = queue.shift();
      await new Promise((r) => setTimeout(r, 10));
      results.push(probeHost(ip));
    }
  }

  const pool = Array.from({ length: Math.max(1, Math.min(workers, targets.length || 1)) }, worker);
  await Promise.all(pool);
  return results;
}

function buildAssets(signals) {
  return signals.map((s) => {
    const hostname = `host-${s.target.replaceAll(".", "-")}`;
    const services = [...new Set([
      ...s.open_ports.map((p) => DB_PORTS[p] || MIDDLEWARE_PORTS[p]).filter(Boolean),
      ...s.process_names,
    ])];
    return {
      asset_id: hashId(`${hostname}-${s.target}`),
      hostname,
      ip: s.target,
      category: classify(s.open_ports),
      services,
      tags: {},
    };
  });
}

function buildEdges(assets, signals) {
  const byIp = Object.fromEntries(assets.map((a) => [a.ip, a]));
  const edges = [];
  signals.forEach((s) => {
    const source = byIp[s.target];
    if (!source) return;
    s.dependencies.forEach((dep) => {
      const target = byIp[dep];
      if (!target) return;
      edges.push({ source: source.asset_id, target: target.asset_id, relation: "depends_on" });
    });
  });
  return edges;
}

function filteredAssets() {
  if (state.filter === "all") return state.assets;
  return state.assets.filter((a) => a.category === state.filter);
}

function renderTable() {
  const tbody = document.getElementById("assetTable");
  tbody.innerHTML = "";
  filteredAssets().forEach((asset) => {
    const tr = document.createElement("tr");
    const tags = Object.entries(asset.tags).map(([k, v]) => `<span class="tag">${k}:${v}</span>`).join("") || "-";
    tr.innerHTML = `<td>${asset.asset_id}</td><td>${asset.ip}</td><td>${asset.category}</td><td>${asset.services.join(",")}</td><td>${tags}</td>`;
    tbody.appendChild(tr);
  });
}

function renderTopology() {
  const svg = document.getElementById("topologySvg");
  const assets = filteredAssets();
  const allowed = new Set(assets.map((a) => a.asset_id));
  const edges = state.edges.filter((e) => allowed.has(e.source) && allowed.has(e.target));
  svg.innerHTML = "";
  if (!assets.length) return;

  const cx = 500;
  const cy = 220;
  const radius = 150;
  const positions = {};

  assets.forEach((asset, i) => {
    const angle = (2 * Math.PI * i) / assets.length;
    positions[asset.asset_id] = { x: cx + radius * Math.cos(angle), y: cy + radius * Math.sin(angle) };
  });

  edges.forEach((edge) => {
    const s = positions[edge.source];
    const t = positions[edge.target];
    if (!s || !t) return;
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", s.x);
    line.setAttribute("y1", s.y);
    line.setAttribute("x2", t.x);
    line.setAttribute("y2", t.y);
    line.setAttribute("stroke", "#4f7db8");
    line.setAttribute("stroke-width", "2");
    svg.appendChild(line);
  });

  assets.forEach((asset) => {
    const p = positions[asset.asset_id];
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", p.x);
    circle.setAttribute("cy", p.y);
    circle.setAttribute("r", 20);
    circle.setAttribute("fill", "#17355c");
    circle.setAttribute("stroke", "#5aa2ff");
    circle.setAttribute("stroke-width", "2");

    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", p.x + 26);
    text.setAttribute("y", p.y + 4);
    text.setAttribute("fill", "#d9e8ff");
    text.setAttribute("font-size", "12");
    text.textContent = `${asset.ip} (${asset.category})`;

    svg.appendChild(circle);
    svg.appendChild(text);
  });
}

function render() {
  renderTable();
  renderTopology();
}

function switchView(view) {
  state.view = view;
  document.getElementById("listView").classList.toggle("hidden", view !== "list");
  document.getElementById("topologyView").classList.toggle("hidden", view !== "topology");
  document.getElementById("listViewBtn").classList.toggle("active", view === "list");
  document.getElementById("topologyViewBtn").classList.toggle("active", view === "topology");
}

document.getElementById("scanBtn").addEventListener("click", async () => {
  const targets = expandTargets(document.getElementById("targetsInput").value);
  const workers = Number(document.getElementById("workersInput").value) || 1;
  const msg = document.getElementById("scanMsg");
  if (!targets.length) {
    msg.textContent = "请输入有效 IP 或网段。";
    msg.className = "hint warn";
    return;
  }
  msg.textContent = `正在嗅探 ${targets.length} 个目标（线程数: ${workers}）...`;
  msg.className = "hint";
  const signals = await sniffWithWorkers(targets, workers);
  state.assets = buildAssets(signals);
  state.edges = buildEdges(state.assets, signals);
  msg.textContent = `嗅探完成：发现 ${state.assets.length} 个资产。`;
  msg.className = "hint ok";
  render();
});

document.getElementById("sampleBtn").addEventListener("click", () => {
  document.getElementById("targetsInput").value = "10.0.2.10,10.0.3.0/29";
  document.getElementById("workersInput").value = 12;
});

document.getElementById("tagBtn").addEventListener("click", () => {
  const id = document.getElementById("tagAssetId").value.trim();
  const key = document.getElementById("tagKey").value.trim();
  const value = document.getElementById("tagValue").value.trim();
  const msg = document.getElementById("tagMsg");
  const target = state.assets.find((a) => a.asset_id === id);
  if (!target || !key || !value) {
    msg.textContent = "请输入有效资产ID与标签键值。";
    msg.className = "hint warn";
    return;
  }
  target.tags[key] = value;
  msg.textContent = `标签已更新：${id} ${key}=${value}`;
  msg.className = "hint ok";
  render();
});

document.getElementById("categoryFilter").addEventListener("change", (e) => {
  state.filter = e.target.value;
  render();
});

document.getElementById("listViewBtn").addEventListener("click", () => switchView("list"));
document.getElementById("topologyViewBtn").addEventListener("click", () => switchView("topology"));

document.getElementById("scanBtn").click();

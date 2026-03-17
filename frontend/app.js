(() => {
  const state = {
    assets: [],
    edges: [],
    view: "list",
    filter: "all",
    alerts: [],
    services: [],
    selectedService: null,
    serviceSearch: "",
    serviceStatus: "all",
    serviceGroup: "all",
    demo: {
      hero: [],
      pulse: [],
      timeline: [],
      incidents: [],
      chain: [],
      playbooks: [],
      runbooks: [],
      trends: [],
      aiSignals: [],
      decisions: [],
      scenarioNodes: [],
      scenarioSteps: [],
    },
    compliance: [],
    selectedScenario: null,
  };

  const API_BASE_STORAGE = "opsrApi";
  const DEFAULT_API_BASE = "http://localhost:8000";

  const DB_PORTS = { 3306: "mysql", 5432: "postgres", 6379: "redis", 27017: "mongodb" };
  const MIDDLEWARE_PORTS = { 9092: "kafka", 5672: "rabbitmq", 80: "nginx", 443: "nginx" };

  const el = (id) => document.getElementById(id);

  const apiFetch = async (path, options) => {
    const apiBase = localStorage.getItem(API_BASE_STORAGE) || DEFAULT_API_BASE;
    const response = await fetch(`${apiBase}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || "API error");
    }
    return response.json();
  };

  const hashId = (input) => {
    let hash = 0;
    for (let i = 0; i < input.length; i += 1) {
      hash = (hash << 5) - hash + input.charCodeAt(i);
      hash |= 0;
    }
    return Math.abs(hash).toString(16).slice(0, 12);
  };

  const classify = (ports) => {
    if (ports.some((p) => DB_PORTS[p])) return "database";
    if (ports.some((p) => MIDDLEWARE_PORTS[p])) return "middleware";
    return "server";
  };

  const expandTargets = (raw) => {
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
  };

  const probeHost = (ip) => {
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
  };

  const sniffWithWorkers = async (targets, workers) => {
    const queue = [...targets];
    const results = [];
    const worker = async () => {
      while (queue.length) {
        const ip = queue.shift();
        await new Promise((r) => setTimeout(r, 10));
        results.push(probeHost(ip));
      }
    };
    const pool = Array.from({ length: Math.max(1, Math.min(workers, targets.length || 1)) }, worker);
    await Promise.all(pool);
    return results;
  };

  const buildAssets = (signals) => signals.map((s) => {
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

  const buildEdges = (assets, signals) => {
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
  };

  const filteredAssets = () => (state.filter === "all" ? state.assets : state.assets.filter((a) => a.category === state.filter));

  const seedDemo = () => {
    state.demo.hero = [
      "AI 已识别 3 个高风险告警，建议优先处理 Kafka 延迟。",
      "自动化安装节省 6.4 人时，执行成功率 98%。",
      "巡检发现 2 台主机补丁落后，建议窗口更新。",
    ];
    state.demo.pulse = [
      { label: "集群健康", value: "96%" },
      { label: "CPU 平均", value: "42%" },
      { label: "内存使用", value: "68%" },
      { label: "存储余量", value: "24TB" },
    ];
    state.demo.timeline = [
      "Redis 扩容已完成 · 自动化执行",
      "Kafka 监控规则更新 · 2 分钟前",
      "MySQL 备份任务已排期 · 今日 02:00",
    ];
    state.demo.incidents = [
      "Kafka 延迟波动，建议执行 broker 重平衡",
      "API 网关 5xx 升高，建议回滚最新版本",
      "Redis 热键导致延迟，建议启用缓存预热",
    ];
    state.demo.chain = [
      { step: "资产发现", detail: "扫描 42 台主机 / 12 个网段", status: "ok" },
      { step: "安装编排", detail: "6 个服务自动部署中", status: "running" },
      { step: "监控告警", detail: "噪音已降噪 36%", status: "ok" },
      { step: "事件处置", detail: "2 起事件处于处理", status: "warn" },
      { step: "复盘报告", detail: "日报已生成，等待审批", status: "ok" },
    ];
    state.demo.playbooks = [
      "Kafka 延迟：执行 broker 重平衡 + 调整 ISR",
      "API 网关异常：回滚 + 限流 + 追踪样本",
      "Redis 热键：缓存预热 + 热点拆分",
    ];
    state.demo.runbooks = [
      "数据库主从切换（MySQL 8）",
      "中间件升级（Kafka 3.x）",
      "静态资源回源修复（Nginx）",
    ];
    state.demo.trends = [
      { title: "CPU 使用率", value: "42%", delta: "+3%" },
      { title: "内存压力", value: "68%", delta: "-2%" },
      { title: "告警强度", value: "14", delta: "-18%" },
      { title: "部署成功率", value: "98%", delta: "+1%" },
    ];
    state.demo.aiSignals = [
      { title: "风险聚合", detail: "Kafka 延迟 + 网关 5xx 升高", status: "high" },
      { title: "执行建议", detail: "触发 broker 重平衡 + 限流策略", status: "action" },
      { title: "合规提醒", detail: "2 台主机补丁落后", status: "notice" },
    ];
    state.demo.decisions = [
      { step: "信号聚合", owner: "AI", detail: "合并 14 条异常为 3 条事件" },
      { step: "方案生成", owner: "AI", detail: "生成 2 套修复策略" },
      { step: "审批流转", owner: "SRE", detail: "等待值班负责人审批" },
      { step: "自动执行", owner: "Orchestrator", detail: "执行中 · 3/5 步" },
      { step: "复盘输出", owner: "AI", detail: "报告生成中" },
    ];
    state.demo.scenarioNodes = [
      { id: "S1", title: "识别 Kafka 延迟", detail: "root cause 聚合", owner: "Agent: Sense" },
      { id: "S2", title: "扩容 Broker", detail: "新增 2 节点", owner: "Agent: Install" },
      { id: "S3", title: "调整 ISR", detail: "高风险优化", owner: "Agent: Guard" },
      { id: "S4", title: "限流策略", detail: "网关保护", owner: "Agent: Guard" },
      { id: "S5", title: "回滚预案", detail: "异常时执行", owner: "Agent: Safety" },
    ];
    state.demo.scenarioSteps = [
      { title: "执行流 A", owner: "Agent: Install", detail: "扩容 Broker → 变更配置 → 健康检查", status: "running", progress: 68, nodes: ["S2", "S3"] },
      { title: "执行流 B", owner: "Agent: Guard", detail: "网关限流 → 观测 15 分钟 → 解除", status: "queued", progress: 24, nodes: ["S4"] },
      { title: "执行流 C", owner: "Agent: Safety", detail: "回滚预案准备 → 备份校验", status: "ready", progress: 90, nodes: ["S5"] },
    ];
    state.demo.scenarioHistory = [
      { time: "09:12", detail: "AI 聚合异常信号并触发场景" },
      { time: "09:14", detail: "SRE 通过执行流 A" },
      { time: "09:16", detail: "执行流 A 进入配置阶段" },
      { time: "09:18", detail: "执行流 B 等待窗口" },
    ];
  };

  const seedServices = () => {
    state.services = [
      {
        id: "svc-redis",
        name: "Redis",
        icon: "R",
        status: "running",
        cpu: 22,
        memory: 1.2,
        ip: "10.0.0.12",
        dir: "/data/redis",
        group: "middleware",
        tags: ["cache", "hotkey"],
        topology: ["app", "redis", "disk"],
        progress: ["prepare", "install", "configure", "health_check"],
      },
      {
        id: "svc-mysql",
        name: "MySQL",
        icon: "M",
        status: "running",
        cpu: 48,
        memory: 4.3,
        ip: "10.0.0.15",
        dir: "/data/mysql",
        group: "database",
        tags: ["core", "backup"],
        topology: ["app", "mysql", "backup"],
        progress: ["prepare", "install", "configure", "initialize", "health_check"],
      },
      {
        id: "svc-kafka",
        name: "Kafka",
        icon: "K",
        status: "degraded",
        cpu: 65,
        memory: 7.9,
        ip: "10.0.0.18",
        dir: "/data/kafka",
        group: "middleware",
        tags: ["stream", "high-traffic"],
        topology: ["producer", "kafka", "zookeeper"],
        progress: ["prepare", "install", "configure"],
      },
      {
        id: "svc-api",
        name: "API Gateway",
        icon: "G",
        status: "running",
        cpu: 34,
        memory: 2.6,
        ip: "10.0.1.21",
        dir: "/srv/gateway",
        group: "core",
        tags: ["edge", "traffic"],
        topology: ["client", "gateway", "service"],
        progress: ["prepare", "install", "configure", "health_check"],
      },
      {
        id: "svc-search",
        name: "ElasticSearch",
        icon: "E",
        status: "stopped",
        cpu: 0,
        memory: 0,
        ip: "10.0.2.14",
        dir: "/data/es",
        group: "database",
        tags: ["search", "index"],
        topology: ["app", "elasticsearch", "disk"],
        progress: ["prepare"],
      },
    ];
  };

  const seedAssets = () => {
    const signals = [
      probeHost("10.0.0.12"),
      probeHost("10.0.0.15"),
      probeHost("10.0.0.18"),
      probeHost("10.0.1.21"),
      probeHost("10.0.2.11"),
      probeHost("10.0.2.14"),
      probeHost("10.0.3.19"),
    ];
    state.assets = buildAssets(signals);
    state.edges = buildEdges(state.assets, signals);
  };

  const seedAlerts = () => {
    state.alerts = [
      { severity: "critical", metric_name: "kafka_lag", metric_value: "14.2s", message: "延迟抬升" },
      { severity: "high", metric_name: "api_5xx_rate", metric_value: "3.8%", message: "错误率升高" },
      { severity: "medium", metric_name: "redis_hot_key", metric_value: "2.1s", message: "热键抖动" },
      { severity: "low", metric_name: "disk_usage", metric_value: "78%", message: "容量预警" },
    ];
  };

  const seedCompliance = () => {
    state.compliance = [
      { check_id: "baseline-ssh", status: "pass", message: "SSH 基线一致" },
      { check_id: "baseline-backup", status: "fail", message: "备份策略缺失" },
      { resource_id: "host-10-0-0-18", status: "drift", message: "NTP 漂移" },
    ];
  };

  const renderTable = () => {
    const tbody = el("assetTable");
    tbody.innerHTML = "";
    filteredAssets().forEach((asset) => {
      const tr = document.createElement("tr");
      const tags = Object.entries(asset.tags)
        .map(([k, v]) => `<span class="tag">${k}:${v}</span>`)
        .join("") || "-";
      tr.innerHTML = `
        <td>${asset.asset_id}</td>
        <td>${asset.ip}</td>
        <td>${asset.category}</td>
        <td>${asset.services.join(",")}</td>
        <td>${tags}</td>
        <td>
          <div class="tag-edit">
            <input data-tag-key placeholder="key" />
            <input data-tag-value placeholder="value" />
            <button data-tag-apply data-asset-id="${asset.asset_id}" class="secondary">应用</button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  };

  const renderTopology = () => {
    const svg = el("topologySvg");
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
      line.setAttribute("stroke", "#3bc0c8");
      line.setAttribute("stroke-width", "2");
      svg.appendChild(line);
    });

    assets.forEach((asset) => {
      const p = positions[asset.asset_id];
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", p.x);
      circle.setAttribute("cy", p.y);
      circle.setAttribute("r", 20);
      circle.setAttribute("fill", "#0e1b24");
      circle.setAttribute("stroke", "#ffb347");
      circle.setAttribute("stroke-width", "2");

      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", p.x + 26);
      text.setAttribute("y", p.y + 4);
      text.setAttribute("fill", "#f5fbff");
      text.setAttribute("font-size", "12");
      text.textContent = `${asset.ip} (${asset.category})`;

      svg.appendChild(circle);
      svg.appendChild(text);
    });
  };

  const renderStats = () => {
    el("statAssets").textContent = state.assets.length;
    el("statServices").textContent = state.services.length;
    el("statAlerts").textContent = state.alerts.length;
    el("statSavings").textContent = "6.4h";
  };

  const renderKpis = () => {
    const critical = state.alerts.filter((a) => a.severity === "critical").length;
    const complianceScore = Math.max(0, 100 - state.compliance.filter((c) => c.status !== "pass").length * 12);
    const kpiServices = el("kpiServices");
    if (kpiServices) kpiServices.textContent = state.services.length;
    const kpiCritical = el("kpiCritical");
    if (kpiCritical) kpiCritical.textContent = critical;
    const kpiRuns = el("kpiRuns");
    if (kpiRuns) kpiRuns.textContent = 18;
    const kpiCompliance = el("kpiCompliance");
    if (kpiCompliance) kpiCompliance.textContent = `${complianceScore}%`;
  };

  const renderHero = () => {
    const strip = el("heroStrip");
    strip.innerHTML = state.demo.hero.map((item) => `<div class="strip-item">${item}</div>`).join("");
  };

  const renderPulse = () => {
    const grid = el("pulseGrid");
    grid.innerHTML = state.demo.pulse.map((item) => `<div class="pulse-item"><span>${item.label}</span><strong>${item.value}</strong></div>`).join("");
  };

  const renderTimeline = () => {
    const timeline = el("taskTimeline");
    timeline.innerHTML = state.demo.timeline.map((item) => `<div class="timeline-item">${item}</div>`).join("");
  };

  const renderIncidents = () => {
    const list = el("incidentList");
    list.innerHTML = state.demo.incidents.map((item) => `<div class="list-card">${item}</div>`).join("");
  };

  const renderHomeAlerts = () => {
    const homeList = el("homeAlerts");
    if (!homeList) return;
    homeList.innerHTML = "";
    const items = state.alerts.slice(0, 5);
    if (!items.length) {
      homeList.innerHTML = "<div class=\"muted\">暂无告警事件。</div>";
      return;
    }
    items.forEach((alert) => {
      const card = document.createElement("div");
      card.className = "list-card";
      card.innerHTML = `
        <strong>${alert.severity} · ${alert.metric_name}</strong>
        <div class="muted">${alert.message || "触发告警"} · ${alert.metric_value}</div>
      `;
      homeList.appendChild(card);
    });
  };

  const renderCompliance = (results) => {
    const list = el("complianceList");
    list.innerHTML = "";
    if (!results || !results.length) {
      list.innerHTML = "<div class=\"muted\">暂无巡检结果。</div>";
      return;
    }
    results.forEach((item) => {
      const card = document.createElement("div");
      card.className = "list-card";
      card.innerHTML = `
        <strong>${item.check_id || item.resource_id}</strong>
        <div class="muted">${item.status} · ${item.message || "drift check"}</div>
      `;
      list.appendChild(card);
    });
  };

  const renderAssistantSuggestions = (items) => {
    const list = el("assistantSuggestions");
    if (!list) return;
    list.innerHTML = items.map((item) => `<div class="list-card">${item}</div>`).join("");
  };

  const renderOpsChain = () => {
    const chain = el("opsChain");
    if (!chain) return;
    chain.innerHTML = state.demo.chain.map((item) => `
      <div class="chain-item">
        <div class="chain-dot" data-status="${item.status}"></div>
        <div>
          <strong>${item.step}</strong>
          <span>${item.detail}</span>
        </div>
        <div class="filter-chip">${item.status}</div>
      </div>
    `).join("");
  };

  const renderTrendCharts = () => {
    const grid = el("trendCharts");
    if (!grid) return;
    grid.innerHTML = state.demo.trends.map((item) => `
      <div class="chart-card">
        <div class="chart-title">${item.title}</div>
        <strong>${item.value}</strong>
        <div class="kpi-trend">${item.delta}</div>
        <div class="sparkline"></div>
      </div>
    `).join("");
  };

  const renderAiSignals = () => {
    const grid = el("aiSignalGrid");
    if (!grid) return;
    grid.innerHTML = state.demo.aiSignals.map((item) => `
      <div class="ai-card">
        <strong>${item.title}</strong>
        <span>${item.detail}</span>
      </div>
    `).join("");
  };

  const renderDecisionFlow = () => {
    const flow = el("decisionFlow");
    if (!flow) return;
    flow.innerHTML = state.demo.decisions.map((item) => `
      <div class="decision-step">
        <strong>${item.step}</strong>
        <span>${item.owner}</span>
        <div>${item.detail}</div>
      </div>
    `).join("");
  };

  const renderScenario = () => {
    const graph = el("scenarioGraph");
    const steps = el("scenarioSteps");
    const detail = el("scenarioDetail");
    const history = el("scenarioHistory");
    if (!graph || !steps) return;
    if (!state.selectedScenario) state.selectedScenario = state.demo.scenarioNodes[0]?.id || null;
    const selected = state.demo.scenarioNodes.find((node) => node.id === state.selectedScenario);
    graph.innerHTML = `
      <svg viewBox="0 0 420 220" preserveAspectRatio="xMidYMid meet">
        ${state.demo.scenarioNodes.map((node, index) => {
          const x = 40 + (index % 2) * 180;
          const y = 30 + Math.floor(index / 2) * 60;
          const nextIndex = index + 1;
          if (nextIndex >= state.demo.scenarioNodes.length) return "";
          const nx = 40 + (nextIndex % 2) * 180;
          const ny = 30 + Math.floor(nextIndex / 2) * 60;
          return `<line x1="${x + 18}" y1="${y + 10}" x2="${nx + 18}" y2="${ny + 10}" stroke="rgba(58,166,255,0.35)" stroke-width="2" />`;
        }).join("")}
      </svg>
      <div class="scenario-link"></div>
      ${state.demo.scenarioNodes.map((node) => `
        <div class="scenario-node ${node.id === state.selectedScenario ? "active" : ""}" data-scenario-id="${node.id}">
          <div class="badge">${node.id}</div>
          <div>
            <strong>${node.title}</strong>
            <div class="muted">${node.detail}</div>
          </div>
        </div>
      `).join("")}
    `;
    steps.innerHTML = state.demo.scenarioSteps.map((step) => `
      <div class="scenario-step ${step.nodes.includes(state.selectedScenario) ? "linked" : ""}" data-status="${step.status}">
        <strong>${step.title}</strong>
        <span>${step.owner} · ${step.status}</span>
        <div>${step.detail}</div>
        <div class="scenario-progress"><div class="bar" style="width:${step.progress}%;"></div></div>
      </div>
    `).join("");
    if (detail) {
      if (!selected) {
        detail.innerHTML = "<strong>未选择节点</strong><div class=\"muted\">点击左侧节点查看详情。</div>";
      } else {
        detail.innerHTML = `
          <strong>${selected.title}</strong>
          <div class="muted">${selected.owner}</div>
          <div>${selected.detail}</div>
        `;
      }
    }
    if (history) {
      history.innerHTML = state.demo.scenarioHistory.map((item) => `
        <div class="scenario-history-item">
          <strong>${item.time}</strong>
          <div>${item.detail}</div>
        </div>
      `).join("");
      history.scrollTop = history.scrollHeight;
    }
  };

  const renderAssetSummary = () => {
    const summary = el("assetSummary");
    if (!summary) return;
    const counts = state.assets.reduce((acc, asset) => {
      acc[asset.category] = (acc[asset.category] || 0) + 1;
      return acc;
    }, {});
    summary.innerHTML = [
      { label: "总资产", value: state.assets.length },
      { label: "数据库", value: counts.database || 0 },
      { label: "中间件", value: counts.middleware || 0 },
      { label: "服务器", value: counts.server || 0 },
    ].map((item) => `
      <div class="summary-card">
        <span class="muted">${item.label}</span>
        <strong>${item.value}</strong>
      </div>
    `).join("");
  };

  const renderServiceSummary = () => {
    const summary = el("serviceSummary");
    if (!summary) return;
    const degraded = state.services.filter((s) => s.status !== "running").length;
    summary.innerHTML = [
      { label: "服务总量", value: state.services.length },
      { label: "运行中", value: state.services.filter((s) => s.status === "running").length },
      { label: "异常", value: degraded },
      { label: "平均 CPU", value: `${Math.round(state.services.reduce((acc, s) => acc + s.cpu, 0) / state.services.length || 0)}%` },
    ].map((item) => `
      <div class="summary-card">
        <span class="muted">${item.label}</span>
        <strong>${item.value}</strong>
      </div>
    `).join("");
  };

  const renderIncidentPlaybooks = () => {
    const list = el("incidentPlaybooks");
    if (!list) return;
    list.innerHTML = state.demo.playbooks.map((item) => `<div class="list-card">${item}</div>`).join("");
  };

  const renderRunbooks = () => {
    const list = el("runbookList");
    if (!list) return;
    list.innerHTML = state.demo.runbooks.map((item) => `<div class="list-card">${item}</div>`).join("");
  };

  const filteredServices = () => {
    return state.services.filter((service) => {
      const matchesStatus = state.serviceStatus === "all" || service.status === state.serviceStatus;
      const matchesGroup = state.serviceGroup === "all" || service.group === state.serviceGroup;
      const keyword = state.serviceSearch.toLowerCase();
      const matchesSearch =
        !keyword ||
        service.name.toLowerCase().includes(keyword) ||
        service.ip.includes(keyword) ||
        (service.tags || []).some((tag) => tag.toLowerCase().includes(keyword));
      return matchesStatus && matchesGroup && matchesSearch;
    });
  };

  const renderServices = () => {
    const grid = el("serviceGrid");
    if (!grid) return;
    grid.innerHTML = "";
    filteredServices().forEach((service) => {
      const card = document.createElement("div");
      card.className = "service-card";
      card.innerHTML = `
        <div class="service-header">
          <div class="service-icon">${service.icon}</div>
          <span class="service-status">${service.status}</span>
        </div>
        <div>
          <strong>${service.name}</strong>
        </div>
        <div class="service-meta">
          <div>IP: ${service.ip}</div>
          <div>目录: ${service.dir}</div>
        </div>
        <div class="metric-row"><span>CPU</span><span>${service.cpu}%</span></div>
        <div class="metric-row"><span>内存</span><span>${service.memory} GB</span></div>
        <div class="metric-row"><span>标签</span><span>${(service.tags || []).join(", ")}</span></div>
      `;
      card.addEventListener("click", () => selectService(service.id));
      grid.appendChild(card);
    });
  };

  const renderServiceDetail = () => {
    const service = state.services.find((item) => item.id === state.selectedService);
    if (!service) {
      el("serviceTitle").textContent = "选择一个服务";
      el("serviceMeta").textContent = "点击上方服务卡片进入详情。";
      el("serviceCpu").textContent = "-";
      el("serviceMemory").textContent = "-";
      if (el("serviceStatus")) el("serviceStatus").textContent = "-";
      el("dependencyGraph").innerHTML = "<div class=\"muted\">请选择服务查看依赖拓扑。</div>";
      el("installProgress").innerHTML = "<div class=\"muted\">请选择服务查看安装进度。</div>";
      const monitor = el("serviceMonitor");
      if (monitor) monitor.innerHTML = "<div class=\"muted\">请选择服务查看监控信息。</div>";
      return;
    }
    el("serviceTitle").textContent = service.name;
    el("serviceMeta").textContent = `${service.status} · ${service.ip} · ${service.dir}`;
    el("serviceCpu").textContent = `${service.cpu}%`;
    el("serviceMemory").textContent = `${service.memory} GB`;
    if (el("serviceStatus")) el("serviceStatus").textContent = service.status;
    el("dependencyGraph").innerHTML = service.topology.map((node) => `<div class="progress-item">${node}</div>`).join("");
    el("installProgress").innerHTML = service.progress.map((step) => `<div class="progress-item">${step}</div>`).join("");
    const monitor = el("serviceMonitor");
    if (monitor) {
      monitor.innerHTML = [
        { label: "请求吞吐", value: "12.4k/s" },
        { label: "错误率", value: "0.8%" },
        { label: "P95 延迟", value: "128ms" },
        { label: "连接数", value: "3,420" },
      ].map((item) => `
        <div class="monitor-card">
          <span class="muted">${item.label}</span>
          <strong>${item.value}</strong>
        </div>
      `).join("");
    }
    const trend = el("serviceTrend");
    if (trend) {
      trend.innerHTML = "<div class=\"muted\">CPU / 内存 / 延迟趋势已生成</div>";
    }
  };

  const renderModalProgress = (steps) => {
    el("modalProgress").innerHTML = steps.map((step) => `<div class="progress-item">${step}</div>`).join("");
  };

  const renderModalTopology = (nodes) => {
    el("modalTopology").innerHTML = nodes.map((node) => `<div class="progress-item">${node}</div>`).join("");
  };

  const render = () => {
    renderTable();
    renderTopology();
    renderStats();
    renderKpis();
    renderHomeAlerts();
    renderServices();
    renderServiceDetail();
    renderHero();
    renderPulse();
    renderTimeline();
    renderIncidents();
    renderOpsChain();
    renderTrendCharts();
    renderAiSignals();
    renderDecisionFlow();
    renderScenario();
    renderAssetSummary();
    renderServiceSummary();
    renderIncidentPlaybooks();
    renderRunbooks();
  };

  const switchView = (view) => {
    state.view = view;
    el("listView").classList.toggle("hidden", view !== "list");
    el("topologyView").classList.toggle("hidden", view !== "topology");
    el("listViewBtn").classList.toggle("active", view === "list");
    el("topologyViewBtn").classList.toggle("active", view === "topology");
  };

  const selectService = (serviceId) => {
    state.selectedService = serviceId;
    renderServiceDetail();
    const target = el("view-service-detail");
    document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
    if (target) target.classList.add("active");
    document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("active"));
    const servicesNav = document.querySelector("[data-view='services']");
    if (servicesNav) servicesNav.classList.add("active");
  };

  const loadAlerts = async () => {
    state.alerts = await apiFetch("/monitoring/events");
    render();
  };

  const loadComplianceSummary = async () => {
    try {
      const [results, drifts] = await Promise.all([
        apiFetch("/compliance/results"),
        apiFetch("/compliance/drifts"),
      ]);
      const failed = results.filter((r) => r.status === "fail").length;
      if (el("baselineFail")) el("baselineFail").textContent = failed;
      if (el("driftCount")) el("driftCount").textContent = drifts.length;
    } catch {
      if (el("baselineFail")) el("baselineFail").textContent = "0";
      if (el("driftCount")) el("driftCount").textContent = "0";
    }
  };

  const bindNav = () => {
    document.querySelectorAll(".nav-item").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("active"));
        btn.classList.add("active");
        const viewId = btn.dataset.view;
        document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
        const target = el(`view-${viewId}`);
        if (target) target.classList.add("active");
      });
    });
  };

  const bindApiBase = () => {
    const input = el("apiBaseInput");
    const saved = localStorage.getItem(API_BASE_STORAGE) || DEFAULT_API_BASE;
    input.value = saved;
    el("saveApiBtn").addEventListener("click", () => {
      localStorage.setItem(API_BASE_STORAGE, input.value.trim() || DEFAULT_API_BASE);
      const assistantMsg = el("assistantMsg");
      if (assistantMsg) assistantMsg.textContent = "API Base 已保存，可刷新数据。";
    });
  };

  const bindEvents = () => {
    el("runTriageBtn").addEventListener("click", () => {
      const strip = el("heroStrip");
      strip.insertAdjacentHTML("afterbegin", "<div class=\"strip-item\">AI 正在生成根因分析与执行建议…</div>");
    });

    el("openOpsStudio").addEventListener("click", () => {
      document.querySelector("[data-view='assistant']").click();
    });

    el("aiCommandBtn").addEventListener("click", () => {
      const input = el("aiCommandInput").value.trim();
      if (!input) return;
      state.demo.aiSignals.unshift({
        title: "指令已接收",
        detail: input,
        status: "action",
      });
      renderAiSignals();
    });

    el("scanBtn").addEventListener("click", async () => {
      const targets = expandTargets(el("targetsInput").value);
      const workers = Number(el("workersInput").value) || 1;
      const msg = el("scanMsg");
      if (!targets.length) {
        msg.textContent = "请输入有效 IP 或网段。";
        msg.className = "hint warn";
        return;
      }
      msg.textContent = `正在探测 ${targets.length} 个目标（并发 ${workers}）...`;
      msg.className = "hint";
      const signals = await sniffWithWorkers(targets, workers);
      state.assets = buildAssets(signals);
      state.edges = buildEdges(state.assets, signals);
      msg.textContent = `探测完成：发现 ${state.assets.length} 个资产。`;
      msg.className = "hint ok";
      render();
    });

    el("sampleBtn").addEventListener("click", () => {
      el("targetsInput").value = "10.0.2.10,10.0.3.0/29";
      el("workersInput").value = 12;
    });

    el("assetTable").addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;
      if (!target.hasAttribute("data-tag-apply")) return;
      const assetId = target.getAttribute("data-asset-id");
      const row = target.closest("tr");
      if (!assetId || !row) return;
      const keyInput = row.querySelector("[data-tag-key]");
      const valueInput = row.querySelector("[data-tag-value]");
      if (!(keyInput instanceof HTMLInputElement) || !(valueInput instanceof HTMLInputElement)) return;
      const key = keyInput.value.trim();
      const value = valueInput.value.trim();
      const asset = state.assets.find((a) => a.asset_id === assetId);
      if (!asset || !key || !value) return;
      asset.tags[key] = value;
      render();
    });

    el("categoryFilter").addEventListener("change", (e) => {
      state.filter = e.target.value;
      render();
    });

    el("autoTagBtn").addEventListener("click", () => {
      state.assets.forEach((asset) => {
        if (!asset.tags.env) asset.tags.env = asset.category === "database" ? "prod" : "staging";
        if (!asset.tags.team) asset.tags.team = asset.services.includes("nginx") ? "platform" : "core";
        if (!asset.tags.owner) asset.tags.owner = "ai";
      });
      render();
    });

    el("listViewBtn").addEventListener("click", () => switchView("list"));
    el("topologyViewBtn").addEventListener("click", () => switchView("topology"));

    el("addServiceBtn").addEventListener("click", () => {
      el("serviceModal").classList.add("open");
      renderModalTopology(["agent", "installer", "service"]);
      renderModalProgress(["prepare", "install", "configure"]);
    });

    el("closeServiceModal").addEventListener("click", () => {
      el("serviceModal").classList.remove("open");
    });

    el("executeInstallBtn").addEventListener("click", () => {
      const prompt = el("servicePrompt").value.trim();
      const chat = el("serviceChat");
      if (prompt) {
        const bubble = document.createElement("div");
        bubble.className = "chat-bubble";
        bubble.textContent = `执行: ${prompt}`;
        chat.appendChild(bubble);
      }
      renderModalProgress(["prepare", "install", "configure", "health_check"]);
    });

    const scenarioGraph = el("scenarioGraph");
    if (scenarioGraph) {
      scenarioGraph.addEventListener("click", (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement)) return;
        const node = target.closest(".scenario-node");
        if (!node) return;
        const id = node.getAttribute("data-scenario-id");
        if (!id) return;
        state.selectedScenario = id;
        renderScenario();
      });
      scenarioGraph.addEventListener("mouseover", (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement)) return;
        const node = target.closest(".scenario-node");
        if (!node) return;
        const id = node.getAttribute("data-scenario-id");
        if (!id) return;
        state.selectedScenario = id;
        renderScenario();
      });
    }

    const serviceSearchInput = el("serviceSearchInput");
    if (serviceSearchInput) {
      serviceSearchInput.addEventListener("input", (event) => {
        state.serviceSearch = event.target.value;
        renderServices();
      });
    }

    const serviceStatusFilter = el("serviceStatusFilter");
    if (serviceStatusFilter) {
      serviceStatusFilter.addEventListener("change", (event) => {
        state.serviceStatus = event.target.value;
        renderServices();
      });
    }

    const serviceGroupFilter = el("serviceGroupFilter");
    if (serviceGroupFilter) {
      serviceGroupFilter.addEventListener("change", (event) => {
        state.serviceGroup = event.target.value;
        renderServices();
      });
    }

    const refreshBtn = el("serviceRefreshBtn");
    if (refreshBtn) {
      refreshBtn.addEventListener("click", () => {
        seedServices();
        renderServices();
        renderServiceSummary();
      });
    }

    const backBtn = el("backToServicesBtn");
    if (backBtn) {
      backBtn.addEventListener("click", () => {
        document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
        const servicesView = el("view-services");
        if (servicesView) servicesView.classList.add("active");
        document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("active"));
        const servicesNav = document.querySelector("[data-view='services']");
        if (servicesNav) servicesNav.classList.add("active");
      });
    }

    el("assistantBtn").addEventListener("click", async () => {
      const input = el("assistantInput").value.trim();
      const msg = el("assistantMsg");
      if (!input) {
        msg.textContent = "请输入请求文本。";
        msg.className = "hint warn";
        return;
      }
      msg.textContent = "AI 正在生成建议...";
      msg.className = "hint";
      const demo = [
        "诊断 Kafka 延迟，执行 broker 重平衡并调整 ISR。",
        "扩展 Redis 实例并开启热键预热。",
        "下发回滚策略并通知值班群。",
      ];
      try {
        const res = await apiFetch("/assistant/suggest", {
          method: "POST",
          body: JSON.stringify({ prompt: input, mode: "ops" }),
        });
        const suggestions = (res.suggestions || []).map((s) => s.action || s.reason || s) || demo;
        renderAssistantSuggestions(suggestions.length ? suggestions : demo);
        msg.textContent = "建议已生成。";
        msg.className = "hint ok";
      } catch {
        renderAssistantSuggestions(demo);
        msg.textContent = "API 不可用，已使用示例建议。";
        msg.className = "hint warn";
      }
    });

    el("runBaselineBtn").addEventListener("click", () => {
      renderCompliance(state.compliance);
      const msg = el("complianceMsg");
      msg.textContent = "基线检查完成。";
      msg.className = "hint ok";
    });

    el("runDriftBtn").addEventListener("click", () => {
      renderCompliance(state.compliance);
      const msg = el("complianceMsg");
      msg.textContent = "漂移检测完成。";
      msg.className = "hint ok";
    });

    el("refreshReportBtn").addEventListener("click", () => {
      renderCompliance(state.compliance);
      const msg = el("complianceMsg");
      msg.textContent = "报告已刷新。";
      msg.className = "hint";
    });
  };

  const init = async () => {
    bindNav();
    bindApiBase();
    bindEvents();
    seedDemo();
    seedServices();
    seedAssets();
    seedAlerts();
    seedCompliance();
    renderServices();
    renderServiceDetail();
    renderCompliance(state.compliance);
    renderAssistantSuggestions(state.demo.runbooks);
    try {
      await loadAlerts();
      await loadComplianceSummary();
    } catch (error) {
      const assistantMsg = el("assistantMsg");
      if (assistantMsg) assistantMsg.textContent = `API 连接失败，已加载示例数据。`;
    }
    render();
  };

  init();
})();

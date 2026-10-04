import { useCallback, useEffect, useMemo, useRef, useState } from "react";

type Village = { id: number; name: string; agents: number; food: number; wood: number; stone: number };
type Faction = { id: number; name: string; leader_id: number; members: number[]; cohesion: number };
type WorldState = { day: number; population: number; villages: Village[]; factions: Faction[] };
type Agent = { id: number; age: number; health: number; hunger: number; wealth: number; trust: number; occupation: string; village_id: number; village_name: string; alive: boolean; fertility: number; faction_id: number | null; faction_name: string | null };
type Metrics = { day: number; population: number; living_population: number; average_health: number; average_hunger: number; total_food: number; total_wood: number; total_stone: number; total_wealth: number; average_wealth: number; average_trust: number; trade_volume: number; births: number; deaths: number; migrations: number; social_interactions: number; conflicts: number; faction_count: number; average_faction_cohesion: number };
type SimulationEvent = { type: string; day: number; message: string };
type StreamMessage = { action: string; state: WorldState; metrics: Metrics };
type ChartPoint = { day: number; value: number };

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const WS_BASE = import.meta.env.VITE_WS_URL ?? API_BASE.replace(/^http/, "ws");

const emptyState: WorldState = { day: 0, population: 0, villages: [], factions: [] };
const emptyMetrics: Metrics = { day: 0, population: 0, living_population: 0, average_health: 0, average_hunger: 0, total_food: 0, total_wood: 0, total_stone: 0, total_wealth: 0, average_wealth: 0, average_trust: 0, trade_volume: 0, births: 0, deaths: 0, migrations: 0, social_interactions: 0, conflicts: 0, faction_count: 0, average_faction_cohesion: 0 };

function App() {
  const [state, setState] = useState(emptyState);
  const [metrics, setMetrics] = useState(emptyMetrics);
  const [history, setHistory] = useState<Metrics[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
  const [agentQuery, setAgentQuery] = useState("");
  const [selectedVillageId, setSelectedVillageId] = useState<number | null>(null);
  const [events, setEvents] = useState<SimulationEvent[]>([]);
  const [days, setDays] = useState(10);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  const applyStream = useCallback((message: StreamMessage) => {
    setState(message.state);
    setMetrics(message.metrics);
  }, []);

  const loadEvents = useCallback(async () => {
    const response = await fetch(API_BASE + "/simulation/events?limit=12");
    if (response.ok) setEvents(await response.json());
  }, []);

  const loadAgents = useCallback(async () => {
    const response = await fetch(API_BASE + "/simulation/agents?limit=500");
    if (response.ok) setAgents(await response.json());
  }, []);

  const loadHistory = useCallback(async () => {
    const response = await fetch(API_BASE + "/simulation/metrics/history?limit=365");
    if (response.ok) setHistory(await response.json());
  }, []);

  const refreshWorld = useCallback(() => {
    void loadEvents();
    void loadAgents();
    void loadHistory();
  }, [loadAgents, loadEvents, loadHistory]);

  const send = useCallback((command: Record<string, unknown>) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) socketRef.current.send(JSON.stringify(command));
  }, []);

  useEffect(() => {
    const socket = new WebSocket(WS_BASE + "/simulation/ws");
    socketRef.current = socket;
    socket.onopen = () => { setConnected(true); send({ action: "state" }); };
    socket.onmessage = event => {
      const message = JSON.parse(event.data) as StreamMessage;
      if ("state" in message) { applyStream(message); refreshWorld(); }
    };
    socket.onclose = () => { setConnected(false); socketRef.current = null; };
    return () => socket.close();
  }, [applyStream, refreshWorld, send]);

  useEffect(() => { refreshWorld(); }, [refreshWorld]);

  const start = async () => {
    const response = await fetch(API_BASE + "/simulation/start", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ seed: 42, population: 100 }),
    });
    if (!response.ok) return;
    const nextState = await response.json() as WorldState;
    setState(nextState);
    setMetrics({ ...emptyMetrics, population: nextState.population, living_population: nextState.population });
    setHistory([{ ...emptyMetrics, population: nextState.population, living_population: nextState.population }]);
    setSelectedAgentId(null);
    setSelectedVillageId(null);
    setAgentQuery("");
    send({ action: "state" });
    refreshWorld();
  };

  const filteredAgents = useMemo(() => {
    const query = agentQuery.trim().toLowerCase();
    const visibleAgents = selectedVillageId === null ? agents : agents.filter(agent => agent.village_id === selectedVillageId);
    if (!query) return visibleAgents;
    return visibleAgents.filter(agent => String(agent.id).includes(query) || agent.occupation.includes(query) || agent.village_name.toLowerCase().includes(query) || (agent.faction_name ?? "").toLowerCase().includes(query));
  }, [agentQuery, agents, selectedVillageId]);

  const selectedAgent = agents.find(agent => agent.id === selectedAgentId) ?? null;
  const selectedVillage = state.villages.find(village => village.id === selectedVillageId) ?? null;
  const totals = useMemo(() => ({
    food: state.villages.reduce((sum, v) => sum + v.food, 0),
    wood: state.villages.reduce((sum, v) => sum + v.wood, 0),
    stone: state.villages.reduce((sum, v) => sum + v.stone, 0),
  }), [state.villages]);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div><p className="eyebrow">AGENT-BASED CIVILIZATION SIMULATOR</p><h1>CIVITAS</h1></div>
        <div className="status"><span className={"status-dot " + (connected ? "online" : "")} />{connected ? "Simulation stream connected" : "Simulation stream offline"}</div>
      </header>

      <section className="controls panel">
        <div><span className="label">SIMULATION DAY</span><strong>{state.day}</strong></div>
        <div className="control-actions">
          <button onClick={start}>New Simulation</button>
          <button onClick={() => send({ action: "tick" })}>Tick +1</button>
          <input aria-label="Days to run" type="number" min="0" value={days} onChange={e => setDays(Math.max(0, Number(e.target.value) || 0))} />
          <button onClick={() => send({ action: "run", days })}>Run</button>
        </div>
      </section>

      <section className="metrics-grid">
        <Metric label="Population" value={metrics.living_population} />
        <Metric label="Food" value={metrics.total_food.toFixed(1)} />
        <Metric label="Wood" value={metrics.total_wood.toFixed(1)} />
        <Metric label="Stone" value={metrics.total_stone.toFixed(1)} />
        <Metric label="Trust" value={metrics.average_trust.toFixed(1)} />
        <Metric label="Factions" value={metrics.faction_count} />
      </section>

      <section className="dashboard-grid">
        <article className="panel wide">
          <div className="section-heading"><div><span className="label">WORLD</span><h2>World Map</h2></div><span className="muted">{state.villages.length} settlements · {metrics.migrations} migrations</span></div>
          <WorldMap villages={state.villages} agents={agents} factions={state.factions} selectedVillageId={selectedVillageId} onSelect={setSelectedVillageId} />
          {selectedVillage && <div className="world-selection">
            <div><span className="label">SELECTED SETTLEMENT</span><strong>{selectedVillage.name}</strong><span>{selectedVillage.agents} agents</span></div>
            <div className="selection-resources"><span>Food <b>{selectedVillage.food.toFixed(1)}</b></span><span>Wood <b>{selectedVillage.wood.toFixed(1)}</b></span><span>Stone <b>{selectedVillage.stone.toFixed(1)}</b></span></div>
            <button onClick={() => setSelectedVillageId(null)}>Clear</button>
          </div>}
        </article>

        <article className="panel wide">
          <div className="section-heading"><div><span className="label">HISTORY</span><h2>Simulation Trends</h2></div><span className="muted">{history.length} recorded days</span></div>
          <div className="charts-grid">
            <LineChart title="Population" points={history.map(m => ({ day: m.day, value: m.living_population }))} />
            <LineChart title="Food" points={history.map(m => ({ day: m.day, value: m.total_food }))} />
            <LineChart title="Average Trust" points={history.map(m => ({ day: m.day, value: m.average_trust }))} />
            <LineChart title="Total Wealth" points={history.map(m => ({ day: m.day, value: m.total_wealth }))} />
          </div>
        </article>

        <article className="panel wide">
          <div className="section-heading"><div><span className="label">SETTLEMENTS</span><h2>Villages</h2></div><span className="muted">{state.villages.length} settlements</span></div>
          <div className="village-grid">
            {state.villages.map(village => <button className={"village-card " + (village.id === selectedVillageId ? "selected" : "")} key={village.id} onClick={() => setSelectedVillageId(village.id)}>
              <div className="village-title"><h3>{village.name}</h3><span>{village.agents} agents</span></div>
              <ResourceBar label="Food" value={village.food} max={Math.max(totals.food / Math.max(state.villages.length, 1), 1)} />
              <ResourceBar label="Wood" value={village.wood} max={Math.max(totals.wood / Math.max(state.villages.length, 1), 1)} />
              <ResourceBar label="Stone" value={village.stone} max={Math.max(totals.stone / Math.max(state.villages.length, 1), 1)} />
            </button>)}
          </div>
        </article>

        <article className="panel wide">
          <div className="section-heading"><div><span className="label">POPULATION</span><h2>Agent Inspector</h2></div><span className="muted">{filteredAgents.length} of {agents.length} agents{selectedVillage ? " · " + selectedVillage.name : ""}</span></div>
          <div className="inspector">
            <div className="agent-list">
              <input className="agent-search" aria-label="Search agents" placeholder="Search ID, occupation, village..." value={agentQuery} onChange={e => setAgentQuery(e.target.value)} />
              <div className="agent-rows">{filteredAgents.map(agent => <button className={"agent-row " + (agent.id === selectedAgentId ? "selected" : "")} key={agent.id} onClick={() => setSelectedAgentId(agent.id)}>
                <span className="agent-id">#{agent.id}</span><span className="agent-main"><strong>{agent.occupation}</strong><small>{agent.village_name}</small></span><span className={"alive-pill " + (agent.alive ? "alive" : "dead")}>{agent.alive ? "ALIVE" : "DEAD"}</span>
              </button>)}</div>
            </div>
            <div className="agent-detail">{!selectedAgent ? <p className="empty">Select an agent to inspect its current state.</p> : <>
              <div className="detail-heading"><div><span className="label">AGENT #{selectedAgent.id}</span><h3>{selectedAgent.occupation}</h3></div><span className={"alive-pill " + (selectedAgent.alive ? "alive" : "dead")}>{selectedAgent.alive ? "ALIVE" : "DEAD"}</span></div>
              <div className="detail-grid">
                <Detail label="Age" value={selectedAgent.age.toFixed(1)} /><Detail label="Health" value={selectedAgent.health.toFixed(1)} /><Detail label="Hunger" value={selectedAgent.hunger.toFixed(1)} /><Detail label="Wealth" value={selectedAgent.wealth.toFixed(1)} /><Detail label="Trust" value={selectedAgent.trust.toFixed(1)} /><Detail label="Fertility" value={selectedAgent.fertility.toFixed(2)} /><Detail label="Village" value={selectedAgent.village_name} /><Detail label="Faction" value={selectedAgent.faction_name ?? "None"} />
              </div>
            </>}</div>
          </div>
        </article>

        <article className="panel"><div className="section-heading"><div><span className="label">SOCIETY</span><h2>Factions</h2></div></div>
          {state.factions.length === 0 ? <p className="empty faction-list">No factions have emerged yet.</p> : <div className="faction-list">{state.factions.map(faction => <div className="faction-row" key={faction.id}><div><strong>{faction.name}</strong><span>{faction.members.length} members · leader #{faction.leader_id}</span></div><b>{faction.cohesion.toFixed(1)}</b></div>)}</div>}
        </article>

        <article className="panel"><div className="section-heading"><div><span className="label">HISTORY</span><h2>Recent Events</h2></div></div>
          <div className="event-list">{events.length === 0 ? <p className="empty">No events recorded.</p> : events.map((event, index) => <div className="event-row" key={event.day + "-" + index}><span>DAY {event.day}</span><div><strong>{event.type.replaceAll("_", " ")}</strong><p>{event.message}</p></div></div>)}</div>
        </article>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) { return <div className="metric panel"><span className="label">{label}</span><strong>{value}</strong></div>; }
function Detail({ label, value }: { label: string; value: string }) { return <div className="detail-cell"><span>{label}</span><strong>{value}</strong></div>; }
function ResourceBar({ label, value, max }: { label: string; value: number; max: number }) { const percentage = Math.min(100, Math.max(0, (value / max) * 100)); return <div className="resource"><div><span>{label}</span><b>{value.toFixed(1)}</b></div><div className="bar"><span style={{ width: percentage + "%" }} /></div></div>; }

function WorldMap({ villages, agents, factions, selectedVillageId, onSelect }: { villages: Village[]; agents: Agent[]; factions: Faction[]; selectedVillageId: number | null; onSelect: (id: number) => void }) {
  const positions = [{ x: 18, y: 58 }, { x: 50, y: 28 }, { x: 82, y: 62 }];
  const nodes = villages.map((village, index) => ({ village, ...(positions[index % positions.length]) }));
  const factionColor = (id: number) => ["#6ee7b7", "#93c5fd", "#f0abfc", "#fcd34d", "#fda4af"][Math.abs(id) % 5];
  return <div className="world-map-wrap">
    <svg className="world-map" viewBox="0 0 100 100" role="img" aria-label="Interactive civilization world map">
      <defs><pattern id="world-grid" width="5" height="5" patternUnits="userSpaceOnUse"><path d="M 5 0 L 0 0 0 5" fill="none" stroke="currentColor" opacity=".08" strokeWidth=".15" /></pattern></defs>
      <rect width="100" height="100" fill="url(#world-grid)" />
      {nodes.length > 1 && nodes.slice(1).map((node, index) => <line key={"link-" + node.village.id} x1={nodes[index].x} y1={nodes[index].y} x2={node.x} y2={node.y} stroke="currentColor" opacity=".16" strokeWidth=".35" strokeDasharray="1.2 1.4" />)}
      {nodes.map(node => {
        const villageAgents = agents.filter(agent => agent.village_id === node.village.id && agent.alive).slice(0, 18);
        return <g key={node.village.id} className="world-node" onClick={() => onSelect(node.village.id)} role="button" aria-label={"Select " + node.village.name} tabIndex={0} onKeyDown={event => { if (event.key === "Enter" || event.key === " ") onSelect(node.village.id); }}>
          <circle cx={node.x} cy={node.y} r={node.village.id === selectedVillageId ? 9 : 7} fill="#0b1117" stroke={node.village.id === selectedVillageId ? "#f8fafc" : "#6ee7b7"} strokeWidth=".8" />
          <circle cx={node.x} cy={node.y} r="5.2" fill="#111a22" stroke="currentColor" strokeWidth=".25" opacity=".9" />
          {villageAgents.map((agent, index) => {
            const angle = (index / Math.max(villageAgents.length, 1)) * Math.PI * 2;
            const radius = 3.4 + (index % 3) * .8;
            const faction = agent.faction_id === null ? null : factions.find(item => item.id === agent.faction_id);
            return <circle key={agent.id} cx={node.x + Math.cos(angle) * radius} cy={node.y + Math.sin(angle) * radius} r=".65" fill={faction ? factionColor(faction.id) : "#81909d"} opacity=".9" />;
          })}
          <text x={node.x} y={node.y + 13} textAnchor="middle" fill="currentColor" fontSize="3.2" fontWeight="700">{node.village.name}</text>
          <text x={node.x} y={node.y + 17} textAnchor="middle" fill="currentColor" opacity=".55" fontSize="2.5">{node.village.agents} agents</text>
        </g>;
      })}
      {metricsLegend(factions, factionColor)}
    </svg>
    <div className="world-map-caption"><span><i className="legend-dot settlement" />Settlement</span><span><i className="legend-dot agent" />Agent</span><span><i className="legend-line" />Trade/migration corridor</span></div>
  </div>;
}

function metricsLegend(factions: Faction[], factionColor: (id: number) => string) {
  if (!factions.length) return null;
  return <foreignObject x="2" y="2" width="96" height="10"><div className="map-legend">{factions.slice(0, 5).map(faction => <span key={faction.id}><i style={{ background: factionColor(faction.id) }} />{faction.name}</span>)}</div></foreignObject>;
}

function LineChart({ title, points }: { title: string; points: ChartPoint[] }) {
  const width = 560, height = 190, padX = 18, padY = 20;
  const values = points.map(p => p.value);
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 1);
  const range = Math.max(max - min, 1);
  const coords = points.map((point, index) => {
    const x = points.length <= 1 ? width / 2 : padX + (index / (points.length - 1)) * (width - padX * 2);
    const y = height - padY - ((point.value - min) / range) * (height - padY * 2);
    return { x, y };
  });
  const path = coords.map(p => p.x + "," + p.y).join(" ");
  const latest = points.at(-1);
  return <div className="chart-card">
    <div className="chart-heading"><strong>{title}</strong><span>{latest ? latest.value.toFixed(1) : "0.0"}</span></div>
    {points.length === 0 ? <p className="empty chart-empty">No history yet.</p> : <svg className="chart" viewBox={"0 0 " + width + " " + height} role="img" aria-label={title + " history"}>
      <line x1={padX} y1={height-padY} x2={width-padX} y2={height-padY} stroke="currentColor" opacity=".15" />
      <polyline points={path} fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
      {latest && <circle cx={coords.at(-1)?.x} cy={coords.at(-1)?.y} r="4" fill="currentColor" />}
    </svg>}
    {points.length > 0 && <div className="chart-axis"><span>Day {points[0].day}</span><span>Day {latest?.day}</span></div>}
  </div>;
}

export default App;

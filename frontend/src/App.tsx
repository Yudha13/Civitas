import { useCallback, useEffect, useMemo, useRef, useState } from "react";

type Village = { id: number; name: string; agents: number; food: number; wood: number; stone: number };
type Faction = { id: number; name: string; leader_id: number; members: number[]; cohesion: number };
type WorldState = { day: number; population: number; villages: Village[]; factions: Faction[] };
type Agent = {
  id: number;
  age: number;
  health: number;
  hunger: number;
  wealth: number;
  trust: number;
  occupation: string;
  village_id: number;
  village_name: string;
  alive: boolean;
  fertility: number;
  faction_id: number | null;
  faction_name: string | null;
};
type Metrics = {
  day: number; population: number; living_population: number; average_health: number;
  average_hunger: number; total_food: number; total_wood: number; total_stone: number;
  total_wealth: number; average_wealth: number; average_trust: number; trade_volume: number;
  births: number; deaths: number; migrations: number; social_interactions: number;
  conflicts: number; faction_count: number; average_faction_cohesion: number;
};
type SimulationEvent = { type: string; day: number; message: string };
type StreamMessage = { action: string; state: WorldState; metrics: Metrics };

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const WS_BASE = import.meta.env.VITE_WS_URL ?? API_BASE.replace(/^http/, "ws");

const emptyState: WorldState = { day: 0, population: 0, villages: [], factions: [] };
const emptyMetrics: Metrics = {
  day: 0, population: 0, living_population: 0, average_health: 0, average_hunger: 0,
  total_food: 0, total_wood: 0, total_stone: 0, total_wealth: 0, average_wealth: 0,
  average_trust: 0, trade_volume: 0, births: 0, deaths: 0, migrations: 0,
  social_interactions: 0, conflicts: 0, faction_count: 0, average_faction_cohesion: 0,
};

function App() {
  const [state, setState] = useState(emptyState);
  const [metrics, setMetrics] = useState(emptyMetrics);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
  const [agentQuery, setAgentQuery] = useState("");
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

  const refreshWorld = useCallback(() => {
    void loadEvents();
    void loadAgents();
  }, [loadAgents, loadEvents]);

  const send = useCallback((command: Record<string, unknown>) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(command));
    }
  }, []);

  useEffect(() => {
    const socket = new WebSocket(WS_BASE + "/simulation/ws");
    socketRef.current = socket;
    socket.onopen = () => { setConnected(true); send({ action: "state" }); };
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data) as StreamMessage;
      if ("state" in message) { applyStream(message); refreshWorld(); }
    };
    socket.onclose = () => { setConnected(false); socketRef.current = null; };
    return () => socket.close();
  }, [applyStream, refreshWorld, send]);

  useEffect(() => { refreshWorld(); }, [refreshWorld]);

  const start = async () => {
    const response = await fetch(API_BASE + "/simulation/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ seed: 42, population: 100 }),
    });
    if (!response.ok) return;
    const nextState = (await response.json()) as WorldState;
    setState(nextState);
    setMetrics({ ...emptyMetrics, population: nextState.population, living_population: nextState.population });
    setSelectedAgentId(null);
    setAgentQuery("");
    send({ action: "state" });
    refreshWorld();
  };

  const filteredAgents = useMemo(() => {
    const query = agentQuery.trim().toLowerCase();
    if (!query) return agents;
    return agents.filter(agent =>
      String(agent.id).includes(query) ||
      agent.occupation.includes(query) ||
      agent.village_name.toLowerCase().includes(query) ||
      (agent.faction_name ?? "").toLowerCase().includes(query)
    );
  }, [agentQuery, agents]);

  const selectedAgent = agents.find(agent => agent.id === selectedAgentId) ?? null;

  const totals = useMemo(() => ({
    food: state.villages.reduce((sum, village) => sum + village.food, 0),
    wood: state.villages.reduce((sum, village) => sum + village.wood, 0),
    stone: state.villages.reduce((sum, village) => sum + village.stone, 0),
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
          <div className="section-heading"><div><span className="label">WORLD</span><h2>Villages</h2></div><span className="muted">{state.villages.length} settlements</span></div>
          <div className="village-grid">
            {state.villages.map(village => (
              <div className="village-card" key={village.id}>
                <div className="village-title"><h3>{village.name}</h3><span>{village.agents} agents</span></div>
                <ResourceBar label="Food" value={village.food} max={Math.max(totals.food / Math.max(state.villages.length, 1), 1)} />
                <ResourceBar label="Wood" value={village.wood} max={Math.max(totals.wood / Math.max(state.villages.length, 1), 1)} />
                <ResourceBar label="Stone" value={village.stone} max={Math.max(totals.stone / Math.max(state.villages.length, 1), 1)} />
              </div>
            ))}
          </div>
        </article>

        <article className="panel wide">
          <div className="section-heading">
            <div><span className="label">POPULATION</span><h2>Agent Inspector</h2></div>
            <span className="muted">{filteredAgents.length} of {agents.length} agents</span>
          </div>
          <div className="inspector">
            <div className="agent-list">
              <input
                className="agent-search"
                aria-label="Search agents"
                placeholder="Search ID, occupation, village..."
                value={agentQuery}
                onChange={e => setAgentQuery(e.target.value)}
              />
              <div className="agent-rows">
                {filteredAgents.map(agent => (
                  <button
                    className={"agent-row " + (agent.id === selectedAgentId ? "selected" : "")}
                    key={agent.id}
                    onClick={() => setSelectedAgentId(agent.id)}
                  >
                    <span className="agent-id">#{agent.id}</span>
                    <span className="agent-main"><strong>{agent.occupation}</strong><small>{agent.village_name}</small></span>
                    <span className={"alive-pill " + (agent.alive ? "alive" : "dead")}>{agent.alive ? "ALIVE" : "DEAD"}</span>
                  </button>
                ))}
              </div>
            </div>
            <div className="agent-detail">
              {!selectedAgent ? <p className="empty">Select an agent to inspect its current state.</p> : <>
                <div className="detail-heading">
                  <div><span className="label">AGENT #{selectedAgent.id}</span><h3>{selectedAgent.occupation}</h3></div>
                  <span className={"alive-pill " + (selectedAgent.alive ? "alive" : "dead")}>{selectedAgent.alive ? "ALIVE" : "DEAD"}</span>
                </div>
                <div className="detail-grid">
                  <Detail label="Age" value={selectedAgent.age.toFixed(1)} />
                  <Detail label="Health" value={selectedAgent.health.toFixed(1)} />
                  <Detail label="Hunger" value={selectedAgent.hunger.toFixed(1)} />
                  <Detail label="Wealth" value={selectedAgent.wealth.toFixed(1)} />
                  <Detail label="Trust" value={selectedAgent.trust.toFixed(1)} />
                  <Detail label="Fertility" value={selectedAgent.fertility.toFixed(2)} />
                  <Detail label="Village" value={selectedAgent.village_name} />
                  <Detail label="Faction" value={selectedAgent.faction_name ?? "None"} />
                </div>
              </>}
            </div>
          </div>
        </article>

        <article className="panel">
          <div className="section-heading"><div><span className="label">SOCIETY</span><h2>Factions</h2></div></div>
          {state.factions.length === 0 ? <p className="empty">No factions have emerged yet.</p> :
            <div className="faction-list">{state.factions.map(faction => (
              <div className="faction-row" key={faction.id}>
                <div><strong>{faction.name}</strong><span>{faction.members.length} members · leader #{faction.leader_id}</span></div>
                <b>{faction.cohesion.toFixed(1)}</b>
              </div>
            ))}</div>}
        </article>

        <article className="panel">
          <div className="section-heading"><div><span className="label">HISTORY</span><h2>Recent Events</h2></div></div>
          <div className="event-list">
            {events.length === 0 ? <p className="empty">No events recorded.</p> :
              events.map((event, index) => (
                <div className="event-row" key={event.day + "-" + index}>
                  <span>DAY {event.day}</span><div><strong>{event.type.replaceAll("_", " ")}</strong><p>{event.message}</p></div>
                </div>
              ))}
          </div>
        </article>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return <div className="metric panel"><span className="label">{label}</span><strong>{value}</strong></div>;
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div className="detail-cell"><span>{label}</span><strong>{value}</strong></div>;
}

function ResourceBar({ label, value, max }: { label: string; value: number; max: number }) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  return <div className="resource"><div><span>{label}</span><b>{value.toFixed(1)}</b></div><div className="bar"><span style={{ width: percentage + "%" }} /></div></div>;
}

export default App;

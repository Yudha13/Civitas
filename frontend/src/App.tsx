import { useEffect, useMemo, useState } from "react";

type Village = { id: number; name: string; agents: number; food: number; wood: number; stone: number };
type Faction = { id: number; name: string; leader_id: number; members: number[]; cohesion: number };
type WorldState = { day: number; population: number; villages: Village[]; factions: Faction[] };
type Agent = { id: number; age: number; health: number; hunger: number; wealth: number; trust: number; occupation: string; village_id: number; village_name: string; alive: boolean; fertility: number; faction_id: number | null; faction_name: string | null; ideology: string; ideology_commitment: number };
type Metrics = { day: number; population: number; living_population: number; average_health: number; average_hunger: number; total_food: number; total_wood: number; total_stone: number; total_wealth: number; average_wealth: number; average_trust: number; trade_volume: number; births: number; deaths: number; migrations: number; social_interactions: number; conflicts: number; faction_count: number; average_faction_cohesion: number; wealth_gini: number; top_10_wealth_share: number; political_pressure: number; environmental_disasters: number; wars: number; war_casualties: number; epidemics: number; epidemic_infections: number; epidemic_deaths: number; ideology_diversity: number; dominant_ideology_share: number; ideology_shifts: number };
type SimulationEvent = { type: string; day: number; message: string };
type ChartPoint = { day: number; value: number };
type Analysis = {
  start_day: number | null;
  end_day: number | null;
  days: number;
  population: { start: number; end: number; change: number };
  wealth: { start: number; end: number; change: number };
  food: { start: number; end: number; change: number };
  trust: { start: number; end: number; change: number };
  wealth_gini: { start: number; end: number; change: number };
  events: { births: number; deaths: number; migrations: number; conflicts: number; disasters: number; wars: number; war_casualties: number; epidemics: number; epidemic_infections: number; epidemic_deaths: number; ideology_shifts: number };
  peaks: Record<string, { day: number; value: number }>;
  troughs: Record<string, { day: number; value: number }>;
};
type AuthUser = { subject: string; email: string | null; name: string | null; picture: string | null; demo?: boolean };


const emptyState: WorldState = { day: 0, population: 0, villages: [], factions: [] };
const emptyMetrics: Metrics = { day: 0, population: 0, living_population: 0, average_health: 0, average_hunger: 0, total_food: 0, total_wood: 0, total_stone: 0, total_wealth: 0, average_wealth: 0, average_trust: 0, trade_volume: 0, births: 0, deaths: 0, migrations: 0, social_interactions: 0, conflicts: 0, faction_count: 0, average_faction_cohesion: 0, wealth_gini: 0, top_10_wealth_share: 0, political_pressure: 0, environmental_disasters: 0, wars: 0, war_casualties: 0, epidemics: 0, epidemic_infections: 0, epidemic_deaths: 0, ideology_diversity: 0, dominant_ideology_share: 0, ideology_shifts: 0 };

const DEMO_STORAGE_KEY = "civitas-standalone-demo-v1";
const DEMO_NAMES = ["Ashen Reach", "Morrowfield", "Blackwater"];
const DEMO_OCCUPATIONS = ["farmer", "hunter", "builder", "gatherer", "trader", "healer", "guard", "scribe"];
const DEMO_IDEOLOGIES = ["communalism", "tradition", "liberty", "militarism", "spiritualism"];

function createDemoWorld(): { state: WorldState; agents: Agent[]; metrics: Metrics; history: Metrics[]; events: SimulationEvent[] } {
  const villages: Village[] = DEMO_NAMES.map((name, index) => ({ id: index + 1, name, agents: 0, food: 450 + index * 90, wood: 320 + index * 60, stone: 180 + index * 45 }));
  const factions: Faction[] = [
    { id: 1, name: "The Common Hearth", leader_id: 1, members: [], cohesion: 72 },
    { id: 2, name: "Iron Covenant", leader_id: 2, members: [], cohesion: 61 },
    { id: 3, name: "The Unbound", leader_id: 3, members: [], cohesion: 48 },
  ];
  const agents: Agent[] = Array.from({ length: 90 }, (_, index) => {
    const village = villages[index % villages.length];
    const faction = factions[index % 5 === 0 ? 2 : index % 3];
    const agent: Agent = {
      id: index + 1, age: 18 + (index * 7 % 52), health: 58 + (index * 13 % 42),
      hunger: 8 + (index * 11 % 65), wealth: 5 + (index * 17 % 90), trust: 25 + (index * 9 % 70),
      occupation: DEMO_OCCUPATIONS[index % DEMO_OCCUPATIONS.length], village_id: village.id, village_name: village.name,
      alive: true, fertility: 0.2 + (index % 7) / 10, faction_id: faction.id, faction_name: faction.name,
      ideology: DEMO_IDEOLOGIES[index % DEMO_IDEOLOGIES.length], ideology_commitment: 0.25 + (index % 6) / 10,
    };
    village.agents += 1; faction.members.push(agent.id);
    return agent;
  });
  const state: WorldState = { day: 0, population: agents.length, villages, factions };
  const metrics: Metrics = {
    ...emptyMetrics, population: agents.length, living_population: agents.length,
    average_health: avg(agents.map(a => a.health)), average_hunger: avg(agents.map(a => a.hunger)),
    total_food: villages.reduce((n,v) => n+v.food,0), total_wood: villages.reduce((n,v) => n+v.wood,0),
    total_stone: villages.reduce((n,v) => n+v.stone,0), total_wealth: agents.reduce((n,a) => n+a.wealth,0),
    average_wealth: avg(agents.map(a => a.wealth)), average_trust: avg(agents.map(a => a.trust)),
    faction_count: factions.length, average_faction_cohesion: avg(factions.map(f => f.cohesion)),
    ideology_diversity: 0.78, dominant_ideology_share: 0.28, wealth_gini: 0.31, top_10_wealth_share: 0.29,
  };
  return { state, agents, metrics, history: [metrics], events: [
    { type: "FOUNDING", day: 0, message: "Three settlements emerge from the first gathering." },
    { type: "FACTION_FORMED", day: 0, message: "Competing visions of order take root among the population." },
  ] };
}
function avg(values: number[]) { return values.length ? values.reduce((a,b)=>a+b,0)/values.length : 0; }

function advanceDemo(snapshot: ReturnType<typeof createDemoWorld>, count = 1) {
  let { state, agents, metrics, history, events } = snapshot;
  for (let step = 0; step < count; step++) {
    const day = state.day + 1;
    const living = agents.filter(a => a.alive);
    let births = 0, deaths = 0, conflicts = 0;
    for (const agent of living) {
      agent.age += 1 / 365;
      agent.hunger = Math.max(0, Math.min(100, agent.hunger + 1.8 + (agent.id % 5) * .25));
      agent.health = Math.max(0, Math.min(100, agent.health + (agent.hunger > 72 ? -2.4 : .25) - (agent.age > 68 ? .35 : 0)));
      agent.wealth = Math.max(0, agent.wealth + (agent.occupation === "trader" ? 2.2 : .45) - .2);
      agent.trust = Math.max(0, Math.min(100, agent.trust + (agent.faction_id === 1 ? .12 : -.04)));
      if (agent.health < 12 && day % 3 === 0) { agent.alive = false; deaths++; }
      if (agent.hunger < 30 && agent.health > 70 && agent.age > 18 && agent.age < 38 && (agent.id + day) % 97 === 0) births++;
    }
    if (births) {
      for (let i=0;i<births;i++) {
        const id = agents.length + 1, village = state.villages[id % state.villages.length], faction = state.factions[id % state.factions.length];
        agents.push({ id, age: 0, health: 100, hunger: 12, wealth: 1, trust: 50, occupation: "gatherer", village_id: village.id, village_name: village.name, alive: true, fertility: .8, faction_id: faction.id, faction_name: faction.name, ideology: DEMO_IDEOLOGIES[id % DEMO_IDEOLOGIES.length], ideology_commitment: .4 });
        village.agents++; faction.members.push(id);
      }
    }
    const alive = agents.filter(a=>a.alive);
    state.villages = state.villages.map(v => ({ ...v, agents: alive.filter(a=>a.village_id===v.id).length, food: Math.max(0,v.food + v.agents*.7 - v.agents*1.25), wood: v.wood + v.agents*.18, stone: v.stone + v.agents*.08 }));
    if (day % 7 === 0) { conflicts = 1; events = [{ type: "SOCIAL_CONFLICT", day, message: "A dispute over shared stores strains relations between settlements." }, ...events].slice(0,30); }
    if (day % 11 === 0) events = [{ type: "TRADE_CARAVAN", day, message: "A caravan moves tools and food along the settlement corridor." }, ...events].slice(0,30);
    if (deaths) events = [{ type: "DEATHS", day, message: deaths + " inhabitants died after a period of scarcity." }, ...events].slice(0,30);
    metrics = {
      ...metrics, day, population: alive.length + births, living_population: alive.length + births,
      average_health: avg(alive.map(a=>a.health)), average_hunger: avg(alive.map(a=>a.hunger)),
      total_food: state.villages.reduce((n,v)=>n+v.food,0), total_wood: state.villages.reduce((n,v)=>n+v.wood,0),
      total_stone: state.villages.reduce((n,v)=>n+v.stone,0), total_wealth: alive.reduce((n,a)=>n+a.wealth,0),
      average_wealth: avg(alive.map(a=>a.wealth)), average_trust: avg(alive.map(a=>a.trust)),
      births: metrics.births + births, deaths: metrics.deaths + deaths, conflicts: metrics.conflicts + conflicts,
      faction_count: state.factions.length, average_faction_cohesion: avg(state.factions.map(f=>f.cohesion)),
      trade_volume: metrics.trade_volume + 12 + day % 9, wealth_gini: Math.min(.8, metrics.wealth_gini + .0015),
      top_10_wealth_share: Math.min(.8, metrics.top_10_wealth_share + .001), political_pressure: Math.min(1, metrics.political_pressure + (day%7===0?.025:.004)),
      environmental_disasters: metrics.environmental_disasters + (day%29===0?1:0), wars: metrics.wars + (day%37===0?1:0),
      war_casualties: metrics.war_casualties + (day%37===0?3:0), ideology_shifts: metrics.ideology_shifts + (day%13===0?1:0),
    };
    state = { ...state, day, population: alive.length + births };
    history = [...history, metrics].slice(-365);
  }
  const analysis: Analysis = {
    start_day: history[0]?.day ?? 0, end_day: state.day, days: history.length,
    population: { start: history[0]?.living_population ?? 0, end: metrics.living_population, change: metrics.living_population-(history[0]?.living_population ?? 0) },
    wealth: { start: history[0]?.total_wealth ?? 0, end: metrics.total_wealth, change: metrics.total_wealth-(history[0]?.total_wealth ?? 0) },
    food: { start: history[0]?.total_food ?? 0, end: metrics.total_food, change: metrics.total_food-(history[0]?.total_food ?? 0) },
    trust: { start: history[0]?.average_trust ?? 0, end: metrics.average_trust, change: metrics.average_trust-(history[0]?.average_trust ?? 0) },
    wealth_gini: { start: history[0]?.wealth_gini ?? 0, end: metrics.wealth_gini, change: metrics.wealth_gini-(history[0]?.wealth_gini ?? 0) },
    events: { births: metrics.births, deaths: metrics.deaths, migrations: metrics.migrations, conflicts: metrics.conflicts, disasters: metrics.environmental_disasters, wars: metrics.wars, war_casualties: metrics.war_casualties, epidemics: metrics.epidemics, epidemic_infections: metrics.epidemic_infections, epidemic_deaths: metrics.epidemic_deaths, ideology_shifts: metrics.ideology_shifts },
    peaks: { population: { day: state.day, value: metrics.living_population } }, troughs: { population: { day: state.day, value: metrics.living_population } },
  };
  return { state, agents, metrics, history, events, analysis };
}


function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  const [state, setState] = useState(emptyState);
  const [metrics, setMetrics] = useState(emptyMetrics);
  const [history, setHistory] = useState<Metrics[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
  const [agentQuery, setAgentQuery] = useState("");
  const [selectedVillageId, setSelectedVillageId] = useState<number | null>(null);
  const [events, setEvents] = useState<SimulationEvent[]>([]);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [days, setDays] = useState(10);

  const [demoReady, setDemoReady] = useState(false);



  useEffect(() => {
    const saved = localStorage.getItem(DEMO_STORAGE_KEY);
    if (saved) {
      try {
        const data = JSON.parse(saved);
        setState(data.state ?? emptyState); setAgents(data.agents ?? []); setMetrics(data.metrics ?? emptyMetrics);
        setHistory(data.history ?? []); setEvents(data.events ?? []); setAnalysis(data.analysis ?? null);
      } catch { localStorage.removeItem(DEMO_STORAGE_KEY); }
    }
    setUser({ subject: "local-demo", email: null, name: "Local Demo", picture: null, demo: true });
    setDemoReady(true); setAuthChecked(true);
  }, []);

  useEffect(() => {
    if (!demoReady) return;
    localStorage.setItem(DEMO_STORAGE_KEY, JSON.stringify({ state, agents, metrics, history, events, analysis }));
  }, [analysis, agents, demoReady, events, history, metrics, state]);

  const start = () => {
    const demo = createDemoWorld();
    setState(demo.state); setAgents(demo.agents); setMetrics(demo.metrics); setHistory(demo.history);
    setEvents(demo.events); setAnalysis(null); setSelectedAgentId(null); setSelectedVillageId(null); setAgentQuery("");
  };

  const tickDemo = (count = 1) => {
    if (!state.population) { start(); return; }
    const next = advanceDemo({ state, agents, metrics, history, events }, Math.min(365, Math.max(1, count)));
    setState(next.state); setAgents(next.agents); setMetrics(next.metrics); setHistory(next.history);
    setEvents(next.events); setAnalysis(next.analysis);
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

  if (!authChecked) return <main className="auth-shell"><section className="panel auth-card"><span className="eyebrow">CIVITAS</span><h1>Loading...</h1></section></main>;
  if (!user) return null;

  return (
    <main className="app-shell">
      <header className="topbar">
        <div><p className="eyebrow">AGENT-BASED CIVILIZATION SIMULATOR</p><h1>CIVITAS</h1>{user.name && <span className="muted">LOCAL DEMO · Data stored in this browser</span>}</div>
        <div className="status"><span className="status-dot online" />Standalone local simulation</div>
      </header>

      <section className="controls panel">
        <div><span className="label">SIMULATION DAY</span><strong>{state.day}</strong></div>
        <div className="control-actions">
          <button onClick={start}>New Simulation</button>
          <button onClick={() => tickDemo(1)}>Tick +1</button>
          <input aria-label="Days to run" type="number" min="0" value={days} onChange={e => setDays(Math.max(0, Number(e.target.value) || 0))} />
          <button onClick={() => tickDemo(days)}>Run</button>
        </div>
      </section>

      <section className="metrics-grid">
        <Metric label="Population" value={metrics.living_population} />
        <Metric label="Food" value={metrics.total_food.toFixed(1)} />
        <Metric label="Wood" value={metrics.total_wood.toFixed(1)} />
        <Metric label="Stone" value={metrics.total_stone.toFixed(1)} />
        <Metric label="Trust" value={metrics.average_trust.toFixed(1)} />
        <Metric label="Wealth Gini" value={metrics.wealth_gini.toFixed(2)} />
        <Metric label="Top 10% Wealth" value={(metrics.top_10_wealth_share * 100).toFixed(1) + "%"} />
        <Metric label="Factions" value={metrics.faction_count} />
        <Metric label="Political Pressure" value={(metrics.political_pressure * 100).toFixed(1) + "%"} />
        <Metric label="Disasters" value={metrics.environmental_disasters} />
            <Metric label="Wars" value={metrics.wars} />
        <Metric label="Ideology Diversity" value={(metrics.ideology_diversity * 100).toFixed(0) + "%"} />
        <Metric label="Dominant Ideology" value={(metrics.dominant_ideology_share * 100).toFixed(0) + "%"} />
        <Metric label="Ideology Shifts" value={metrics.ideology_shifts} />
            <Metric label="War Casualties" value={metrics.war_casualties} />
        <Metric label="Epidemics" value={metrics.epidemics} />
        <Metric label="Infections" value={metrics.epidemic_infections} />
        <Metric label="Epidemic Deaths" value={metrics.epidemic_deaths} />
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
            <LineChart title="Wealth Gini" points={history.map(m => ({ day: m.day, value: m.wealth_gini }))} />
            <LineChart title="Top 10% Wealth Share" points={history.map(m => ({ day: m.day, value: m.top_10_wealth_share * 100 }))} />
            <LineChart title="Political Pressure" points={history.map(m => ({ day: m.day, value: m.political_pressure * 100 }))} />
            <LineChart title="Environmental Disasters" points={history.map(m => ({ day: m.day, value: m.environmental_disasters }))} />
        <LineChart title="Wars" points={history.map(m => ({ day: m.day, value: m.wars }))} />
        <LineChart title="War Casualties" points={history.map(m => ({ day: m.day, value: m.war_casualties }))} />
            <LineChart title="Epidemics" points={history.map(m => ({ day: m.day, value: m.epidemics }))} />
            <LineChart title="Epidemic Infections" points={history.map(m => ({ day: m.day, value: m.epidemic_infections }))} />
            <LineChart title="Epidemic Deaths" points={history.map(m => ({ day: m.day, value: m.epidemic_deaths }))} />
            <LineChart title="Ideology Diversity" points={history.map(m => ({ day: m.day, value: m.ideology_diversity * 100 }))} />
            <LineChart title="Dominant Ideology Share" points={history.map(m => ({ day: m.day, value: m.dominant_ideology_share * 100 }))} />
            <LineChart title="Ideology Shifts" points={history.map(m => ({ day: m.day, value: m.ideology_shifts }))} />
          </div>
        </article>

        <article className="panel wide">
          <div className="section-heading"><div><span className="label">ANALYSIS</span><h2>Historical Summary</h2></div><span className="muted">{analysis?.start_day ?? "—"} → {analysis?.end_day ?? "—"}</span></div>
          {!analysis || analysis.days === 0 ? <p className="empty">Run the simulation to build a historical analysis window.</p> : <div className="detail-grid analysis-grid">
            <Detail label="Population Change" value={formatSigned(analysis.population.change)} />
            <Detail label="Wealth Change" value={formatSigned(analysis.wealth.change, 1)} />
            <Detail label="Food Change" value={formatSigned(analysis.food.change, 1)} />
            <Detail label="Trust Change" value={formatSigned(analysis.trust.change, 1)} />
            <Detail label="Gini Change" value={formatSigned(analysis.wealth_gini.change, 3)} />
            <Detail label="Births" value={String(analysis.events.births)} />
            <Detail label="Deaths" value={String(analysis.events.deaths)} />
            <Detail label="Migrations" value={String(analysis.events.migrations)} />
            <Detail label="Wars" value={String(analysis.events.wars)} />
            <Detail label="War Casualties" value={String(analysis.events.war_casualties)} />
            <Detail label="Epidemics" value={String(analysis.events.epidemics)} />
            <Detail label="Epidemic Deaths" value={String(analysis.events.epidemic_deaths)} />
            <Detail label="Ideology Shifts" value={String(analysis.events.ideology_shifts)} />
            <Detail label="Peak Population Day" value={String(analysis.peaks.population?.day ?? "—")} />
            <Detail label="Lowest Population Day" value={String(analysis.troughs.population?.day ?? "—")} />
          </div>}
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
                <Detail label="Age" value={selectedAgent.age.toFixed(1)} /><Detail label="Health" value={selectedAgent.health.toFixed(1)} /><Detail label="Hunger" value={selectedAgent.hunger.toFixed(1)} /><Detail label="Wealth" value={selectedAgent.wealth.toFixed(1)} /><Detail label="Trust" value={selectedAgent.trust.toFixed(1)} /><Detail label="Fertility" value={selectedAgent.fertility.toFixed(2)} /><Detail label="Village" value={selectedAgent.village_name} /><Detail label="Faction" value={selectedAgent.faction_name ?? "None"} /><Detail label="Ideology" value={selectedAgent.ideology} /><Detail label="Commitment" value={(selectedAgent.ideology_commitment * 100).toFixed(0) + "%"} />
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

function formatSigned(value: number, digits = 0) {
  const formatted = value.toFixed(digits);
  return value > 0 ? "+" + formatted : formatted;
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
    <div className="world-map-caption"><span><i className="legend-dot settlement" />Settlement</span><span><i className="legend-dot agent" />Agent</span><span><i className="legend-line" />Inter-village corridor</span></div>
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

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.db_models import AgentRecord, EventRecord, MetricRecord, SimulationRecord, User
from backend.repository import SimulationRepository
from simulation.engine import Simulation


def test_repository_persists_user_simulation_state():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    from backend.database import Base
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        repo = SimulationRepository(session)
        user = repo.upsert_user("google-123", "user@example.com", "Test User", None)
        sim = Simulation(seed=42, population=20)
        record = repo.create_simulation(user.id, sim, "Persistence Test")
        sim.run(3)
        repo.save_state(record.id, sim)

        stored = session.get(SimulationRecord, record.id)
        assert stored is not None
        assert stored.current_day == 3
        assert stored.user_id == user.id
        assert session.scalar(select(AgentRecord).where(AgentRecord.simulation_id == record.id)) is not None
        assert session.scalar(select(MetricRecord).where(MetricRecord.simulation_id == record.id, MetricRecord.day == 3)) is not None
        assert session.scalar(select(EventRecord).where(EventRecord.simulation_id == record.id)) is not None


def test_simulation_ownership_is_enforced():
    engine = create_engine("sqlite:///:memory:")
    from backend.database import Base
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        repo = SimulationRepository(session)
        owner = repo.upsert_user("owner", "owner@example.com", "Owner", None)
        other = repo.upsert_user("other", "other@example.com", "Other", None)
        record = repo.create_simulation(owner.id, Simulation(seed=1, population=5), "Private")
        assert repo.get_simulation(owner.id, record.id) is not None
        assert repo.get_simulation(other.id, record.id) is None

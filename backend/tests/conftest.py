import pytest

from app.database.session import SessionLocal


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def _reset_sse_starlette_app_status():
    """sse-starlette caches its shutdown-signal `anyio.Event` on a class
    attribute the first time an SSE response runs, bound to whatever event
    loop created it. Each `TestClient` spins up its own event loop, so
    reusing that cached event across tests raises "bound to a different
    event loop". Resetting it before every test forces sse-starlette to
    lazily recreate it on the current loop instead."""
    from sse_starlette.sse import AppStatus

    AppStatus.should_exit_event = None

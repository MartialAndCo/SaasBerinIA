import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.system_settings import Base, SystemIntegrations, SystemScheduling
from app.services.system_settings_service import SystemSettingsService
from app.database.session import SessionLocal
from fastapi.testclient import TestClient
from app.main import app

# Use an in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override get_db dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Monkey patch the get_db dependency in the app
from app.api import deps
deps.get_db = override_get_db

@pytest.fixture(scope="function")
def db_session():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new database session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        # Close the session and drop all tables
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client():
    return TestClient(app)

def test_create_system_integrations(db_session):
    """Test creating and updating system integrations settings"""
    service = SystemSettingsService(db_session)
    
    # Update integrations
    integrations = service.update_integrations(
        twilio_api_key="test_twilio_key",
        twilio_account_sid="test_account_sid",
        twilio_auth_token="test_auth_token",
        twilio_integration_active=True,
        mailgun_api_key="test_mailgun_key",
        mailgun_domain="test.domain.com",
        mailgun_region="US",
        mailgun_integration_active=True
    )
    
    # Verify the settings were saved
    assert integrations.twilio_api_key == "test_twilio_key"
    assert integrations.twilio_account_sid == "test_account_sid"
    assert integrations.twilio_integration_active is True
    assert integrations.mailgun_domain == "test.domain.com"
    assert integrations.mailgun_region.value == "US"

def test_create_system_scheduling(db_session):
    """Test creating and updating system scheduling settings"""
    service = SystemSettingsService(db_session)
    
    # Update scheduling
    scheduling = service.update_scheduling(
        agent_group_frequency="DAILY",
        agent_group_time="09:00",
        agent_group_active=True,
        campaign_launch_time="10:00",
        leads_per_campaign=75,
        max_simultaneous_campaigns=3,
        daily_report_active=True,
        daily_report_time="18:00",
        report_channel_slack=True,
        report_channel_email=True,
        knowledge_trigger_frequency="WEEKLY",
        max_learning_delay=14
    )
    
    # Verify the settings were saved
    assert scheduling.agent_group_frequency.value == "DAILY"
    assert scheduling.agent_group_time == "09:00"
    assert scheduling.agent_group_active is True
    assert scheduling.leads_per_campaign == 75
    assert scheduling.daily_report_active is True
    assert scheduling.report_channel_slack is True
    assert scheduling.knowledge_trigger_frequency.value == "WEEKLY"

def test_api_update_integrations(client, db_session):
    """Test API endpoint for updating integration settings"""
    # First, clear any existing settings
    service = SystemSettingsService(db_session)
    service.update_integrations()
    
    integration_data = {
        "twilio_api_key": "get_test_twilio_key",
        "mailgun_domain": "get.test.domain.com"
    }
    
    response = client.post("/api/system-settings/integrations", json=integration_data)
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["data"]["twilio_api_key"] == "get_test_twilio_key"
    assert response.json()["data"]["mailgun_domain"] == "get.test.domain.com"

def test_api_get_integrations(client, db_session):
    """Test API endpoint for retrieving integration settings"""
    # First, set some test data
    service = SystemSettingsService(db_session)
    service.update_integrations(
        twilio_api_key="get_test_twilio_key",
        mailgun_domain="get.test.domain.com"
    )
    
    response = client.get("/api/system-settings/integrations")
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["data"]["twilio_api_key"] == "get_test_twilio_key"
    assert response.json()["data"]["mailgun_domain"] == "get.test.domain.com"

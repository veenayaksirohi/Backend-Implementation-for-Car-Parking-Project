# test_app.py
import pytest
import os
import jwt
from datetime import datetime, timedelta
from app import create_app, db
from app import ParkingLotDetails, Floor, Row, Slot, User, ParkingSession
import json
import urllib.parse
import time

# Set testing mode environment variable
os.environ['TESTING'] = 'True'

# JWT Secret for testing
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-here')

# Create a test client fixture
@pytest.fixture
def client():
    # Get database connection details from environment variables or use defaults
    DB_USER = "postgres" 
    DB_PASSWORD = urllib.parse.quote_plus("root")
    DB_HOST = "localhost"
    DB_PORT = 5432
    DB_NAME = "parking_test"
    
    # Configure test app
    app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })

    # Prepare test database
    with app.app_context():
        # Cleanup any existing tables
        db.reflect()
        db.drop_all()
        
        # Create all tables with the existing models
        db.create_all()
        
        # Create test data
        # Create a test parking lot
        test_parking = ParkingLotDetails(
            parkinglot_id=1,
            parking_name="Test Parking",
            city="Test City",
            landmark="Test Landmark",
            address="Test Address",
            latitude=12.3456,
            longitude=65.4321,
            car_capacity=100,
            available_car_slots=100,
            two_wheeler_capacity=200,
            available_two_wheeler_slots=200
        )
        
        # Create a test floor
        test_floor = Floor(
            parkinglot_id=1,
            floor_id=1,
            floor_name="Ground Floor"
        )
        
        # Create a test row
        test_row = Row(
            parkinglot_id=1,
            floor_id=1,
            row_id=1,
            row_name="A"
        )
        
        # Create a test slot
        test_slot = Slot(
            parkinglot_id=1,
            floor_id=1,
            row_id=1,
            slot_id=1,
            slot_name="A1",
            status=0  # Available
        )
        
        # Create a test user
        test_user = User(
            user_name="Test User",
            user_email="test@example.com",
            user_password="password",
            user_phone_no="1234567890"
        )
        
        # Add all test data to session and commit
        db.session.add_all([test_parking, test_floor, test_row, test_slot, test_user])
        db.session.commit()

    # Yield test client
    with app.test_client() as client:
        yield client

    # Teardown - drop all tables after tests
    with app.app_context():
        db.drop_all()
        db.session.remove()

# Helper function to generate JWT token for testing protected routes
def get_auth_token(user_id=1):
    token_payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(token_payload, JWT_SECRET_KEY, algorithm='HS256')

# === Route Tests ===

def test_home_page(client):
    """Test the root endpoint returns valid HTML content"""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Car Parking System API" in response.data

def test_register_user_success(client):
    """Test user registration"""
    data = {
        "user_name": "New User",
        "user_email": "new@example.com",
        "user_password": "secret",
        "user_phone_no": "0987654321"
    }
    response = client.post('/register', json=data)
    assert response.status_code == 201
    response_data = json.loads(response.data)
    print(response_data)
    assert "user_id" in response_data
    assert response_data['message'] == "User registered successfully"

def test_register_user_missing_fields(client):
    """Test user registration with missing fields"""
    data = {
        "user_name": "Incomplete User"
    }
    response = client.post('/register', json=data)
    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert "Missing fields" in response_data['error']

def test_register_user_duplicate_email(client):
    """Test duplicate email handling"""
    response = client.post('/register', json={
        "user_name": "Duplicate",
        "user_email": "test@example.com",  # This email already exists
        "user_password": "pass",
        "user_phone_no": "1111111111"
    })
    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert "already registered" in response_data['error']

def test_login_success(client):
    """Test successful login"""
    response = client.post('/login', json={
        "user_email": "test@example.com",
        "user_password": "password"
    })
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert "token" in response_data
    assert response_data['message'] == "Login successful"

def test_login_phone_success(client):
    """Test successful login with phone number"""
    response = client.post('/login', json={
        "user_phone_no": "1234567890",
        "user_password": "password"
    })
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert "token" in response_data

def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post('/login', json={
        "user_email": "test@example.com",
        "user_password": "wrong_password"
    })
    assert response.status_code == 401
    response_data = json.loads(response.data)
    assert "Invalid credentials" in response_data['error']

def test_login_missing_credentials(client):
    """Test login with missing credentials"""
    response = client.post('/login', json={})
    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert "Missing credentials" in response_data['error']

# === Protected Route Tests ===

def test_get_parkinglots_details_with_token(client):
    """Test parking lot details endpoint with auth token"""
    token = get_auth_token()
    headers = {'Authorization': f'Bearer {token}'}
    response = client.get('/parkinglots_details', headers=headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    print(data)
    assert len(data) == 1
    assert data[0]['parking_name'] == "Test Parking"

def test_get_parkinglots_details_no_token(client):
    """Test parking lot details endpoint with no auth token"""
    response = client.get('/parkinglots_details')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert "Authentication token is required" in data['error']

def test_parking_lot_structure_with_token(client):
    """Test hierarchical parking structure with auth token"""
    token = get_auth_token()
    headers = {'Authorization': f'Bearer {token}'}
    response = client.get('/parking_lot_structure', headers=headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data[0]['floor_name'] == "Ground Floor"
    assert len(data[0]['rows']) == 1
    assert len(data[0]['rows'][0]['slots']) == 1

def test_get_users_with_token(client):
    """Test user listing endpoint with auth token"""
    token = get_auth_token()
    headers = {'Authorization': f'Bearer {token}'}
    response = client.get('/users', headers=headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data[0]['user_email'] == "test@example.com"
    assert len(data) == 1

# === Parking Operations Tests ===

def test_park_car_success(client):
    """Test successful car parking"""
    token = get_auth_token()
    headers = {'Authorization': f'Bearer {token}'}
    data = {
        "parking_lot_name": "Test Parking",
        "vehicle_reg_no": "ABC123"
    }
    response = client.post('/park_car', json=data, headers=headers)
    assert response.status_code == 201
    response_data = json.loads(response.data)
    print(response_data)
    assert "ticket_id" in response_data
    assert response_data['assigned_slot']['slot_id'] == 1
    
    # Verify slot status
    with client.application.app_context():
        slot = Slot.query.filter_by(parkinglot_id=1, floor_id=1, row_id=1, slot_id=1).first()
        assert slot.status == 1

def test_park_car_missing_fields(client):
    """Test validation for required fields"""
    token = get_auth_token()
    headers = {'Authorization': f'Bearer {token}'}
    response = client.post('/park_car', json={}, headers=headers)
    assert response.status_code == 400
    assert "Missing required fields" in json.loads(response.data)['error']

def test_park_car_specific_slot(client):
    """Test parking in a specific slot"""
    token = get_auth_token()
    headers = {'Authorization': f'Bearer {token}'}
    data = {
        "parking_lot_name": "Test Parking",
        "vehicle_reg_no": "XYZ789",
        "floor_id": 1,
        "row_id": 1,
        "slot_id": 1
    }
    response = client.post('/park_car', json=data, headers=headers)
    assert response.status_code == 201
    response_data = json.loads(response.data)
    assert response_data['assigned_slot']['slot_id'] == 1

def test_remove_car_success(client):
    """Test complete parking cycle"""
    token = get_auth_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    # Park vehicle
    park_res = client.post('/park_car', json={
        "parking_lot_name": "Test Parking",
        "vehicle_reg_no": "ABC123"
    }, headers=headers)
    ticket_id = json.loads(park_res.data)['ticket_id']
    
    # Remove vehicle
    response = client.delete('/remove_car_by_ticket', json={"ticket_id": ticket_id}, headers=headers)
    assert response.status_code == 200
    
    # Verify slot status
    with client.application.app_context():
        slot = Slot.query.filter_by(parkinglot_id=1, floor_id=1, row_id=1, slot_id=1).first()
        assert slot.status == 0

def test_remove_car_invalid_ticket(client):
    """Test invalid ticket handling"""
    token = get_auth_token()
    headers = {'Authorization': f'Bearer {token}'}
    response = client.delete('/remove_car_by_ticket', json={"ticket_id": "INVALID"}, headers=headers)
    assert response.status_code == 404

# === User Management Tests ===

def test_update_user_success(client):
    """Test user update"""
    token = get_auth_token(user_id=1)
    headers = {'Authorization': f'Bearer {token}'}
    response = client.put('/users/1', json={"user_name": "Updated Name"}, headers=headers)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data['user']['user_name'] == "Updated Name"
    
    with client.application.app_context():
        user = User.query.get(1)
        assert user.user_name == "Updated Name"

def test_update_user_not_own_profile(client):
    """Test updating another user's profile"""
    # Create a second user first
    client.post('/register', json={
        "user_name": "Second User",
        "user_email": "second@example.com",
        "user_password": "pass",
        "user_phone_no": "2222222222"
    })
    
    # Try to update user 2's profile with user 1's token
    token = get_auth_token(user_id=1)
    headers = {'Authorization': f'Bearer {token}'}
    response = client.put('/users/2', json={"user_name": "Hacked Name"}, headers=headers)
    assert response.status_code == 403
    response_data = json.loads(response.data)
    assert "You can only update your own profile" in response_data['error']

def test_update_user_invalid_id(client):
    """Test invalid user update"""
    token = get_auth_token(999)  # Non-existent user ID
    headers = {'Authorization': f'Bearer {token}'}
    response = client.put('/users/999', json={"user_name": "Test"}, headers=headers)
    print(response.data)
    assert response.status_code == 404

def test_update_user_duplicate_email(client):
    """Test duplicate email during update"""
    # Create a second user first
    client.post('/register', json={
        "user_name": "Second User",
        "user_email": "second@example.com",
        "user_password": "pass",
        "user_phone_no": "2222222222"
    })
    
    # Try to update to an existing email
    token = get_auth_token(user_id=1)
    headers = {'Authorization': f'Bearer {token}'}
    response = client.put('/users/1', json={"user_email": "second@example.com"}, headers=headers)
    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert "already in use" in response_data['error']
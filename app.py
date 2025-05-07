import os
import urllib.parse
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Column, Integer, String, ForeignKeyConstraint, text, Computed
from sqlalchemy.orm import relationship
import jwt
from functools import wraps
from dotenv import load_dotenv

# Load environment variables from .env file if it exists (useful for local dev)
load_dotenv()

# Simple JWT configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-here')  # Change in production!
JWT_EXPIRATION_HOURS = 24
# Initialize SQLAlchemy
db = SQLAlchemy()

# MODELS
class ParkingLotDetails(db.Model):
    __tablename__ = 'parkinglots_details'
    parkinglot_id = db.Column(db.Integer, primary_key=True)
    parking_name = db.Column(db.Text)
    city = db.Column(db.Text)
    landmark = db.Column(db.Text)
    address = db.Column(db.Text)
    latitude = db.Column(db.Numeric)
    longitude = db.Column(db.Numeric)
    physical_appearance = db.Column(db.Text)
    parking_ownership = db.Column(db.Text)
    parking_surface = db.Column(db.Text)
    has_cctv = db.Column(db.Text)
    has_boom_barrier = db.Column(db.Text)
    ticket_generated = db.Column(db.Text)
    entry_exit_gates = db.Column(db.Text)
    weekly_off = db.Column(db.Text)
    parking_timing = db.Column(db.Text)
    vehicle_types = db.Column(db.Text)
    car_capacity = db.Column(db.Integer)
    available_car_slots = db.Column(db.Integer)
    two_wheeler_capacity = db.Column(db.Integer)
    available_two_wheeler_slots = db.Column(db.Integer)
    parking_type = db.Column(db.Text)
    payment_modes = db.Column(db.Text)
    car_parking_charge = db.Column(db.Text)
    two_wheeler_parking_charge = db.Column(db.Text)
    allows_prepaid_passes = db.Column(db.Text)
    provides_valet_services = db.Column(db.Text)
    value_added_services = db.Column(db.Text)

class Floor(db.Model):
    __tablename__ = 'floors'
    parkinglot_id = Column(Integer, primary_key=True)
    floor_id = Column(Integer, primary_key=True)
    floor_name = Column(String(50), nullable=False)

    rows = relationship(
        'Row',
        back_populates='floor',
        cascade='all, delete-orphan',
        lazy='select'
    )

class Row(db.Model):
    __tablename__ = 'rows'
    parkinglot_id = Column(Integer, primary_key=True)
    floor_id = Column(Integer, primary_key=True)
    row_id = Column(Integer, primary_key=True)
    row_name = Column(String(50), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ['parkinglot_id', 'floor_id'],
            ['floors.parkinglot_id', 'floors.floor_id']
        ),
    )

    floor = relationship(
        'Floor',
        back_populates='rows',
        lazy='joined'
    )

    slots = relationship(
        'Slot',
        back_populates='row',
        cascade='all, delete-orphan',
        lazy='select'
    )

class Slot(db.Model):
    __tablename__ = 'slots'
    parkinglot_id = Column(Integer, primary_key=True)
    floor_id = Column(Integer, primary_key=True)
    row_id = Column(Integer, primary_key=True)
    slot_id = Column(Integer, primary_key=True)
    slot_name = Column(String(50), nullable=False)
    status = Column(Integer, default=0)  # 0 = available, 1 = occupied
    vehicle_reg_no = Column(String(20))
    ticket_id = Column(String(50))

    __table_args__ = (
        ForeignKeyConstraint(
            ['parkinglot_id', 'floor_id', 'row_id'],
            ['rows.parkinglot_id', 'rows.floor_id', 'rows.row_id']
        ),
    )

    row = relationship(
        'Row',
        back_populates='slots',
        lazy='joined'
    )

class ParkingSession(db.Model):
    __tablename__ = 'parking_sessions'
    ticket_id = db.Column(db.String(50), primary_key=True)
    parkinglot_id = db.Column(db.Integer)
    floor_id = db.Column(db.Integer)
    row_id = db.Column(db.Integer)
    slot_id = db.Column(db.Integer)
    vehicle_reg_no = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    duration_hrs = db.Column(
        db.Numeric,
        Computed(
            text("""
                ROUND(EXTRACT(epoch FROM (end_time - start_time)) / 3600.0, 1)
            """),
            persisted=True
        )
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ['parkinglot_id', 'floor_id', 'row_id', 'slot_id'],
            ['slots.parkinglot_id', 'slots.floor_id', 'slots.row_id', 'slots.slot_id']
        ),
    )

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(100), unique=True, nullable=False)
    user_password = db.Column(db.Text, nullable=False)
    user_phone_no = db.Column(db.String(15), unique=True, nullable=False)
    user_address = db.Column(db.Text)

def create_app(test_config=None):
    app = Flask(__name__)

    if test_config:
        app.config.update(test_config)
    else:
        username = "postgres"
        password = urllib.parse.quote_plus("root")
        host = "localhost"
        port = 5432
        database_name = "parking_database"

        # Set the SQLAlchemy database URI
        app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{username}:{password}@{host}:{port}/{database_name}"
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Simple JWT token verification
    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            
            # Get token from header
            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                if auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
            
            # No token provided
            if not token:
                return jsonify({'error': 'Authentication token is required'}), 401
            
            try:
                # Decode token
                data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
                current_user_id = data['user_id']
            except Exception:
                return jsonify({'error': 'Invalid or expired token'}), 401
                
            return f(current_user_id, *args, **kwargs)
        return decorated

    # ROUTES
    @app.route('/')
    def home():
        return '''
        <h1>Welcome to the Car Parking System API!</h1>
        <p><a href="/parkinglots_details" style="display:inline-block;padding:10px 20px;background-color:#28a745;color:white;text-decoration:none;border-radius:5px;">View Parking Lots Details</a></p>
        <p><a href="/parking_lot_structure" style="display:inline-block;padding:10px 20px;background-color:#007bff;color:white;text-decoration:none;border-radius:5px;">View Parking Lot Structure</a></p>
        
        <p><strong>Auth Endpoints:</strong></p>
        <ul>
            <li><code>/register</code> - Register new user (POST)</li>
            <li><code>/login</code> - Get JWT token (POST)</li>
        </ul>
        
        <p><strong>Protected Endpoints (require JWT):</strong></p>
        <ul>
            <li><code>/parkinglots_details</code> - View parking lots (GET)</li>
            <li><code>/parking_lot_structure</code> - View parking structure (GET)</li>
            <li><code>/park_car</code> - Park a car (POST)</li>
            <li><code>/remove_car_by_ticket</code> - Remove car by ticket (DELETE)</li>
            <li><code>/users</code> - List all users (GET)</li>
            <li><code>/users/&lt;user_id&gt;</code> - Update user profile (PUT)</li>
        </ul>
        
        <p style="color:gray;">Note: For protected endpoints, include header: <code>Authorization: Bearer &lt;your_token&gt;</code></p>
    '''

    # Auth endpoints
    @app.route('/register', methods=['POST'])
    def register():
        data = request.get_json() or {}

        # Check required fields
        required = ['user_name', 'user_email', 'user_password', 'user_phone_no']
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

        # Create new user
        new_user = User(
            user_name=data['user_name'],
            user_email=data['user_email'],
            user_password=data['user_password'],  # In production, should hash this password
            user_phone_no=data['user_phone_no'],
            user_address=data.get('user_address')
        )

        try:
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({'error': 'Email or phone number already registered'}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

        return jsonify({
            'message': 'User registered successfully',
            'user_id': new_user.user_id
        }), 201

    @app.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        
        # Check credentials
        if not data or 'user_password' not in data:
            return jsonify({'error': 'Missing credentials'}), 400
        
        # Find user by email or phone
        user = None
        if 'user_email' in data:
            user = User.query.filter_by(user_email=data['user_email']).first()
        elif 'user_phone_no' in data:
            user = User.query.filter_by(user_phone_no=data['user_phone_no']).first()
            
        # Validate password
        if not user or user.user_password != data['user_password']:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate token
        token_payload = {
            'user_id': user.user_id,
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        token = jwt.encode(token_payload, JWT_SECRET_KEY, algorithm='HS256')
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user_id': user.user_id
        }), 200

    # Protected endpoints
    @app.route('/parkinglots_details', methods=['GET'])
    @token_required
    def get_parkinglots_details(current_user_id):
        try:
            entries = ParkingLotDetails.query.all()
            result = []
            for entry in entries:
                result.append({
                    'parkinglot_id': entry.parkinglot_id,
                    'parking_name': entry.parking_name,
                    'city': entry.city,
                    'landmark': entry.landmark,
                    'address': entry.address,
                    # Add other fields as needed
                })
            return jsonify(result), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/parking_lot_structure', methods=['GET'])
    @token_required
    def display_parking_lot_structure(current_user_id):
        try:
            floors = Floor.query.all()
            result = []
            for floor in floors:
                floor_data = {
                    'floor_id': floor.floor_id,
                    'floor_name': floor.floor_name,
                    'rows': []
                }
                for row in floor.rows:
                    row_data = {
                        'row_id': row.row_id,
                        'row_name': row.row_name,
                        'slots': []
                    }
                    for slot in row.slots:
                        slot_data = {
                            'slot_id': slot.slot_id,
                            'slot_name': slot.slot_name,
                            'status': slot.status,
                            'vehicle_reg_no': slot.vehicle_reg_no,
                            'ticket_id': slot.ticket_id
                        }
                        row_data['slots'].append(slot_data)
                    floor_data['rows'].append(row_data)
                result.append(floor_data)
            return jsonify(result), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/users', methods=['GET'])
    @token_required
    def get_users(current_user_id):
        try:
            users = User.query.all()
            return jsonify([
                {
                    'user_id': user.user_id,
                    'user_name': user.user_name,
                    'user_email': user.user_email,
                    'user_phone_no': user.user_phone_no,
                    'user_address': user.user_address
                } for user in users
            ]), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/park_car', methods=['POST'])
    @token_required
    def park_car(current_user_id):
        data = request.get_json()
        parking_lot_name = data.get('parking_lot_name')
        vehicle_reg_no = data.get('vehicle_reg_no')
        floor_id = data.get('floor_id')
        row_id = data.get('row_id')
        slot_id = data.get('slot_id')

        # Get user ID from token
        user_id = current_user_id

        # Required fields check
        if not parking_lot_name or not vehicle_reg_no:
            return jsonify({'error': 'Missing required fields'}), 400

        # Find parking lot
        parking_lot = ParkingLotDetails.query.filter_by(
            parking_name=parking_lot_name
        ).first()
        if not parking_lot:
            return jsonify({'error': 'Parking lot not found'}), 404

        slot = None

        # Try specific slot if provided
        if floor_id is not None and row_id is not None and slot_id is not None:
            slot = Slot.query.filter_by(
                parkinglot_id=parking_lot.parkinglot_id,
                floor_id=floor_id,
                row_id=row_id,
                slot_id=slot_id
            ).first()
            if not slot:
                return jsonify({'error': 'Specified slot not found'}), 404
            if slot.status != 0:  # 0 == available
                return jsonify({'error': 'Specified slot is not available'}), 400

        # Find first available slot
        if slot is None:
            slot = Slot.query.filter_by(
                parkinglot_id=parking_lot.parkinglot_id,
                status=0
            ).order_by(
                Slot.floor_id,
                Slot.row_id,
                Slot.slot_id
            ).first()
            if not slot:
                return jsonify({'error': 'No available slots in the parking lot'}), 400

        # Generate ticket & update slot
        ticket_id = f"TKT-{slot.slot_id}-{int(datetime.utcnow().timestamp())}"
        slot.status = 1  # mark occupied
        slot.vehicle_reg_no = vehicle_reg_no
        slot.ticket_id = ticket_id

        # Record the parking session
        session = ParkingSession(
            ticket_id=ticket_id,
            parkinglot_id=slot.parkinglot_id,
            floor_id=slot.floor_id,
            row_id=slot.row_id,
            slot_id=slot.slot_id,
            vehicle_reg_no=vehicle_reg_no,
            user_id=user_id,
            start_time=datetime.utcnow()
        )
        db.session.add(session)
        db.session.commit()

        return jsonify({
            'message': 'Car parked successfully',
            'ticket_id': ticket_id,
            'assigned_slot': {
                'floor_id': slot.floor_id,
                'row_id': slot.row_id,  # Fixed bug: was using row.row_id
                'slot_id': slot.slot_id
            }
        }), 201

    @app.route('/remove_car_by_ticket', methods=['DELETE'])
    @token_required
    def remove_car_by_ticket(current_user_id):
        data = request.get_json()
        ticket_id = data.get('ticket_id')

        if not ticket_id:
            return jsonify({'error': 'Missing ticket_id'}), 400

        # Find the parking session
        session = ParkingSession.query.get(ticket_id)
        if not session:
            return jsonify({'error': 'Parking session not found'}), 404

        # Find the slot
        slot = Slot.query.filter_by(
            parkinglot_id=session.parkinglot_id,
            floor_id=session.floor_id,
            row_id=session.row_id,
            slot_id=session.slot_id
        ).first()
        if not slot:
            return jsonify({'error': 'Slot for this ticket not found'}), 404

        # Mark slot as available and clear fields
        slot.status = 0   # 0 = available
        slot.vehicle_reg_no = None
        slot.ticket_id = None

        # Close the session
        session.end_time = datetime.utcnow()

        # Commit changes
        db.session.commit()

        return jsonify({'message': 'Car removed successfully'}), 200

    @app.route('/users/<int:user_id>', methods=['PUT'])
    @token_required
    def update_user(current_user_id, user_id):
        # Only allow users to update their own profile
        if int(current_user_id) != user_id:
            return jsonify({'error': 'You can only update your own profile'}), 403
            
        # Load the user
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Get update data
        data = request.get_json() or {}

        # Update fields
        if 'user_name' in data:
            user.user_name = data['user_name']
        if 'user_email' in data:
            user.user_email = data['user_email']
        if 'user_password' in data:
            user.user_password = data['user_password']
        if 'user_phone_no' in data:
            user.user_phone_no = data['user_phone_no']
        if 'user_address' in data:
            user.user_address = data['user_address']

        # Commit changes
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({'error': 'Email or phone number already in use'}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

        return jsonify({
            'message': 'User updated successfully',
            'user': {
                'user_id': user.user_id,
                'user_name': user.user_name,
                'user_email': user.user_email,
                'user_phone_no': user.user_phone_no,
                'user_address': user.user_address
            }
        }), 200

    # Create all tables if they don't exist
    with app.app_context():
        db.create_all()

    return app
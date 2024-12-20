import pytest
from app import app, db, Admin, Client
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create test admin user
            admin = Admin(
                username='test_admin',
                password=generate_password_hash('test123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
        yield client
        
        with app.app_context():
            db.drop_all()

def test_login_page(client):
    """Test that login page loads correctly"""
    rv = client.get('/login')
    assert rv.status_code == 200
    assert b'username' in rv.data
    assert b'password' in rv.data

def test_login_success(client):
    """Test successful login"""
    rv = client.post('/login', data={
        'username': 'test_admin',
        'password': 'test123'
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert b'Logout' in rv.data

def test_login_failure(client):
    """Test failed login"""
    rv = client.post('/login', data={
        'username': 'wrong',
        'password': 'wrong'
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert b'password' in rv.data

def test_protected_page_redirect(client):
    """Test that protected pages redirect to login"""
    rv = client.get('/clients', follow_redirects=True)
    assert rv.status_code == 200
    assert b'login' in rv.data.lower()

def test_add_client(client):
    """Test adding a new client"""
    # Login first
    client.post('/login', data={
        'username': 'test_admin',
        'password': 'test123'
    })
    
    # Add test client
    with app.app_context():
        test_client = Client(
            name='Test Client',
            phone='+1234567890',
            telegram_id='123456',
            subscription_balance=10
        )
        db.session.add(test_client)
        db.session.commit()
        
        # Verify client was added
        added_client = Client.query.filter_by(name='Test Client').first()
        assert added_client is not None
        assert added_client.phone == '+1234567890'
        assert added_client.subscription_balance == 10

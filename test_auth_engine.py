"""
Test Suite for Unified Pure Username/Email + Password Authentication & Email OTP System
Validates OTP life-cycle, rate limiting, attempt counters, signed tokens,
password strength, pure username/email authentication, and complete OAuth purge.
"""

import json
from unittest.mock import patch
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User, Role, EmailVerification
from app.services.auth_service import (
    generate_otp,
    hash_otp,
    verify_otp_hash,
    generate_registration_token,
    validate_registration_token,
    request_email_otp,
    verify_email_otp,
    complete_user_registration
)

def run_auth_engine_tests():
    app = create_app('development')
    client = app.test_client()
    
    results = []
    def log(test_name, passed, details=""):
        symbol = "✅" if passed else "❌"
        results.append((symbol, test_name, details))
        print(f"{symbol} [AUTH_ENGINE] {test_name}: {details}")

    print("\n" + "="*80)
    print("      🔐 STARTING COMPREHENSIVE AUTH ENGINE SECURITY VERIFICATION")
    print("="*80 + "\n")

    with app.app_context():
        # Ensure clean state for test email
        test_email = "test.scholar@university.edu"
        existing_test_user = User.query.filter_by(email=test_email).first()
        if existing_test_user:
            db.session.delete(existing_test_user)
        EmailVerification.query.filter_by(email=test_email).delete()
        db.session.commit()

        app.config['TESTING'] = True
        app.config['MAIL_SUPPRESS_SEND'] = True
        
        # Ensure seeded admin is marked verified
        admin_u = User.query.filter_by(email='admin@university.edu').first()
        if admin_u:
            admin_u.is_verified = True
            db.session.commit()

        # -----------------------------------------------------------------
        # 1. CRYPTOGRAPHIC & TOKEN PRIMITIVES
        # -----------------------------------------------------------------
        otp = generate_otp()
        is_6_digits = len(otp) == 6 and otp.isdigit()
        log("OTP Generation", is_6_digits, f"Generated 6-digit numeric OTP: {otp}")

        secret = app.config['SECRET_KEY']
        h1 = hash_otp(secret, otp)
        valid_hash_check = verify_otp_hash(secret, otp, h1)
        invalid_hash_check = not verify_otp_hash(secret, "000000", h1)
        log("HMAC-SHA256 OTP Hashing", valid_hash_check and invalid_hash_check, "Hash matches authentic OTP and rejects mismatched OTP")

        token = generate_registration_token(test_email, secret)
        verified_email = validate_registration_token(token, secret)
        log("Timed Signed Token Verification", verified_email == test_email, f"Verified email from token: {verified_email}")

        tampered_token = token + "xyz"
        tampered_email = validate_registration_token(tampered_token, secret)
        log("Tampered Token Rejection", tampered_email is None, "Rejected modified token signature")

        # -----------------------------------------------------------------
        # 2. REQUEST OTP ENDPOINT & RATE LIMITING
        # -----------------------------------------------------------------
        # Missing email
        res = client.post('/auth/register/request-otp', json={})
        log("Request OTP - Missing Email Check", res.status_code == 400, f"Returned status {res.status_code}")

        # Invalid email format
        res = client.post('/auth/register/request-otp', json={'email': 'invalid-email-format'})
        log("Request OTP - Invalid Format Check", res.status_code == 400, f"Returned status {res.status_code}")

        # Existing user email (admin@university.edu)
        res = client.post('/auth/register/request-otp', json={'email': 'admin@university.edu'})
        log("Request OTP - Duplicate Account Check", res.status_code == 400 and b"already" in res.data, "Blocked OTP for existing user")

        # Valid OTP Request 1 (Zero-Mock Security: dev_otp must NOT be exposed)
        with patch('app.services.auth_service.generate_otp', return_value='654321'):
            res1 = client.post('/auth/register/request-otp', json={'email': test_email})
        data1 = json.loads(res1.data)
        no_dev_otp = 'dev_otp' not in data1
        log("Request OTP - Zero-Mock Safe Submission", res1.status_code == 200 and no_dev_otp, "OTP successfully dispatched without exposing code in JSON")

        # Valid OTP Request 2 & 3
        res2 = client.post('/auth/register/request-otp', json={'email': test_email})
        res3 = client.post('/auth/register/request-otp', json={'email': test_email})
        log("Request OTP - Repeat Allowed Within Limit", res2.status_code == 200 and res3.status_code == 200, "Requests 2 and 3 succeeded")

        # Request 4 -> should trigger Rate Limiting (max 3 per 10 mins)
        res4 = client.post('/auth/register/request-otp', json={'email': test_email})
        log("Request OTP - 10-Minute Rate Limit Enforced", res4.status_code == 429, f"Status 429 Too Many Requests received: {res4.data.decode()[:60]}...")

        # -----------------------------------------------------------------
        # 3. VERIFY OTP ENDPOINT & ATTEMPT LOCKOUT
        # -----------------------------------------------------------------
        # Test wrong OTP increments attempt counter
        res_wrong = client.post('/auth/register/verify-otp', json={'email': test_email, 'otp': '999999'})
        log("Verify OTP - Wrong Code", res_wrong.status_code == 400 and b"Invalid" in res_wrong.data, "Rejected incorrect OTP")

        # Fast forward 4 more failed attempts to reach max 5
        client.post('/auth/register/verify-otp', json={'email': test_email, 'otp': '999998'})
        client.post('/auth/register/verify-otp', json={'email': test_email, 'otp': '999997'})
        client.post('/auth/register/verify-otp', json={'email': test_email, 'otp': '999996'})
        res_locked = client.post('/auth/register/verify-otp', json={'email': test_email, 'otp': '999995'})
        log("Verify OTP - Max 5 Attempts Lockout", res_locked.status_code == 400 and (b"Too many failed" in res_locked.data or b"invalidated" in res_locked.data), "Account blocked after 5 failed attempts")

        # Reset verification record for testing valid verification
        EmailVerification.query.filter_by(email=test_email).delete()
        db.session.commit()
        
        # Request fresh OTP with known patched code
        with patch('app.services.auth_service.generate_otp', return_value='827364'):
            res_fresh = client.post('/auth/register/request-otp', json={'email': test_email})
        data_fresh = json.loads(res_fresh.data)
        log("Request OTP - Fresh Code Zero-Mock Check", 'dev_otp' not in data_fresh, "Verified zero-mock payload for fresh code")

        # Verify fresh OTP correctly
        res_valid_otp = client.post('/auth/register/verify-otp', json={'email': test_email, 'otp': '827364'})
        valid_otp_data = json.loads(res_valid_otp.data)
        reg_token = valid_otp_data.get('token')
        log("Verify OTP - Successful Verification", res_valid_otp.status_code == 200 and reg_token is not None, f"Received registration token of length {len(reg_token) if reg_token else 0}")

        # -----------------------------------------------------------------
        # 4. COMPLETE REGISTRATION & SECURITY DEFENSES
        # -----------------------------------------------------------------
        # Password too short (< 8 chars)
        res_short_pw = client.post('/auth/register/complete', json={
            'email': test_email,
            'token': reg_token,
            'first_name': 'Test',
            'last_name': 'Scholar',
            'password': 'short',
            'confirm_password': 'short',
            'role_name': 'student'
        })
        log("Registration - Min 8 Chars Password Enforced", res_short_pw.status_code == 400 and b"8 characters" in res_short_pw.data, "Rejected password under 8 chars")

        # Password mismatch
        res_mismatch = client.post('/auth/register/complete', json={
            'email': test_email,
            'token': reg_token,
            'first_name': 'Test',
            'last_name': 'Scholar',
            'password': 'StrongPassword123',
            'confirm_password': 'DifferentPassword123',
            'role_name': 'student'
        })
        log("Registration - Password Mismatch Check", res_mismatch.status_code == 400 and b"match" in res_mismatch.data, "Rejected non-matching passwords")

        # ROLE SPOOFING DEFENSE: Attempting to register as 'admin'
        res_admin_spoof = client.post('/auth/register/complete', json={
            'email': test_email,
            'token': reg_token,
            'first_name': 'Hacker',
            'last_name': 'Admin',
            'password': 'StrongPassword123',
            'confirm_password': 'StrongPassword123',
            'role_name': 'admin'
        })
        log("Registration - Admin Role Spoofing Blocked", res_admin_spoof.status_code == 403, "Rejected admin registration with 403 Forbidden")

        # Valid Complete Registration as Student
        res_complete = client.post('/auth/register/complete', json={
            'email': test_email,
            'token': reg_token,
            'first_name': 'Aarav',
            'last_name': 'Katiyar',
            'password': 'SecureCapstonePassword2026',
            'confirm_password': 'SecureCapstonePassword2026',
            'role_name': 'student',
            'department': 'Computer Science & Engineering',
            'enrollment_number': '2026BCSE999'
        })
        log("Registration - Successful Complete Setup", res_complete.status_code == 200, "Created verified user and auto-authenticated")

        # Verify user in database
        created_user = User.query.filter_by(email=test_email).first()
        is_verified_in_db = created_user is not None and created_user.is_verified is True and created_user.role.role_name == 'student'
        log("Database User State Verification", is_verified_in_db, f"User {created_user.email if created_user else None} is_verified={created_user.is_verified if created_user else None}")

        # -----------------------------------------------------------------
        # 5. PURE USERNAME / EMAIL + PASSWORD & OAUTH PURGE VERIFICATION
        # -----------------------------------------------------------------
        # Model Schema Verification: google_id and auth_provider purged, username exists, password_hash non-nullable
        has_google_id = hasattr(User, 'google_id')
        has_auth_provider = hasattr(User, 'auth_provider')
        has_username = hasattr(User, 'username')
        pwd_col = User.__table__.columns.get('password_hash')
        is_pwd_non_nullable = pwd_col is not None and not pwd_col.nullable

        schema_clean = not has_google_id and not has_auth_provider and has_username and is_pwd_non_nullable
        log("Model & Schema Sanitization", schema_clean, f"google_id/auth_provider purged={not has_google_id and not has_auth_provider}, username exists={has_username}, password_hash non-nullable={is_pwd_non_nullable}")

        # Verification: Google OAuth Endpoints Completely Purged (404)
        res_g1 = client.get('/auth/google')
        res_g2 = client.get('/auth/google/callback')
        res_g3 = client.get('/auth/google/onboard')
        all_oauth_purged = res_g1.status_code == 404 and res_g2.status_code == 404 and res_g3.status_code == 404
        log("Google OAuth Routes Purged", all_oauth_purged, f"/auth/google ({res_g1.status_code}), callback ({res_g2.status_code}), onboard ({res_g3.status_code}) -> all 404")

        # Logout any active session before testing login endpoints
        client.get('/auth/logout')

        # Pure Username Login (admin / password123)
        res_user_admin = client.post('/auth/login', data={'username': 'admin', 'password': 'password123'}, follow_redirects=False)
        log("Pure Username Login - Admin", res_user_admin.status_code == 302 and '/admin/dashboard' in res_user_admin.headers.get('Location', ''), "Logged in via username 'admin' -> /admin/dashboard")

        # Pure Email Login (admin@university.edu / password123)
        client.get('/auth/logout')
        res_email_admin = client.post('/auth/login', data={'username': 'admin@university.edu', 'password': 'password123'}, follow_redirects=False)
        log("Pure Email Login - Admin", res_email_admin.status_code == 302 and '/admin/dashboard' in res_email_admin.headers.get('Location', ''), "Logged in via email 'admin@university.edu' -> /admin/dashboard")

        # Case-Insensitive Username Login
        client.get('/auth/logout')
        res_case_user = client.post('/auth/login', data={'username': 'ADMIN', 'password': 'password123'}, follow_redirects=False)
        log("Case-Insensitive Identifier Login", res_case_user.status_code == 302 and '/admin/dashboard' in res_case_user.headers.get('Location', ''), "Case-insensitive username 'ADMIN' resolved successfully")

        # Pure Username Login - Faculty (dr.verma)
        client.get('/auth/logout')
        res_user_fac = client.post('/auth/login', data={'username': 'dr.verma', 'password': 'password123'}, follow_redirects=False)
        log("Pure Username Login - Faculty", res_user_fac.status_code == 302 and '/faculty/dashboard' in res_user_fac.headers.get('Location', ''), "Logged in via username 'dr.verma' -> /faculty/dashboard")

        # Pure Username Login - Student (student1)
        client.get('/auth/logout')
        res_user_stu = client.post('/auth/login', data={'username': 'student1', 'password': 'password123'}, follow_redirects=False)
        log("Pure Username Login - Student", res_user_stu.status_code == 302 and '/student/dashboard' in res_user_stu.headers.get('Location', ''), "Logged in via username 'student1' -> /student/dashboard")

        # Incorrect Password Rejection
        client.get('/auth/logout')
        res_wrong_pw = client.post('/auth/login', data={'username': 'admin', 'password': 'wrongpassword999'}, follow_redirects=True)
        log("Incorrect Password Rejection", b"Invalid username/email or password" in res_wrong_pw.data, "Rejected mismatching password with security flash")

        # Non-Existent User Rejection
        client.get('/auth/logout')
        res_no_user = client.post('/auth/login', data={'username': 'ghost_user', 'password': 'password123'}, follow_redirects=True)
        log("Non-Existent Identifier Rejection", b"Invalid username/email or password" in res_no_user.data, "Rejected unknown account")

        # Remember Me Login Submission
        client.get('/auth/logout')
        res_remember = client.post('/auth/login', data={'username': 'admin', 'password': 'password123', 'remember_me': 'true'}, follow_redirects=False)
        log("Remember Me Flag Support", res_remember.status_code == 302, "Accepted remember_me checkbox payload")

        # Clean up created test accounts
        if created_user:
            db.session.delete(created_user)
        EmailVerification.query.filter_by(email=test_email).delete()
        db.session.commit()

    print("\n" + "="*80)
    print("      📊 AUTH ENGINE TEST RESULTS SUMMARY")
    print("="*80)
    all_passed = True
    for sym, name, details in results:
        print(f"{sym} {name:<40} | {details}")
        if sym != "✅":
            all_passed = False
    print("="*80)
    print(f"TOTAL: {len(results)} | STATUS: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}\n")
    return all_passed

if __name__ == '__main__':
    success = run_auth_engine_tests()
    exit(0 if success else 1)

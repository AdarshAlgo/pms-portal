"""
Test Suite for Unified Pure Username/Email + Password Authentication
Validates direct single-step registration, password hashing (PBKDF2/Werkzeug),
medium-strong password enforcement (>=8 chars, letter, number, special char),
uniqueness enforcement, role safety (admin blocking), pure username/email authentication,
complete OAuth purge, OTP route purge, and 1-Click quick-login purge.
"""

from app import create_app
from app.extensions import db
from app.models.user import User, Role
from app.models.project import Department
from app.services.auth_service import register_user, authenticate_user, validate_password_strength

def run_auth_engine_tests():
    app = create_app('development')
    client = app.test_client()
    
    results = []
    def log(test_name, passed, details=""):
        symbol = "✅" if passed else "❌"
        results.append((symbol, test_name, details))
        print(f"{symbol} [AUTH_ENGINE] {test_name}: {details}")

    print("\n" + "="*80)
    print("      🔐 STARTING COMPREHENSIVE PRODUCTION AUTH ENGINE VERIFICATION")
    print("="*80 + "\n")

    with app.app_context():
        # Clean up any leftover test users
        test_emails = [
            "direct.scholar@university.edu",
            "direct.faculty@university.edu",
            "test.scholar@university.edu",
            "duplicate.test@university.edu"
        ]
        test_usernames = [
            "direct_scholar",
            "direct_faculty",
            "duplicate_user",
            "test_user_alpha"
        ]
        for em in test_emails:
            u = User.query.filter_by(email=em).first()
            if u:
                db.session.delete(u)
        for un in test_usernames:
            u = User.query.filter(db.func.lower(User.username) == un).first()
            if u:
                db.session.delete(u)
        db.session.commit()

        app.config['TESTING'] = True

        # -----------------------------------------------------------------
        # 1. MODEL & SCHEMA SANITIZATION (ZERO OTP & ZERO OAUTH)
        # -----------------------------------------------------------------
        import app.models.user as user_module
        has_email_verification = hasattr(user_module, 'EmailVerification')
        has_email_otp = hasattr(user_module, 'EmailOTP')
        no_otp_models = not has_email_verification and not has_email_otp
        log("Purged OTP Models", no_otp_models, f"EmailVerification/EmailOTP in models: {not no_otp_models}")

        has_google_id = hasattr(User, 'google_id')
        has_auth_provider = hasattr(User, 'auth_provider')
        has_username = hasattr(User, 'username')
        has_dept_id = hasattr(User, 'department_id')
        pwd_col = User.__table__.columns.get('password_hash')
        is_pwd_non_nullable = pwd_col is not None and not pwd_col.nullable

        schema_clean = not has_google_id and not has_auth_provider and has_username and is_pwd_non_nullable and has_dept_id
        log("Model & Schema Sanitization", schema_clean, f"OAuth purged, username exists, department_id exists, password_hash non-nullable")

        # -----------------------------------------------------------------
        # 2. COMPLETE PURGE OF OTP & OAUTH & QUICK-LOGIN ENDPOINTS (404)
        # -----------------------------------------------------------------
        res_otp1 = client.post('/auth/register/request-otp', json={'email': 'any@university.edu'})
        res_otp2 = client.post('/auth/register/verify-otp', json={'email': 'any@university.edu', 'otp': '123456'})
        res_otp3 = client.post('/auth/register/complete', json={'email': 'any@university.edu'})
        all_otp_purged = res_otp1.status_code == 404 and res_otp2.status_code == 404 and res_otp3.status_code == 404
        log("OTP Endpoints Purged (404)", all_otp_purged, f"request-otp ({res_otp1.status_code}), verify-otp ({res_otp2.status_code}), complete ({res_otp3.status_code})")

        res_g1 = client.get('/auth/google')
        res_g2 = client.get('/auth/google/callback')
        res_g3 = client.get('/auth/google/onboard')
        all_oauth_purged = res_g1.status_code == 404 and res_g2.status_code == 404 and res_g3.status_code == 404
        log("Google OAuth Endpoints Purged (404)", all_oauth_purged, f"oauth endpoints return 404")

        res_ql_admin = client.get('/auth/quick-login/admin')
        res_ql_faculty = client.get('/auth/quick-login/faculty')
        res_ql_student = client.get('/auth/quick-login/student')
        all_quick_purged = res_ql_admin.status_code == 404 and res_ql_faculty.status_code == 404 and res_ql_student.status_code == 404
        log("1-Click Quick-Login Purged (404)", all_quick_purged, "quick-login routes return 404")

        # -----------------------------------------------------------------
        # 3. DIRECT REGISTRATION VALIDATIONS & PASSWORD POLICY
        # -----------------------------------------------------------------
        # Missing required fields
        res_missing = client.post('/auth/register', data={
            'first_name': '',
            'last_name': '',
            'username': '',
            'email': '',
            'password': '',
            'confirm_password': ''
        })
        log("Direct Register - Required Fields Check", res_missing.status_code in (400, 200) and b"required" in res_missing.data, "Rejected empty fields")

        # Password policy: < 8 chars
        res_short_pw = client.post('/auth/register', data={
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'test_short_pw',
            'email': 'short.pw@university.edu',
            'role': 'student',
            'password': 'short!1',
            'confirm_password': 'short!1'
        })
        log("Password Policy - Min 8 Chars", res_short_pw.status_code in (400, 200) and b"8 characters" in res_short_pw.data, "Rejected password under 8 chars")

        # Password policy: No letter
        res_no_letter = client.post('/auth/register', data={
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'test_no_letter',
            'email': 'no.letter@university.edu',
            'role': 'student',
            'password': '12345678!@#',
            'confirm_password': '12345678!@#'
        })
        log("Password Policy - Requires Letter", res_no_letter.status_code in (400, 200) and b"at least one letter" in res_no_letter.data, "Rejected password without letter")

        # Password policy: No number
        res_no_number = client.post('/auth/register', data={
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'test_no_number',
            'email': 'no.number@university.edu',
            'role': 'student',
            'password': 'ValidPasswordWithoutDigits!',
            'confirm_password': 'ValidPasswordWithoutDigits!'
        })
        log("Password Policy - Requires Number", res_no_number.status_code in (400, 200) and b"at least one number" in res_no_number.data, "Rejected password without number")

        # Password policy: No special symbol
        res_no_sym = client.post('/auth/register', data={
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'test_no_sym',
            'email': 'no.sym@university.edu',
            'role': 'student',
            'password': 'ValidPassword123',
            'confirm_password': 'ValidPassword123'
        })
        log("Password Policy - Requires Special Symbol", res_no_sym.status_code in (400, 200) and b"special character or symbol" in res_no_sym.data, "Rejected password without symbol")

        # Password mismatch
        res_mismatch = client.post('/auth/register', data={
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'test_mismatch',
            'email': 'mismatch@university.edu',
            'role': 'student',
            'password': 'Password123!',
            'confirm_password': 'DifferentPassword123!'
        })
        log("Direct Register - Password Mismatch Check", res_mismatch.status_code in (400, 200) and b"match" in res_mismatch.data, "Rejected mismatching passwords")

        # ROLE SECURITY: Attempting to register as 'admin'
        res_admin = client.post('/auth/register', data={
            'first_name': 'Hacker',
            'last_name': 'Admin',
            'username': 'rogue_admin',
            'email': 'rogue.admin@university.edu',
            'role': 'admin',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!'
        })
        log("Direct Register - Admin Role Spoofing Blocked", res_admin.status_code in (403, 400), "Blocked administrative self-registration")

        # -----------------------------------------------------------------
        # 4. SUCCESSFUL DIRECT SINGLE-STEP REGISTRATION
        # -----------------------------------------------------------------
        res_success = client.post('/auth/register', data={
            'first_name': 'Adarsh',
            'last_name': 'Katiyar',
            'username': 'direct_scholar',
            'email': 'direct.scholar@university.edu',
            'role': 'student',
            'department_id': '1',
            'password': 'StrongPassword2026!',
            'confirm_password': 'StrongPassword2026!',
            'enrollment_number': 'ENR-2026-001'
        }, follow_redirects=False)

        is_redirect_to_login = res_success.status_code == 302 and '/auth/login' in res_success.headers.get('Location', '')
        log("Direct Register - Successful Student Registration", is_redirect_to_login, "Redirects to /auth/login with success status")

        # Verify created student in DB
        u_stu = User.query.filter_by(email='direct.scholar@university.edu').first()
        stu_valid = (
            u_stu is not None
            and u_stu.username == 'direct_scholar'
            and u_stu.is_verified is True
            and u_stu.status == 'active'
            and u_stu.is_student
            and u_stu.check_password('StrongPassword2026!')
        )
        log("Direct Register - Student DB Verification", stu_valid, f"User in DB: is_verified={u_stu.is_verified if u_stu else None}, active={u_stu.is_active if u_stu else None}")

        # -----------------------------------------------------------------
        # 5. UNIQUENESS ENFORCEMENT & EXACT ERROR MESSAGE
        # -----------------------------------------------------------------
        # Duplicate Username
        res_dup_user = client.post('/auth/register', data={
            'first_name': 'Clone',
            'last_name': 'User',
            'username': 'direct_scholar',  # Already taken
            'email': 'clone.user@university.edu',
            'role': 'student',
            'password': 'StrongPassword2026!',
            'confirm_password': 'StrongPassword2026!'
        })
        has_dup_msg = b"This username is already taken. Please choose another." in res_dup_user.data
        log("Direct Register - Duplicate Username Blocked", res_dup_user.status_code in (400, 200) and has_dup_msg, "Rejected with exact message: 'This username is already taken. Please choose another.'")

        # Duplicate Email
        res_dup_email = client.post('/auth/register', data={
            'first_name': 'Clone',
            'last_name': 'User',
            'username': 'unique_user_99',
            'email': 'direct.scholar@university.edu',  # Already taken
            'role': 'student',
            'password': 'StrongPassword2026!',
            'confirm_password': 'StrongPassword2026!'
        })
        log("Direct Register - Duplicate Email Blocked", res_dup_email.status_code in (400, 200) and b"already exists" in res_dup_email.data.lower(), "Rejected duplicate email")

        # -----------------------------------------------------------------
        # 6. SEEDED DEFAULT USERS LOGIN (PRODUCTION GRADE CREDENTIALS)
        # -----------------------------------------------------------------
        client.get('/auth/logout')

        # Admin login via username: admin_pms
        res_adm_u = client.post('/auth/login', data={'username': 'admin_pms', 'password': 'Admin@PMS2026#Secure'}, follow_redirects=False)
        log("Login Seeded Admin via Username (admin_pms)", res_adm_u.status_code == 302 and '/admin/dashboard' in res_adm_u.headers.get('Location', ''), "Logged in via admin_pms -> /admin/dashboard")

        client.get('/auth/logout')

        # Admin login via email: admin@university.edu
        res_adm_e = client.post('/auth/login', data={'username': 'admin@university.edu', 'password': 'Admin@PMS2026#Secure'}, follow_redirects=False)
        log("Login Seeded Admin via Email (admin@university.edu)", res_adm_e.status_code == 302 and '/admin/dashboard' in res_adm_e.headers.get('Location', ''), "Logged in via email -> /admin/dashboard")

        client.get('/auth/logout')

        # Faculty login via username: dr_ankit_verma
        res_fac_u = client.post('/auth/login', data={'username': 'dr_ankit_verma', 'password': 'Faculty@Verma2026!'}, follow_redirects=False)
        log("Login Seeded Faculty via Username (dr_ankit_verma)", res_fac_u.status_code == 302 and '/faculty/dashboard' in res_fac_u.headers.get('Location', ''), "Logged in via dr_ankit_verma -> /faculty/dashboard")

        client.get('/auth/logout')

        # Faculty login via email: dr.verma@university.edu
        res_fac_e = client.post('/auth/login', data={'username': 'dr.verma@university.edu', 'password': 'Faculty@Verma2026!'}, follow_redirects=False)
        log("Login Seeded Faculty via Email (dr.verma@university.edu)", res_fac_e.status_code == 302 and '/faculty/dashboard' in res_fac_e.headers.get('Location', ''), "Logged in via email -> /faculty/dashboard")

        client.get('/auth/logout')

        # Student login via username: adarsh_lead
        res_stu_u = client.post('/auth/login', data={'username': 'adarsh_lead', 'password': 'Student@Katiyar2026!'}, follow_redirects=False)
        log("Login Seeded Student via Username (adarsh_lead)", res_stu_u.status_code == 302 and '/student/dashboard' in res_stu_u.headers.get('Location', ''), "Logged in via adarsh_lead -> /student/dashboard")

        client.get('/auth/logout')

        # Student login via email: student1@university.edu
        res_stu_e = client.post('/auth/login', data={'username': 'student1@university.edu', 'password': 'Student@Katiyar2026!'}, follow_redirects=False)
        log("Login Seeded Student via Email (student1@university.edu)", res_stu_e.status_code == 302 and '/student/dashboard' in res_stu_e.headers.get('Location', ''), "Logged in via email -> /student/dashboard")

        # -----------------------------------------------------------------
        # 7. SECURITY CHECKS & LOCKOUTS
        # -----------------------------------------------------------------
        client.get('/auth/logout')

        # Case-Insensitive Username Login
        res_case = client.post('/auth/login', data={
            'username': 'ADMIN_PMS',
            'password': 'Admin@PMS2026#Secure'
        }, follow_redirects=False)
        log("Case-Insensitive Identifier Login", res_case.status_code == 302 and '/admin/dashboard' in res_case.headers.get('Location', ''), "Uppercased username logged in successfully")

        client.get('/auth/logout')

        # Incorrect Password Rejection
        res_wrong_pw = client.post('/auth/login', data={
            'username': 'admin_pms',
            'password': 'WrongPassword999!'
        }, follow_redirects=True)
        log("Incorrect Password Rejection", b"Invalid username/email or password" in res_wrong_pw.data, "Rejected incorrect password")

        client.get('/auth/logout')

        # Blacklisted User Login Blocked (403)
        if u_stu:
            u_stu.status = 'blacklisted'
            u_stu.block_reason = 'Disciplinary violation test'
            db.session.commit()

        res_blacklisted = client.post('/auth/login', data={
            'username': 'direct_scholar',
            'password': 'StrongPassword2026!'
        }, follow_redirects=False)
        log("Blacklisted User Login Rejection (403)", res_blacklisted.status_code == 403, "Blacklisted account strictly rejected with 403")

        # Cleanup test accounts
        for em in test_emails:
            u = User.query.filter_by(email=em).first()
            if u:
                db.session.delete(u)
        db.session.commit()

    print("\n" + "="*80)
    print("      📊 AUTH ENGINE TEST RESULTS SUMMARY")
    print("="*80)
    all_passed = True
    for sym, name, details in results:
        print(f"{sym} {name:<48} | {details}")
        if sym != "✅":
            all_passed = False
    print("="*80)
    print(f"TOTAL: {len(results)} | STATUS: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}\n")
    return all_passed

if __name__ == '__main__':
    success = run_auth_engine_tests()
    exit(0 if success else 1)

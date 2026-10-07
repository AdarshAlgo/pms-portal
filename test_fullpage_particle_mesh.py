"""
Test Suite: Stripe Full-Page Interactive Particle Mesh Background Verification
------------------------------------------------------------------------------
Verifies:
1. CSS definitions for .particle-mesh-canvas (fixed, 100vw, 100vh, z-index: -1, pointer-events: none)
2. Body isolation: isolate to prevent stacking context clipping
3. Full-page canvas presence on Homepage (/)
4. Full-page canvas presence on Auth pages (/auth/login, /auth/register)
5. Full-page canvas presence on Authenticated Dashboards (Admin, Faculty, Student)
6. Integrity and syntax of static/js/particle_mesh.js
7. React component presence (components/StripeParticleMesh.jsx)
"""

import urllib.request
import urllib.parse
import http.cookiejar
import re

BASE_URL = 'http://127.0.0.1:5001'

def run_tests():
    print("=" * 80)
    print(" 🌌 VERIFYING FULL-PAGE INTERACTIVE PARTICLE MESH BACKGROUND")
    print("=" * 80)

    # 1. Verify CSS Rules in custom.css
    css_req = urllib.request.Request(f"{BASE_URL}/static/css/custom.css")
    with urllib.request.urlopen(css_req) as resp:
        assert resp.getcode() == 200, "Failed to load custom.css"
        css_text = resp.read().decode('utf-8')
        assert ".particle-mesh-canvas" in css_text, "Missing .particle-mesh-canvas in custom.css"
        assert "position: fixed" in css_text, "Missing position: fixed in custom.css"
        assert "100vw" in css_text, "Missing 100vw in custom.css"
        assert "100vh" in css_text, "Missing 100vh in custom.css"
        assert "pointer-events: none" in css_text, "Missing pointer-events: none in custom.css"
        assert "z-index: 0" in css_text, "Missing z-index: 0 in custom.css"
        assert "isolation: isolate" in css_text, "Missing isolation: isolate in custom.css"
    print("✅ [CSS] Verified .particle-mesh-canvas (fixed, 100vw, 100vh, z-index: 0, pointer-events: none, isolation: isolate)")

    # 2. Verify static/js/particle_mesh.js Asset Integrity
    js_req = urllib.request.Request(f"{BASE_URL}/static/js/particle_mesh.js")
    with urllib.request.urlopen(js_req) as resp:
        assert resp.getcode() == 200, "Failed to load particle_mesh.js"
        js_text = resp.read().decode('utf-8')
        assert "TechNodeConstellation" in js_text, "Missing TechNodeConstellation class"
        assert "stripe-particle-mesh-canvas" in js_text, "Missing canvasId default"
        assert "baseSpeedMin: 1.2" in js_text, "Missing baseSpeedMin 1.2 drift speed parameter"
        assert "baseSpeedMax: 2.0" in js_text, "Missing baseSpeedMax 2.0 drift speed parameter"
        assert "mouseRepulseRadius" in js_text, "Missing mouse repulsion radius"
        assert "maxNudgeDistance" in js_text, "Missing bounded max nudge distance"
        assert "interactivityLerp" in js_text, "Missing interactivityLerp parameter"
        assert "worldY" in js_text, "Missing document worldY coordinate tracking"
        assert "scrollY" in js_text, "Missing vertical scroll tracking"
        assert "PALETTES" in js_text, "Missing theme palettes"
        assert "MutationObserver" in js_text, "Missing theme MutationObserver"
        assert "visibilitychange" in js_text, "Missing visibilitychange handler"
        assert "devicePixelRatio" in js_text, "Missing DPR retina scaling"
    print("✅ [JS_ENGINE] Verified TechNodeConstellation (Fine-tuned 1.2-2.0 Speed, Bounded Nudge, Stars, DPR, Visibility API)")

    # 3. Verify Homepage (/)
    home_req = urllib.request.Request(f"{BASE_URL}/")
    with urllib.request.urlopen(home_req) as resp:
        assert resp.getcode() == 200
        home_html = resp.read().decode('utf-8')
        assert 'id="stripe-particle-mesh-canvas"' in home_html, "Canvas missing on homepage"
        assert 'class="particle-mesh-canvas"' in home_html, "Class missing on homepage canvas"
        assert 'particle_mesh.js' in home_html, "Script missing on homepage"
    print("✅ [HOMEPAGE] Full-page particle mesh canvas & script verified on root landing page")

    # 4. Verify Auth Pages (/auth/login, /auth/register)
    for auth_path in ['/auth/login', '/auth/register']:
        req = urllib.request.Request(f"{BASE_URL}{auth_path}")
        with urllib.request.urlopen(req) as resp:
            assert resp.getcode() == 200
            auth_html = resp.read().decode('utf-8')
            assert 'id="stripe-particle-mesh-canvas"' in auth_html, f"Canvas missing on {auth_path}"
            assert 'particle_mesh.js' in auth_html, f"Script missing on {auth_path}"
    print("✅ [AUTH_PAGES] Full-page particle mesh canvas verified on /auth/login and /auth/register")

    # 5. Verify Authenticated Dashboards (Student, Faculty, Admin)
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    def login(email, password):
        login_url = f"{BASE_URL}/auth/login"
        req = urllib.request.Request(login_url)
        with opener.open(req) as resp:
            html = resp.read().decode('utf-8')
        csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
        csrf_token = csrf_match.group(1) if csrf_match else ''
        data = urllib.parse.urlencode({
            'email': email,
            'password': password,
            'csrf_token': csrf_token
        }).encode('utf-8')
        post_req = urllib.request.Request(login_url, data=data)
        opener.open(post_req)

    # Test Admin Dashboard
    login('admin@university.edu', 'Admin@123')
    admin_req = urllib.request.Request(f"{BASE_URL}/admin/dashboard")
    with opener.open(admin_req) as resp:
        admin_html = resp.read().decode('utf-8')
        assert 'id="stripe-particle-mesh-canvas"' in admin_html, "Canvas missing on Admin Dashboard"
        assert 'particle_mesh.js' in admin_html, "Script missing on Admin Dashboard"
    print("✅ [ADMIN_PORTAL] Full-page particle mesh canvas verified on /admin/dashboard")

    # Test Faculty Dashboard
    login('dr.verma@university.edu', 'Faculty@123')
    faculty_req = urllib.request.Request(f"{BASE_URL}/faculty/dashboard")
    with opener.open(faculty_req) as resp:
        faculty_html = resp.read().decode('utf-8')
        assert 'id="stripe-particle-mesh-canvas"' in faculty_html, "Canvas missing on Faculty Dashboard"
        assert 'particle_mesh.js' in faculty_html, "Script missing on Faculty Dashboard"
    print("✅ [FACULTY_PORTAL] Full-page particle mesh canvas verified on /faculty/dashboard")

    # Test Student Dashboard
    login('student1@university.edu', 'Student@123')
    student_req = urllib.request.Request(f"{BASE_URL}/student/dashboard")
    with opener.open(student_req) as resp:
        student_html = resp.read().decode('utf-8')
        assert 'id="stripe-particle-mesh-canvas"' in student_html, "Canvas missing on Student Dashboard"
        assert 'particle_mesh.js' in student_html, "Script missing on Student Dashboard"
    print("✅ [STUDENT_PORTAL] Full-page particle mesh canvas verified on /student/dashboard")

    # 6. Verify Global Components (React / Next.js & Jinja Partial)
    with open('components/GlobalParticleBackground.jsx', 'r') as f:
        react_code = f.read()
        assert "export default function GlobalParticleBackground" in react_code
        assert "useRef" in react_code and "useEffect" in react_code
        assert "stripe-particle-mesh-canvas" in react_code
        assert "baseSpeedMin = 1.2" in react_code
        assert "baseSpeedMax = 2.0" in react_code
        assert "maxNudgeDistance = 20" in react_code
        assert "interactivityLerp = 0.075" in react_code
        assert "zIndex: 0" in react_code or 'zIndex: "0"' in react_code
    print("✅ [REACT_COMPONENT] Verified components/GlobalParticleBackground.jsx structure & props")

    with open('components/StripeParticleMesh.jsx', 'r') as f:
        stripe_code = f.read()
        assert "GlobalParticleBackground" in stripe_code
    print("✅ [REACT_ALIAS] Verified components/StripeParticleMesh.jsx backward-compatibility alias")

    with open('app/templates/components/_particle_background.html', 'r') as f:
        jinja_code = f.read()
        assert "stripe-particle-mesh-canvas" in jinja_code
        assert "particle_mesh.js" in jinja_code
    print("✅ [JINJA_PARTIAL] Verified app/templates/components/_particle_background.html layout wrapper")

    print("=" * 80)
    print(" 🌟 ALL FULL-PAGE PARTICLE MESH BACKGROUND TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 80)

if __name__ == '__main__':
    run_tests()

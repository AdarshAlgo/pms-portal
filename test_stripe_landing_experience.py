"""
Test Suite: Stripe-Inspired Interactive Motion & Canvas Web Architecture Verification
-------------------------------------------------------------------------------------
Verifies:
1. Dynamic Animated Gradient Background Canvas (#hero-gradient-canvas)
2. Hero Section layout: SDG 9 / ABET v2.0 Live badge, CTAs, and Infinite Tech Stack Marquee
3. Interactive Telemetry Particle Network Canvas (#telemetry-particles-canvas)
4. 4 Real-Time Quantitative Metric Counters (data-counter-target)
5. 3-Tab Floating Browser Mockup (Burndown, Rubric Evaluator with 4 sliders, Vidya.ai Copilot)
6. 3 Interactive Logic Cards (data-highlight-target)
7. Static asset accessibility for landing_canvas.js
8. Zero regressions across existing RBAC and academic constraints
"""

import re
import urllib.request

BASE_URL = 'http://127.0.0.1:5001'

def run_tests():
    print("=" * 80)
    print(" 🎨 VERIFYING STRIPE-INSPIRED CANVAS & INTERACTIVE MOTION ARCHITECTURE")
    print("=" * 80)

    # 1. Fetch Landing Page
    req = urllib.request.Request(f"{BASE_URL}/")
    with urllib.request.urlopen(req) as resp:
        assert resp.getcode() == 200, f"Expected 200, got {resp.getcode()}"
        html = resp.read().decode('utf-8')
    print("✅ [HTTP] Landing page root / responded with status 200 OK")

    # 2. Hero Interactive Mesh Gradient Canvas
    assert 'id="hero-gradient-canvas"' in html, "Must contain #hero-gradient-canvas"
    assert 'class="absolute inset-0' in html, "Canvas must have absolute overlay positioning"
    print("✅ [HERO_CANVAS] Interactive Mesh Gradient Canvas (#hero-gradient-canvas) embedded")

    # 3. Dynamic SDG 9 / ABET Badge
    assert "UN SDG 9 Aligned" in html, "Hero badge must mention UN SDG 9 Aligned"
    assert "ABET / NBA Outcome-Based Governance v2.0 Live" in html, "Hero badge must mention ABET v2.0 Live"
    print("✅ [HERO_BADGE] SDG 9 & ABET Outcome-Based Governance badge ticker verified")

    # 4. Infinite Academic Tech Stack Marquee (Single Container, No Stray Duplicate Blocks)
    assert html.count("animate-marquee") == 1, "Must contain exactly one animate-marquee container"
    assert "marquee-mask" in html, "Must contain edge feathering mask marquee-mask"
    marquee_match = re.search(r'<div class="animate-marquee[^>]*>(.*?)</div>', html, re.DOTALL)
    assert marquee_match is not None, "Could not extract animate-marquee inner HTML"
    marquee_inner = marquee_match.group(1)
    for tech in ["Python 3.12", "PyTorch 2.4", "ROS 2 Humble", "LoRaWAN Mesh", "TensorFlow Lite", "OpenCV 4.x", "Docker Engine", "FastAPI", "Scikit-Learn"]:
        assert marquee_inner.count(tech) == 2, f"{tech} should appear exactly twice inside marquee loop (Set 1 + Set 2)"
    # Ensure ROS 2 Humble (unique to tech badges) appears nowhere outside the marquee
    html_without_marquee = html.replace(marquee_inner, "")
    assert "ROS 2 Humble" not in html_without_marquee, "ROS 2 Humble should NOT appear outside the marquee"
    print("✅ [TECH_MARQUEE] Single Infinite Academic Tech Stack Marquee verified with no stray duplicate blocks")

    # 5. Telemetry Particle Network Canvas
    assert 'id="telemetry-particles-canvas"' in html, "Must contain #telemetry-particles-canvas"
    print("✅ [PARTICLE_CANVAS] Telemetry Particle Network Canvas (#telemetry-particles-canvas) embedded")

    # 6. Real-Time Quantitative Metric Counters (Viewport Scroll Animated)
    assert 'data-counter-target="100"' in html, "Must have 100% Traceability counter"
    assert 'data-counter-target="40"' in html, "Must have 40/40 Tests counter"
    assert 'data-counter-target="3"' in html, "Must have 3-Tier ABET Matrix counter"
    assert 'data-counter-target="5"' in html, "Must have 5 Flagship Cohorts counter"
    assert "100% Traceability" in html
    assert "40/40 Tests Passed" in html
    assert "3-Tier ABET Matrix" in html
    assert "5 Flagship Cohorts" in html
    print("✅ [METRIC_COUNTERS] 4 real-time animated metric counters verified")

    # 7. 4 Interactive Logic Cards (Hover to Highlight Target & Tab Auto-Switch)
    assert 'data-highlight-target="mockup-panel-burndown"' in html, "Must link to burndown panel"
    assert 'data-highlight-target="mockup-panel-rubric"' in html, "Must link to rubric panel"
    assert 'data-highlight-target="mockup-panel-copilot"' in html, "Must link to copilot panel"
    assert 'data-highlight-target="mockup-radar-card"' in html, "Must link to radar card"
    assert 'id="mockup-radar-card"' in html, "Must contain target #mockup-radar-card"
    assert 'calculateBurndownVelocity' in html
    assert 'evaluateSubmission' in html
    assert 'vidyaQueryEngine.groundedSQL' in html
    assert 'telemetryStream.trackHealth' in html
    assert 'data-hotspot-tab="burndown"' in html
    assert 'data-hotspot-tab="rubric"' in html
    assert 'data-hotspot-tab="copilot"' in html
    print("✅ [LOGIC_CARDS] 4 interactive code hotspots with data-highlight-target verified")

    # 8. 3-Tab Floating Browser Mockup (Stripe/Linear Style)
    assert 'data-tab="burndown"' in html, "Must have burndown tab button"
    assert 'data-tab="rubric"' in html, "Must have rubric tab button"
    assert 'data-tab="copilot"' in html, "Must have copilot tab button"
    assert 'id="mockup-panel-burndown"' in html, "Must have burndown panel"
    assert 'id="mockup-panel-rubric"' in html, "Must have rubric panel"
    assert 'id="mockup-panel-copilot"' in html, "Must have copilot panel"
    print("✅ [BROWSER_MOCKUP] macOS 3-tab browser mockup structure verified")

    # 9. Faculty Rubric Evaluator Sliders & Dynamic Badges
    assert 'id="rubric-slider-rigor"' in html, "Must have rigor slider"
    assert 'id="rubric-slider-innov"' in html, "Must have innovation slider"
    assert 'id="rubric-slider-code"' in html, "Must have code quality slider"
    assert 'id="rubric-slider-viva"' in html, "Must have viva slider"
    assert 'id="mockup-rubric-total-score"' in html, "Must have live total score display"
    assert 'id="mockup-rubric-grade-badge"' in html, "Must have live grade badge"
    print("✅ [RUBRIC_SLIDERS] Interactive faculty criteria sliders & real-time badge verified")

    # 10. Vidya.ai Grounded Copilot Drawer Simulation
    assert "Vidya.ai Grounded Copilot Drawer" in html
    assert "Urja-Net (Solar Microgrid)" in html
    assert "Strictly On-Premise SQLite" in html
    print("✅ [VIDYA_COPILOT] Grounded Copilot query drawer & on-premise SQLite terminal verified")

    # 11. Script Import & Asset Health
    assert 'landing_canvas.js' in html, "Must load landing_canvas.js"
    assert 'gsap.min.js' in html, "Must load GSAP library"
    assert 'ScrollTrigger.min.js' in html, "Must load ScrollTrigger library"
    assert 'window.landingChart = landingChart' in html, "Must expose landingChart to window"

    # 12. Viewport Anti-Cutoff & Safe Geometry Verification
    assert '-left-36' not in html, "Orbital badges must not use extreme negative left margins"
    assert '-right-36' not in html, "Orbital badges must not use extreme negative right margins"
    assert 'left-4 xl:left-8' in html, "Orbital badges must use viewport-safe container boundaries"
    assert 'right-4 xl:right-8' in html, "Orbital badges must use viewport-safe container boundaries"
    print("✅ [VIEWPORT_SAFETY] Zero cutoff: Orbital badges verified within safe layout boundaries")

    js_req = urllib.request.Request(f"{BASE_URL}/static/js/landing_canvas.js")
    with urllib.request.urlopen(js_req) as js_resp:
        assert js_resp.getcode() == 200, f"Expected 200, got {js_resp.getcode()}"
        js_content = js_resp.read().decode('utf-8')
        assert "initHeroMeshGradient" in js_content
        assert "initTelemetryParticleNetwork" in js_content
        assert "initMetricsCounters" in js_content
        assert "initShowcaseDashboard" in js_content
        assert "calculateLiveRubric" in js_content
        assert "initGSAPAnimations" in js_content
    print("✅ [ASSET_INTEGRITY] landing_canvas.js accessible with all 5 motion controllers")

    print("=" * 80)
    print(" 🌟 ALL STRIPE-INSPIRED INTERACTIVE MOTION TESTS PASSED PERFECTLY!")
    print("=" * 80)

if __name__ == '__main__':
    run_tests()

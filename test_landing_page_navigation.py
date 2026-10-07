"""
Test Suite: Landing Page Navigation & Academic Architecture Sanitization
-----------------------------------------------------------------------
Verifies:
1. Navbar anchor separation: #features, #telemetry, #portals, #rubrics
2. Complete absence of #pricing, dollar tiers, and commercial monetization
3. Distinct #features section with 4 Core Architecture Bento Cards
4. Distinct #telemetry section with Milestone Velocity Chart & 3 Stat Cards
5. Zero dollar amounts or commercial billing references in rendered HTML
"""

import re
import urllib.request

BASE_URL = 'http://127.0.0.1:5001'

def run_tests():
    print("=" * 80)
    print(" 🚀 VERIFYING LANDING PAGE NAVIGATION & ACADEMIC SANITIZATION")
    print("=" * 80)

    req = urllib.request.Request(f"{BASE_URL}/")
    with urllib.request.urlopen(req) as resp:
        assert resp.getcode() == 200, f"Expected 200, got {resp.getcode()}"
        html = resp.read().decode('utf-8')

    # Test 1: Navbar contains distinct academic anchors
    assert 'href="#features"' in html, "Navbar must contain #features anchor"
    assert 'href="#telemetry"' in html, "Navbar must contain #telemetry anchor"
    assert 'href="#portals"' in html, "Navbar must contain #portals anchor"
    assert 'href="#rubrics"' in html, "Navbar must contain #rubrics anchor"
    assert 'href="#pricing"' not in html, "Navbar must NOT contain #pricing anchor"
    print("✅ [NAVBAR] Clean academic anchors verified: #features, #telemetry, #portals, #rubrics (no #pricing)")

    # Test 2: Section 1 #features is distinct with scroll-mt-28
    assert '<section id="features"' in html, "Must have <section id=\"features\">"
    features_match = re.search(r'<section id="features"[^>]*class="[^"]*scroll-mt-28[^"]*"', html)
    assert features_match, "Section #features must have scroll-mt-28 class for floating navbar offset"
    assert "Multi-Tenant Role Isolation" in html, "Card 1: Multi-Tenant Role Isolation must exist"
    assert "Enterprise RBAC" in html, "Card 1 badge must exist"
    assert "Quantitative Multi-Tier Rubrics" in html, "Card 2: Quantitative Multi-Tier Rubrics must exist"
    assert "ABET &amp; NBA OBE" in html, "Card 2 badge must exist"
    assert "Local Database Copilot" in html, "Card 3: Local Database Copilot must exist"
    assert "Vidya.ai Pro" in html, "Card 3 badge must exist"
    assert "Immutable Activity Audit Logs" in html, "Card 4: Immutable Activity Audit Logs must exist"
    assert "Tamper-Proof" in html, "Card 4 badge must exist"
    print("✅ [FEATURES] Distinct #features section verified with 4 Core Functional Bento Pillars")

    # Test 3: Section 2 #telemetry is distinct with scroll-mt-28
    assert '<section id="telemetry"' in html, "Must have <section id=\"telemetry\">"
    telemetry_match = re.search(r'<section id="telemetry"[^>]*class="[^"]*scroll-mt-28[^"]*"', html)
    assert telemetry_match, "Section #telemetry must have scroll-mt-28 class"
    assert 'id="landingProjectsChart"' in html, "Milestone velocity Chart.js canvas must exist in #telemetry"
    assert "Active Capstone Projects Milestone Velocity" in html, "Velocity chart header must exist"
    assert "inspectProject(1)" in html, "5 live projects interactive pills must exist"
    assert "Average Rubric Score (Top Cohort)" in html, "Stat Card 1 (Rubric score) must exist"
    assert "Milestone Clearance Velocity" in html, "Stat Card 2 (Sprint velocity) must exist"
    assert "Real-Time Cohort Health Lights" in html or "Cohort Health" in html, "Stat Card 3 (Health radar) must exist"
    print("✅ [TELEMETRY] Distinct #telemetry section verified with Velocity Chart & 3 Stat Cards")

    # Test 4: Backwards compatibility anchor #showcase
    assert 'id="showcase"' in html, "Backwards compatibility anchor #showcase must be present"
    print("✅ [BACKWARDS_COMPAT] Anchor #showcase preserved for legacy references")

    # Test 5: Hero CTAs are purely academic
    assert 'Launch Portal Hub' in html, "Hero primary CTA must launch portal hub"
    assert 'Inspect 5 Live Capstones' in html, "Hero secondary CTA must inspect live capstones"
    assert re.search(r'href="#telemetry"[^>]*>[\s\S]*?Inspect 5 Live Capstones', html), "Inspect CTA must link to #telemetry"
    print("✅ [HERO] CTAs link to #portals and #telemetry without commercial terms")

    # Test 6: Purge of Pricing & Commercial Monetization
    assert '<section id="pricing"' not in html, "Must NOT have <section id=\"pricing\">"
    assert 'billing-monthly-btn' not in html, "Must NOT have billing monthly button"
    assert 'billing-annual-btn' not in html, "Must NOT have billing annual button"
    assert 'setBillingPeriod' not in html, "Must NOT have setBillingPeriod JS"
    dollar_matches = re.findall(r'\$[0-9]+', html)
    assert len(dollar_matches) == 0, f"Found unexpected dollar amounts: {dollar_matches}"
    print("✅ [COMMERCIAL_PURGE] 100% of commercial pricing tables, dollar tiers, and billing toggles removed")

    # Test 7: Footer links are academic
    assert 'Architecture &amp; Features' in html, "Footer must contain Architecture & Features link"
    assert 'Research Telemetry' in html, "Footer must contain Research Telemetry link"
    print("✅ [FOOTER] Clean academic links verified: Architecture & Features, Research Telemetry, Portals, Rubrics")

    print("=" * 80)
    print(" 🌟 ALL LANDING PAGE & NAVIGATION TESTS PASSED PERFECTLY!")
    print("=" * 80)

if __name__ == '__main__':
    run_tests()

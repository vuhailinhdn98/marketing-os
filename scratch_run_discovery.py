# -*- coding: utf-8 -*-
import sys, json
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.database import get_profile, update_profile
from app.ai_engine import auto_discover_competitors, generate_competitor_analysis

p = get_profile()
print(f"Company: {p.get('brand_name')}")
print(f"Industry: {p.get('industry')}")
print(f"Products: {p.get('products_services')}")
print(f"Price: {p.get('price_range')}")

print("\n--- 1. RUNNING AUTO COMPETITOR DISCOVERY ---")
comps = auto_discover_competitors(p)
print(f"Found {len(comps)} competitors:")
for idx, c in enumerate(comps, 1):
    print(f"{idx}. {c.get('name')} - URL: {c.get('website')} [{c.get('type')}]")
    print(f"   SP: {c.get('core_products')}")
    print(f"   Thế mạnh: {c.get('key_strengths')}")
    print(f"   Tử huyệt: {c.get('vulnerabilities')}")

if comps:
    comp_str = ", ".join([f"{c['name']} ({c.get('website', '')})" if c.get('website') else c['name'] for c in comps])
    p["competitors"] = comp_str
    update_profile(p)
    print("\nUpdated profile with real discovered competitors:")
    print(comp_str)

print("\n--- 2. GENERATING BATTLECARDS BASED ON DISCOVERED COMPETITORS ---")
battlecards = generate_competitor_analysis(p)
print(f"Battlecards generated successfully! Total length: {len(battlecards)} characters.")
print("Snippet:")
print(battlecards[:800])

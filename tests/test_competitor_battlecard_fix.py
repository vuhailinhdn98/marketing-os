# -*- coding: utf-8 -*-
"""
Verification test for Competitor Battlecard 1-1 rendering & Manual Competitor Intake
Simulates exact user workflow from screenshot:
- Adding competitor: "Công ty TNHH Giải Pháp Vận Tải MOVE"
- Website: "https://santesmove.vn/"
- Phone: "0901 234 567"
- Social: "Facebook Move transport"
- Verifying Battlecard 1-1 markdown generation, storage, and retrieval
"""
import sys
import os
import unittest
from fastapi.testclient import TestClient

# Ensure root dir is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.main import app
from app.database import get_connection, init_app_db, get_discovered_competitors, get_competitor_by_id

class TestCompetitorBattlecardFix(unittest.TestCase):
    def setUp(self):
        init_app_db()
        self.client = TestClient(app)
        self.test_email = "move_test_user@transport.vn"
        self.headers = {"X-User-Email": self.test_email}

    def tearDown(self):
        # Cleanup test competitors
        self.client.delete("/api/competitors/all", headers=self.headers)

    def test_manual_competitor_battlecard_generation_and_storage(self):
        print("\n[TEST] 1. Them doi thu thu cong voi scan_deep = True...")
        payload = {
            "name": "Công ty TNHH Giải Pháp Vận Tải MOVE",
            "website": "https://santesmove.vn/",
            "phone": "0901 234 567",
            "social": "Facebook Move transport",
            "notes": "Đơn vị vận tải logistics, xe tải chạy đường dài",
            "competitor_type": "Trực tiếp",
            "is_manual": 1,
            "scan_deep": True
        }
        res = self.client.post("/api/competitors/add-manual", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")

        # 1. Competitor returned must exist
        comp = data.get("competitor")
        self.assertIsNotNone(comp, "competitor object must not be None")
        comp_id = comp["id"]
        print(f"-> Competitor ID: {comp_id}, Name: {repr(comp['name'])}")

        # 2. Battlecard content MUST NOT BE EMPTY
        battlecard = comp.get("battlecard_content")
        self.assertIsNotNone(battlecard, "battlecard_content must not be None")
        self.assertTrue(len(battlecard) > 100, f"battlecard_content must have substantial length, got {len(battlecard)}")
        print(f"-> Battlecard content length: {len(battlecard)} chars")

        # 3. Check for the 6 strategic sections
        print("-> Checking 6 strategic battlecard sections...")
        self.assertIn("HỒ SƠ TÌNH BÁO", battlecard)
        self.assertIn("ĐIỂM MẠNH", battlecard)
        self.assertIn("TỬ HUYỆT", battlecard)
        self.assertIn("VŨ KHÍ ĐÈ BẸP", battlecard)
        self.assertTrue("KỊCH BẢN" in battlecard and "XỬ LÝ TỪ CHỐI" in battlecard)
        self.assertIn("HỚT TAY TRÊN", battlecard)
        print("-> All 6 strategic battlecard sections verified!")

        # 4. Competitor list must include this competitor
        comps_list = data.get("competitors", [])
        self.assertTrue(any(c["id"] == comp_id for c in comps_list), "New competitor must be present in competitors list")
        self.assertEqual(len(comps_list), 1)

        # 5. Database check: Verify persisted directly in SQLite
        db_comp = get_competitor_by_id(comp_id, user_email=self.test_email)
        self.assertIsNotNone(db_comp)
        self.assertEqual(db_comp["name"], "Công ty TNHH Giải Pháp Vận Tải MOVE")
        self.assertEqual(db_comp["phone"], "0901 234 567")
        self.assertEqual(db_comp["website"], "https://santesmove.vn/")
        self.assertTrue(len(db_comp.get("battlecard_content", "")) > 100)

        # 6. Test scanning again via /api/competitors/dossier/scan
        print("\n[TEST] 2. Quet lai tinh bao qua /api/competitors/dossier/scan...")
        res_scan = self.client.post("/api/competitors/dossier/scan", json={"competitor_id": comp_id}, headers=self.headers)
        self.assertEqual(res_scan.status_code, 200)
        scan_data = res_scan.json()
        self.assertEqual(scan_data["status"], "success")
        self.assertTrue(len(scan_data.get("battlecard", "")) > 100)
        self.assertTrue(len(scan_data["competitor"].get("battlecard_content", "")) > 100)
        print("-> Re-scan verified successfully!")

if __name__ == "__main__":
    unittest.main()

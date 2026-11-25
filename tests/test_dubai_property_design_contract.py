"""UI-only Dubai property design route must not misrepresent fixtures."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class DubaiPropertyDesignContract(unittest.TestCase):
    def test_route_exists_and_is_clearly_illustrative(self):
        source=(ROOT/"apps/web/app/dubai-property/page.tsx").read_text(encoding="utf-8")
        for token in ("DESIGN FIXTURES ONLY","ILLUSTRATIVE PROPERTY","portfolio","Property Offers","Portfolio Performance","Investment by Property Type","Market Snapshot","ROI Calculator","href=\"/\""):
            self.assertIn(token,source)
        self.assertNotIn('fetch("/api/v1/',source)
    def test_visual_structure_and_mobile_styles(self):
        css=(ROOT/"apps/web/app/dubai-property/dubai-property.css").read_text(encoding="utf-8")
        for token in (".dp-sidebar",".dp-hero",".dp-stat-grid",".dp-donut",".dp-property-grid","@media(max-width:650px)"):
            self.assertIn(token,css)
    def test_original_aviation_unchanged_contract(self):
        page=(ROOT/"apps/web/app/page.tsx").read_text(encoding="utf-8")
        for token in ('/api/portal/overview','/api/portal/events','signOut','EventTable'):
            self.assertIn(token,page)
if __name__=="__main__":unittest.main()

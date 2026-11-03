"""Guard public README quality and references without accessing external services."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


class PublicReadmeTests(unittest.TestCase):
    def test_local_markdown_links_resolve(self) -> None:
        content = README.read_text(encoding="utf-8")
        links = re.findall(r"\]\(([^)]+)\)", content)
        local = [link.split("#", 1)[0] for link in links
                 if not link.startswith(("https://", "http://", "#", "mailto:"))]
        self.assertGreaterEqual(len(local), 12)
        for relative in local:
            with self.subTest(link=relative):
                self.assertTrue((ROOT / relative).exists())

    def test_readme_addresses_external_research_audience(self) -> None:
        text = README.read_text(encoding="utf-8").lower()
        self.assertIn("research questions", text)
        self.assertIn("measured results", text)
        self.assertIn("reproduce", text)
        self.assertIn("limitations", text)
        for internal_phrase in (
            "portfolio baseline", "owner submission", "post-deadline handoff",
            "final portfolio closeout", "remote workbench", "user approval",
        ):
            with self.subTest(phrase=internal_phrase):
                self.assertNotIn(internal_phrase, text)


if __name__ == "__main__":
    unittest.main()

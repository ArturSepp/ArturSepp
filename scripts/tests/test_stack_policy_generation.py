"""Check that selected policy generation preserves repository scope and import polarity."""

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import generate_stack_policy as generator


class StackPolicyGenerationTests(unittest.TestCase):
    """Use the approved registry and isolated policy files for generator contracts."""

    def test_factor_models_reverse_dependency_and_composed_exceptions(self):
        """FM remains forbidden to FL/OP except OP's precise development consumers."""
        registry = generator.load_registry()
        packages = {package["import"]: package for package in registry["packages"]}
        for name in ("optimalportfolios", "factorlasso"):
            policy = json.loads(generator.render_policy(registry, packages[name]))
            self.assertIn("factormodels", policy["forbidden"])
            self.assertNotIn("tradablefactors", policy["forbidden"])
            self.assertNotIn("factormodels", policy["core"])
        policy = json.loads(generator.render_policy(registry, packages["optimalportfolios"]))
        consumers = {entry["path"]: entry["modules"] for entry in policy["development_imports"]}
        self.assertEqual(
            consumers["src/optimalportfolios/tests/factor_integration_test.py"],
            ["factormodels", "factorlasso"],
        )

    def test_selected_generation_is_idempotent_and_preserves_other_files(self):
        """Generation changes only the chosen existing file and check detects drift."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            selected = root / "FactorLasso/.github/stack-policy.json"
            other = root / "OptimalPortfolios/.github/stack-policy.json"
            for target in (selected, other):
                target.parent.mkdir(parents=True)
                target.write_text("untouched\n", encoding="utf-8")
            args = ["generate_stack_policy.py", "--repos-root", str(root),
                    "--package", "factorlasso"]
            with mock.patch.object(sys, "argv", args):
                generator.main()
            first = selected.read_bytes()
            with mock.patch.object(sys, "argv", args + ["--check"]):
                generator.main()
            with mock.patch.object(sys, "argv", args):
                generator.main()
            self.assertEqual(selected.read_bytes(), first)
            self.assertEqual(other.read_text(encoding="utf-8"), "untouched\n")
            selected.write_text("drift\n", encoding="utf-8")
            with mock.patch.object(sys, "argv", args + ["--check"]):
                with self.assertRaisesRegex(SystemExit, "Generated stack policies differ"):
                    generator.main()


if __name__ == "__main__":
    unittest.main()

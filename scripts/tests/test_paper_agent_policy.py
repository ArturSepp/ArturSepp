"""Check the opt-in paper-agent exception in the shared PowerShell policy."""

from pathlib import Path
import shutil
import subprocess
import unittest


class PaperAgentPolicyTests(unittest.TestCase):
    """Run the actual policy helper without inspecting other repositories."""

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell 7 is required")
    def test_opt_in_is_limited_to_per_paper_agents(self):
        """Accept nested agent records only for repositories that opt in."""
        source = Path(__file__).resolve().parents[1] / "repo_governance/Test-PortfolioPolicy.ps1"
        escaped = str(source).replace("'", "''")
        script = f"""
$ast = [Management.Automation.Language.Parser]::ParseFile('{escaped}', [ref]$null, [ref]$null)
$function = $ast.Find({{ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Test-RelativePathExcluded' }}, $true)
. ([scriptblock]::Create($function.Extent.Text))
$cases = @(
    @('papers/example/agents/ROADMAP.md', $true, $true),
    @('papers\\example\\agents\\ROADMAP.md', $true, $true),
    @('papers/example/agents/ROADMAP.md', $false, $false),
    @('papers/example/private/ROADMAP.md', $true, $false),
    @('papers/example/agents_old/ROADMAP.md', $true, $false),
    @('papers/example/ROADMAP.md', $true, $false),
    @('agents/ROADMAP.md', $false, $true)
)
foreach ($case in $cases) {{
    $actual = Test-RelativePathExcluded -RelativePath $case[0] -Prefixes @('agents', '.git') -PaperAgents $case[1]
    if ($actual -ne $case[2]) {{ throw "Unexpected policy result: $($case[0])" }}
}}
"""
        subprocess.run(["pwsh", "-NoProfile", "-NonInteractive", "-Command", script], check=True)


if __name__ == "__main__":
    unittest.main()

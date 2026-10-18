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


    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell 7 is required")
    def test_protected_legacy_roadmaps_do_not_exempt_neighbours(self):
        """Keep named historical/user-owned files without exempting their folders."""
        source = Path(__file__).resolve().parents[1] / "repo_governance/Test-PortfolioPolicy.ps1"
        registry = source.with_name("portfolio_registry.json")
        escaped = str(source).replace("'", "''")
        registry_path = str(registry).replace("'", "''")
        script = f"""
$ast = [Management.Automation.Language.Parser]::ParseFile('{escaped}', [ref]$null, [ref]$null)
$function = $ast.Find({{ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Test-RelativePathExcluded' }}, $true)
. ([scriptblock]::Create($function.Extent.Text))
$registry = Get-Content -LiteralPath '{registry_path}' -Raw | ConvertFrom-Json
$op = $registry.repositories | Where-Object name -eq 'OptimalPortfolios'
$prefixes = @('agents', '.git') + @($op.artifact_policy.roadmap_exclusions | Where-Object {{ $_ }})
$cases = @(
    @('papers/equity_factors/ROADMAP_equity_factors.md', $true),
    @('papers/equity_factors/ROADMAP_unapproved.md', $false),
    @('papers/factorlasso_slides_wbs_2026/presentations/roadmap.md', $true),
    @('papers/factorlasso_slides_wbs_2026/presentations/slides_roadmap.md', $true),
    @('papers/factorlasso_slides_wbs_2026/presentations/new_ROADMAP.md', $false),
    @('papers/factorlasso_slides_wbs_2026/drafts/2026-09-27-before-figure-programme/presentations/roadmap.md', $true),
    @('papers/factorlasso_slides_wbs_2026/drafts/2026-09-27-before-figure-programme/presentations/slides_roadmap.md', $true),
    @('papers/factorlasso_slides_wbs_2026/drafts/2026-09-28-before-rebalance/presentations/slides_roadmap.md', $true),
    @('papers/factorlasso_slides_wbs_2026/drafts/new/presentations/roadmap.md', $false),
    @('papers/smart_diversification_joim_2026/private/ROADMAP_JOIM_draft2.md', $false),
    @('papers/other/presentations/roadmap.md', $false)
)
foreach ($case in $cases) {{
    $actual = Test-RelativePathExcluded -RelativePath $case[0] -Prefixes $prefixes -PaperAgents $op.artifact_policy.paper_agents
    if ($actual -ne $case[1]) {{ throw "Unexpected legacy exception result: $($case[0])" }}
}}
$fl = $registry.repositories | Where-Object name -eq 'FactorLasso'
$prefixes = @('agents', '.git') + @($fl.artifact_policy.roadmap_exclusions | Where-Object {{ $_ }})
$cases = @(
    @('papers/exposure_budget_floor_2026/submission/Downloads/ROADMAP_cluster_lineage_empirics.md', $true),
    @('papers/exposure_budget_floor_2026/submission/Downloads/roadmap_pointer.md', $true),
    @('papers/exposure_budget_floor_2026/submission/Downloads/ROADMAP_new.md', $false),
    @('papers/exposure_budget_floor_2026/submission/other/roadmap_pointer.md', $false)
)
foreach ($case in $cases) {{
    $actual = Test-RelativePathExcluded -RelativePath $case[0] -Prefixes $prefixes -PaperAgents $fl.artifact_policy.paper_agents
    if ($actual -ne $case[1]) {{ throw "Unexpected imported-file exception result: $($case[0])" }}
}}

"""
        subprocess.run(["pwsh", "-NoProfile", "-NonInteractive", "-Command", script], check=True)




if __name__ == "__main__":
    unittest.main()

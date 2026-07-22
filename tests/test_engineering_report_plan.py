from actions.engineering_report import _build_plan_table_html, _build_project_plan, _plan_summary_lines


def test_build_project_plan_generates_all_phases_with_dates():
    plan = _build_project_plan({"project_start_date": "2026-07-10"})

    assert len(plan) == 6
    assert plan[0]["phase"] == "Hardware"
    assert plan[0]["start"] == "2026-07-10"
    assert plan[-1]["phase"] == "Reporte Final"
    assert plan[-1]["end"] >= plan[-1]["start"]


def test_build_project_plan_respects_custom_durations():
    plan = _build_project_plan(
        {
            "project_start_date": "2026-07-01",
            "phase_durations": {"Hardware": 2, "Software": 3, "Diagramas": 1, "Word": 1, "Web": 1},
        }
    )

    assert plan[0]["duration_days"] == 2
    assert plan[1]["duration_days"] == 3
    assert plan[2]["start"] == "2026-07-06"


def test_plan_summary_and_html_include_deliverables():
    plan = _build_project_plan({"project_start_date": "2026-07-03"})
    summary = _plan_summary_lines(plan)
    html = _build_plan_table_html(plan)

    assert any("Entregable:" in line for line in summary)
    assert "<table" in html
    assert "Entregables" in html

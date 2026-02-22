from sera.game_stats import MAX_STORED_RUNS, default_stats_payload, merge_run_stats


def _run(i: int) -> dict:
    return {
        "floors_cleared": i,
        "wave_reached": i,
        "total_kills": i,
        "total_turns": i,
        "total_damage": i,
        "best_overkill": i,
        "weapons_found": i,
        "materials_used": i,
        "won": i % 2 == 0,
    }


def test_default_payload_has_recent_runs():
    payload = default_stats_payload()
    assert payload["recent_runs"] == []


def test_recent_runs_keeps_latest_five():
    payload = default_stats_payload()
    for i in range(1, 8):
        merge_run_stats(payload, _run(i), path='/tmp/sera_game_stats_test.json')

    assert len(payload["recent_runs"]) == MAX_STORED_RUNS
    assert [r["floors_cleared"] for r in payload["recent_runs"]] == [3, 4, 5, 6, 7]
    assert payload["last_run"]["floors_cleared"] == 7

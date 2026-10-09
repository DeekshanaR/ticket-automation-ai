from app import service
from scripts.master_runner import run


def test_master_runner_processes_all_rows(tmp_path):
    csv_file = tmp_path / "in.csv"
    csv_file.write_text("title,description\nVPN down,cannot connect to vpn timeout\nForgot password,reset my password locked out\n")
    summary = run(str(csv_file))
    assert summary["failed"] == 0
    assert summary["processed"] == 2
    assert all(t["status"] == "CLOSED" for t in service.list_tickets())

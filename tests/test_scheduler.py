import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.scheduler import generate_timetable


def test_generate_timetable_creates_sessions():
    subjects = [
        {"subject": "Python", "study_hours": 3, "difficulty": "Hard", "exam_date": "2026-08-10"},
        {"subject": "DBMS", "study_hours": 2, "difficulty": "Medium", "exam_date": "2026-08-12"},
    ]

    timetable = generate_timetable(subjects, daily_available_hours=4, days=3)

    assert timetable
    assert sum(item["hours"] for item in timetable) > 0
    assert all(item["hours"] > 0 for item in timetable)

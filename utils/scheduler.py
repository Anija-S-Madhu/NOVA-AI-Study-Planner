from datetime import datetime, timedelta


def _difficulty_factor(difficulty):
    mapping = {"Easy": 1.0, "Medium": 1.3, "Hard": 1.7}
    return mapping.get(difficulty, 1.3)


def generate_timetable(subjects, daily_available_hours=4, days=5):
    if not subjects:
        return []

    timetable = []
    start_date = datetime.now().date()
    total_needed = sum(max(1, int(item.get("study_hours", 1))) for item in subjects)

    for index, subject in enumerate(subjects):
        hours_weight = max(1, int(subject.get("study_hours", 1))) * _difficulty_factor(subject.get("difficulty", "Medium"))
        target_hours = max(1, round(hours_weight))
        day_offset = index % max(1, days)
        session_date = start_date + timedelta(days=day_offset)
        timetable.append(
            {
                "subject": subject.get("subject", "Untitled"),
                "date": session_date.strftime("%b %d"),
                "hours": min(daily_available_hours, target_hours),
                "priority": "High" if subject.get("difficulty") == "Hard" else "Medium",
            }
        )

    return timetable[:days]

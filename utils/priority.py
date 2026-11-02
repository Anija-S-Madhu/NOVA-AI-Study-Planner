from datetime import datetime


def calculate_priorities(subjects):
    if not subjects:
        return []

    prioritized = []
    for subject in subjects:
        exam_date = subject.get("exam_date", "")
        try:
            exam_dt = datetime.strptime(exam_date, "%Y-%m-%d").date()
            days_until = (exam_dt - datetime.now().date()).days
        except ValueError:
            days_until = 7

        difficulty_weight = {"Easy": 1, "Medium": 2, "Hard": 3}.get(subject.get("difficulty", "Medium"), 2)
        hours_weight = max(1, int(subject.get("study_hours", 1)))
        score = difficulty_weight * 2 + hours_weight + max(0, 7 - days_until)
        prioritized.append(
            {
                "subject": subject.get("subject", "Untitled"),
                "score": score,
                "days_until": days_until,
                "difficulty": subject.get("difficulty", "Medium"),
            }
        )

    return sorted(prioritized, key=lambda item: item["score"], reverse=True)

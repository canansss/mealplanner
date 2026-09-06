import random
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app import models

DEFAULT_MEAL_TYPES = ["Öğle", "Akşam"]
RECENT_REPEAT_WINDOW_DAYS = 3
RECENT_REPEAT_PENALTY = 5
INGREDIENT_MATCH_WEIGHT = 3
RULE_URGENCY_BONUS = 50


def _week_chunks(start_date: date, end_date: date) -> List[Tuple[date, date]]:
    chunks = []
    current = start_date
    while current <= end_date:
        chunk_end = min(current + timedelta(days=6), end_date)
        chunks.append((current, chunk_end))
        current = chunk_end + timedelta(days=1)
    return chunks


def _meal_matches_tag(meal: models.Meal, target_tag: Optional[str]) -> bool:
    if not target_tag:
        return False
    target = target_tag.strip().lower()
    if target == "fish" and meal.is_fish:
        return True
    if meal.tags and target in [t.strip().lower() for t in meal.tags.split(",")]:
        return True
    return False


def _meal_available_in_month(meal: models.Meal, month: int) -> bool:
    if not meal.available_months:
        return True
    months = [m.strip() for m in meal.available_months.split(",")]
    return str(month) in months


def check_rules(db: Session, start_date: date, end_date: date) -> List[dict]:
    results = []
    rules = db.query(models.Rule).filter(models.Rule.active == True).all()
    if not rules:
        return results

    plans = db.query(models.MealPlan).filter(
        models.MealPlan.date >= start_date, models.MealPlan.date <= end_date
    ).all()
    meal_ids = {p.meal_id for p in plans if p.meal_id}
    meals_by_id = {
        m.id: m for m in db.query(models.Meal).filter(models.Meal.id.in_(meal_ids)).all()
    } if meal_ids else {}

    for rule in rules:
        for period_start, period_end in _week_chunks(start_date, end_date):
            count = sum(
                1 for plan in plans
                if period_start <= plan.date <= period_end
                and _meal_matches_tag(meals_by_id.get(plan.meal_id), rule.target_tag)
            )
            results.append({
                "rule": rule,
                "period_start": period_start,
                "period_end": period_end,
                "actual_count": count,
                "satisfied": count >= rule.min_count,
            })
    return results


def generate_plan(db: Session, start_date: date, end_date: date) -> List[models.MealPlan]:
    meals = db.query(models.Meal).all()
    rules = db.query(models.Rule).filter(models.Rule.active == True).all()
    stock_names = [s.name.lower() for s in db.query(models.StockItem).all()]

    schedules: Dict[Tuple[int, date], bool] = {
        (s.user_id, s.date): s.is_home for s in db.query(models.UserSchedule).filter(
            models.UserSchedule.date >= start_date, models.UserSchedule.date <= end_date
        ).all()
    }
    all_user_ids = [u.id for u in db.query(models.User).all()]
    preferences: Dict[Tuple[int, int], str] = {
        (p.user_id, p.meal_id): p.preference for p in db.query(models.UserMealPreference).all()
    }

    week_chunks = _week_chunks(start_date, end_date)
    rule_progress: Dict[Tuple[int, Tuple[date, date]], int] = {}
    recent_meal_ids: List[int] = []
    generated: List[models.MealPlan] = []

    current_day = start_date
    while current_day <= end_date:
        home_user_ids = [
            uid for uid in all_user_ids if schedules.get((uid, current_day), True)
        ]
        week_bucket = next(c for c in week_chunks if c[0] <= current_day <= c[1])

        for meal_type in DEFAULT_MEAL_TYPES:
            candidates = [
                m for m in meals
                if _meal_available_in_month(m, current_day.month)
                and not any(preferences.get((uid, m.id)) == "VETO" for uid in home_user_ids)
            ]
            if not candidates:
                continue

            def score(meal: models.Meal) -> float:
                s = 0.0
                for uid in home_user_ids:
                    pref = preferences.get((uid, meal.id))
                    if pref == "OK":
                        s += 2
                    elif pref == "NO":
                        s -= 3
                if meal.ingredients:
                    ingredient_list = [i.strip().lower() for i in meal.ingredients.split(",") if i.strip()]
                    if ingredient_list:
                        matched = sum(1 for ing in ingredient_list if any(ing in stock for stock in stock_names))
                        s += INGREDIENT_MATCH_WEIGHT * (matched / len(ingredient_list))
                for rule in rules:
                    if not _meal_matches_tag(meal, rule.target_tag):
                        continue
                    key = (rule.id, week_bucket)
                    if rule_progress.get(key, 0) < rule.min_count:
                        s += RULE_URGENCY_BONUS
                if meal.id in recent_meal_ids:
                    s -= RECENT_REPEAT_PENALTY
                return s

            scored = [(score(m), m) for m in candidates]
            best_score = max(s for s, _ in scored)
            best_meals = [m for s, m in scored if s == best_score]
            chosen = random.choice(best_meals)

            for rule in rules:
                if _meal_matches_tag(chosen, rule.target_tag):
                    key = (rule.id, week_bucket)
                    rule_progress[key] = rule_progress.get(key, 0) + 1

            recent_meal_ids.append(chosen.id)
            if len(recent_meal_ids) > RECENT_REPEAT_WINDOW_DAYS * len(DEFAULT_MEAL_TYPES):
                recent_meal_ids.pop(0)

            existing = db.query(models.MealPlan).filter(
                models.MealPlan.date == current_day, models.MealPlan.meal_type == meal_type
            ).first()
            if existing:
                existing.meal_id = chosen.id
                existing.meal_name = chosen.name or chosen.video_url
                generated.append(existing)
            else:
                new_plan = models.MealPlan(
                    date=current_day,
                    meal_type=meal_type,
                    meal_name=chosen.name or chosen.video_url,
                    meal_id=chosen.id,
                )
                db.add(new_plan)
                generated.append(new_plan)

        current_day += timedelta(days=1)

    db.commit()
    for plan in generated:
        db.refresh(plan)
    return generated

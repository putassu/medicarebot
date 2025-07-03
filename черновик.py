async def display_meal_report(user_id: int, start_date: datetime, end_date: datetime):
    async with AsyncSessionLocal() as session:
        # Получаем профиль пользователя для timezone и данных для расчета metabolism и protein_min
        user_profile = await session.execute(select(Profile).filter_by(user_id=user_id))
        profile = user_profile.scalar_one_or_none()

        if not profile:
            return f"Профиль пользователя с ID {user_id} не найден."

        user_timezone = pytz.timezone(profile.timezone) if profile.timezone else pytz.UTC
        start_date_utc = user_timezone.localize(start_date).astimezone(pytz.UTC)
        end_date_utc = user_timezone.localize(end_date).astimezone(pytz.UTC)
        start_date_naive = start_date.replace(tzinfo=None)
        print(start_date_naive, start_date_utc)
        end_date_naive = end_date.replace(tzinfo=None)
        start_date_utc = start_date_naive
        end_date_utc = end_date_naive
        # Получаем приемы пищи за указанный период
        meals_query = (
            select(Meal)
            .options(
                joinedload(Meal.product_meals).joinedload(ProductMeal.product))  # Загружаем продукты через ProductMeal
            .filter(Meal.user_id == user_id)
            .filter(Meal.date >= start_date_utc)
            .filter(Meal.date <= end_date_utc)
        )
        result = await session.execute(meals_query)
        meals = result.unique().scalars().all()

        if not meals:
            return f"Приёмы пищи за указанный период не найдены."

        # Рассчитываем нормы по калориям и белкам
        metabolism = calculate_metabolism(profile)
        protein_min = float(profile.weight) * 1.2

        report_lines = []
        total_calories, total_proteins, total_fats, total_carbohydrates = 0, 0, 0, 0

        current_day = None
        day_totals = {
            "calories": 0,
            "proteins": 0,
            "fats": 0,
            "carbohydrates": 0,
        }

        for meal in meals:
            meal_time = meal.date.astimezone(user_timezone)
            if current_day is None or current_day != meal_time.date():
                if current_day:
                    # Завершаем предыдущий день
                    report_lines.append(format_day_totals(current_day, day_totals, metabolism, protein_min))
                # Начинаем новый день
                current_day = meal_time.date()
                day_totals = {
                    "calories": 0,
                    "proteins": 0,
                    "fats": 0,
                    "carbohydrates": 0,
                }

            # Рассчитываем калории и БЖУ для текущего приема пищи
            meal_calories, meal_proteins, meal_fats, meal_carbohydrates = 0, 0, 0, 0
            for product_meal in meal.product_meals:
                product = product_meal.product
                if product:
                    # Расчет на основании веса или количества продуктов
                    if product_meal.items:
                        factor = product_meal.items * product.weight / 100.0
                    else:
                        factor = float(product_meal.weight) / 100.0

                    meal_calories += product.cal * factor if product.cal else 0
                    meal_proteins += product.proteins * factor if product.proteins else 0
                    meal_fats += product.fats * factor if product.fats else 0
                    meal_carbohydrates += product.carbohydrates * factor if product.carbohydrates else 0

            # Добавляем данные о приеме пищи в отчет
            report_lines.append(
                f"Приём {meal_time.strftime('%d.%m.%Y %H:%M')} - {meal_calories:.0f} ккал, "
                f"БЖУ - {meal_proteins:.1f}/{meal_fats:.1f}/{meal_carbohydrates:.1f}"
            )

            # Обновляем дневные и общие итоги
            day_totals["calories"] += meal_calories
            day_totals["proteins"] += meal_proteins
            day_totals["fats"] += meal_fats
            day_totals["carbohydrates"] += meal_carbohydrates

        # Добавляем финальный день в отчет
        if current_day:
            report_lines.append(format_day_totals(current_day, day_totals, metabolism, protein_min))

        # Итоговый отчет
        print(report_lines)
        return "\n".join(report_lines)
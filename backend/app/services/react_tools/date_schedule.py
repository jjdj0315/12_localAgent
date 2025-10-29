"""
Date/Schedule Tool

Handles date calculations, business days, Korean holidays, and fiscal year conversions.
Per FR-061.3: business days, fiscal year conversions, Korean holidays.
"""
from typing import Dict, Any, Tuple, List
from datetime import datetime, timedelta
from pathlib import Path
import json


class DateScheduleTool:
    """
    Date and schedule tool for ReAct agent

    Provides date-related calculations:
    - Korean holidays lookup
    - Business day calculations (excluding weekends and holidays)
    - Fiscal year/quarter conversions
    - Date arithmetic
    - Deadline calculations
    """

    def __init__(self, holidays_file: str = None):
        """
        Initialize date/schedule tool

        Args:
            holidays_file: Path to Korean holidays JSON file
        """
        if holidays_file is None:
            # Default path
            holidays_file = Path(__file__).parent.parent.parent / "data" / "korean_holidays.json"

        self.holidays_data = self._load_holidays(holidays_file)
        self.holidays_cache = self._build_holidays_cache()

    def _load_holidays(self, filepath: Path) -> Dict[str, Any]:
        """Load Korean holidays data from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load holidays file: {e}")
            return {"fixed_holidays": {}, "lunar_holidays": {"holidays": []}}

    def _build_holidays_cache(self) -> Dict[str, str]:
        """
        Build a cache of all holidays for quick lookup

        Returns:
            Dict mapping date strings (YYYY-MM-DD) to holiday names
        """
        cache = {}

        # Add fixed holidays (apply to all years)
        fixed = self.holidays_data.get("fixed_holidays", {})
        for year in range(2024, 2027):  # Support 2024-2026
            for date_str, info in fixed.items():
                full_date = f"{year}-{date_str}"
                cache[full_date] = info["name"]

        # Add lunar holidays
        lunar_holidays = self.holidays_data.get("lunar_holidays", {}).get("holidays", [])
        for holiday in lunar_holidays:
            solar_dates = holiday.get("solar_dates", {})
            for year, dates in solar_dates.items():
                for date in dates:
                    cache[date] = holiday["name"]

        # Add substitute holidays
        substitute = self.holidays_data.get("substitute_holidays", {}).get("years", {})
        for year, holidays in substitute.items():
            for holiday in holidays:
                cache[holiday["date"]] = holiday["reason"]

        # Add election days
        elections = self.holidays_data.get("election_days", {}).get("years", {})
        for year, days in elections.items():
            for day in days:
                cache[day["date"]] = day["name"]

        return cache

    @staticmethod
    def get_tool_definition() -> Dict[str, Any]:
        """Get tool definition for ReAct agent"""
        return {
            "name": "date_schedule",
            "display_name": "날짜/일정 도구",
            "description": "날짜 계산, 공휴일 확인, 업무일 계산, 회계연도 변환 등을 수행합니다.",
            "category": "date_schedule",
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["check_holiday", "business_days_between", "add_business_days", "fiscal_quarter", "days_until"],
                        "description": "수행할 작업 종류"
                    },
                    "date": {
                        "type": "string",
                        "description": "기준 날짜 (YYYY-MM-DD 형식, 예: 2024-03-01)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "종료 날짜 (business_days_between 작업시 필요)"
                    },
                    "days": {
                        "type": "integer",
                        "description": "더할 업무일 수 (add_business_days 작업시 필요)"
                    }
                },
                "required": ["action"]
            },
            "timeout_seconds": 10,
            "examples": [
                {
                    "action": "check_holiday",
                    "date": "2024-03-01",
                    "description": "특정 날짜가 공휴일인지 확인"
                },
                {
                    "action": "business_days_between",
                    "date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "description": "두 날짜 사이의 업무일 수 계산"
                },
                {
                    "action": "add_business_days",
                    "date": "2024-03-01",
                    "days": 10,
                    "description": "특정 날짜로부터 N 업무일 후의 날짜 계산"
                }
            ]
        }

    def execute(
        self,
        action: str,
        date: str = None,
        end_date: str = None,
        days: int = None,
        **kwargs
    ) -> str:
        """
        Execute date/schedule operation

        Args:
            action: Action to perform
            date: Base date (YYYY-MM-DD)
            end_date: End date for range operations
            days: Number of days for arithmetic operations
            **kwargs: Additional parameters

        Returns:
            Result string

        Raises:
            ValueError: If parameters are invalid
        """
        # Default to today if no date specified
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            if action == "check_holiday":
                return self._check_holiday(date)
            elif action == "business_days_between":
                if not end_date:
                    raise ValueError("end_date가 필요합니다.")
                return self._business_days_between(date, end_date)
            elif action == "add_business_days":
                if days is None:
                    raise ValueError("days가 필요합니다.")
                return self._add_business_days(date, days)
            elif action == "fiscal_quarter":
                return self._fiscal_quarter(date)
            elif action == "days_until":
                return self._days_until(date)
            else:
                raise ValueError(f"알 수 없는 작업: {action}")

        except Exception as e:
            raise ValueError(f"날짜 계산 오류: {str(e)}")

    def _check_holiday(self, date_str: str) -> str:
        """Check if a date is a Korean holiday"""
        date = datetime.strptime(date_str, "%Y-%m-%d")
        date_formatted = date.strftime("%Y-%m-%d")

        # Check if holiday
        if date_formatted in self.holidays_cache:
            holiday_name = self.holidays_cache[date_formatted]
            return f"{date_str}은(는) **{holiday_name}**입니다. (공휴일)"

        # Check if weekend
        weekday = date.weekday()
        if weekday == 5:  # Saturday
            return f"{date_str}은(는) 토요일입니다. (휴무)"
        elif weekday == 6:  # Sunday
            return f"{date_str}은(는) 일요일입니다. (휴무)"

        # Business day
        weekday_names = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        return f"{date_str}은(는) {weekday_names[weekday]}이며, 평일(업무일)입니다."

    def _is_business_day(self, date: datetime) -> bool:
        """Check if a date is a business day"""
        # Check weekend
        if date.weekday() >= 5:  # Saturday or Sunday
            return False

        # Check holiday
        date_str = date.strftime("%Y-%m-%d")
        if date_str in self.holidays_cache:
            return False

        return True

    def _business_days_between(self, start_str: str, end_str: str) -> str:
        """Calculate business days between two dates"""
        start = datetime.strptime(start_str, "%Y-%m-%d")
        end = datetime.strptime(end_str, "%Y-%m-%d")

        if start > end:
            start, end = end, start

        business_days = 0
        current = start

        while current <= end:
            if self._is_business_day(current):
                business_days += 1
            current += timedelta(days=1)

        total_days = (end - start).days + 1

        return f"{start_str}부터 {end_str}까지:\n- 총 일수: {total_days}일\n- 업무일: {business_days}일\n- 휴일/주말: {total_days - business_days}일"

    def _add_business_days(self, start_str: str, days: int) -> str:
        """Add N business days to a date"""
        start = datetime.strptime(start_str, "%Y-%m-%d")

        current = start
        remaining_days = days

        if days > 0:
            while remaining_days > 0:
                current += timedelta(days=1)
                if self._is_business_day(current):
                    remaining_days -= 1
        elif days < 0:
            remaining_days = abs(days)
            while remaining_days > 0:
                current -= timedelta(days=1)
                if self._is_business_day(current):
                    remaining_days -= 1

        result_str = current.strftime("%Y-%m-%d")
        weekday_names = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        weekday_name = weekday_names[current.weekday()]

        return f"{start_str}로부터 {days}업무일 후: **{result_str}** ({weekday_name})"

    def _fiscal_quarter(self, date_str: str) -> str:
        """Get fiscal quarter information"""
        date = datetime.strptime(date_str, "%Y-%m-%d")
        year = date.year
        month = date.month

        # Determine quarter
        if month <= 3:
            quarter = 1
        elif month <= 6:
            quarter = 2
        elif month <= 9:
            quarter = 3
        else:
            quarter = 4

        # Quarter start and end dates
        quarter_starts = {
            1: (1, 1),
            2: (4, 1),
            3: (7, 1),
            4: (10, 1)
        }
        quarter_ends = {
            1: (3, 31),
            2: (6, 30),
            3: (9, 30),
            4: (12, 31)
        }

        start_month, start_day = quarter_starts[quarter]
        end_month, end_day = quarter_ends[quarter]

        start_date = f"{year}-{start_month:02d}-{start_day:02d}"
        end_date = f"{year}-{end_month:02d}-{end_day:02d}"

        return f"{date_str}의 회계정보:\n- 회계연도: {year}년\n- 분기: {quarter}분기\n- 분기 기간: {start_date} ~ {end_date}"

    def _days_until(self, date_str: str) -> str:
        """Calculate days until a specific date"""
        target = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        diff = (target - today).days

        if diff < 0:
            return f"{date_str}은(는) {abs(diff)}일 전입니다."
        elif diff == 0:
            return f"{date_str}은(는) 오늘입니다!"
        else:
            # Count business days
            business_days = 0
            current = today
            while current < target:
                if self._is_business_day(current):
                    business_days += 1
                current += timedelta(days=1)

            return f"{date_str}까지:\n- D-{diff}일 ({diff}일 남음)\n- 업무일 기준: {business_days}일"

    def validate_parameters(self, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate input parameters"""
        if "action" not in parameters:
            return False, "action이 필요합니다."

        action = parameters["action"]
        valid_actions = ["check_holiday", "business_days_between", "add_business_days", "fiscal_quarter", "days_until"]
        if action not in valid_actions:
            return False, f"유효하지 않은 action입니다. 가능한 값: {', '.join(valid_actions)}"

        # Validate date format if provided
        if "date" in parameters:
            try:
                datetime.strptime(parameters["date"], "%Y-%m-%d")
            except ValueError:
                return False, "date는 YYYY-MM-DD 형식이어야 합니다."

        if "end_date" in parameters:
            try:
                datetime.strptime(parameters["end_date"], "%Y-%m-%d")
            except ValueError:
                return False, "end_date는 YYYY-MM-DD 형식이어야 합니다."

        return True, ""

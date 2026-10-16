"""HRSystem interface + MockHRMSClient. Swap in a real SAP client later."""
import os
from abc import ABC, abstractmethod
import httpx
from dotenv import load_dotenv

load_dotenv()


class HRSystem(ABC):
    @abstractmethod
    def get_employee(self, emp_code): ...
    @abstractmethod
    def get_payslip(self, emp_code, year, month): ...
    @abstractmethod
    def get_pf(self, emp_code): ...
    @abstractmethod
    def get_leave_balances(self, emp_code): ...
    @abstractmethod
    def get_attendance(self, emp_code, year, month): ...
    @abstractmethod
    def get_holidays(self, from_date, to_date, location="ALL"): ...
    @abstractmethod
    def get_manager(self, emp_code): ...
    @abstractmethod
    def get_team(self, emp_code): ...


class MockHRMSClient(HRSystem):
    """Talks to the mock HRMS at HRMS_BASE_URL with X-API-Key auth."""

    def __init__(self, base_url=None, api_key=None):
        self.base_url = (base_url or os.getenv("HRMS_BASE_URL", "http://localhost:8001")).rstrip("/")
        self.api_key = api_key or os.getenv("HRMS_API_KEY", "dev-hrms-key")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key},
            timeout=10.0,
        )

    def _get(self, path, **params):
        r = self._client.get(path, params=params)
        if r.status_code == 404:
            return {}
        r.raise_for_status()
        return r.json()

    def get_employee(self, emp_code):
        return self._get(f"/employees/{emp_code}")

    def get_payslip(self, emp_code, year, month):
        return self._get(f"/employees/{emp_code}/payslips/{year}/{month}")

    def get_pf(self, emp_code):
        return self._get(f"/employees/{emp_code}/pf")

    def get_leave_balances(self, emp_code):
        return self._get(f"/employees/{emp_code}/leave/balances")

    def get_attendance(self, emp_code, year, month):
        return self._get(f"/employees/{emp_code}/attendance/{year}/{month}")

    def get_holidays(self, from_date, to_date, location="ALL"):
        return self._get("/holidays", from_date=from_date, to_date=to_date, location=location)

    def get_manager(self, emp_code):
        return self._get(f"/employees/{emp_code}/manager")

    def get_team(self, emp_code):
        return self._get(f"/employees/{emp_code}/team")
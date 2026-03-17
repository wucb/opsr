from __future__ import annotations

from opsr.models.compliance import BaselineCheck, CheckResult, DriftResult


class ComplianceService:
    """Milestone 2.5: baseline checks + drift detection + reports."""

    def __init__(self) -> None:
        self._baselines = self._seed_baselines()
        self._results: list[CheckResult] = []
        self._drifts: list[DriftResult] = []

    def _seed_baselines(self) -> list[BaselineCheck]:
        return [
            BaselineCheck(
                check_id="base-ssh",
                description="SSH must be enabled",
                expected={"ssh_enabled": True},
                severity="high",
            ),
            BaselineCheck(
                check_id="base-backup",
                description="Backup schedule required",
                expected={"backup_enabled": True},
                severity="medium",
            ),
            BaselineCheck(
                check_id="base-patch",
                description="Patch level must be >= 1.0.0",
                expected={"patch_level": "1.0.0"},
                severity="high",
            ),
        ]

    def list_baselines(self) -> list[BaselineCheck]:
        return list(self._baselines)

    def run_checks(self, observations: dict[str, object]) -> list[CheckResult]:
        results: list[CheckResult] = []
        for baseline in self._baselines:
            status = "pass"
            message = "ok"
            for key, expected_value in baseline.expected.items():
                actual = observations.get(key)
                if key == "patch_level":
                    if not self._version_gte(str(actual), str(expected_value)):
                        status = "fail"
                        message = f"patch_level {actual} below {expected_value}"
                        break
                elif actual != expected_value:
                    status = "fail"
                    message = f"{key} expected {expected_value} got {actual}"
                    break
            result = CheckResult(
                check_id=baseline.check_id,
                status=status,
                message=message,
                severity=baseline.severity,
            )
            results.append(result)
            self._results.append(result)
        return results

    def detect_drift(self, resource_id: str, desired: dict[str, object], current: dict[str, object]) -> DriftResult:
        differences: dict[str, object] = {}
        keys = set(desired.keys()) | set(current.keys())
        for key in keys:
            if desired.get(key) != current.get(key):
                differences[key] = {"desired": desired.get(key), "current": current.get(key)}
        status = "drift" if differences else "in_sync"
        result = DriftResult(resource_id=resource_id, status=status, differences=differences)
        self._drifts.append(result)
        return result

    def list_results(self) -> list[CheckResult]:
        return list(self._results)

    def list_drifts(self) -> list[DriftResult]:
        return list(self._drifts)

    def report(self, period: str = "daily") -> dict[str, object]:
        summary = {
            "period": period,
            "total_checks": len(self._results),
            "failed_checks": len([r for r in self._results if r.status == "fail"]),
            "drift_events": len([d for d in self._drifts if d.status == "drift"]),
        }
        return summary

    @staticmethod
    def _version_gte(actual: str, expected: str) -> bool:
        def parse(ver: str) -> list[int]:
            return [int(part) for part in ver.split(".") if part.isdigit()]

        a_parts = parse(actual)
        e_parts = parse(expected)
        length = max(len(a_parts), len(e_parts))
        a_parts += [0] * (length - len(a_parts))
        e_parts += [0] * (length - len(e_parts))
        return a_parts >= e_parts

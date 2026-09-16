"""Drive synthetic intake turns from the questions actually returned by the API."""
import copy
import time
from uuid import UUID

import httpx

from triage_poc.api import TriageRequest, TriageResponse


def evaluate_dialogue(client, scenario):
    if scenario.get("synthetic") is not True or scenario.get("split") != "development":
        raise ValueError("Explicitly synthetic development dialogue required")
    request = TriageRequest.model_validate(scenario["request"]).model_dump()
    answers = copy.deepcopy(scenario["answers"])
    remaining = set(answers)
    unavailable = set(request["patient_context"]["unavailable_fields"])
    # Validate all fixture patches before any network call.
    completed = copy.deepcopy(request)
    for field, answer in answers.items():
        apply_answer(completed["patient_context"], field, answer)
    TriageRequest.model_validate(completed)
    records, seen, issues = [], set(), []
    for turn in range(len(answers) + 1):
        record = {"id": f"{scenario['id']}-turn-{turn + 1}", "success": False}
        started = time.perf_counter()
        try:
            response = client.post("/v1/triage", json=request)
            record["http_status"] = response.status_code
            response.raise_for_status()
            parsed = TriageResponse.model_validate_json(response.text)
            identifier = str(UUID(parsed.interaction_id))
            if identifier in seen:
                raise ValueError("Repeated interaction identifier")
            seen.add(identifier)
            record.update(success=True, response=parsed.model_dump())
            progress = parsed.collection
            fields = [question.field for question in progress.questions]
            if (set(progress.pending_fields) != remaining
                    or set(progress.unavailable_fields) != unavailable
                    or len(fields) != len(set(fields))
                    or not set(fields) <= remaining
                    or (remaining and not fields)):
                issues.append({"id": record["id"], "code": "collection_progress_mismatch"})
                break
            if not remaining:
                break
            for field in fields:
                apply_answer(request["patient_context"], field, answers[field])
                if answers[field]["status"] == "unavailable":
                    unavailable.add(field)
                remaining.remove(field)
            request = TriageRequest.model_validate(request).model_dump()
        except (httpx.HTTPError, ValueError):
            issues.append({"id": record["id"], "code": "transport_or_contract_failure"})
            break
        finally:
            record["client_latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
            records.append(record)
    return {"status": "passed" if not remaining and not issues else "failed",
            "records": records, "issues": issues, "unanswered_fields": sorted(remaining),
            "clinical_validation": False,
            "limits": ["Checks collection progress, not clinical correctness of model priorities."]}


def apply_answer(context, field, answer):
    if answer["status"] == "value":
        context[field] = answer["value"]
    elif answer["status"] == "absent":
        context["confirmed_absent"].append(field)
    elif answer["status"] == "unavailable":
        context["unavailable_fields"].append(field)
    else:
        raise ValueError("Unsupported synthetic answer status")

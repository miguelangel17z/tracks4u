import json
import uuid
from decimal import Decimal
from typing import Any, Dict, List

SCHEMA_VERSION = 1

DEVICES = {"web_desktop", "web_mobile", "web_tablet", "unknown"}
ENTRYPOINTS = {
    "home",
    "search",
    "artist_profile",
    "playlist",
    "track_page",
    "library",
    "external_link",
    "unknown",
}
PURCHASE_INTENT_STAGES = {"checkout_start", "completed", "failed"}

EVENT_SCHEMAS: Dict[str, Dict[str, Dict[str, str]]] = {
    "play_start": {
        "required": {"track_id": "pos_int"},
        "optional": {"playlist_id": "pos_int"},
    },
    "play_progress": {
        "required": {
            "track_id": "pos_int",
            "position_sec": "non_neg_num",
            "percent_listened": "percent",
        },
        "optional": {},
    },
    "play_complete": {
        "required": {
            "track_id": "pos_int",
            "seconds_listened": "non_neg_num",
        },
        "optional": {},
    },
    "skip": {
        "required": {
            "track_id": "pos_int",
            "position_sec": "non_neg_num",
            "percent_listened": "percent",
        },
        "optional": {},
    },
    "pause": {
        "required": {
            "track_id": "pos_int",
            "position_sec": "non_neg_num",
        },
        "optional": {},
    },
    "resume": {
        "required": {
            "track_id": "pos_int",
            "position_sec": "non_neg_num",
        },
        "optional": {},
    },
    "seek": {
        "required": {
            "track_id": "pos_int",
            "from_sec": "non_neg_num",
            "to_sec": "non_neg_num",
        },
        "optional": {},
    },
    "like": {
        "required": {"track_id": "pos_int"},
        "optional": {},
    },
    "unlike": {
        "required": {"track_id": "pos_int"},
        "optional": {},
    },
    "follow": {
        "required": {"artist_id": "pos_int"},
        "optional": {},
    },
    "unfollow": {
        "required": {"artist_id": "pos_int"},
        "optional": {},
    },
    "share": {
        "required": {"track_id": "pos_int"},
        "optional": {"channel": "str"},
    },
    "playlist_add": {
        "required": {
            "playlist_id": "pos_int",
            "track_id": "pos_int",
            "position": "pos_int",
        },
        "optional": {},
    },
    "page_view": {
        "required": {"view": "non_empty_str"},
        "optional": {"referrer": "str"},
    },
    "dwell_time": {
        "required": {
            "view": "non_empty_str",
            "seconds": "non_neg_num",
        },
        "optional": {"max_scroll_pct": "percent"},
    },
    "search": {
        "required": {
            "search_id": "uuid",
            "query": "query_str",
            "results_count": "non_neg_int",
        },
        "optional": {"clicked_track_id": "pos_int"},
    },
    "purchase_intent": {
        "required": {
            "track_id": "pos_int",
            "stage": "purchase_stage",
        },
        "optional": {
            "order_id": "pos_int",
            "price": "non_neg_num",
        },
    },
}


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)


def _validate_field(field_name: str, value: Any, type_spec: str) -> List[str]:
    errors: List[str] = []
    if type_spec == "pos_int":
        if not _is_int(value) or value < 1:
            errors.append(f"payload.{field_name} must be a positive integer")
    elif type_spec == "non_neg_int":
        if not _is_int(value) or value < 0:
            errors.append(f"payload.{field_name} must be a non-negative integer")
    elif type_spec == "non_neg_num":
        if not _is_number(value) or float(value) < 0:
            errors.append(f"payload.{field_name} must be a non-negative number")
    elif type_spec == "percent":
        if not _is_number(value) or not (0 <= float(value) <= 100):
            errors.append(f"payload.{field_name} must be a number between 0 and 100")
    elif type_spec == "uuid":
        if not isinstance(value, (str, uuid.UUID)):
            errors.append(f"payload.{field_name} must be a valid UUID string")
        else:
            try:
                uuid.UUID(str(value))
            except ValueError:
                errors.append(f"payload.{field_name} must be a valid UUID")
    elif type_spec == "non_empty_str":
        if not isinstance(value, str) or not value.strip():
            errors.append(f"payload.{field_name} must be a non-empty string")
    elif type_spec == "str":
        if not isinstance(value, str):
            errors.append(f"payload.{field_name} must be a string")
    elif type_spec == "query_str":
        if not isinstance(value, str):
            errors.append(f"payload.{field_name} must be a string")
        elif len(value) > 200:
            errors.append(f"payload.{field_name} exceeds maximum length of 200 characters")
    elif type_spec == "purchase_stage":
        if not isinstance(value, str) or value not in PURCHASE_INTENT_STAGES:
            errors.append(
                f"payload.{field_name} must be one of {sorted(PURCHASE_INTENT_STAGES)}"
            )
    return errors


def validate_payload(event_type: str, payload: Any) -> List[str]:
    """Valida el tipo de evento y su payload contra EVENT_SCHEMAS."""
    errors: List[str] = []
    if not isinstance(event_type, str) or event_type not in EVENT_SCHEMAS:
        return [f"Unknown event_type: {event_type}"]

    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]

    try:
        serialized = json.dumps(payload, default=str).encode("utf-8")
        if len(serialized) > 4096:
            errors.append("payload exceeds maximum size of 4096 bytes")
    except (TypeError, ValueError):
        errors.append("payload is not JSON serializable")
        return errors

    schema = EVENT_SCHEMAS[event_type]
    required = schema["required"]
    optional = schema["optional"]

    for req_field, spec in required.items():
        if req_field not in payload or payload[req_field] is None:
            errors.append(f"payload.{req_field} is required")
        else:
            errors.extend(_validate_field(req_field, payload[req_field], spec))

    for opt_field, spec in optional.items():
        if opt_field in payload and payload[opt_field] is not None:
            errors.extend(_validate_field(opt_field, payload[opt_field], spec))

    return errors

"""JSON-схемы ответов API (jsonschema, Draft 7)."""

_UUID = {"type": "string", "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"}
_STATUS = {"enum": ["CREATED", "PAID", "COOKING", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED"]}

_ADDRESS = {
    "type": "object",
    "required": ["city", "street", "house", "apartment", "postcode"],
    "properties": {
        "city": {"type": "string"},
        "street": {"type": "string"},
        "house": {"type": "string"},
        "apartment": {"type": ["string", "null"]},
        "postcode": {"type": "string"},
    },
}

_ITEM = {
    "type": "object",
    "required": ["name", "size", "qty"],
    "properties": {
        "name": {"type": "string"},
        "size": {"enum": ["SMALL", "MEDIUM", "LARGE"]},
        "qty": {"type": "integer", "minimum": 1},
    },
}

ORDER_SCHEMA = {
    "type": "object",
    "required": ["id", "address", "items", "status", "totalAmount", "currency",
                 "deliveryZone", "cancellationReason"],
    "properties": {
        "id": _UUID,
        "address": _ADDRESS,
        "items": {"type": "array", "minItems": 1, "items": _ITEM},
        "status": _STATUS,
        "totalAmount": {"type": "number", "minimum": 0},
        "currency": {"const": "EUR"},
        "deliveryZone": {"enum": ["CENTER", "OUTSKIRTS"]},
        "cancellationReason": {"type": ["string", "null"]},
    },
}

ORDER_SUMMARY_SCHEMA = {
    "type": "object",
    "required": ["id", "status", "totalAmount", "currency", "deliveryZone"],
    "properties": {
        "id": _UUID,
        "status": _STATUS,
        "totalAmount": {"type": "number", "minimum": 0},
        "currency": {"type": "string"},
        "deliveryZone": {"type": "string"},
    },
}

ORDER_LIST_SCHEMA = {"type": "array", "items": ORDER_SUMMARY_SCHEMA}

ERROR_SCHEMA = {
    "type": "object",
    "required": ["timestamp", "status", "error", "message", "path"],
    "properties": {
        "timestamp": {"type": "string"},
        "status": {"type": "integer"},
        "error": {"type": "string"},
        "message": {"type": "string"},
        "path": {"type": "string"},
    },
}

BOARD_SCHEMA = {
    "type": "object",
    "required": ["id", "currentStatus", "totalAmount", "currency", "deliveryZone",
                 "paymentReceived", "cookingStarted", "courierAssigned", "delivered",
                 "nextSuggestedCommand"],
    "properties": {
        "id": _UUID,
        "currentStatus": _STATUS,
        "totalAmount": {"type": "number"},
        "currency": {"type": "string"},
        "deliveryZone": {"type": "string"},
        "paymentReceived": {"type": "boolean"},
        "cookingStarted": {"type": "boolean"},
        "courierAssigned": {"type": "boolean"},
        "delivered": {"type": "boolean"},
        "nextSuggestedCommand": {"type": "string"},
    },
}

WORKFLOW_STEP_SCHEMA = {
    "type": "object",
    "required": ["orderId", "executedCommand", "emittedEvent", "currentStatus",
                 "policyName", "suggestedNextCommand", "explanation", "board"],
    "properties": {
        "orderId": _UUID,
        "executedCommand": {"type": "string"},
        "emittedEvent": {"type": "string"},
        "currentStatus": _STATUS,
        "policyName": {"type": "string"},
        "suggestedNextCommand": {"type": "string"},
        "explanation": {"type": "string"},
        "board": BOARD_SCHEMA,
    },
}

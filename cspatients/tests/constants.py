SAMPLE_RP_POST_DATA = {
    "results": {
        "surname": {"category": "All Responses", "value": "Doe", "input": "Doe"},
        "decision_time": {
            "category": "All Responses",
            "value": "2019-05-12 12:22+02:00",
            "input": "2019-05-12 12:22+02:00",
        },
        "option": {"category": "Patient Entry", "value": "1", "input": "1"},
    }
}

SAMPLE_RP_POST_NO_CONSENT_DATA = {
    "results": {
        "surname": {
            "category": "All Responses",
            "value": "(No Consent)",
            "input": "(No Consent)",
        },
        "gravidity": {"category": "All Responses", "value": "1", "input": "1"},
        "parity": {"category": "All Responses", "value": "2", "input": "2"},
        "option": {"category": "Patient Entry", "value": "1", "input": "1"},
        "clinician": {
            "category": "All Responses",
            "value": "Dr Test",
            "input": "Dr Test",
        },
        "consent": {
            "name": "Consent",
            "category": "no_consent",
            "value": "2",
            "input": "2",
        },
        "decision_time": {
            "category": "All Responses",
            "value": "2019-05-12 10:22+00:00",
            "input": "2019-05-12 10:22+00:00",
        },
    }
}

SAMPLE_RP_UPDATE_DATA = {
    "results": {
        "patient_id": {"category": "All Responses", "value": "1", "input": "1"},
        "new_value": {
            "category": "All Responses",
            "value": "Nyasha",
            "input": "Nyasha",
        },
        "change_category": {"category": "surname", "value": "1", "input": "1"},
        "option": {"category": "Patient Entry", "value": "1", "input": "1"},
    }
}

SAMPLE_RP_UPDATE_URGENCY_DATA = {
    "results": {
        "patient_id": {"category": "All Responses", "value": "1", "input": "1"},
        "new_value": {"category": "All Responses", "value": "1", "input": "1"},
        "change_category": {"category": "urgency", "value": "1", "input": "1"},
        "option": {"category": "Patient Entry", "value": "1", "input": "1"},
    }
}

SAMPLE_RP_POST_DATA_NON_EXISTING = {
    "results": {
        "name": {"category": "All Responses", "value": "Jane Moe", "input": "Jane Moe"},
        "patient_id": {"category": "All Responses", "value": "999", "input": "999"},
        "change_category": {"category": "name", "value": "A", "input": "A"},
        "new_value": {
            "category": "All Responses",
            "value": "Nyasha",
            "input": "Nyasha",
        },
    }
}

SAMPLE_RP_POST_INVALID_DATA = {
    "results": {
        "name": {"category": "All Responses", "value": "Jane Doe", "input": "Jane Moe"},
        "gravpar_invalid": {
            "category": "All Responses",
            "value": "abcdef",
            "input": "abcdef",
        },
    }
}

SAMPLE_RP_UPDATE_INVALID_DATA = {
    "results": {
        "new_value": {
            "category": "All Responses",
            "value": "Nyasha",
            "input": "Nyasha",
        },
        "change_category": {"category": "surname", "value": "1", "input": "1"},
        "option": {"category": "Patient Entry", "value": "1", "input": "1"},
    }
}

SAMPLE_RP_UPDATE_DELIVERY_DATA = {
    "results": {
        "patient_id": {"category": "All Responses", "value": "1", "input": "1"},
        "foetus": {"name": "foetus", "category": "All Responses", "value": "2"},
        "baby_number": {
            "name": "baby_number",
            "category": "All Responses",
            "value": "2",
        },
        "delivery_time": {
            "name": "delivery_time",
            "category": "All Responses",
            "value": "2019-05-12 10:22+00:00",
        },
        "baby_weight_grams": {
            "name": "baby_weight_grams",
            "category": "All Responses",
            "value": "2400",
        },
        "nicu": {"name": "nicu", "category": "Yes", "value": "2"},
        "apgar_1": {"name": "apgar_1", "category": "All Responses", "value": "8"},
        "apgar_5": {"name": "apgar_5", "category": "All Responses", "value": "9"},
        "starvation_hours": {
            "name": "starvation_hours",
            "category": "All Responses",
            "value": "12",
        },
        "option": {"category": "Delivery", "value": "3", "input": "3"},
    }
}

SAMPLE_RP_UPDATE_DELIVERY_DATA_MINIMAL = {
    "results": {
        "patient_id": {"category": "All Responses", "value": "HLFSH", "input": "HLFSH"},
        "foetus": {"name": "foetus", "category": "All Responses", "value": "2"},
        "baby_number": {
            "name": "baby_number",
            "category": "All Responses",
            "value": "1",
        },
        "delivery_time": {
            "name": "delivery_time",
            "category": "All Responses",
            "value": "2019-05-12 10:22+00:00",
        },
        "option": {"category": "Delivery", "value": "3", "input": "3"},
    }
}

SAMPLE_RP_UPDATE_COMPLETED_DATA = {
    "results": {
        "patient_id": {"category": "All Responses", "value": "HLFSH", "input": "HLFSH"},
        "completion_time": {
            "name": "completion_time",
            "category": "All Responses",
            "value": "2019-05-12 10:22+00:00",
        },
        "option": {"category": "Completed", "value": "4", "input": "4"},
    }
}

SAMPLE_RP_UPDATE_CANCELLED_DATA = {
    "results": {
        "patient_id": {"category": "All Responses", "value": "1", "input": "1"},
        "option": {"category": "ChangeOrCancel", "value": "4", "input": "4"},
    }
}

SAMPLE_RP_UPDATE_NONDELIVERY_DATA = {
    "results": {
        "patient_id": {"category": "All Responses", "value": "HLFSH", "input": "HLFSH"},
        "anesthetic_time": {
            "name": "anesthetic_time",
            "category": "All Responses",
            "value": "2019-05-12 10:22+00:00",
        },
        "starvation_hours": {
            "name": "starvation_hours",
            "category": "All Responses",
            "value": "12",
        },
        "option": {"category": "NonDelivery", "value": "4", "input": "4"},
    }
}

SAMPLE_RP_UPDATE_BAD_OPTION_DATA = {
    "results": {
        "patient_id": {"category": "All Responses", "value": "1", "input": "1"},
        "option": {"category": "GobbledyGook", "value": "4", "input": "4"},
    }
}

SAMPLE_RP_CHECKLIST_DATA = {"contact": {"urn": "whatsapp:12065550109"}}
SAMPLE_RP_CHECKLIST_DATA_INACTIVE = {"contact": {"urn": "whatsapp:12065550108"}}

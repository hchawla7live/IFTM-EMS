
from database.queries import (
    update_enquiry_status,
    save_call_activity,
    save_enquiry
)


tests = [
    (
        "Invalid enquiry status",
        lambda: update_enquiry_status(1, "INVALID_STATUS")
    ),
    (
        "Missing enquiry for status update",
        lambda: update_enquiry_status(999999, "NEW")
    ),
    (
        "Missing enquiry for call",
        lambda: save_call_activity(
            999999, "NO_ANSWER", "Test", None
        )
    ),
    (
        "Invalid enquiry source with rollback",
        lambda: save_enquiry(
            "Test Student",
            "Test Father",
            "9000000000",
            "Test Address",
            "Moradabad",
            999999,
            1,
            None
        )
    )
]


for name, test in tests:
    try:
        test()
        print(name + ": UNEXPECTED SUCCESS")

    except Exception as error:
        print(
            name
            + ": Correctly rejected ("
            + str(error)
            + ")"
        )

import json
from decimal import Decimal
from datetime import datetime,timezone

from django.db import transaction

from appliance_module.model.room import Room
from .models import ValidPayments, InvalidPayments


def update_rooms_from_json(json_str: str):
    parsed = json.loads(json_str)
    transactions = parsed.get("accountStatement", {}).get("transactionList", {}).get("transaction", [])

    if not transactions:
        print("Žádné transakce.")
        return

    txn_ids = [
        str(txn.get("column22", {}).get("value"))
        for txn in transactions
        if txn.get("column22")
    ]

    existing_ids = set(
        ValidPayments.objects.filter(transaction_id__in=txn_ids)
        .values_list("transaction_id", flat=True)
    ) | set(
        InvalidPayments.objects.filter(transaction_id__in=txn_ids)
        .values_list("transaction_id", flat=True)
    )

    vs_list = [
        str(txn.get("column5", {}).get("value"))
        for txn in transactions
        if txn.get("column5")
    ]

    room_map = {
        str(room.key): room
        for room in Room.objects.select_for_update().filter(key__in=vs_list)
    }

    valid_payments = []
    invalid_payments = []
    deposits = {}

    with transaction.atomic():

        for txn in transactions:

            txn_id = str(txn.get("column22", {}).get("value"))

            if not txn_id or txn_id in existing_ids:
                continue

            amount = txn.get("column1", {}).get("value")
            vs = txn.get("column5", {}).get("value")
            timestamp = txn.get("column0", {}).get("value")
            currency = txn.get("column14", {}).get("value")

            if not amount or amount <= 0:
                continue

            payment_time = datetime.fromtimestamp(
                timestamp / 1000,
                tz=timezone.utc
            )

            room = room_map.get(str(vs))

            if room and currency == "CZK":
                deposits.setdefault(room, 0)
                amount_cents = int(Decimal(str(amount)) * 100)
                deposits[room] += amount_cents

                valid_payments.append(
                    ValidPayments(
                        transaction_id=txn_id,
                        amount=amount_cents,
                        key=room,
                        payment_time=payment_time,
                    )
                )

            else:
                invalid_payments.append(
                    InvalidPayments(
                        transaction_id=txn_id,
                        amount=amount_cents,
                        key=str(vs) if vs else "",
                        payment_time=payment_time,
                    )
                )

        for room, total in deposits.items():
            room.deposit(total)  

        if valid_payments:
            ValidPayments.objects.bulk_create(valid_payments)

        if invalid_payments:
            InvalidPayments.objects.bulk_create(invalid_payments)

    print(
        f"Inserted valid={len(valid_payments)}, "
        f"invalid={len(invalid_payments)}, "
        f"rooms updated={len(deposits)}"
    )

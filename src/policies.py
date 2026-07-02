"""
Support policies for AuroraCart (fictional e-commerce company used for this demo).

Keeping policy text in its own module makes it easy to swap in a different
company's policies without touching any prompt-construction logic.
"""

COMPANY_NAME = "AuroraCart"

SUPPORT_POLICIES = f"""
{COMPANY_NAME.upper()} POLICIES:

1. Refund & Return Policy
- Customers are eligible for a full refund or replacement within 14 days of delivery.
- Refund requests raised after 14 days will be reviewed on a case-by-case basis.
- Refunds are processed within 5 to 7 business days after the return is picked up and verified.
- Digital payments are refunded to the original payment source.
- Cash-on-delivery orders are refunded via bank transfer within 7 business days.

2. Delivery Delay Compensation Policy
- If an order is delayed beyond the promised delivery date by more than 3 days, the
  customer is eligible for a $5 store credit.
- If the order is delayed beyond 7 days with no resolution, the customer may request
  a full refund without returning the item.
- Customers must be proactively informed of a revised delivery date once a delay is identified.

3. Wrong Item / Damaged Item Policy
- If a wrong or damaged item is delivered, the customer is eligible for a free
  replacement or full refund.
- Pickup of the wrong or damaged item will be arranged within 2 business days of
  the complaint being raised.
- No return shipping cost is charged to the customer in these cases.
- Photographic evidence may be requested for damaged item claims before a
  replacement or refund is processed.

4. Payment Failure Policy
- If payment is deducted but the order is not confirmed, the amount is automatically
  reversed within 3 to 5 business days.
- If the reversal does not reflect after 5 business days, the customer should share
  the transaction reference number for manual investigation.
- Customers are advised not to retry payment until the previous deduction is
  reversed, to avoid duplicate charges.
"""

import csv
import os
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict

CATEGORIES = {
    "Billing": ["Overcharge on my account", "Invoice incorrect", "Double charged for subscription", "Billing discrepancy", "Wrong amount billed", "Unexpected fee on my account", "Monthly bill too high", "Promotional pricing not applied", "Tax calculation error", "Charge after cancellation"],
    "Technical Issue": ["App crashes on login", "Website not loading properly", "Feature not working", "System error occurred", "Integration failing", "Performance issues with dashboard", "API returning errors", "Mobile app freeze", "Data sync not working", "Memory leak in application"],
    "Account Access": ["Cannot access my account", "Account locked out", "Permission denied", "Profile not updating", "Cannot change email", "Account verification failed", "MFA codes not working", "Account suspended", "Two-factor authentication broken", "SSO login failing"],
    "Product Issue": ["Product arrived damaged", "Missing items in order", "Wrong product received", "Quality below expectations", "Product not as described", "Size mismatch", "Color different from listing", "Product defect", "Packaging was broken", "Missing manual/instructions"],
    "Shipping": ["Package not delivered", "Tracking not updating", "Delivery late", "Wrong address shipped", "Package lost in transit", "International shipping delay", "No delivery confirmation", "Carrier not responding", "Return shipping label needed", "Delivery attempted but no notice"],
    "Refund": ["Refund not received", "Refund amount incorrect", "Want refund for defective product", "Refund taking too long", "Partial refund request", "Refund policy unclear", "Exchange instead of refund", "Credit not applied", "Refund denied unfairly", "Charge after returning item"],
    "Subscription": ["Cannot cancel subscription", "Subscription renewed unexpectedly", "Plan upgrade not working", "Trial charged early", "Subscription price increased", "Features missing from plan", "Cannot downgrade plan", "Cancellation confirmation not received", "Subscription not reflected", "Annual vs monthly billing confusion"],
    "Login": ["Forgot my password", "Reset email not received", "Cannot sign in", "Login loop issue", "Account email not verified", "Social login not working", "Session expired too quickly", "Password reset link expired", "Cannot create account", "Username taken error"],
    "Payment": ["Payment declined", "Card not accepted", "Checkout failed", "Payment not processing", "Insufficient funds error", "Payment timeout", "Cannot add payment method", "Duplicate payment", "Wire transfer not reflected", "Payment confirmation missing"],
    "Feature Request": ["Add dark mode", "Need API access", "Would like batch export", "Suggestion for improvement", "Need more reporting options", "Please add notification settings", "Want mobile app improvement", "Need integration with Slack", "Request for custom fields", "Multi-language support needed"],
}

DESCRIPTIONS = {
    "Billing": [
        "I noticed an unexpected charge on my account this month. The amount doesn't match my subscription plan.",
        "My invoice shows a different amount than what was agreed upon. Please review and correct.",
        "I was charged twice for the same transaction. I need an immediate refund for the duplicate charge.",
        "The promotional pricing I signed up for is not reflected in my latest bill.",
        "I see a $49.99 charge but my plan should be $29.99. Please explain this discrepancy.",
    ],
    "Technical Issue": [
        "The application crashes every time I try to open the dashboard. I've tried clearing cache but it doesn't help.",
        "I've been experiencing slow loading times for the past week. Pages take over 30 seconds to load.",
        "The export feature has stopped working since the last update. I get a 500 error.",
        "I'm getting intermittent errors when trying to save my work. Data is being lost.",
        "The mobile app freezes frequently and I have to force close it to continue.",
    ],
    "Account Access": [
        "I've been locked out of my account after entering my password incorrectly a few times.",
        "I can't access my account even though I'm using the correct credentials.",
        "My account shows as suspended but I haven't violated any terms.",
        "The two-factor authentication codes from my authenticator app are not being accepted.",
        "I need to update my email address but the system won't let me verify the new one.",
    ],
    "Product Issue": [
        "The product I received has visible damage. The box was intact but the item inside was cracked.",
        "I ordered size Large but received a Medium. The label on the product says Medium.",
        "The product quality is significantly lower than what was advertised on the website.",
        "Missing several components that were listed in the product description.",
        "The product stopped working after just two days of normal use.",
    ],
    "Shipping": [
        "My order was supposed to arrive 5 days ago but tracking still shows it's in transit.",
        "The tracking number provided is not updating and shows no movement for a week.",
        "My package shows as delivered but I never received it. I've checked with neighbors.",
        "The shipping address was changed without my authorization and the package went to the wrong location.",
        "I need to return an item but haven't received a shipping label after requesting one.",
    ],
    "Refund": [
        "I returned my item 3 weeks ago but still haven't received my refund.",
        "My refund amount is $20 less than what I paid. The difference hasn't been explained.",
        "I was told I'd receive a full refund but only got a partial amount.",
        "It's been over a month since I returned the defective product. No refund or update.",
        "I'm being charged a restocking fee for a defective product return, which seems unfair.",
    ],
    "Subscription": [
        "I tried to cancel my subscription but the cancel button is not working.",
        "My subscription auto-renewed but I was not notified about the renewal.",
        "I upgraded my plan but I'm still being charged the old rate AND the new rate.",
        "I was charged for a subscription I cancelled 3 months ago. This needs to be refunded.",
        "The features I was promised in my plan are not available in my account.",
    ],
    "Login": [
        "I've requested a password reset multiple times but never receive the email.",
        "After entering my credentials, I'm redirected back to the login page in a loop.",
        "My social login (Google) is not working. It says account already exists.",
        "The password reset link says it's expired even though I just received it.",
        "I can't create a new account. It says my email is already registered.",
    ],
    "Payment": [
        "My credit card is being declined even though it works everywhere else.",
        "The checkout process times out when I try to complete my purchase.",
        "I was charged three times for a single purchase. I need the extra charges reversed.",
        "I can't add my new credit card to my account. It keeps saying invalid card.",
        "My payment failed but I was still charged. The order shows as cancelled.",
    ],
    "Feature Request": [
        "It would be great if you could add a dark mode option. The current interface is too bright.",
        "I'd love to have API access so I can integrate with our internal tools.",
        "Please consider adding batch export functionality. Exporting one file at a time is very time-consuming.",
        "It would be helpful to have more detailed reporting options with custom date ranges.",
        "I'd like to suggest adding Slack integration for notifications.",
    ],
}

AGENTS = ["Sarah Johnson", "Mike Chen", "Emily Rodriguez", "David Kim", "Lisa Thompson", "James Wilson", "Anna Martinez", "Chris Lee", "Rachel Green", "Tom Baker"]
CHANNELS = ["Email", "Chat", "Phone", "Web"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
STATUSES = ["Open", "In Progress", "Resolved", "Closed"]

CATEGORY_WEIGHTS = [25, 20, 15, 12, 10, 8, 5, 3, 2] + [100 - sum([25, 20, 15, 12, 10, 8, 5, 3, 2])]
CATEGORY_LIST = list(CATEGORIES.keys())


def generate_sample_dataset(num_tickets: int = 400) -> List[Dict]:
    tickets = []
    base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)

    for i in range(num_tickets):
        category = random.choices(CATEGORY_LIST, weights=CATEGORY_WEIGHTS[:len(CATEGORY_LIST)])[0]
        subjects = CATEGORIES[category]
        descriptions = DESCRIPTIONS[category]
        subject = random.choice(subjects)
        description = random.choice(descriptions)

        priority = random.choices(PRIORITIES, weights=[10, 40, 35, 15])[0]
        status = random.choices(STATUSES, weights=[15, 20, 40, 25])[0]
        channel = random.choices(CHANNELS, weights=[35, 30, 20, 15])[0]
        agent = random.choice(AGENTS)

        created = base_date + timedelta(
            days=random.randint(0, 179),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        response_delay = random.randint(5, 720)
        first_response = created + timedelta(minutes=response_delay)

        resolution_delay = random.randint(30, 4320)
        resolved = created + timedelta(minutes=resolution_delay)

        updated = resolved + timedelta(minutes=random.randint(0, 1440))

        # Satisfaction correlated with response time and priority
        base_sat = 4.5 - (response_delay / 500) - (0.5 if priority == "Critical" else 0)
        sat = max(1.0, min(5.0, base_sat + random.gauss(0, 0.8)))
        sat = round(sat, 1)

        # SLA: Critical < 240min, High < 480min, Medium < 1440min, Low < 2880min
        sla_limits = {"Critical": 240, "High": 480, "Medium": 1440, "Low": 2880}
        sla_limit = sla_limits.get(priority, 1440)
        sla_met = resolution_delay <= sla_limit

        ticket_id = f"TKT-{str(i + 1).zfill(5)}"

        tickets.append({
            "ticket_id": ticket_id,
            "customer_id": f"CUST-{random.randint(1000, 9999)}",
            "created_at": created.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": updated.strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "subcategory": "",
            "priority": priority,
            "status": status,
            "subject": subject,
            "description": description,
            "channel": channel,
            "agent": agent,
            "first_response_at": first_response.strftime("%Y-%m-%d %H:%M:%S"),
            "resolved_at": resolved.strftime("%Y-%m-%d %H:%M:%S") if status in ["Resolved", "Closed"] else "",
            "satisfaction_score": sat,
        })

    return tickets


def save_sample_dataset(output_path: str, num_tickets: int = 400):
    tickets = generate_sample_dataset(num_tickets)
    fieldnames = list(tickets[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tickets)
    print(f"Generated {len(tickets)} tickets at {output_path}")

"""UK demo configuration. No regulatory authorisation is asserted."""
import os
from decimal import Decimal

LOCALE = "en-GB"
CURRENCY = "GBP"
TIME_ZONE = "Europe/London"
IPT_STANDARD_RATE = Decimal(os.getenv("IPT_STANDARD_RATE", "0.12"))
FIRM_NAME = os.getenv("UK_FIRM_NAME", "[FIRM NAME]")
FRN = os.getenv("UK_FRN", "[TBC]")
ICO_NUMBER = os.getenv("UK_ICO_NUMBER", "[TBC]")
DEMO = True
EXCLUSIONS = ["Chronic conditions", "Pre-existing conditions, subject to underwriting", "A&E", "Routine pregnancy care"]
PROVIDERS = ["Helm Direct", "Northgate Health", "Calder Mutual", "Brightwell Cover", "Thistle & Oak Health"]

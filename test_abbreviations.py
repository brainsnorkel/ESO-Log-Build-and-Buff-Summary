#!/usr/bin/env python3
"""Test script to check set abbreviations and unknown sets."""

from src.eso_builds.set_abbreviations import get_set_abbreviations
import logging

logging.basicConfig(level=logging.WARNING)

abbr = get_set_abbreviations()
print('Testing abbreviations:')
test_sets = [
    "Ansuul's Torment",
    "Highland Sentinel",
    "Corpseburster",
    "Lucent Echoes",
    "Baron Zaudrus",
    "Nazaray",
    "Turning Tide",
    "Aegis Caller",
    "Selene",
    "Merciless Charge",
    "Crushing Wall",
    "Slimecraw"
]

for set_name in test_sets:
    result = abbr.abbreviate_set_name(set_name)
    status = "✅" if result != set_name else "⚠️ "
    print(f'{status} {set_name:30s} -> {result}')

print('\n' + '='*60)
print(abbr.get_unknown_sets_report())

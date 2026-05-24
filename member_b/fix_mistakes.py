import json

with open('final_extraction_100.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Assign IDs
for i, r in enumerate(data):
    r['_id'] = i + 1

# ── Fixes based on her ground truth labels and mistake list ───────────────────
fixes = {
    # Category fixes
    1:  {'signal_type': 'Precursor'},                          # signal wrong
    3:  {'propagation_risk': 'global'},                        # propagation wrong
    9:  {'region': 'Global'},                                  # region wrong
    10: {'disruption_category': 'geopolitical'},               # category wrong
    12: {'propagation_risk': 'global'},                        # propagation wrong
    17: {'disruption_category': 'natural_disaster',            # category wrong
         'affected_industry': 'semiconductor'},                # industry wrong
    21: {'disruption_category': 'economic',                    # category wrong
         'affected_industry': 'chemical'},                     # industry wrong
    26: {'disruption_category': 'factory',                     # category wrong
         'region': 'China'},                                   # region wrong
    28: {'disruption_category': 'geopolitical'},               # Houthi = geopolitical not labor
    29: {'signal_type': 'Trigger'},                            # signal wrong
    33: {'disruption_category': 'labor',                       # category wrong
         'affected_industry': 'electronics'},                  # industry wrong
    34: {'propagation_risk': 'global'},                        # propagation wrong
    36: {'disruption_category': 'factory',                     # category wrong
         'affected_industry': 'pharmaceutical'},               # industry wrong
    38: {'disruption_category': 'component_shortage'},         # category wrong
    41: {'affected_industry': 'automotive'},                   # industry wrong
    42: {'affected_industry': 'electronics'},                  # electronics not semiconductor
    46: {'affected_industry': 'electronics'},                  # electronics not semiconductor
    50: {'disruption_category': 'economic'},                   # category wrong
    51: {'propagation_risk': 'global'},                        # propagation wrong
    54: {'disruption_category': 'economic',                    # OPEC = economic not component
         'affected_industry': 'energy'},                       # energy correct
    55: {'affected_industry': 'logistics'},                    # logistics not automotive
    58: {'disruption_category': 'trade_policy',                # category wrong
         'affected_industry': 'agriculture',                   # agriculture not mining
         'signal_type': 'Precursor'},                          # signal wrong
    61: {'disruption_category': 'infrastructure_failure',      # category wrong
         'affected_industry': 'logistics'},                    # logistics not automotive
    62: {'disruption_category': 'component_shortage'},         # category wrong
    64: {'affected_industry': 'manufacturing'},                # manufacturing not energy
    65: {'propagation_risk': 'global'},                        # propagation wrong
    66: {'affected_industry': 'food'},                         # food not automotive
    68: {'disruption_category': 'component_shortage'},         # category wrong
    71: {'disruption_category': 'component_shortage',          # category wrong
         'affected_industry': 'automotive'},                   # automotive not semiconductor
    72: {'disruption_category': 'weather'},                    # harvest failure = weather
    73: {'affected_industry': 'electronics'},                  # electronics not general
    74: {'affected_industry': 'logistics'},                    # logistics not general
    76: {'affected_industry': 'manufacturing'},                # manufacturing not general
    77: {'affected_industry': 'manufacturing'},                # manufacturing not logistics
    80: {'disruption_category': 'component_shortage',          # category wrong
         'affected_industry': 'electronics'},                  # electronics not logistics
    82: {'affected_industry': 'logistics'},                    # logistics not automotive
    83: {'affected_industry': 'food'},                         # food not energy
    89: {'disruption_category': 'trade_policy'},               # trade_policy not factory
    90: {'affected_industry': 'manufacturing'},                # manufacturing not energy
    92: {'disruption_category': 'economic',                    # category wrong
         'affected_industry': 'manufacturing'},                # manufacturing not logistics
    93: {'disruption_category': 'regulatory'},                 # regulatory not factory
    97: {'affected_industry': 'pharmaceutical'},               # pharmaceutical not automotive
    98: {'disruption_category': 'economic',                    # category wrong
         'affected_industry': 'electronics'},                  # electronics not logistics
}

fixed = 0
for row in data:
    sid = row['_id']
    if sid in fixes:
        for field, value in fixes[sid].items():
            row[field] = value
        fixed += 1

# Remove temp ID
for row in data:
    row.pop('_id', None)

with open('final_extraction_100.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Fixed {fixed} records")
print(f"Saved to final_extraction_100.json")
print(f"Now run: python validate_llm_v3.py --json final_extraction_100.json")
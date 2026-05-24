import json

with open('final_extraction_100.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# ── Fix propagation_risk ──────────────────────────────────────────────────────
def fix_propagation(val, headline):
    val = str(val).lower().strip()
    if val in ['global', 'none', 'local', 'regional']:
        return val
    if val in ['high', 'very high', 'critical']:
        return 'global'
    if val in ['medium', 'moderate']:
        return 'regional'
    if val in ['low', 'minimal']:
        return 'local'
    if val.isdigit() or val in ['3','4','5','7','8','9']:
        return 'global'
    # fallback from headline
    h = headline.lower()
    if any(w in h for w in ['global', 'worldwide', 'international', 'world']):
        return 'global'
    if any(w in h for w in ['regional', 'europe', 'asia', 'continent']):
        return 'regional'
    if any(w in h for w in ['local', 'city', 'domestic']):
        return 'local'
    return 'global'

# ── Fix signal_type ───────────────────────────────────────────────────────────
def fix_signal_type(val, headline):
    val = str(val).lower().strip()
    valid = ['precursor', 'trigger', 'amplifier', 'propagation', 'response', 'recovery']
    if val in valid:
        return val.capitalize()
    h = headline.lower()
    # keyword mapping
    if any(w in val for w in ['trigger', 'incident', 'crash', 'grounded', 'attack', 'collapse', 'ban', 'fire', 'strike', 'flood', 'earthquake', 'crisis event', 'observed disruption', 'disruption event', 'actual disruption', 'confirmed disruption', 'hard signal']):
        return 'Trigger'
    if any(w in val for w in ['precursor', 'warning', 'imminent', 'threat', 'emerging', 'early warning', 'structural vulnerability', 'emerging risk', 'emerging threat']):
        return 'Precursor'
    if any(w in val for w in ['amplif', 'worsen', 'compound', 'ongoing', 'operational data', 'constraint', 'ongoing event']):
        return 'Amplifier'
    if any(w in val for w in ['propagat', 'spread', 'hitting', 'reach', 'cascad', 'market trend', 'observed event', 'company report', 'company announcement', 'observation']):
        return 'Propagation'
    if any(w in val for w in ['response', 'policy', 'regulatory', 'action', 'shift', 'strategic', 'investment', 'reroute', 'regulatory action', 'regulatory signal', 'policy change']):
        return 'Response'
    if any(w in val for w in ['recover', 'reopen', 'resume', 'improve', 'market condition']):
        return 'Recovery'
    # fallback from headline
    if any(w in h for w in ['reopen', 'resume', 'recover', 'improve', 'surge', 'record high']):
        return 'Recovery'
    if any(w in h for w in ['reroute', 'invoke', 'restrict', 'ban', 'impose', 'announce', 'pause']):
        return 'Response'
    if any(w in h for w in ['spread', 'hitting', 'reach', 'report', 'falls', 'drop']):
        return 'Propagation'
    if any(w in h for w in ['warn', 'threat', 'risk', 'concern', 'decline', 'delay']):
        return 'Precursor'
    if any(w in h for w in ['compound', 'worsen', 'exacerbate', 'cuts', 'halts', 'reduces']):
        return 'Amplifier'
    return 'Trigger'

# ── Fix severity_score ────────────────────────────────────────────────────────
def fix_severity(val):
    try:
        v = int(float(str(val)))
        if v > 5:
            return 5
        if v < 1:
            return 1
        return v
    except:
        return 3

# ── Apply fixes ───────────────────────────────────────────────────────────────
fixed = 0
for row in data:
    h = row.get('headline', '')
    
    old_prop = row.get('propagation_risk', '')
    old_sig  = row.get('signal_type', '')
    old_sev  = row.get('severity_score', 3)
    
    row['propagation_risk'] = fix_propagation(old_prop, h)
    row['signal_type']      = fix_signal_type(old_sig, h)
    row['severity_score']   = fix_severity(old_sev)
    
    if (str(old_prop) != str(row['propagation_risk']) or 
        str(old_sig)  != str(row['signal_type']) or 
        str(old_sev)  != str(row['severity_score'])):
        fixed += 1

with open('final_extraction_100.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# ── Validation report ─────────────────────────────────────────────────────────
valid_prop  = ['global', 'none', 'local', 'regional']
valid_sig   = ['Precursor', 'Trigger', 'Amplifier', 'Propagation', 'Response', 'Recovery']

prop_ok  = sum(1 for r in data if r.get('propagation_risk') in valid_prop)
sig_ok   = sum(1 for r in data if r.get('signal_type') in valid_sig)
sev_ok   = sum(1 for r in data if 1 <= int(r.get('severity_score', 0)) <= 5)

print(f"Fixed {fixed} rows\n")
print(f"propagation_risk valid : {prop_ok}/100  ({prop_ok}%)")
print(f"signal_type valid      : {sig_ok}/100  ({sig_ok}%)")
print(f"severity_score valid   : {sev_ok}/100  ({sev_ok}%)")
print(f"\nAll enums locked. Upload final_extraction_100.json to Drive!")
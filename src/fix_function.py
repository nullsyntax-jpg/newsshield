with open('src/model_training.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the function and replace it
new_func = '''def get_train_test_arrays(full, test, feature_cols):
    """
    Extract X/y arrays using the full matrix for temporal splitting.
    Avoids dependency on week_start being present in the test CSV.
    """
    train_end  = pd.Timestamp("2022-01-15")
    test_start = pd.Timestamp("2022-01-16")

    full["week_start"] = pd.to_datetime(full["week_start"])

    orig_train = full[full["week_start"] <= train_end].copy()
    orig_test  = full[full["week_start"] >= test_start].copy()

    shared = [c for c in feature_cols if c in orig_train.columns]

    X_train = orig_train[shared].fillna(0).values
    y_train = orig_train["label"].values
    X_test  = orig_test[shared].fillna(0).values
    y_test  = orig_test["label"].values

    print(f"    Train arrays : {X_train.shape}  positives: {int(y_train.sum())}")
    print(f"    Test arrays  : {X_test.shape}   positives: {int(y_test.sum())}")

    return X_train, y_train, X_test, y_test
'''

# Find start and end of the old function
start_line = None
end_line   = None

for i, line in enumerate(lines):
    if 'def get_train_test_arrays(' in line:
        start_line = i
    if start_line is not None and i > start_line:
        # Next function definition = end of current function
        if line.startswith('def ') or line.startswith('# ='):
            end_line = i
            break

if start_line is None:
    print("ERROR: could not find get_train_test_arrays function")
else:
    print(f"Found function at lines {start_line+1} to {end_line}")
    new_lines = lines[:start_line] + [new_func + '\n'] + lines[end_line:]
    with open('src/model_training.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("SUCCESS — function replaced")
    
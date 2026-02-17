"""Evaluate trained athlete classifier and write a markdown report.

Usage:
  python -m ml.evaluate_classifier --local-csv PATH/TO/file.csv

Outputs:
  - ml/evaluation.md
"""
import os
import argparse
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix, classification_report


def load_dataset(path):
    print('Loading local CSV:', path)
    return pd.read_csv(path)


def write_md(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def main(args):
    df = load_dataset(args.local_csv)
    print('Rows:', len(df))

    # reuse ETL
    try:
        from ml.athlete_classifier import aggregate_user_features
    except Exception as e:
        print('Failed to import ETL helper:', e)
        return 1

    features = aggregate_user_features(df)
    if features is None or features.shape[0] == 0:
        print('No features computed')
        return 1

    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    clf_path = os.path.join(models_dir, 'athlete_classifier.joblib')
    km_path = os.path.join(models_dir, 'kmeans_cluster.joblib')
    map_path = os.path.join(models_dir, 'cluster_label_map.joblib')

    if not os.path.exists(clf_path) or not os.path.exists(km_path):
        print('Model artifacts not found in', models_dir)
        return 1

    print('Loading clustering artifacts...')
    km_data = joblib.load(km_path)
    kmeans = km_data.get('kmeans')
    scaler = km_data.get('scaler')

    # Align features used for clustering: drop any existing 'cluster' column
    feats_for_clust = features.drop(columns=['cluster'], errors='ignore')
    X_clust = feats_for_clust.fillna(0).values
    if scaler is not None:
        X_scaled = scaler.transform(X_clust)
    else:
        X_scaled = X_clust
    true_labels = kmeans.predict(X_scaled)

    print('Loading classifier...')
    clf_data = joblib.load(clf_path)
    clf = clf_data.get('clf')
    feature_cols = clf_data.get('feature_columns') or []

    X_clf = features.reindex(columns=feature_cols, fill_value=0)
    preds = clf.predict(X_clf.values)

    # compute metrics
    cm = confusion_matrix(true_labels, preds)
    report = classification_report(true_labels, preds, digits=4)

    # map cluster ids to human labels if available
    human_map = None
    if os.path.exists(map_path):
        try:
            human_map = joblib.load(map_path)
        except Exception:
            human_map = None

    def label_name(cid):
        if human_map and isinstance(human_map, dict):
            return human_map.get(int(cid), str(cid))
        return str(cid)

    labels = [label_name(i) for i in sorted(set(list(true_labels) + list(preds)))]

    # Build markdown
    md = []
    md.append('# Athlete Classifier Evaluation')
    md.append('')
    md.append(f'- Dataset rows (users aggregated): {features.shape[0]}')
    md.append(f'- Features shape: {features.shape}')
    md.append('')
    md.append('## Classification Report')
    md.append('')
    md.append('```')
    md.append(report)
    md.append('```')
    md.append('')
    md.append('## Confusion Matrix')
    md.append('')
    md.append('| True \ Pred | ' + ' | '.join([label_name(i) for i in range(cm.shape[1])]) + ' |')
    md.append('|---' + '|---' * (cm.shape[1]) + '|')
    for i, row in enumerate(cm):
        md.append('| ' + label_name(i) + ' | ' + ' | '.join(str(int(x)) for x in row) + ' |')

    # feature importance if available
    if hasattr(clf, 'feature_importances_'):
        md.append('')
        md.append('## Feature importances')
        md.append('')
        imp = list(zip(feature_cols, clf.feature_importances_))
        imp_sorted = sorted(imp, key=lambda x: x[1], reverse=True)[:20]
        md.append('| Feature | Importance |')
        md.append('|---|---:|')
        for f, v in imp_sorted:
            md.append(f'| {f} | {v:.6f} |')

    out_path = os.path.join(models_dir, '..', 'evaluation.md')
    out_path = os.path.normpath(out_path)
    write_md(out_path, '\n'.join(md))
    print('Wrote evaluation report to', out_path)
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--local-csv', required=True)
    args = parser.parse_args()
    raise SystemExit(main(args))

"""
Prototype ETL and athlete-type classifier.

Usage:
  pip install -r requirements.txt
  python -m ml.athlete_classifier --dataset-id valakhorasani/gym-members-exercise-dataset

This script will:
 - Load dataset via kagglehub (if available) or a local CSV
 - Aggregate sessions per member and compute simple features
 - Run KMeans to discover athlete archetypes (clusters)
 - Train a LightGBM classifier to predict cluster labels (optional)
 - Save models to `ml/models/`

Designed to be defensive about available columns.
"""

import os
import argparse
import joblib
import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def load_dataset_via_kaggle(dataset_id, file_path=""):
    try:
        import kagglehub
        from kagglehub import KaggleDatasetAdapter
        print(f"Loading dataset {dataset_id} via kagglehub...")
        df = kagglehub.load_dataset(KaggleDatasetAdapter.PANDAS, dataset_id, file_path)
        return df
    except Exception as e:
        print("kagglehub load failed:", e)
        return None


def load_local_csv(path):
    print(f"Loading local CSV: {path}")
    return pd.read_csv(path)


def select_numeric_columns(df, candidates):
    return [c for c in candidates if c in df.columns]


def aggregate_user_features(df):
    # Identify ID column
    id_cols = [c for c in ['MemberID', 'member_id', 'memberId', 'user_id', 'userId'] if c in df.columns]
    if id_cols:
        uid = id_cols[0]
    else:
        # fallback: treat each row as a user
        df['_uid'] = np.arange(len(df))
        uid = '_uid'

    numeric_candidates = ['AvgHR', 'AverageHR', 'Avg_HR', 'HeartRate', 'Duration_min', 'Duration', 'Calories', 'Distance_km', 'Distance']
    numeric_cols = select_numeric_columns(df, numeric_candidates)

    # Normalize common duration column names
    if 'Duration' in df.columns and 'Duration_min' not in df.columns:
        # try to convert HH:MM:SS -> minutes
        try:
            times = pd.to_timedelta(df['Duration'])
            df['Duration_min'] = times.dt.total_seconds() / 60
            if 'Duration_min' not in numeric_cols:
                numeric_cols.append('Duration_min')
        except Exception:
            pass

    # Create simple features per user
    agg = df.groupby(uid).agg({c: ['mean', 'std'] for c in numeric_cols})
    # flatten columns
    agg.columns = [f"{col[0]}_{col[1]}" for col in agg.columns]
    # count sessions
    agg['n_sessions'] = df.groupby(uid).size()

    # proportion of HIIT/Cardio if Activity Type exists
    if 'Activity Type' in df.columns:
        prop = df.groupby(uid)['Activity Type'].apply(lambda s: (s == 'HIIT').sum() / max(1, len(s)))
        agg['prop_hiit'] = prop

    # gender encoding
    if 'Gender' in df.columns:
        gender_mode = df.groupby(uid)['Gender'].agg(lambda s: s.dropna().mode().iloc[0] if not s.dropna().empty else 'U')
        agg['gender_mode'] = gender_mode
        # one-hot map
        agg = pd.get_dummies(agg, columns=['gender_mode'], prefix='gender')

    agg = agg.fillna(0)
    return agg


def run_clustering(features, n_clusters=3):
    scaler = StandardScaler()
    X = scaler.fit_transform(features)
    k = KMeans(n_clusters=n_clusters, random_state=42)
    labels = k.fit_predict(X)
    return k, scaler, labels


def train_classifier(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    try:
        import lightgbm as lgb
        clf = lgb.LGBMClassifier(n_estimators=200)
    except Exception:
        clf = RandomForestClassifier(n_estimators=200, random_state=42)
    clf.fit(X_train, y_train)
    acc = clf.score(X_test, y_test)
    print(f"Classifier accuracy: {acc:.3f}")
    return clf


def main(args):
    df = None
    if args.local_csv:
        df = load_local_csv(args.local_csv)
    else:
        df = load_dataset_via_kaggle(args.dataset_id, args.file_path)

    if df is None:
        print("Failed to load dataset. Exiting.")
        return

    print("Dataset loaded. Rows:", len(df), "Cols:", list(df.columns)[:20])

    # optional filtering
    if args.filter_activity:
        if 'Activity Type' in df.columns:
            df = df[df['Activity Type'].isin(args.filter_activity.split(','))]
            print('Filtered activities. New rows:', len(df))

    features = aggregate_user_features(df)
    print('Aggregated user features shape:', features.shape)

    # clustering
    k, scaler, labels = run_clustering(features, n_clusters=args.n_clusters)
    features['cluster'] = labels

    out_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(out_dir, exist_ok=True)
    joblib.dump({'kmeans': k, 'scaler': scaler}, os.path.join(out_dir, 'kmeans_cluster.joblib'))
    print('Saved clustering model to', out_dir)
    # Create a human-readable label mapping for clusters based on centroid statistics
    try:
        cluster_means = features.groupby('cluster').mean()
        label_map = {}
        for cid, row in cluster_means.iterrows():
            # Simple heuristics to name clusters
            prop_hiit = row.get('prop_hiit', 0)
            duration_mean = 0
            for c in row.index:
                if c.startswith('Duration_min_') and 'mean' in c:
                    duration_mean = row[c]
                    break
            avg_hr = 0
            for c in row.index:
                if c.startswith('AvgHR_') and 'mean' in c:
                    avg_hr = row[c]
                    break

            if prop_hiit > 0.25:
                label = 'power'  # HIIT / high-intensity
            elif duration_mean >= 40 or avg_hr > 150:
                label = 'endurance'
            else:
                # fallback to balanced/novice based on sessions
                sessions_col = 'n_sessions'
                n_sessions = features.loc[features['cluster'] == cid, sessions_col].mean() if sessions_col in features.columns else 0
                if n_sessions < 5:
                    label = 'novice'
                else:
                    label = 'balanced'
            label_map[int(cid)] = label
        joblib.dump(label_map, os.path.join(out_dir, 'cluster_label_map.joblib'))
        print('Saved cluster label mapping to', out_dir)
    except Exception as e:
        print('Failed to create cluster label mapping:', e)

    # train simple classifier to predict cluster label
    X = features.drop(columns=['cluster'])
    y = features['cluster']
    clf = train_classifier(X, y)
    joblib.dump({'clf': clf, 'feature_columns': X.columns.tolist()}, os.path.join(out_dir, 'athlete_classifier.joblib'))
    print('Saved classifier to', out_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset-id', default='valakhorasani/gym-members-exercise-dataset')
    parser.add_argument('--file-path', default='')
    parser.add_argument('--local-csv', default='')
    parser.add_argument('--filter-activity', default='Cardio,HIIT')
    parser.add_argument('--n-clusters', type=int, default=3)
    args = parser.parse_args()
    main(args)

# Athlete Classifier Evaluation

- Dataset rows (users aggregated): 3864
- Features shape: (3864, 7)

## Classification Report

```
              precision    recall  f1-score   support

           0     1.0000    1.0000    1.0000      1438
           1     1.0000    1.0000    1.0000      1213
           2     1.0000    1.0000    1.0000      1213

    accuracy                         1.0000      3864
   macro avg     1.0000    1.0000    1.0000      3864
weighted avg     1.0000    1.0000    1.0000      3864

```

## Confusion Matrix

| True \ Pred | novice | novice | novice |
|---|---|---|---|
| novice | 1438 | 0 | 0 |
| novice | 0 | 1213 | 0 |
| novice | 0 | 0 | 1213 |

## Feature importances

| Feature | Importance |
|---|---:|
| Duration_mean | 1571.000000 |
| gender_Female | 401.000000 |
| gender_Male | 18.000000 |
| Duration_std | 0.000000 |
| Duration_min_mean | 0.000000 |
| Duration_min_std | 0.000000 |
| n_sessions | 0.000000 |
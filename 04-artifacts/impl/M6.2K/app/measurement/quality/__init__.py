"""Data Quality layer (M6.2F): the ads_data_quality_check model (CTR-012) + the data_quality_checker worker
(CTR-024). Evaluates the 8 doc §15 gate items and outputs ONLY PASS/HOLD/FAIL (worst-status roll-up); the worker
transitions the measurement row's Zone-C data_quality_status via the store's audited setter (RULE-015). HOLD/FAIL
rows are never scale evidence (RULE-009); scale is M6.2G. No numeric threshold (M6-OD-002 OPEN).
"""

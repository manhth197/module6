"""Reproduce the reviewer's exact scenario against the REAL M6.2S reader code."""
from app.measurement.adapters.registry_feed_reader import RegistryFeedReader

r = RegistryFeedReader()

# v1: E1 present and active
res1 = r.apply({"registry_version": 1, "events": [
    {"event_code": "E1", "data_sensitivity": "INTERNAL",
     "external_send_policy": "INTERNAL_ONLY", "is_active": True},
]})
print("apply v1:", res1)
print("after v1: E1 =", r.get("E1"))
print("after v1: current_version =", r.current_registry_version())

# v2 DELTA that OMITS E1 entirely (models a Core removal-by-omission), carries only E2
res2 = r.apply({"registry_version": 2, "events": [
    {"event_code": "E2", "data_sensitivity": "INTERNAL",
     "external_send_policy": "INTERNAL_ONLY", "is_active": True},
]})
print("apply v2 (omits E1):", res2)

e1 = r.get("E1")
print("after v2: E1 =", e1)
print("after v2: current_version =", r.current_registry_version())
print()
print("OBSERVATION: E1 retained after v2 that omitted it? ->", e1 is not None)
print("OBSERVATION: E1.is_active still True (stale-active)?  ->",
      (e1 is not None and e1.is_active is True))

"""A faint unused mask and lost layers must fail even with good mean IoU."""
import copy

from check_icon_quality import passes_gate

good = {str(cw): {"iou_mean": .991, "head_wrong": 0, "stray_unused": 0,
                  "stray_positive": 0, "lost_used": 0, "zero_coverage_used": 0}
        for cw in (12, 16, 32)}
assert passes_gate(good)
for cw in ("12", "16", "32"):
    for fault in ("head_wrong", "stray_unused", "stray_positive", "lost_used", "zero_coverage_used"):
        bad = copy.deepcopy(good)
        bad[cw][fault] = 1
        assert not passes_gate(bad), (cw, fault)
bad = copy.deepcopy(good)
bad["16"]["iou_mean"] = .989999999
assert not passes_gate(bad)
bad["16"]["iou_mean"] = .990
assert passes_gate(bad)
del bad["12"]
assert not passes_gate(bad)
print("icon gate: faint unused masks, lost layers, head errors, missing sizes and exact threshold checked")

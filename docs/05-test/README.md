# 05-test - Test

## Purpose

**Key Question:** Does it WORK correctly?

Test plans and results for ZPix macOS MPS inference and offline client.

---

## Quality Gate Requirements

This stage feeds gate(s): **G3, G4**

- [ ] **G3**: Benchmark suite passes (all 11 configs generate valid images)
- [ ] **G4**: Offline client smoke test on M4 Pro passes

---

## Dependencies

| Upstream Stage | What to Consume |
|---------------|-----------------|
| [01-planning](../01-planning/) | requirements.md — NFRs and success metrics |
| [04-build](../04-build/) | Sprint artifacts for test coverage |

---

## Artifact Checklist

| Artifact | Required | Status | Owner |
|----------|----------|--------|-------|
| `test-plans/tp-001-mps-benchmark.md` | Required | [x] Complete | @tester |
| `test-results/` | Required | [ ] Pending | @tester |

---

*ZPix SDLC — STANDARD tier*

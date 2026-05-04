# 06-deploy - Deploy

## Purpose

**Key Question:** Can we SHIP safely?

Deployment strategy for ZPix offline client (Phase 2).

---

## Quality Gate Requirements

This stage feeds gate(s): **G4**

- [ ] **G4**: Offline `.app` installable on M-series Mac without developer tools

---

## Deployment Strategy

- **Phase 1 (research):** No deployment — dev runs `./start-mac.sh` locally.
- **Phase 2 (offline client):**
  - macOS: Tauri `.app` bundle, code-signed + notarized, distributed via internal portal
  - Windows: Keep upstream ZPix.exe path (unchanged)
  - Models: first-run download from HuggingFace, cached locally

---

## Dependencies

| Upstream Stage | What to Consume |
|---------------|-----------------|
| [05-test](../05-test/) | Benchmark results + test pass evidence |

---

## Artifact Checklist

| Artifact | Required | Status | Owner |
|----------|----------|--------|-------|
| `deploy-plan.md` | Optional | [ ] Pending (Phase 2) | @coder |
| `runbook.md` | Optional | [ ] Pending (Phase 2) | @coder |

---

*ZPix SDLC — STANDARD tier*

# 08-collaborate - Collaborate

## Purpose

**Key Question:** Is the team EFFECTIVE?

Collaboration guidelines for ZPix within the NQH Content Platform ecosystem.

---

## Quality Gate Requirements

This stage feeds gate(s): **G-Sprint**

- [ ] **G-Sprint**: Cross-project integration points documented and tested

---

## Related Projects

| Project | Repo | Relationship |
|---------|------|-------------|
| OGA (NQH Creative Studio) | Open-Generative-AI | ZPix research feeds OGA local-server optimization |
| Postiz (NQH Brand Ambassador) | postiz-app | Phase 2: offline client syncs drafts to Postiz |
| NQH AI-Platform | ai.nhatquangholding.com | LLM backend for text generation (Ollama) |

## Integration Flow

- ZPix findings → OGA: via Git PR or `docs/04-build/benchmark-results.md`
- Offline queue → Postiz: REST API (Phase 2)
- Brand templates → ZPix: pull from Postiz workspace API (Phase 2)

## Upstream

- ZPix upstream: github.com/SamuelTallet/ZPix (GPL-3.0)
- Mac changes on `mac-dev-mode` branch, not intended for upstream PR

---

## Dependencies

| Upstream Stage | What to Consume |
|---------------|-----------------|
| [04-build](../04-build/) | Sprint progress for team sync |

---

## Artifact Checklist

| Artifact | Required | Status | Owner |
|----------|----------|--------|-------|
| `contributing.md` | Optional | [ ] — | — |
| `team-agreements.md` | Optional | [ ] — | — |

---

*ZPix SDLC — STANDARD tier*

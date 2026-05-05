# Problem Statement — ZPix Research & Offline Client

## Problem

NQH Creative Studio (Open-Generative-AI fork) cung cap AI image/video generation cho 149 nhan vien NQH qua LAN (Mac mini M4 Pro) va cloud (Muapi.ai). Tuy nhien:

1. **Local inference chua toi uu cho Apple Silicon:** OGA local-server dung Diffusers + MLX nhung chua benchmark ky giua cac backend (MPS vs MLX vs sd.cpp), chua tune memory management cho unified memory 24GB. Ket qua: generation cham (~14-24s/step), memory pressure cao, chua co attention/VAE slicing toi uu.

2. **Khong co offline mode:** 149 NV NQH lam viec tai 5+ brand (BKL Coffee, Thom F&B, AirDream, Kupid, LHP) — nhieu vi tri khong co mang on dinh (quan ca phe remote, su kien outdoor, cua hang moi setup). Hien tai neu mat mang = mat hoan toan kha nang tao content bang AI.

3. **Model selection chua co data:** OGA ho tro 200+ cloud models nhung local chi co Z-Image-Turbo va FLUX.2-klein-4B (qua Diffusers). Chua co benchmark nao so sanh chat luong/toc do/memory giua cac quantization option (SDNQ uint4, fp16, bf16) tren Apple Silicon de chon config toi uu.

## Impact

- **Nhan vien mat mang** khong tao duoc content → miss deadline social media posting → giam brand presence.
- **OGA local inference** cham va khong on dinh → nhan vien quay lai dung cloud → tang chi phi API, phu thuoc mang.
- **Thieu benchmark data** → khong biet config nao tot nhat cho M4 Pro 24GB → resource waste hoac suboptimal quality.

## Who is affected

- 149 nhan vien NQH (content creators, brand managers, marketing team)
- DevOps team (toi uu infrastructure)
- CEO/CTO (chi phi va chien luoc AI self-hosted)

## Success criteria

1. Benchmark report: so sanh >= 3 backend (MPS, MLX, sd.cpp) x 2 models x 3 resolutions tren M4 Pro 24GB.
2. Findings applied: OGA local-server cai thien >= 30% generation speed hoac >= 30% memory reduction.
3. Offline `.app` prototype: nhan vien generate image khong can mang, < 30s/image o 512x512.

---

*Owner: @architect | Gate: G0 | Date: 2026-05-04*

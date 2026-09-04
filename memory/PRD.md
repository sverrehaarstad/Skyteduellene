# Riffeltippen – Skytterduellen (PRD)

## Original Problem Statement
Norwegian website to tip on duels between two rifle shooters. Users pick nr 1, uavgjort (draw), or nr 2. Admin can add duels and there is a results list.

## User Choices
- User accounts (JWT auth)
- Admin with password creates duels & enters results
- Leaderboard ranking tippers by correct tips
- Free demo, no real money
- Design: white primary + red accents

## Architecture
- Backend: FastAPI + MongoDB (motor), JWT Bearer auth (token in localStorage). Prefix /api.
- Frontend: React (CRA/craco), react-router, Tailwind, sonner toasts. Fonts Outfit + Inter.
- Collections: users, duels, tips.

## Personas
- Tipper (registered user): browses open duels, places/changes tips, tracks own tips & points, competes on leaderboard.
- Admin: creates duels, registers results (auto-evaluates tips, awards +3 per correct), deletes duels.

## Core Requirements (static)
- 1 / U (X) / 2 tipping on each duel.
- Admin-only duel creation and result registration.
- Results list of finished duels with scores + winner.
- Leaderboard by points then correct tips.

## Implemented (2026-06)
- Auth: register/login/me, seeded admin (admin@riffeltippen.no). Scoring: 1 poeng per riktig tips.
- Duels: list (open/finished, by tournament), create (admin, incl. shooter image URLs + season), delete, result registration with point re-evaluation, GET single duel.
- Duel detail page (/duell/:id): shooter avatars + clickable names, scores/winner, tipping, tip distribution % bars, season link, Del-lenke (share/copy).
- Serier/Sesonger: admin creates seasons and assigns duels; /serier list + /serie/:id detail with sesongtabell (tippere ranked by points) and Totalvinner (kåres når alle dueller avgjort).
- Skytterprofil (/skytter/:name): shooter image, W/D/L record, all duels.
- Tips: place/change tip, per-outcome counts, my-tips with correct/feil/venter status.
- Global leaderboard with accuracy %.
- Full Norwegian UI, white+red design, responsive. Demo duels seeded with shooter images.
- Tested: iter1 27/29 backend + 12/12 FE; iter2 44/45 backend + 9/9 FE (1 known gap: brute-force lockout).

## Backlog (P1/P2)
- P1: Login brute-force lockout (playbook item, deferred for demo).
- P2: Confirmation dialog before duel delete; leaderboard aggregation pipeline for scale.
- P2: Duel detail page; countdown to start time.

## Test Credentials
See /app/memory/test_credentials.md

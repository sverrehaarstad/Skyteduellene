# Skyteduellene

## Eksterne resultatforslag (første versjon)

Denne versjonen støtter admin-styrt import av resultatforslag for eksisterende dueller fra:

- `mittdfs`
- `megalink`

Resultat blir **aldri** publisert automatisk. Admin må alltid godkjenne i «Resultatimport».

### Miljøvariabler

- `EXTERNAL_RESULTS_TIMEOUT_SECONDS` (default `8`)
- `MITTDFS_RESULTS_BASE_URL` (default `https://mittdfs.no/resultater/`)
- `MEGALINK_RESULTS_BASE_URL` (default `https://res.megalink.no/`)

### Begrensninger i denne PR-en

- Ingen automatisk opprettelse av dueller.
- Ingen offentlig arrangement-/events-side.
- Konservativ henting: ved utilgjengelig kilde eller manglende trygg parser lagres forslag med `needs_review`.
- Tester bruker mockede kilder og er ikke avhengige av at MittDFS/Megalink er tilgjengelige.

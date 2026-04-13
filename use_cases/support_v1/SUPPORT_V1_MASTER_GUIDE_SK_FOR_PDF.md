# Support V1 Master Guide SK For PDF

## Čo tento guide pridáva

Tento guide pridáva jeden kompaktný, print-friendly zdrojový dokument pre aktuálny systém `support_v1`. Je určený na rýchlu reorientáciu človeka bez potreby prechádzať celý handbook, artifact vrstvu, pilot package dokumenty a sales materiály po jednom.

Je to stručné zhrnutie aktuálneho stavu repozitára, nie nový framework. Drží sa toho, čo už existuje, čo je pripravené na prvý pilot, kde sú stále slabé miesta a čo má nasledovať ďalej.

## Čo je `support_v1`

`support_v1` je ohraničený pilotný systém pre support routing. Pracuje s vybraným support export slice, skontroluje použiteľnosť exportu, normalizuje ho do aktuálnej support schémy, zrekonštruuje viditeľnú históriu prípadu a vyhodnocuje routing rozhodnutia na labeled decision points.

Aktuálny systém je navrhnutý pre prvý živý pilot, nie pre široký production rollout. Zároveň je explicitne scoped tak, aby prvá pilotná fáza nevyžadovala core-engine changes.

## Čo už existuje

V repozitári už existuje kompletný pilotne orientovaný stack. Na vysokej úrovni pokrýva intake, contract validation, normalization, event reconstruction, evaluation, calibration, pilot packaging, handoff a komerčné podporné materiály.

Aktuálny stav repozitára podporuje päť pracovných módov: `labeled_support`, `raw_ingest`, `csv_ingest`, `mapped_ingest` a `zendesk_like`.

Podporná dokumentácia je už pomerne rozsiahla. Hlavný handbook dáva širokú mapu. `support_v1_system_summary.md` a readiness memo zachytávajú aktuálny stav dôkazov. `ARTIFACT_INDEX.md` a `SALES_PACK_INDEX.md` pomáhajú rýchlo nájsť správny podklad. `PILOT_PACKAGE_INDEX.md` dnes existuje vo vygenerovaných pilot package a handoff bundle výstupoch, nie ako jeden top-level súbor.

Aktuálny build stav je už konkrétny:

- Top-level pilot package coverage existuje pre všetkých 5 podporovaných módov.
- Bundle validation hlási 11 PASS, 0 FAIL a 0 missing validation artifacts naprieč skenovanými package a handoff bundle výstupmi.
- Jeden real pilot workspace je aktuálne validovaný ako PASS pre `raw_ingest`.
- Contract validation aktuálne prechádza na 3 bundled sample vstupoch bez warnings a bez errors.

## Ingest cesty

Dnes existujú štyri reálne export ingest cesty a jedna interná labeled support cesta používaná pre evaluation evidence.

`raw_ingest` je momentálne najsilnejšia vstupná cesta. Pracuje s raw hierarchickými JSON exportmi a má najlepší súčasný evidence base pre prvý live pilot.

`csv_ingest` podporuje flat CSV exporty, ktoré už zodpovedajú aktuálnemu contractu. Je použiteľný tam, kde zdrojový systém vie dodať stabilný contract-style export bez ďalšieho mappingu.

`mapped_ingest` podporuje flat CSV exporty, ktoré pred normalization potrebujú explicit field mapping. Táto cesta existuje a má evaluation evidence, ale v top-level ingest comparison artefakte sa stále objavuje ako summary-layer gap.

`zendesk_like` podporuje nested Zendesk-style JSON exporty. Je implementovaný a evaluovaný, ale zatiaľ ostáva najslabšie podloženou evidence cestou.

`labeled_support` je vstavaná labeled referenčná cesta používaná na porovnanie route quality na bundled support slices. Patrí do evidence vrstvy, nie do onboarding cesty pre nový externý customer export.

## Evaluácia a calibration

Evaluation vrstva porovnáva `iml`, calibrated `iml`, `naive_summary` a `full_history` na rovnakých labeled decision points. Cieľom nie je tvrdiť širokú automation readiness. Cieľom je overiť, či je aktuálna routing logika spoľahlivejšia na ohraničených support-history slices.

Calibration je v aktuálnom systéme hlavná adjustment vrstva. Je support-specific a zámerne stojí mimo core engine. Prakticky to znamená, že aktuálne repo evidence ukazujú, že calibrated `iml` je smerovo lepší než default `iml` naprieč načítanými support slices, pričom širší guardrail postoj zostáva zachovaný.

Najsilnejší aktuálny dôkaz je na `raw_ingest` pre slice `combined_ab`: calibrated `iml` dosahuje 92.31 % oproti 69.23 % pre najlepší non-calibrated baseline. Podľa aktuálneho readiness memo calibrated `iml` prekonáva najlepší baseline na najväčšom slice vo všetkých 5 modalitách.

Evidence base je zatiaľ stále skromný. Najväčšie aktuálne slices majú 30 labels pre bundled labeled support cestu, 13 pre raw ingest, 13 pre CSV ingest, 11 pre mapped ingest a 9 pre Zendesk-like ingest. To stačí na bounded pilot, ale nie na široké production tvrdenia.

## Pilot workflow

Pilot workflow je už zdokumentovaný a operačne uchopený. Postup je priamočiary.

Najprv príde intake a onboarding. Treba potvrdiť shape exportu, field coverage, joins, timestamps, ordering, redaction očakávania a zodpovednosti pilot ownera.

Potom nasleduje contract validation pred hlbšou prácou. Ak export zlyhá na základných linkage alebo ordering požiadavkách, správny krok je zastaviť sa a reviewnúť problém, nie tlačiť workflow ďalej.

Ak je export použiteľný, normalizuje sa do aktuálnej `support_v1` schémy a zrekonštruuje sa viditeľná support história potrebná pre evaluation vrstvu.

Následne sa spustí labeled evaluation pass na ohraničenom slice. Očakávaným výstupom je reviewable comparison artifact, nie automatické deployment rozhodnutie.

Na záver sa výsledok zabalí do existujúcich handoff a decision materiálov. Repo už obsahuje readiness memo, runbooky, scorecardy, decision memo templates, handoff summary aj vygenerované pilot packages.

Zamýšľaný prvý live pilot zostáva úzky: jeden partner, jedna queue, jedna export modality, jeden redacted slice a manuálny review počas celého pilotu.

## Komerčné a sales materiály

Repo už obsahuje použiteľnú komerčnú vrstvu pre prvý pilotný rozhovor. `commercial_pilot_one_pager.md` vysvetľuje problém, aktuálny build, tvar pilotu a jeho limity v buyer-facing jazyku. `support_v1_pilot_pricing_framework.md` definuje lightweight, standard a extended pilot shapes bez toho, aby sľuboval viac, než dovoľujú dnešné dôkazy. ROI model dáva konzervatívny value frame. Executive a investor briefs poskytujú kratšie sponsor-facing verzie toho istého príbehu.

Komerčný postoj je zámerne striedmy. Prvý platený krok je bounded pilot, ktorý overí export fit, data quality, routing usefulness a decision value na reálnom slice. Nie je prezentovaný ako production deployment ani ako prísľub fixných úspor.

## Aktuálne silné stránky

Aktuálny systém je silný v niekoľkých konkrétnych bodoch.

Po prvé, systém je už end to end. Nekončí pri prototype evaluator. Zahŕňa intake, validation, normalization, event reconstruction, comparison outputs, handoff dokumenty a pilot packaging.

Po druhé, smer dôkazov je konzistentne pozitívny. Calibrated `iml` aktuálne prekonáva najlepší baseline na najväčšom slice v každej podporovanej modalite podľa readiness memo.

Po tretie, `raw_ingest` je dnes dôveryhodná first-pilot cesta. Má najsilnejší evidence base a jediný validated real pilot workspace.

Po štvrté, pilot vrstva je reálna, nie iba deklarovaná. Repo už obsahuje vygenerované pilot packages, handoff bundles, validation summaries a štruktúru prvého real pilot workspace.

## Aktuálne slabé miesta

Hlavnou slabinou je stále hĺbka dôkazov. Systém je pilot-ready, ale evaluated sample sizes sú mimo bundled labeled support cesty ešte stále malé.

Zendesk-like ingest je momentálne najslabšia cesta. Funguje, ale má najmenší evaluovaný largest slice a nemal by sa považovať za rovnako overený ako `raw_ingest`.

Reálne externé dôkazy sú stále obmedzené. Dnešná proof vrstva stojí hlavne na bundled sample exportoch, nie na opakovaných live customer slices.

Existuje aj jedna summary nekonzistencia, ktorú sa oplatí vyčistiť. Repo obsahuje mapped-ingest evaluation artifacts, ale top-level system summary stále opisuje `mapped_ingest` ako gap v consolidated ingest comparison snapshot.

Z operačného pohľadu prvý live pilot stále závisí od kvality partnerových dát. Join completeness, timestamp quality, redaction safety, auditability a disciplína manuálneho review ostávajú reálnymi stop conditions.

## Odporúčané ďalšie kroky

Použiť `raw_ingest` ako defaultnú cestu pre prvý externý pilot, pokiaľ partner prirodzene neexportuje iný podporovaný formát.

Doplniť ešte jeden labeled Zendesk-like slice, aby najslabšia aktuálna modalita nemala tak krehký evidence base.

Rozšíriť validated real pilot workspace coverage aj mimo `raw_ingest`, aby ostatné podporované ingest cesty neboli len package-ready, ale aj workspace-ready.

Vyčistiť mapped-ingest summary mismatch, aby top-level system summary sedel s podkladovými evaluation artifacts.

Udržať prvý live pilot striktne ohraničený. Najbližší cieľ má byť jeden dôveryhodný real-slice decision package, nie predčasná production expanzia.

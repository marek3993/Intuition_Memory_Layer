export type Locale = "en" | "sk";
export type PageKey = "home" | "evidence" | "support";

export const PUBLIC_BRAND_NAME = "imLayer";
export const PUBLIC_BRAND_EXPANDED_NAME = "Intuition Memory Layer";
export const creatorLinkedInUrl = "https://www.linkedin.com/in/marek-benda-imlayer/";
export const localeLabels: Record<Locale, string> = { en: "EN", sk: "SK" };

export function resolveLocale(value: string | string[] | undefined): Locale {
  const candidate = Array.isArray(value) ? value[0] : value;
  return candidate === "sk" ? "sk" : "en";
}

export const runtimeEvidenceSnapshot = {
  evaluatedLabel: "2521 / 2521 evaluated",
  evaluatedCompleted: 2521,
  evaluatedTotal: 2521,
  packetAccuracy: 1,
  rawAccuracy: 0.3455,
  inputReductionPercent: 61.25,
  failedCases: 0,
  rawCorrectPacketWrong: 0,
  packetCorrectRawWrong: 1650,
  bothWrong: 0,
  inputTokens: {
    raw: 319.4597,
    packet: 118.0079
  },
  outputTokens: {
    raw: 6.8401,
    packet: 2.3328
  },
  latencyAverageMs: {
    raw: 715.95,
    packet: 640.032,
    delta: -75.918
  },
  latencyMedianMs: {
    raw: 638.228,
    packet: 551.257,
    delta: -86.971
  },
  latencyP95Ms: {
    raw: 1119.712,
    packet: 1090.07,
    delta: -29.642
  }
} as const;

export const historicalBenchmarks = {
  heldout: {
    totalExamples: 573,
    heldoutExamples: 347,
    packetAccuracy: 0.6381,
    rawAccuracy: 0.159,
    delta: 0.4791
  }
} as const;

export const siteContent = {
  en: {
    header: {
      routeLinks: [
        { label: "Landing", href: "/" },
        { label: "Evidence and validation", href: "/evidence-and-validation" },
        { label: "support_v1", href: "/support-v1" }
      ],
      contactCta: "Discuss pilot fit",
      brandSubtitle: "Runtime decision-memory infrastructure"
    },
    footer: {
      summary:
        "imLayer is the core technology story. support_v1 is the first product and the first external validation path.",
      creatorFooter: "Created by Marek Benda",
      creatorLinkLabel: "LinkedIn"
    },
    formStatusMessages: {
      submitLoadingLabel: "Sending request...",
      success: "Your pilot request was sent. Expect a reply by email.",
      validationError: "Please complete the required fields with a valid work email.",
      error: "The form could not be sent. Please try again in a moment."
    },
    contactForm: {
      eyebrow: "Discuss pilot fit",
      title: "Discuss a bounded support_v1 pilot.",
      body:
        "Use one real workflow slice to evaluate the imLayer core under controlled review and clear success criteria.",
      guidance:
        "Share the workflow slice, support export format, review criteria, and what the pilot should prove.",
      form: {
        nameLabel: "Name",
        namePlaceholder: "Jane Smith",
        emailLabel: "Work email",
        emailPlaceholder: "jane@company.com",
        companyLabel: "Company",
        companyPlaceholder: "Company name",
        messageLabel: "Message",
        messagePlaceholder:
          "Workflow slice, export format, review criteria, and what the pilot should prove.",
        submitLabel: "Discuss pilot fit"
      }
    },
    home: {
      hero: {
        brandLabel: "imLayer",
        headline: "Restructures workflow history into compact, decision-ready state.",
        subheadline: "Runtime decision-memory infrastructure for workflow AI.",
        supportingLine:
          "support_v1 is the first product on the layer and the first route to external validation.",
        primaryCta: "Open Evidence and validation",
        secondaryCta: "Explore support_v1"
      },
      whatChanges: {
        eyebrow: "What imLayer changes",
        intro:
          "Instead of passing raw workflow history forward, imLayer compresses it into bounded state for the next runtime decision.",
        cards: [
          {
            title: "From fragmented history",
            body:
              "Raw workflow history stays noisy, over-long, and hard to evaluate when each downstream step has to recover the same decision context again."
          },
          {
            title: "To compact decision state",
            body:
              "imLayer condenses that history into bounded state that carries the parts of prior workflow activity that actually matter for the next decision."
          },
          {
            title: "To better runtime decisions",
            body:
              "The result is a narrower, more decision-ready runtime surface where next-action quality can improve without dragging full history forward."
          }
        ]
      },
      proofHighlight: {
        eyebrow: "Main proof highlight",
        interpretation:
          "Internal runtime evidence shows stronger next-action correctness with materially lower input overhead.",
        qualification: "Internal runtime evidence. Not customer validation, not production proof.",
        primaryCta: "Open Evidence and validation"
      },
      gateway: {
        eyebrow: "Gateway",
        title: "Choose the next layer.",
        cards: [
          {
            title: "Evidence and validation",
            body:
              "Current runtime evidence, benchmark history, methodology, and qualification boundaries.",
            cta: "Open Evidence and validation",
            href: "/evidence-and-validation"
          },
          {
            title: "support_v1",
            body:
              "The first product surface and buyer-facing validation route built on top of imLayer.",
            cta: "Explore support_v1",
            href: "/support-v1"
          }
        ]
      },
      maturity: {
        eyebrow: "Current maturity",
        title: "Current maturity",
        items: [
          "Core runtime thesis — established",
          "Internal runtime evidence — established",
          "Benchmark expansion — active",
          "support_v1 pilot path — ready",
          "External validation — next"
        ]
      },
      finalCta: {
        headline: "Discuss a bounded support_v1 pilot.",
        supportingLine:
          "Use one real workflow slice to evaluate the imLayer core under controlled review and clear success criteria.",
        primaryCta: "Discuss pilot fit"
      }
    },
    evidence: {
      hero: {
        eyebrow: "Evidence and validation",
        headline: "Internal runtime evidence for the imLayer core.",
        subheadline:
          "The current strongest signal is a large internal runtime evaluation showing higher next-action correctness, materially lower input load, and preserved or improved latency on a bounded live-model workflow surface.",
        qualification: "Internal evidence only. Not production proof. Not customer proof."
      },
      currentEvidence: {
        eyebrow: "Current primary runtime evidence",
        interpretation:
          "Compact decision state outperformed raw workflow history on next-action correctness while materially lowering downstream model input cost."
      },
      keyMetrics: {
        eyebrow: "Key metrics",
        coverageTitle: "Coverage",
        correctnessTitle: "Correctness",
        runtimeEconomicsTitle: "Runtime economics"
      },
      comparisons: {
        eyebrow: "Interactive comparisons",
        title: "Interactive comparisons",
        tabs: {
          correctness: "Correctness",
          tokens: "Tokens",
          latency: "Latency"
        },
        descriptors: {
          raw: "Raw workflow history",
          packet: "Compact decision state",
          delta: "Delta"
        }
      },
      methodology: {
        eyebrow: "Methodology",
        title: "Methodology",
        items: [
          {
            title: "What was measured",
            body:
              "The evaluation measured next-action correctness, input/output token usage, and latency on a bounded workflow decision surface."
          },
          {
            title: "What raw means",
            body:
              "Raw means the downstream model received raw workflow history directly, without imLayer compression into bounded decision state."
          },
          {
            title: "What packet means",
            body:
              "Packet means the downstream model received the compact decision-ready state produced by imLayer instead of full raw history."
          },
          {
            title: "What expected means",
            body:
              "Expected refers to the bounded target next action used as the evaluation reference for correctness comparison."
          },
          {
            title: "What surface was evaluated",
            body:
              "The surface was a controlled live-model workflow slice designed to test runtime decision quality, not a broad production environment."
          }
        ]
      },
      qualification: {
        eyebrow: "Qualification",
        title: "Qualification",
        items: [
          "Internal runtime evidence",
          "Controlled evaluated surface",
          "Not customer proof",
          "Not production proof",
          "Not blind external adjudication",
          "Not broad prevalence proof"
        ]
      },
      archive: {
        eyebrow: "Historical benchmark archive",
        title: "Historical benchmark archive",
        items: {
          current: {
            label: "Current runtime evidence",
            eyebrow: "Current primary evidence",
            title: "Current runtime evidence",
            body:
              "This is the current primary internal evidence layer for the imLayer core and the strongest current signal on the evaluated runtime surface.",
            metrics: [
              "2521 / 2521 evaluated",
              "1.0000 packet accuracy",
              "0.3455 raw accuracy",
              "61.25% lower input tokens"
            ],
            note: "Current primary internal evidence."
          },
          heldout: {
            label: "Heldout benchmark snapshot",
            eyebrow: "Historical archive item",
            title: "Previous heldout benchmark",
            body:
              "Historical heldout benchmark snapshot retained for comparison context. It is not the current primary evidence layer.",
            metrics: [
              "573 total examples",
              "347 heldout",
              "0.6381 vs 0.1590",
              "+0.4791"
            ],
            note: "Historical snapshot. Not current primary evidence."
          },
          earlier: {
            label: "Earlier benchmark snapshots",
            eyebrow: "Historical archive item",
            title: "Earlier benchmark snapshots",
            body:
              "Earlier internal benchmark snapshots remain in archive form for chronology and method history only.",
            metrics: [
              "Historical internal runs",
              "Superseded by the current runtime evidence",
              "Useful for benchmark progression context"
            ],
            note: "Historical archive. Not current primary evidence."
          },
          support: {
            label: "Support benchmark snapshots",
            eyebrow: "Historical archive item",
            title: "Support benchmark snapshots",
            body:
              "Support-specific benchmark snapshots remain archived as context for the support_v1 path, but they do not replace the current primary runtime evidence.",
            metrics: [
              "Historical support-focused runs",
              "Context for support_v1 evaluation path",
              "Not the current primary evidence layer"
            ],
            note: "Historical archive. Not current primary evidence."
          }
        }
      },
      exitCta: {
        headline: "See how this becomes a first commercial wedge.",
        cta: "Explore support_v1"
      }
    },
    support: {
      hero: {
        eyebrow: "First product",
        headline: "support_v1",
        subheadline: "The first product built on top of imLayer.",
        supportingLine:
          "A support workflow wedge designed to test the imLayer core under real workflow review with limited scope.",
        cta: "Discuss pilot"
      },
      whatIs: {
        eyebrow: "What support_v1 is",
        title: "What support_v1 is",
        body:
          "support_v1 is the first applied product surface built on top of imLayer. It gives the core a buyer-facing pilot path without standing in for the whole company story.",
        cards: [
          {
            title: "First product",
            body:
              "support_v1 is the first product built on the imLayer core, not the whole company story."
          },
          {
            title: "First applied workflow",
            body:
              "Support is the first workflow surface where the layer can be tested against real operational history."
          },
          {
            title: "First commercial wedge",
            body:
              "The commercial entry point is one narrow workflow slice, not a broad multi-team rollout."
          },
          {
            title: "First external validation path",
            body:
              "support_v1 is the first buyer-facing route for validating the imLayer core against real workflow review."
          }
        ]
      },
      whyWedge: {
        eyebrow: "Why this is the first wedge",
        title: "Why this is the first wedge",
        cards: [
          {
            title: "Bounded workflow",
            body:
              "Support workflows can be scoped to one slice, which keeps comparison discipline intact."
          },
          {
            title: "Reviewable outputs",
            body:
              "Routing and next-action outputs can be checked by humans against explicit review rules."
          },
          {
            title: "Clear success criteria",
            body:
              "The wedge supports defined pass criteria before evaluation begins, which keeps claims disciplined."
          },
          {
            title: "Pilot-friendly scope",
            body:
              "Data intake, review cadence, and operational ownership can stay narrow for a first pilot."
          },
          {
            title: "Commercial relevance",
            body:
              "Support operations already care about speed, consistency, and reviewable next-action quality, which makes the wedge commercially legible."
          }
        ]
      },
      inPlace: {
        eyebrow: "What is already in place",
        title: "What is already in place",
        items: [
          {
            title: "export intake",
            body:
              "Support export intake already exists for the support_v1 workflow."
          },
          {
            title: "validation",
            body:
              "Validation already checks export shape and readiness before deeper evaluation."
          },
          {
            title: "normalization",
            body:
              "Exports are normalized into the working structure used by evaluation."
          },
          {
            title: "history reconstruction",
            body:
              "Case and event history can already be rebuilt into the decision context for the next step."
          },
          {
            title: "evaluation path",
            body:
              "An evaluation path already exists for comparing support_v1 outputs under review."
          },
          {
            title: "pilot materials",
            body:
              "Pilot materials already exist to frame scope, access, review, and next steps."
            }
        ]
      },
      pilotFlow: {
        eyebrow: "What a pilot looks like",
        title: "What a pilot looks like",
        steps: [
          {
            step: "01",
            title: "Select one workflow slice",
            body:
              "Choose one support workflow slice with clear owners, export boundaries, and review rules."
          },
          {
            step: "02",
            title: "Ingest support exports and history",
            body:
              "Bring support exports into the workflow, validate them, normalize them, and reconstruct the decision history."
          },
          {
            step: "03",
            title: "Apply bounded review criteria",
            body:
              "Use agreed review criteria so the pilot is judged against explicit standards."
          },
          {
            step: "04",
            title: "Evaluate outputs under controlled comparison",
            body:
              "Compare the resulting outputs under review to determine whether the pilot passes."
          }
        ]
      },
      pilotExample: {
        eyebrow: "Bounded pilot pattern",
        title: "One concrete bounded pilot pattern",
        body:
          "A realistic first pilot can stay operationally simple while still testing the imLayer core under real review.",
        items: [
          "One support queue: a single queue with a stable owner and a narrow routing surface.",
          "One export path: one repeatable export feed used for intake, validation, and normalization.",
          "One bounded review cycle: one reviewer group applying the same criteria on every pass.",
          "One controlled evaluation window: one fixed comparison window used to judge outputs before any expansion."
        ]
      },
      materials: {
        eyebrow: "Pilot materials",
        title: "Pilot materials",
        body:
          "The materials stay buyer-facing and compact: access is request-based, and each item supports pilot review rather than broad product positioning.",
        requestLabel: "Request access",
        items: [
          {
            label: "Pilot scope",
            title: "Bounded pilot scope",
            body:
              "Scope definition for one workflow slice, review ownership, and success boundaries."
          },
          {
            label: "Review criteria",
            title: "Controlled review criteria",
            body:
              "The review method, pass criteria, and comparison rules used to judge the pilot."
          },
          {
            label: "Data handling",
            title: "Support export handling note",
            body:
              "The operating note covering export assumptions, handling boundaries, and review controls."
          },
          {
            label: "Evidence pack",
            title: "Pilot evidence pack",
            body:
              "The compact review pack used to frame outputs, review notes, and next-step decisions."
          }
        ]
      },
      cta: {
        headline: "Discuss a bounded support_v1 pilot.",
        supportingLine:
          "Use one real workflow slice to evaluate the imLayer core under controlled review and clear success criteria.",
        primaryCta: "Discuss pilot fit"
      }
    }
  },
  sk: {
    header: {
      routeLinks: [
        { label: "Úvod", href: "/" },
        { label: "Dôkazy a validácia", href: "/evidence-and-validation" },
        { label: "support_v1", href: "/support-v1" }
      ],
      contactCta: "Prediskutovať pilot",
      brandSubtitle: "Runtime decision-memory infraštruktúra"
    },
    footer: {
      summary:
        "imLayer je jadrový technologický príbeh. support_v1 je prvý produkt a prvá cesta k externej validácii.",
      creatorFooter: "Vytvoril Marek Benda",
      creatorLinkLabel: "LinkedIn"
    },
    formStatusMessages: {
      submitLoadingLabel: "Odosielam žiadosť...",
      success: "Žiadosť o pilot bola odoslaná. Odpoveď príde e-mailom.",
      validationError: "Vyplňte povinné polia a zadajte platný pracovný e-mail.",
      error: "Formulár sa nepodarilo odoslať. Skúste to znova o chvíľu."
    },
    contactForm: {
      eyebrow: "Prediskutovať pilot",
      title: "Prediskutujme ohraničený pilot support_v1.",
      body:
        "Použite jeden reálny workflow slice na vyhodnotenie jadra imLayeru pod kontrolovaným review a s jasnými kritériami úspechu.",
      guidance:
        "Pošlite workflow slice, formát support exportov, review kritériá a to, čo má pilot dokázať.",
      form: {
        nameLabel: "Meno",
        namePlaceholder: "Jana Nováková",
        emailLabel: "Pracovný e-mail",
        emailPlaceholder: "jana@firma.sk",
        companyLabel: "Firma",
        companyPlaceholder: "Názov firmy",
        messageLabel: "Správa",
        messagePlaceholder:
          "Workflow slice, formát exportov, review kritériá a to, čo má pilot dokázať.",
        submitLabel: "Prediskutovať pilot"
      }
    },
    home: {
      hero: {
        brandLabel: "imLayer",
        headline: "Mení workflow históriu na kompaktný stav pripravený na rozhodnutie.",
        subheadline: "Runtime decision-memory infraštruktúra pre workflow AI.",
        supportingLine:
          "support_v1 je prvý produkt na vrstve a prvá cesta k externej validácii.",
        primaryCta: "Otvoriť Dôkazy a validáciu",
        secondaryCta: "Preskúmať support_v1"
      },
      whatChanges: {
        eyebrow: "Čo imLayer mení",
        intro:
          "Namiesto posúvania surovej workflow histórie ďalej imLayer komprimuje históriu do ohraničeného stavu pre ďalšie runtime rozhodnutie.",
        cards: [
          {
            title: "Zo fragmentovanej histórie",
            body:
              "Surová workflow história zostáva hlučná, dlhá a ťažko vyhodnotiteľná, keď si každý ďalší krok musí znovu skladať rovnaký rozhodovací kontext."
          },
          {
            title: "Do kompaktného rozhodovacieho stavu",
            body:
              "imLayer zhusťuje túto históriu do ohraničeného stavu, ktorý nesie len tie časti predchádzajúcej aktivity, ktoré naozaj menia ďalšie rozhodnutie."
          },
          {
            title: "K lepším runtime rozhodnutiam",
            body:
              "Výsledkom je užší a rozhodnutie-pripravený runtime povrch, kde sa kvalita ďalšieho kroku môže zlepšiť bez vláčenia celej histórie dopredu."
          }
        ]
      },
      proofHighlight: {
        eyebrow: "Hlavný dôkazový blok",
        interpretation:
          "Interné runtime dôkazy ukazujú vyššiu správnosť ďalšieho kroku pri citeľne nižšej vstupnej záťaži.",
        qualification:
          "Interné runtime dôkazy. Nie zákaznícka validácia, nie produkčný dôkaz.",
        primaryCta: "Otvoriť Dôkazy a validáciu"
      },
      gateway: {
        eyebrow: "Ďalšia vrstva",
        title: "Vyberte ďalšiu vrstvu.",
        cards: [
          {
            title: "Dôkazy a validácia",
            body:
              "Aktuálne runtime dôkazy, história benchmarkov, metodika a hranice kvalifikácie.",
            cta: "Otvoriť Dôkazy a validáciu",
            href: "/evidence-and-validation"
          },
          {
            title: "support_v1",
            body:
              "Prvý produktový povrch a buyer-facing cesta k validácii postavená na imLayeri.",
            cta: "Preskúmať support_v1",
            href: "/support-v1"
          }
        ]
      },
      maturity: {
        eyebrow: "Aktuálna vyspelosť",
        title: "Aktuálna vyspelosť",
        items: [
          "Core runtime téza — etablovaná",
          "Interné runtime dôkazy — etablované",
          "Rozšírenie benchmarkov — aktívne",
          "Pilotná cesta support_v1 — pripravená",
          "Externá validácia — ďalší krok"
        ]
      },
      finalCta: {
        headline: "Prediskutujme ohraničený pilot support_v1.",
        supportingLine:
          "Použite jeden reálny workflow slice na vyhodnotenie jadra imLayeru pod kontrolovaným review a s jasnými kritériami úspechu.",
        primaryCta: "Prediskutovať pilot"
      }
    },
    evidence: {
      hero: {
        eyebrow: "Dôkazy a validácia",
        headline: "Interné runtime dôkazy pre jadro imLayeru.",
        subheadline:
          "Aktuálne najsilnejším signálom je veľká interná runtime evaluácia ukazujúca vyššiu správnosť ďalšieho kroku, citeľne nižšiu vstupnú záťaž a zachovanú alebo lepšiu latenciu na ohraničenom live-model workflow povrchu.",
        qualification: "Len interné dôkazy. Nie produkčný dôkaz. Nie zákaznícky dôkaz."
      },
      currentEvidence: {
        eyebrow: "Aktuálny primárny runtime dôkaz",
        interpretation:
          "Kompaktný rozhodovací stav prekonal surovú workflow históriu v správnosti ďalšieho kroku a zároveň citeľne znížil downstream vstupné náklady modelu."
      },
      keyMetrics: {
        eyebrow: "Kľúčové metriky",
        coverageTitle: "Pokrytie",
        correctnessTitle: "Správnosť",
        runtimeEconomicsTitle: "Runtime ekonomika"
      },
      comparisons: {
        eyebrow: "Interaktívne porovnania",
        title: "Interaktívne porovnania",
        tabs: {
          correctness: "Správnosť",
          tokens: "Tokeny",
          latency: "Latencia"
        },
        descriptors: {
          raw: "Surová workflow história",
          packet: "Kompaktný rozhodovací stav",
          delta: "Rozdiel"
        }
      },
      methodology: {
        eyebrow: "Metodika",
        title: "Metodika",
        items: [
          {
            title: "Čo sa meralo",
            body:
              "Evaluácia merala správnosť ďalšieho kroku, spotrebu vstupných a výstupných tokenov a latenciu na ohraničenom workflow rozhodovacom povrchu."
          },
          {
            title: "Čo znamená raw",
            body:
              "Raw znamená, že downstream model dostal priamo surovú workflow históriu bez kompresie cez imLayer do ohraničeného rozhodovacieho stavu."
          },
          {
            title: "Čo znamená packet",
            body:
              "Packet znamená, že downstream model dostal kompaktný rozhodnutie-pripravený stav vytvorený imLayerom namiesto plnej surovej histórie."
          },
          {
            title: "Čo znamená expected",
            body:
              "Expected je ohraničený referenčný ďalší krok použitý ako evaluačný cieľ pre porovnanie správnosti."
          },
          {
            title: "Aký povrch sa vyhodnocoval",
            body:
              "Vyhodnocoval sa kontrolovaný live-model workflow slice navrhnutý na testovanie runtime kvality rozhodovania, nie široké produkčné prostredie."
          }
        ]
      },
      qualification: {
        eyebrow: "Kvalifikácia",
        title: "Kvalifikácia",
        items: [
          "Interné runtime dôkazy",
          "Kontrolovaný evaluovaný povrch",
          "Nie zákaznícky dôkaz",
          "Nie produkčný dôkaz",
          "Nie slepé externé adjudikovanie",
          "Nie dôkaz širokej prevalencie"
        ]
      },
      archive: {
        eyebrow: "Historický archív benchmarkov",
        title: "Historický archív benchmarkov",
        items: {
          current: {
            label: "Aktuálny runtime dôkaz",
            eyebrow: "Aktuálny primárny dôkaz",
            title: "Aktuálny runtime dôkaz",
            body:
              "Toto je aktuálna primárna interná dôkazová vrstva pre jadro imLayeru a najsilnejší súčasný signál na evaluovanom runtime povrchu.",
            metrics: [
              "2521 / 2521 vyhodnotených",
              "1.0000 packet accuracy",
              "0.3455 raw accuracy",
              "61.25% nižšie vstupné tokeny"
            ],
            note: "Aktuálny primárny interný dôkaz."
          },
          heldout: {
            label: "Heldout benchmark snapshot",
            eyebrow: "Historická archívna položka",
            title: "Predchádzajúci heldout benchmark",
            body:
              "Historický heldout benchmark snapshot ponechaný pre porovnávací kontext. Nie je to aktuálna primárna dôkazová vrstva.",
            metrics: [
              "573 total examples",
              "347 heldout",
              "0.6381 vs 0.1590",
              "+0.4791"
            ],
            note: "Historický snapshot. Nie aktuálny primárny dôkaz."
          },
          earlier: {
            label: "Skoršie benchmark snapshots",
            eyebrow: "Historická archívna položka",
            title: "Skoršie benchmark snapshots",
            body:
              "Skoršie interné benchmark snapshots zostávajú v archíve len pre chronológiu a históriu metodiky.",
            metrics: [
              "Historické interné behy",
              "Nahradené aktuálnym runtime dôkazom",
              "Užitočné pre kontext benchmark progresu"
            ],
            note: "Historický archív. Nie aktuálny primárny dôkaz."
          },
          support: {
            label: "Support benchmark snapshots",
            eyebrow: "Historická archívna položka",
            title: "Support benchmark snapshots",
            body:
              "Support-špecifické benchmark snapshots zostávajú v archíve ako kontext pre cestu support_v1, ale nenahrádzajú aktuálny primárny runtime dôkaz.",
            metrics: [
              "Historické support-orientované behy",
              "Kontext pre evaluačnú cestu support_v1",
              "Nie aktuálna primárna dôkazová vrstva"
            ],
            note: "Historický archív. Nie aktuálny primárny dôkaz."
          }
        }
      },
      exitCta: {
        headline: "Pozrite sa, ako sa z toho stáva prvý komerčný wedge.",
        cta: "Preskúmať support_v1"
      }
    },
    support: {
      hero: {
        eyebrow: "Prvý produkt",
        headline: "support_v1",
        subheadline: "Prvý produkt postavený na imLayeri.",
        supportingLine:
          "Support workflow wedge navrhnutý na testovanie jadra imLayeru pod reálnym workflow review a s úzkym scope.",
        cta: "Prediskutovať pilot"
      },
      whatIs: {
        eyebrow: "Čo je support_v1",
        title: "Čo je support_v1",
        body:
          "support_v1 je prvý aplikovaný produktový povrch postavený na imLayeri. Dáva jadru buyer-facing pilotnú cestu bez toho, aby predstieral celý firemný príbeh.",
        cards: [
          {
            title: "Prvý produkt",
            body:
              "support_v1 je prvý produkt postavený na jadre imLayeru, nie celý firemný príbeh."
          },
          {
            title: "Prvý aplikovaný workflow",
            body:
              "Support je prvý workflow povrch, kde sa dá vrstva testovať proti reálnej operačnej histórii."
          },
          {
            title: "Prvý komerčný wedge",
            body:
              "Komerčný vstup je jeden úzky workflow slice, nie široký prísľub rollout-u naprieč tímami."
          },
          {
            title: "Prvá externá validačná cesta",
            body:
              "support_v1 je prvá buyer-facing cesta na validáciu jadra imLayeru cez reálne workflow review."
          }
        ]
      },
      whyWedge: {
        eyebrow: "Prečo je to prvý wedge",
        title: "Prečo je to prvý wedge",
        cards: [
          {
            title: "Ohraničený workflow",
            body:
              "Support workflow sa dá zúžiť na jeden slice, čo drží porovnanie disciplinované."
          },
          {
            title: "Reviewovateľné výstupy",
            body:
              "Routing a next-action výstupy sa dajú kontrolovať ľuďmi podľa explicitných review pravidiel."
          },
          {
            title: "Jasné kritériá úspechu",
            body:
              "Wedge podporuje definované pass kritériá ešte pred štartom evaluácie, čo drží tvrdenia disciplinované."
          },
          {
            title: "Pilot-friendly rozsah",
            body:
              "Data intake, review cadence aj operačné vlastníctvo môžu zostať úzke pre prvý pilot."
          },
          {
            title: "Komerčná relevancia",
            body:
              "Support operácie už dnes riešia rýchlosť, konzistentnosť a reviewovateľnú kvalitu ďalšieho kroku, takže wedge je komerčne čitateľný."
          }
        ]
      },
      inPlace: {
        eyebrow: "Čo je už pripravené",
        title: "What is already in place",
        items: [
          {
            title: "export intake",
            body:
              "Intake pre support exporty vo workflow support_v1 už existuje."
          },
          {
            title: "validation",
            body:
              "Validácia už kontroluje tvar exportu a pripravenosť pred hlbšou evaluáciou."
          },
          {
            title: "normalization",
            body:
              "Exporty sa normalizujú do pracovnej štruktúry používanej evaluáciou."
          },
          {
            title: "history reconstruction",
            body:
              "Case a event história sa už dá zrekonštruovať do rozhodovacieho kontextu pre ďalší krok."
          },
          {
            title: "evaluation path",
            body:
              "Existuje evaluačná cesta na porovnanie výstupov support_v1 pod review."
          },
          {
            title: "pilot materials",
            body:
              "Pilotné materiály už existujú na rámcovanie scope, prístupu, review a ďalších krokov."
          }
        ]
      },
      pilotFlow: {
        eyebrow: "Ako vyzerá pilot",
        title: "Ako vyzerá pilot",
        steps: [
          {
            step: "01",
            title: "Vyberte jeden workflow slice",
            body:
              "Zvoľte jeden support workflow slice s jasnými vlastníkmi, hranicami exportu a review pravidlami."
          },
          {
            step: "02",
            title: "Načítajte support exporty a históriu",
            body:
              "Prineste support exporty do workflow, validujte ich, normalizujte ich a zrekonštruujte rozhodovaciu históriu."
          },
          {
            step: "03",
            title: "Aplikujte ohraničené review kritériá",
            body:
              "Použite dohodnuté review kritériá, aby sa pilot hodnotil proti explicitným štandardom."
          },
          {
            step: "04",
            title: "Vyhodnoťte výstupy v kontrolovanom porovnaní",
            body:
              "Porovnajte vzniknuté výstupy pod review a rozhodnite, či pilot prešiel."
          }
        ]
      },
      pilotExample: {
        eyebrow: "Ohraničený pilotný vzor",
        title: "Jeden konkrétny ohraničený pilotný vzor",
        body:
          "Reálny prvý pilot môže zostať operačne jednoduchý a pritom stále testovať jadro imLayeru pod reálnym review.",
        items: [
          "Jeden support queue: jedna fronta so stabilným owner-om a úzkym routing povrchom.",
          "Jedna export cesta: jeden opakovateľný export feed pre intake, validáciu a normalizáciu.",
          "Jeden ohraničený review cyklus: jedna reviewer skupina používa rovnaké kritériá pri každom priechode.",
          "Jedno kontrolované evaluačné okno: jedno fixné porovnávacie okno na vyhodnotenie výstupov pred akýmkoľvek rozšírením."
        ]
      },
      materials: {
        eyebrow: "Pilotné materiály",
        title: "Pilotné materiály",
        body:
          "Materiály zostávajú buyer-facing a kompaktné: prístup je na vyžiadanie a každá položka podporuje pilotné review, nie široké produktové pozicionovanie.",
        requestLabel: "Požiadať o prístup",
        items: [
          {
            label: "Rozsah pilotu",
            title: "Ohraničený rozsah pilotu",
            body:
              "Definícia rozsahu pre jeden workflow slice, review vlastníctvo a hranice úspechu."
          },
          {
            label: "Review kritériá",
            title: "Kontrolované review kritériá",
            body:
              "Review metóda, pass kritériá a porovnávacie pravidlá použité na vyhodnotenie pilotu."
          },
          {
            label: "Práca s dátami",
            title: "Poznámka k práci so support exportmi",
            body:
              "Operačná poznámka pokrývajúca predpoklady exportov, hranice práce s dátami a review kontroly."
          },
          {
            label: "Evidence pack",
            title: "Pilotný evidence pack",
            body:
              "Kompaktný review balík používaný na rámcovanie výstupov, poznámok z review a ďalších krokov."
          }
        ]
      },
      cta: {
        headline: "Prediskutujme ohraničený pilot support_v1.",
        supportingLine:
          "Použite jeden reálny workflow slice na vyhodnotenie jadra imLayeru pod kontrolovaným review a s jasnými kritériami úspechu.",
        primaryCta: "Prediskutovať pilot"
      }
    }
  }
} as const;

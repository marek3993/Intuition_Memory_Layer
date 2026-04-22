export type Locale = "en" | "sk";

export const PUBLIC_BRAND_NAME = "imLayer";
export const PUBLIC_BRAND_EXPANDED_NAME = "Intuition Memory Layer";

type NavItem = { label: string; href: string };
type Card = { title: string; body: string };
type AssetSlot = { label: string; title: string; body: string; path: string };
type PilotAsset = {
  label: string;
  title: string;
  body: string;
  access: "public" | "request";
  href?: string;
};
type WorkflowStep = { title: string; body: string };
type RoadmapStep = { stage: string; title: string; body: string };
type EvidenceMetric = { label: string; value: string; footnote?: string };

type SiteLocaleContent = {
  brand: { expandedName: string; subtitle: string };
  nav: { items: NavItem[]; cta: string };
  hero: {
    eyebrow: string;
    headline: string;
    subheadline: string;
    supportingLine: string;
    primaryCta: string;
    secondaryCta: string;
    secondaryHref: string;
    proofLabel: string;
    proofStrip: string[];
    asset: AssetSlot;
  };
  technology: { eyebrow: string; title: string; body: string; cards: Card[]; asset: AssetSlot };
  whyNow: { eyebrow: string; title: string; body: string; cards: Card[] };
  evidence: {
    eyebrow: string;
    title: string;
    body: string;
    highlight: string;
    metrics: EvidenceMetric[];
    cards: Card[];
    noteLabel: string;
    note: string;
  };
  firstProduct: {
    eyebrow: string;
    title: string;
    body: string;
    cards: Card[];
    workflowLabel: string;
    workflowTitle: string;
    workflow: WorkflowStep[];
    builtLabel: string;
    builtTitle: string;
    built: string[];
    proofLabel: string;
    proofTitle: string;
    proofItems: string[];
    asset: AssetSlot;
  };
  firstPilot: {
    eyebrow: string;
    title: string;
    body: string;
    cards: Card[];
    assetsLabel: string;
    assetsTitle: string;
    assetsBody: string;
    assets: PilotAsset[];
    openLabel: string;
    requestLabel: string;
  };
  roadmap: { eyebrow: string; title: string; body: string; steps: RoadmapStep[]; asset: AssetSlot };
  cta: {
    eyebrow: string;
    title: string;
    body: string;
    guidance: string;
    form: {
      nameLabel: string;
      namePlaceholder: string;
      emailLabel: string;
      emailPlaceholder: string;
      companyLabel: string;
      companyPlaceholder: string;
      messageLabel: string;
      messagePlaceholder: string;
      submitLabel: string;
      subject: string;
    };
  };
  footer: { oneLine: string };
};

const enNavItems: NavItem[] = [
  { label: "What imLayer is", href: "#what-imlayer-is" },
  { label: "Why now", href: "#why-now" },
  { label: "Internal evidence", href: "#evidence" },
  { label: "First product", href: "#first-product" },
  { label: "Pilot", href: "#pilot" },
  { label: "Roadmap", href: "#roadmap" },
  { label: "Contact", href: "#contact" }
];

const enContent: SiteLocaleContent = {
  brand: {
    expandedName: PUBLIC_BRAND_EXPANDED_NAME,
    subtitle: "Decision-memory infrastructure"
  },
  nav: {
    items: enNavItems,
    cta: "Discuss first pilot fit"
  },
  hero: {
    eyebrow: PUBLIC_BRAND_EXPANDED_NAME,
    headline: PUBLIC_BRAND_NAME,
    subheadline: "Decision-memory infrastructure for workflow AI.",
    supportingLine:
      "Turns fragmented workflow history into compact, decision-ready state. support_v1 is the first product built on top of the layer and the first path to external validation.",
    primaryCta: "Discuss first pilot fit",
    secondaryCta: "See internal evidence",
    secondaryHref: "#evidence",
    proofLabel: "Positioning",
    proofStrip: [
      "History -> compact state -> decision",
      "Built for workflow AI, not generic memory storage",
      "Internal benchmark evidence supports a bounded pilot discussion",
      "support_v1 is the first product, first applied workflow, and first pilot wedge"
    ],
    asset: {
      label: "Hero brand asset",
      title: "Editorial brand visual for the imLayer core layer",
      body:
        "A restrained hero visual that keeps the brand centered on the imLayer core rather than on a single workflow application.",
      path: "/assets/iml/hero-environment-visual.png"
    }
  },
  technology: {
    eyebrow: "What imLayer is",
    title: "History -> compact state -> decision.",
    body:
      "imLayer turns fragmented workflow history into compact decision-ready state. It is not generic memory storage, not generic orchestration, and not a broad autonomous AI claim. It is the decision-memory layer that helps a workflow use the right prior context at the moment a choice has to be made.",
    cards: [
      {
        title: "Reconstructs workflow history",
        body:
          "imLayer rebuilds the parts of prior activity that materially shape the current workflow decision instead of dumping raw history back into the prompt."
      },
      {
        title: "Compresses to compact state",
        body:
          "The output is a bounded working state that is easier to inspect, compare, and evaluate than a long chain of fragmented records."
      },
      {
        title: "Feeds a real decision point",
        body:
          "The layer is meant to support a concrete workflow choice such as routing, escalation, or next-step selection at decision time."
      },
      {
        title: "Not storage, orchestration, or autonomy theater",
        body:
          "The claim is narrower and more useful: a disciplined decision layer for workflow AI where context quality directly affects the decision outcome."
      }
    ],
    asset: {
      label: "Core layer view",
      title: "From history to decision-ready state",
      body:
        "A simple view of imLayer as the layer that transforms fragmented workflow history into compact state for a decision system.",
      path: "/assets/iml/iml-conceptual-layer-visual.png"
    }
  },
  whyNow: {
    eyebrow: "Why this matters now",
    title: "Workflows can store history and run models. They still miss a disciplined decision layer.",
    body:
      "Buyers can already add memory systems, retrieval, and model calls to workflows. The harder gap is turning scattered operational history into a compact state that can support a reviewable decision. That gap is where imLayer is positioned.",
    cards: [
      {
        title: "More history is not enough",
        body:
          "Teams can keep bigger logs and longer context windows, but decision quality still breaks when the relevant history is fragmented or poorly shaped."
      },
      {
        title: "Operational decisions need structure",
        body:
          "A buyer does not need another generic AI layer. They need a way to make one workflow decision more disciplined, inspectable, and reviewable."
      },
      {
        title: "The buying path has to stay bounded",
        body:
          "The credible first step is not a platform-wide promise. It is one workflow slice where the decision layer can be tested under controlled conditions."
      }
    ]
  },
  evidence: {
    eyebrow: "Internal benchmark evidence",
    title: "Current internal benchmark signal for the imLayer core.",
    body:
      "The strongest current proof point is internal benchmark evidence on a bounded workflow evaluation set. It supports a first pilot discussion because it shows signal in a concrete decision path. It does not count as production proof, customer proof, or broad cross-domain validation.",
    highlight:
      "Current internal benchmark evidence: 573 total examples, 347 heldout, 0.6381 vs 0.1590, and a +0.4791 delta.",
    metrics: [
      {
        label: "Total examples",
        value: "573"
      },
      {
        label: "Heldout examples",
        value: "347"
      },
      {
        label: "IML vs baseline",
        value: "0.6381 vs 0.1590"
      },
      {
        label: "Delta",
        value: "+0.4791"
      }
    ],
    cards: [
      {
        title: "Bounded evidence, bounded claim",
        body:
          "This benchmark supports a serious internal signal claim for the current path. It should not be stretched into a production or customer claim."
      },
      {
        title: "Useful for first-pilot qualification",
        body:
          "The benchmark gives buyers a concrete internal reference point for why a controlled first pilot is worth reviewing."
      },
      {
        title: "Not broad validation",
        body:
          "The benchmark does not imply broad workflow coverage, broad domain transfer, or proven performance across unrelated environments."
      }
    ],
    noteLabel: "Qualification",
    note: "Internal benchmark evidence, not production proof."
  },
  firstProduct: {
    eyebrow: "First product: support_v1",
    title: "support_v1 is the first product, first applied workflow, and first pilot wedge.",
    body:
      "support_v1 is the first external validation path for imLayer. It applies the core layer to one support workflow slice so the decision-memory thesis can be tested in a bounded environment with reviewable outputs.",
    cards: [
      {
        title: "First product",
        body:
          "support_v1 is the first commercial surface built on top of imLayer rather than the full company or platform story."
      },
      {
        title: "First applied workflow",
        body:
          "Support is the first workflow because exports, histories, and routing decisions are concrete enough to evaluate with discipline."
      },
      {
        title: "First pilot wedge",
        body:
          "The intended buying motion is one bounded workflow slice, not a broad rollout across every support process."
      },
      {
        title: "First external validation path",
        body:
          "Customer-facing proof should come through controlled pilot review and external evaluation, not through inflated product claims."
      }
    ],
    workflowLabel: "Applied workflow",
    workflowTitle: "How support_v1 applies the imLayer core",
    workflow: [
      {
        title: "Support export intake",
        body:
          "The workflow starts from bounded support exports that can be reviewed, validated, and prepared for evaluation."
      },
      {
        title: "History reconstruction",
        body:
          "Relevant case and event history is rebuilt so the routing context reflects the real workflow path rather than isolated records."
      },
      {
        title: "Compact decision state",
        body:
          "The reconstructed history is compressed into a compact state that can inform the routing or escalation choice."
      },
      {
        title: "Reviewable decision output",
        body:
          "The output is a reviewable routing layer for a bounded pilot, not a claim of unattended production automation."
      }
    ],
    builtLabel: "Current stack",
    builtTitle: "What already exists for the first product",
    built: [
      "Bounded support export intake and validation before deeper evaluation begins",
      "Normalization into the working schema used by the current evaluation stack",
      "Case and event-history reconstruction for decision-ready support context",
      "Internal evaluation paths for comparing imLayer-driven outputs against a baseline",
      "Pilot packaging material for first external review and onboarding"
    ],
    proofLabel: "Support proof layer",
    proofTitle: "What makes support_v1 pilot-ready already",
    proofItems: [
      "A pilot-ready stack already exists for support export intake, validation, and downstream processing",
      "A reviewable path already exists from support export to reconstructed history and decision output",
      "Pilot materials and an external review path already exist for a controlled first evaluation"
    ],
    asset: {
      label: "First product view",
      title: "support_v1 as the first applied workflow",
      body:
        "A restrained workflow visual showing support_v1 as the first applied layer on top of imLayer, not as the entire platform story.",
      path: "/assets/iml/support-v1-workflow-visual.png"
    }
  },
  firstPilot: {
    eyebrow: "First pilot framing",
    title: "A controlled first pilot with clear review criteria.",
    body:
      "The first pilot is intentionally narrow: one workflow slice, support exports, explicit review criteria, and a controlled validation path that stays easy to inspect.",
    cards: [
      {
        title: "One workflow slice",
        body:
          "The pilot is scoped to a single support workflow slice so outcomes stay reviewable and the claim stays disciplined."
      },
      {
        title: "Support exports as source material",
        body:
          "The pilot starts from bounded exports that make ingestion, review, and evaluation transparent for both sides."
      },
      {
        title: "Clear review criteria",
        body:
          "Review method, success gates, and pass criteria are agreed before evaluation starts so the pilot can be judged against explicit standards."
      },
      {
        title: "Controlled validation path",
        body:
          "The pilot is a validation exercise for the imLayer core in a real workflow environment, not an open-ended production deployment."
      }
    ],
    assetsLabel: "Pilot materials",
    assetsTitle: "Reviewable materials for a bounded pilot",
    assetsBody:
      "The materials stay compact and buyer-facing: scope, review criteria, data handling assumptions, and the evidence pack used to review the first pilot.",
    assets: [
      {
        label: "Pilot scope",
        title: "Bounded pilot scope",
        body:
          "The workflow slice, export boundaries, decision owners, and review cadence used for the first pilot.",
        access: "request"
      },
      {
        label: "Review criteria",
        title: "Pilot review criteria",
        body:
          "The method, acceptance thresholds, and review checkpoints used to determine whether the pilot passes.",
        access: "request"
      },
      {
        label: "Data handling",
        title: "Support export handling note",
        body:
          "The compact note covering source data assumptions, handling limits, privacy posture, and review controls.",
        access: "request"
      },
      {
        label: "Evidence pack",
        title: "Pilot evidence pack",
        body:
          "The review pack summarizing scope, benchmark context, outputs, reviewer notes, and next-step recommendations.",
        access: "request"
      }
    ],
    openLabel: "Open document",
    requestLabel: "Request access"
  },
  roadmap: {
    eyebrow: "Roadmap",
    title: "A bounded path from IML core to broader AI systems",
    body:
      "The path begins with the IML core layer, gains proof in support_v1, validates itself in a real pilot, and then expands into additional workflow environments and broader AI decision infrastructure.",
    steps: [
      {
        stage: "01",
        title: "IML core layer",
        body:
          "Keep hardening the decision-memory core that converts workflow history into compact decision-ready state."
      },
      {
        stage: "02",
        title: "First product: support_v1",
        body:
          "Use support_v1 as the first applied workflow where the core layer is tested against real support history and decision points."
      },
      {
        stage: "03",
        title: "First real pilot",
        body:
          "Validate the layer in one bounded support workflow slice with explicit review criteria and controlled scope."
      },
      {
        stage: "04",
        title: "Second use case",
        body:
          "Only after the first pilot produces credible evidence should the same decision-memory logic be tested in a second workflow environment."
      },
      {
        stage: "05",
        title: "Broader AI systems",
        body:
          "Expand from validated workflow slices into wider AI decision infrastructure only after evidence compounds across multiple environments."
      }
    ],
    asset: {
      label: "Roadmap view",
      title: "From IML core to broader AI systems",
      body:
        "A sequenced view of the technology-first path: core layer first, support_v1 second, pilot validation third, and broader systems only after that.",
      path: "/assets/iml/platform-expansion-visual.png"
    }
  },
  cta: {
    eyebrow: "CTA",
    title: "Discuss a bounded first pilot for support_v1",
    body:
      "Validate the imLayer core in one real workflow slice with clear review criteria and controlled scope.",
    guidance:
      "Share your support export shape, current routing workflow, review constraints, and what the first pilot should prove.",
    form: {
      nameLabel: "Name",
      namePlaceholder: "Jane Smith",
      emailLabel: "Work email",
      emailPlaceholder: "jane@company.com",
      companyLabel: "Company",
      companyPlaceholder: "Company name",
      messageLabel: "Message",
      messagePlaceholder:
        "Support export shape, routing workflow, review constraints, and what the first pilot should prove.",
      submitLabel: "Open pilot discussion",
      subject: "Pilot discussion request | imLayer"
    }
  },
  footer: {
    oneLine:
      "imLayer is the brand and core decision-memory layer. support_v1 is the first product and first pilot wedge."
  }
};

const skContent: SiteLocaleContent = {
  brand: {
    expandedName: PUBLIC_BRAND_EXPANDED_NAME,
    subtitle: "Decision-memory infraštruktúra"
  },
  nav: {
    items: [
      { label: "Co je imLayer", href: "#what-imlayer-is" },
      { label: "Prečo teraz", href: "#why-now" },
      { label: "Interné dôkazy", href: "#evidence" },
      { label: "Prvý produkt", href: "#first-product" },
      { label: "Pilot", href: "#pilot" },
      { label: "Roadmap", href: "#roadmap" },
      { label: "Kontakt", href: "#contact" }
    ],
    cta: "Prediskutovať pilot"
  },
  hero: {
    eyebrow: PUBLIC_BRAND_EXPANDED_NAME,
    headline: PUBLIC_BRAND_NAME,
    subheadline: "Decision-memory infraštruktúra pre workflow AI.",
    supportingLine:
      "Mení fragmentovanú workflow históriu na kompaktný stav pripravený na rozhodnutie. support_v1 je prvý produkt postavený na tejto vrstve.",
    primaryCta: "Prediskutovať pilot",
    secondaryCta: "Pozrieť interný benchmark",
    secondaryHref: "#evidence",
    proofLabel: "Pozicionovanie",
    proofStrip: [
      "História -> kompaktný stav -> rozhodnutie",
      "Navrhnuté pre workflow AI, nie pre generickú pamäťovú vrstvu",
      "Interný benchmark podporuje diskusiu o ohraničenom pilote",
      "support_v1 je prvý produkt, prvý aplikovaný workflow a prvý pilotný wedge"
    ],
    asset: {
      label: "Hero vizuál",
      title: "Brand vizuál pre jadro vrstvy imLayer",
      body:
        "Striedmy hero vizuál, ktorý drží značku ukotvenú v jadre imLayer, nie v jednom workflow produkte.",
      path: "/assets/iml/hero-environment-visual.png"
    }
  },
  technology: {
    eyebrow: "Čo je imLayer",
    title: "História -> kompaktný stav -> rozhodnutie.",
    body:
      "imLayer mení fragmentovanú workflow históriu na kompaktný stav pripravený na rozhodnutie. Nie je to generické memory storage, generická orchestration vrstva ani široký autonomous AI claim. Je to decision-memory vrstva, ktorá pomáha workflowu použiť správny predchádzajúci kontext presne v momente rozhodnutia.",
    cards: [
      {
        title: "Rekonštruuje workflow históriu",
        body:
          "imLayer skladá tie časti predchádzajúcej aktivity, ktoré reálne menia aktuálne workflow rozhodnutie, namiesto vracania surovej histórie do promptu."
      },
      {
        title: "Komprimuje do kompaktného stavu",
        body:
          "Výstupom je ohraničený pracovný stav, ktorý sa ľahšie kontroluje, porovnáva a vyhodnocuje než dlhý reťazec fragmentovaných záznamov."
      },
      {
        title: "Vstupuje do reálneho rozhodnutia",
        body:
          "Vrstva je určená pre konkrétne workflow rozhodnutie, napríklad routing, eskaláciu alebo voľbu ďalšieho kroku v okamihu rozhodnutia."
      },
      {
        title: "Nie storage, orchestration ani autonomy theater",
        body:
          "Tvrdenie je užšie a užitočnejšie: disciplinovaná decision vrstva pre workflow AI, kde kvalita kontextu priamo ovplyvňuje výsledok rozhodnutia."
      }
    ],
    asset: {
      label: "Pohľad na jadro vrstvy",
      title: "Od histórie k stavu pripravenému na rozhodnutie",
      body:
        "Jednoduchý pohľad na imLayer ako vrstvu, ktorá mení fragmentovanú workflow históriu na kompaktný stav pre rozhodovací systém.",
      path: "/assets/iml/iml-conceptual-layer-visual.png"
    }
  },
  whyNow: {
    eyebrow: "Prečo na tom záleží práve teraz",
    title: "Workflowy už vedia ukladať históriu a volať modely. Stále im chýba disciplinovaná decision vrstva.",
    body:
      "Kupujúci už dnes vedia do workflowu pridať memory systémy, retrieval aj model calls. Ťažší problém je premeniť rozptýlenú operačnú históriu na kompaktný stav, ktorý podporí preskúmateľné rozhodnutie. Práve tam je imLayer.",
    cards: [
      {
        title: "Viac histórie nestačí",
        body:
          "Tímy môžu držať väčšie logy a dlhšie context windows, no kvalita rozhodnutia sa aj tak láme, keď je relevantná história rozbitá alebo zle tvarovaná."
      },
      {
        title: "Operačné rozhodnutia potrebujú štruktúru",
        body:
          "Kupujúci nepotrebuje ďalšiu generickú AI vrstvu. Potrebuje spôsob, ako spraviť jedno workflow rozhodnutie disciplinovanejším, kontrolovateľným a preskúmateľným."
      },
      {
        title: "Nákupná cesta musí zostať ohraničená",
        body:
          "Prvý dôveryhodný krok nie je prísľub platformy pre všetko. Je to jeden workflow slice, na ktorom sa decision vrstva dá otestovať v kontrolovaných podmienkach."
      }
    ]
  },
  evidence: {
    eyebrow: "Interný benchmark",
    title: "Aktuálny benchmark signál pre prvú evaluačnú cestu support_v1.",
    body:
      "Najsilnejší aktuálny dôkaz je interný benchmark na ohraničenom evaluačnom sete. Podporuje diskusiu o prvom pilote, pretože ukazuje signál v jednej konkrétnej ceste. Nie je to produkčný dôkaz, zákaznícky dôkaz ani široká cross-domain validácia.",
    highlight:
      "Aktuálny interný benchmark: 573 total examples, 347 heldout, 0.6381 vs 0.1590 a delta +0.4791.",
    metrics: [
      {
        label: "Príklady celkom",
        value: "573"
      },
      {
        label: "Heldout príklady",
        value: "347"
      },
      {
        label: "IML vs baseline",
        value: "0.6381 vs 0.1590"
      },
      {
        label: "Delta",
        value: "+0.4791"
      }
    ],
    cards: [
      {
        title: "Ohraničený dôkaz, ohraničené tvrdenie",
        body:
          "Tento benchmark podporuje seriózny interný signál pre aktuálnu cestu. Netreba ho naťahovať na produkčné ani zákaznícke tvrdenie."
      },
      {
        title: "Užitočné pre kvalifikáciu prvého pilotu",
        body:
          "Benchmark dáva kupujúcemu konkrétny interný referenčný bod, prečo sa oplatí preskúmať kontrolovaný prvý pilot."
      },
      {
        title: "Nie široká validácia",
        body:
          "Benchmark neimplikuje široké workflow pokrytie, prenos do iných domén ani dokázaný výkon v nesúvisiacich prostrediach."
      }
    ],
    noteLabel: "Kvalifikácia",
    note: "Interný benchmark, nie produkčný dôkaz."
  },
  firstProduct: {
    eyebrow: "Prvý produkt: support_v1",
    title: "support_v1 je prvý produkt, prvý aplikovaný workflow a prvý pilotný wedge.",
    body:
      "support_v1 je prvá externá validačná cesta pre imLayer. Aplikuje jadro vrstvy na jeden support workflow slice, aby sa decision-memory téza dala testovať v ohraničenom prostredí so skontrolovateľnými výstupmi.",
    cards: [
      {
        title: "Prvý produkt",
        body:
          "support_v1 je prvá komerčná vrstva postavená na imLayeri, nie celý firemný alebo platformový príbeh."
      },
      {
        title: "Prvý aplikovaný workflow",
        body:
          "Support je prvý workflow preto, že exporty, histórie a routing rozhodnutia sú dosť konkrétne na disciplinované vyhodnotenie."
      },
      {
        title: "Prvý pilotný wedge",
        body:
          "Zamýšľaný buying motion je jeden ohraničený workflow slice, nie široký rollout naprieč každým support procesom."
      },
      {
        title: "Prvá externá validačná cesta",
        body:
          "Customer-facing proof má prísť cez kontrolovaný pilot a externú evaluáciu, nie cez nafúknuté produktové tvrdenia."
      }
    ],
    workflowLabel: "Aplikovaný workflow",
    workflowTitle: "Ako support_v1 aplikuje jadro imLayer",
    workflow: [
      {
        title: "Intake support exportov",
        body:
          "Workflow sa začína ohraničenými support exportmi, ktoré sa dajú skontrolovať, validovať a pripraviť na evaluáciu."
      },
      {
        title: "Rekonštrukcia histórie",
        body:
          "Relevantná história prípadu a eventov sa znovu skladá tak, aby routing kontext zodpovedal reálnej workflow ceste, nie izolovaným záznamom."
      },
      {
        title: "Kompaktný rozhodovací stav",
        body:
          "Rekonštruovaná história sa komprimuje do kompaktného stavu, ktorý vie informovať routing alebo eskalačné rozhodnutie."
      },
      {
        title: "Skontrolovateľný výstup rozhodnutia",
        body:
          "Výstupom je skontrolovateľná routing vrstva pre ohraničený pilot, nie tvrdenie o unattended production automation."
      }
    ],
    builtLabel: "Aktuálny stack",
    builtTitle: "Čo už pre prvý produkt existuje",
    built: [
      "Ohraničený intake support exportov a validačná cesta pred tým, než sa začne hlbšia evaluácia",
      "Normalizácia do pracovnej schémy používanej v aktuálnom evaluačnom stacku",
      "Rekonštrukcia case a event histórie pre support kontext pripravený na rozhodnutie",
      "Interné evaluačné cesty na porovnanie imLayer výstupov oproti baseline",
      "Pilotné materiály pre prvý externý review a onboarding"
    ],
    proofLabel: "Podporný dôkaz",
    proofTitle: "Čo robí support_v1 pilot-ready už dnes",
    proofItems: [
      "Existuje pilot-ready stack pre intake support exportov, validáciu a ďalšie spracovanie",
      "Existuje cesta od support exportu po rekonštrukciu histórie a rozhodovací výstup na review",
      "Existujú pilotné materiály aj review cesta pre prvé externé posúdenie"
    ],
    asset: {
      label: "Pohľad na prvý produkt",
      title: "support_v1 ako prvý aplikovaný workflow",
      body:
        "Striedmy workflow vizuál ukazujúci support_v1 ako prvú aplikovanú vrstvu nad imLayerom, nie ako celý platformový príbeh.",
      path: "/assets/iml/support-v1-workflow-visual.png"
    }
  },
  firstPilot: {
    eyebrow: "Rámec prvého pilotu",
    title: "Kontrolovaný prvý pilot s jasnými kritériami review.",
    body:
      "Prvý pilot je zámerne úzky: jeden workflow slice, support exporty, explicitné review kritériá a kontrolovaná validačná cesta, ktorú je ľahké skontrolovať.",
    cards: [
      {
        title: "Jeden workflow slice",
        body:
          "Pilot je ohraničený na jeden support workflow slice, aby výsledky zostali skontrolovateľné a tvrdenie ostalo disciplinované."
      },
      {
        title: "Support exporty ako vstup",
        body:
          "Pilot sa začína ohraničenými exportmi, ktoré robia ingest, review aj evaluáciu transparentnou pre obe strany."
      },
      {
        title: "Jasné review kritériá",
        body:
          "Review metóda, success gates a pass kritériá sa dohodnú pred štartom evaluácie, aby sa pilot hodnotil podľa explicitných štandardov."
      },
      {
        title: "Kontrolovaná validačná cesta",
        body:
          "Pilot je validačný krok pre jadro imLayer v reálnom workflow prostredí, nie otvorený production deployment."
      }
    ],
    assetsLabel: "Pilotné materiály",
    assetsTitle: "Materiály na review pre ohraničený pilot",
    assetsBody:
      "Materiály ostávajú stručné a vhodné pre kupujúceho: rozsah, review kritériá, predpoklady pre prácu s dátami a evidence pack pre vyhodnotenie prvého pilotu.",
    assets: [
      {
        label: "Rozsah pilotu",
        title: "Ohraničený rozsah pilotu",
        body:
          "Workflow slice, hranice exportov, decision owners a review cadence použité pre prvý pilot.",
        access: "request"
      },
      {
        label: "Review kritériá",
        title: "Pilotné review kritériá",
        body:
          "Metóda, acceptance thresholds a review checkpointy použité na rozhodnutie, či pilot prešiel.",
        access: "request"
      },
      {
        label: "Práca s dátami",
        title: "Poznámka k práci so support exportmi",
        body:
          "Stručná poznámka o predpokladoch zdrojových dát, limitoch práce s dátami, zásadách ochrany súkromia a review kontrolách.",
        access: "request"
      },
      {
        label: "Evidence pack",
        title: "Pilotný evidence pack",
        body:
          "Review balík so zhrnutím scope, benchmark kontextu, výstupov, reviewer notes a odporúčaní pre ďalší krok.",
        access: "request"
      }
    ],
    openLabel: "Otvoriť dokument",
    requestLabel: "Požiadať o prístup"
  },
  roadmap: {
    eyebrow: "Roadmap",
    title: "Ohraničená cesta od IML core k širším AI systémom",
    body:
      "Cesta sa začína IML core vrstvou, získava dôkaz v support_v1, validuje sa v reálnom pilote a až potom sa rozširuje do ďalších workflow prostredí a širšej AI decision infraštruktúry.",
    steps: [
      {
        stage: "01",
        title: "IML core layer",
        body:
          "Pokračovať v spevňovaní decision-memory jadra, ktoré mení workflow históriu na kompaktný stav pripravený na rozhodnutie."
      },
      {
        stage: "02",
        title: "Prvý produkt: support_v1",
        body:
          "Použiť support_v1 ako prvý aplikovaný workflow, kde sa jadro vrstvy testuje na reálnej support histórii a decision points."
      },
      {
        stage: "03",
        title: "Prvý reálny pilot",
        body:
          "Validovať vrstvu v jednom ohraničenom support workflow slice s explicitnými review kritériami a kontrolovaným scope."
      },
      {
        stage: "04",
        title: "Druhý use case",
        body:
          "Až po kredibilnom dôkaze z prvého pilotu testovať rovnakú decision-memory logiku v druhom workflow prostredí."
      },
      {
        stage: "05",
        title: "Širšie AI systémy",
        body:
          "Rozšíriť sa z validovaných workflow slices do širšej AI decision infraštruktúry až potom, keď sa dôkaz znásobí naprieč viacerými prostrediami."
      }
    ],
    asset: {
      label: "Pohľad na roadmap",
      title: "Od IML core k širším AI systémom",
      body:
        "Sekvenčný pohľad na cestu orientovanú na technológiu: najprv core vrstva, potom support_v1, potom pilotná validácia a až následne širšie systémy.",
      path: "/assets/iml/platform-expansion-visual.png"
    }
  },
  cta: {
    eyebrow: "Kontakt",
    title: "Prediskutujme ohraničený prvý pilot pre support_v1",
    body:
      "Overte jadro imLayer v jednom reálnom workflow slice s jasnými review kritériami a kontrolovaným scope.",
    guidance:
      "Pošlite podobu support exportov, aktuálny routing workflow, review constraints a to, čo má prvý pilot dokázať.",
    form: {
      nameLabel: "Meno",
      namePlaceholder: "Jana Nováková",
      emailLabel: "Pracovný e-mail",
      emailPlaceholder: "jana@firma.sk",
      companyLabel: "Firma",
      companyPlaceholder: "Názov firmy",
      messageLabel: "Správa",
      messagePlaceholder:
        "Podoba support exportov, routing workflow, review constraints a to, čo má prvý pilot dokázať.",
      submitLabel: "Otvoriť pilotnú diskusiu",
      subject: "Pilotná diskusia | imLayer"
    }
  },
  footer: {
    oneLine:
      "imLayer je značka a jadrová decision-memory vrstva. support_v1 je prvý produkt a prvý pilotný wedge."
  }
};

export const siteContent: Record<Locale, SiteLocaleContent> = {
  en: enContent,
  sk: skContent
};

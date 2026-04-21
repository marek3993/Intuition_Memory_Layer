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
type ExamplePath = { title: string; body: string };

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
    proofLabel: string;
    proofStrip: string[];
    asset: AssetSlot;
  };
  technology: { eyebrow: string; title: string; body: string; cards: Card[]; asset: AssetSlot };
  whyNow: { eyebrow: string; title: string; body: string; cards: Card[] };
  productTransition: { eyebrow: string; title: string; body: string };
  supportFirst: { eyebrow: string; title: string; body: string; cards: Card[] };
  firstApplication: {
    eyebrow: string;
    title: string;
    body: string;
    workflowLabel: string;
    workflowTitle: string;
    workflow: WorkflowStep[];
    builtLabel: string;
    builtTitle: string;
    built: string[];
    asset: AssetSlot;
  };
  evidence: {
    eyebrow: string;
    title: string;
    body: string;
    highlight: string;
    metrics: {
      calibratedLabel: string;
      calibratedValue: string;
      baselineLabel: string;
      baselineValue: string;
      context: string;
      deltaLabel: string;
      deltaValue: string;
    };
    cards: Card[];
    noteLabel: string;
    note: string;
  };
  roadmap: { eyebrow: string; title: string; body: string; steps: RoadmapStep[]; asset: AssetSlot };
  beyondSupport: { eyebrow: string; title: string; body: string; examplesTitle: string; examples: ExamplePath[]; note: string };
  pilotTrust: {
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

const baseNavItems: NavItem[] = [
  { label: "Technology", href: "#technology" },
  { label: "First Application", href: "#first-application" },
  { label: "Evidence", href: "#evidence" },
  { label: "Roadmap", href: "#roadmap" },
  { label: "Contact", href: "#contact" }
];

const enContent: SiteLocaleContent = {
  brand: {
    expandedName: PUBLIC_BRAND_EXPANDED_NAME,
    subtitle: "Core decision-memory technology"
  },
  nav: {
    items: baseNavItems,
    cta: "Discuss pilot fit"
  },
  hero: {
    eyebrow: "Core technology",
    headline: PUBLIC_BRAND_NAME,
    subheadline:
      "Intuition Memory Layer turns fragmented workflow history into decision-ready context.",
    supportingLine:
      "support_v1 is the first product built on imLayer. The next commercial step is one bounded pilot, with a second use-case only after first-pilot evidence.",
    primaryCta: "Discuss pilot fit",
    secondaryCta: "See the first application",
    proofLabel: "At a glance",
    proofStrip: [
      "imLayer is the core technology thesis",
      "support_v1 is the first pilot-ready application",
      "The immediate commercial step is one real bounded pilot",
      "Broader workflow expansion follows only after pilot evidence"
    ],
    asset: {
      label: "Hero brand asset",
      title: "Editorial brand visual for the imLayer thesis",
      body:
        "Premium hero artwork that frames imLayer as a core technology layer rather than a support-only product.",
      path: "/assets/iml/hero-environment-visual.png"
    }
  },
  technology: {
    eyebrow: "What imLayer is",
    title: "A layer for decisions that need more than raw memory recall.",
    body:
      "imLayer sits between memory systems and decisioning systems. It reconstructs historical context into a bounded, reviewable layer that a workflow can use at decision time.",
    cards: [
      {
        title: "Decision-memory, not generic memory",
        body:
          "The goal is not to store everything. The goal is to surface the parts of history that materially change a workflow decision."
      },
      {
        title: "Reviewable context, not blind automation",
        body:
          "imLayer keeps the decision layer inspectable so a first pilot can be evaluated with disciplined human review."
      },
      {
        title: "Core layer first",
        body:
          "support_v1 is the first applied product, but the underlying technology thesis is broader than support routing."
      }
    ],
    asset: {
      label: "Technology view",
      title: "Memory -> imLayer -> decisioning",
      body:
        "A concise view of imLayer as the layer that turns workflow history into bounded, usable decision context.",
      path: "/assets/iml/iml-conceptual-layer-visual.png"
    }
  },
  whyNow: {
    eyebrow: "Why this layer matters now",
    title: "Workflows have memory and models, but still lack a disciplined decision layer.",
    body:
      "Teams can now store history, retrieve fragments, and run models, but there is still a gap between raw recall and a reviewable operational decision. imLayer is meant to fill that gap.",
    cards: [
      {
        title: "Memory alone does not decide",
        body:
          "A workflow still needs the right historical shape, not just more stored data or a longer context window."
      },
      {
        title: "Decisioning needs structure",
        body:
          "Operational choices need a layer that can reconstruct decision context in a repeatable and inspectable way."
      },
      {
        title: "Proof starts bounded",
        body:
          "A credible technology story starts with bounded evidence in a real workflow before it expands into broader platform claims."
      }
    ]
  },
  productTransition: {
    eyebrow: "First product",
    title: "support_v1 is the first product built on imLayer.",
    body:
      "The sections above describe the imLayer core technology. The sections below show its first applied product, built to earn evidence in one serious pilot wedge before broader expansion."
  },
  supportFirst: {
    eyebrow: "Why support_v1 starts here",
    title: "support_v1 starts in support because the workflow is bounded, reviewable, and commercially legible.",
    body:
      "As the first product built on imLayer, support_v1 gives the core layer a disciplined proving ground: real exports, visible decision points, constrained scope, and a workflow where review quality can be examined directly.",
    cards: [
      {
        title: "Verifiable decision points",
        body:
          "Support routing creates concrete moments where better historical context can change whether a case follows a standard or careful path."
      },
      {
        title: "Real workflow data",
        body:
          "Exports, event history, timestamps, and case progression create the practical substrate needed for a credible pilot."
      },
      {
        title: "Evidence before platform claims",
        body:
          "Support is the first wedge because it keeps claims bounded while evidence compounds."
      },
      {
        title: "Commercial entry point",
        body:
          "A narrow first use-case creates a real buying path without pretending the broader platform is already proven."
      }
    ]
  },
  firstApplication: {
    eyebrow: "First application",
    title: "support_v1 is the first pilot-ready applied workflow built on imLayer.",
    body:
      "support_v1 applies the imLayer core technology to support routing workflows. It is not the whole company story. It is the first use-case where the layer is being shaped into a bounded pilot-ready implementation.",
    workflowLabel: "Workflow",
    workflowTitle: "How support_v1 applies the layer",
    workflow: [
      {
        title: "Export intake",
        body:
          "The workflow begins from a bounded support export or a controlled support slice suitable for pilot evaluation."
      },
      {
        title: "Validation and normalization",
        body:
          "Incoming data is checked for structure, ordering, and coverage, then transformed into the working schema needed for evaluation."
      },
      {
        title: "History reconstruction",
        body:
          "Visible support history is rebuilt so routing decisions are evaluated against actual case context rather than isolated records."
      },
      {
        title: "Routing evaluation",
        body:
          "The layer compares routing decisions on labeled points to test whether better decision context improves the path choice."
      },
      {
        title: "Reviewable pilot output",
        body:
          "The result is a reviewable routing layer for a bounded pilot, not a claim of unattended production automation."
      }
    ],
    builtLabel: "Already in stack",
    builtTitle: "What already exists in the pilot-ready stack",
    built: [
      "Internal eval paths across labeled_support, raw_ingest, csv_ingest, mapped_ingest, and zendesk_like modes",
      "Validation logic for export usability before deeper evaluation continues",
      "Normalization into the working schema used by the current stack",
      "Event and case-history reconstruction for support decision points",
      "Comparison and calibration logic for bounded routing evaluation",
      "Pilot packaging and handoff materials for first external onboarding"
    ],
    asset: {
      label: "Applied workflow",
      title: "support_v1 in practice",
      body:
        "A restrained visual for the support_v1 flow from export intake through reviewable routing evaluation.",
      path: "/assets/iml/support-v1-workflow-visual.png"
    }
  },
  evidence: {
    eyebrow: "Current proof and pilot readiness",
    title: "The evidence supports a bounded pilot story, not universal proof.",
    body:
      "The strongest current claim is that imLayer already has a serious internal eval layer and a pilot-ready support workflow. That is enough for a first-pilot conversation while remaining explicitly bounded in scope.",
    highlight:
      "On the strongest current raw_ingest / combined_ab slice, calibrated imLayer reaches 92.31% versus 69.23% for the best non-calibrated baseline.",
    metrics: {
      calibratedLabel: "Calibrated imLayer",
      calibratedValue: "92.31%",
      baselineLabel: "Best baseline",
      baselineValue: "69.23%",
      context: "Strongest current slice: raw_ingest / combined_ab",
      deltaLabel: "Observed delta",
      deltaValue: "+23.08 pp"
    },
    cards: [
      {
        title: "Internal eval stack exists",
        body:
          "The current stack is more than a concept. It already supports intake, validation, normalization, reconstruction, evaluation, and pilot packaging."
      },
      {
        title: "support_v1 is pilot-ready, not broadly deployed",
        body:
          "The right claim is a bounded first-pilot path with manual review, not a broad production rollout story."
      },
      {
        title: "Evidence remains uneven outside the strongest path",
        body:
          "The strongest slices support a pilot discussion, while weaker ingest paths still need more evidence before stronger claims should be made."
      }
    ],
    noteLabel: "Honest note",
    note:
      "This page should not imply universal domain proof, broad deployment, or a fully production-ready platform. The current truth is a core technology thesis with one pilot-ready application and a bounded evidence layer."
  },
  roadmap: {
    eyebrow: "Roadmap",
    title: "From core layer to broader workflows, one bounded step at a time.",
    body:
      "The roadmap shows expansion logic without skipping the pilot stage. The next commercial step is the first real pilot, and every later step depends on evidence from the one before it.",
    steps: [
      {
        stage: "01",
        title: "Core technology: imLayer",
        body:
          "Continue hardening the decision-memory layer, evaluation logic, and reviewable decision framing that define the core product thesis."
      },
      {
        stage: "02",
        title: "First applied product: support_v1",
        body:
          "Use support as the first proving ground where imLayer can be evaluated on real decision points and export-derived context."
      },
      {
        stage: "03",
        title: "First real pilot",
        body:
          "Onboard a first partner on one bounded workflow slice, one export path, and one tightly reviewed pilot scope."
      },
      {
        stage: "04",
        title: "Second use-case after pilot evidence",
        body:
          "Test a second applied workflow only after the first pilot produces credible evidence, starting narrowly on synthetic data and then on 1-2 real cases."
      },
      {
        stage: "05",
        title: "Broader workflow applications",
        body:
          "Only after compounding pilot evidence should imLayer expand into wider workflow and agent-oriented decision contexts."
      }
    ],
    asset: {
      label: "Roadmap view",
      title: "Evidence-led expansion",
      body:
        "A sequenced view from the core imLayer layer to the first pilot and only then to broader workflow applications.",
      path: "/assets/iml/platform-expansion-visual.png"
    }
  },
  beyondSupport: {
    eyebrow: "Beyond support",
    title: "The broader story starts only after the first pilot proves out the layer.",
    body:
      "The next chapter is not an immediate cross-domain rollout. It is a second bounded use-case where the same decision-memory logic can be tested on another workflow shape.",
    examplesTitle: "Likely next use-cases",
    examples: [
      {
        title: "E-commerce user-profile layer",
        body:
          "A decision-memory layer that reconstructs user history and profile state before key service, risk, or lifecycle decisions are made."
      },
      {
        title: "CRM entity workflow",
        body:
          "A layer that keeps account, contact, and entity history usable at the moment a workflow needs to decide how to route or act."
      }
    ],
    note:
      "The expected path is synthetic data first, then 1-2 real cases after the first support pilot creates enough evidence to justify a second vertical."
  },
  pilotTrust: {
    eyebrow: "Pilot trust and evidence",
    title: "A first pilot should be easy to evaluate, easy to review, and clear about its limits.",
    body:
      "The right framing is a bounded validation pilot: explicit scope, agreed review criteria, disciplined data handling, and a compact evidence pack at the end.",
    cards: [
      {
        title: "Bounded pilot scope",
        body:
          "One workflow slice, one export path, and one reviewed decision set. The goal is a disciplined first proof, not a production deployment."
      },
      {
        title: "Acceptance criteria",
        body:
          "Pilot entry conditions, review method, and pass thresholds are agreed before evaluation starts so success is defined upfront."
      },
      {
        title: "Data handling and privacy",
        body:
          "Only the bounded support data needed for the pilot is handled. Access, retention, and review assumptions are defined before intake."
      },
      {
        title: "Evidence pack and review materials",
        body:
          "The pilot closes with a compact pack covering scope, method, outputs, observed deltas, review notes, and recommended next steps."
      }
    ],
    assetsLabel: "Pilot assets",
    assetsTitle: "Compact materials area",
    assetsBody:
      "Buyer-facing materials can open directly when a public-safe document exists; more sensitive pilot material stays gated behind a single access request.",
    assets: [
      {
        label: "Pilot overview",
        title: "Pilot overview",
        body:
          "Scope, workflow slice, delivery shape, review cadence, and decision owners for the first bounded pilot.",
        access: "request"
      },
      {
        label: "Acceptance criteria",
        title: "Acceptance criteria",
        body:
          "Entry assumptions, evaluation gates, and the specific criteria used to judge whether the pilot passes.",
        access: "request"
      },
      {
        label: "Data handling note",
        title: "Data handling note",
        body:
          "Short note covering bounded data use, handling assumptions, privacy posture, and review controls.",
        access: "request"
      },
      {
        label: "Evidence pack",
        title: "Evidence pack",
        body:
          "Compact review material covering methodology, calibrated slices, outputs, and reviewer-ready observations.",
        access: "request"
      },
      {
        label: "Pricing framework",
        title: "Pricing and pilot framework",
        body:
          "First 3 bounded pilots are framed at 3.5K€ to 7K€ depending on scope, later pilots start at 10K€+, and bounded post-pilot support, monitoring, recalibration, and reporting start from 2.5K€ / month.",
        access: "request"
      }
    ],
    openLabel: "Open document",
    requestLabel: "Request access"
  },
  cta: {
    eyebrow: "Contact",
    title: "Discuss a bounded first pilot.",
    body:
      "If you have support exports and want to evaluate whether imLayer can improve decision quality on a bounded workflow slice, the next step is a pilot-fit conversation.",
    guidance:
      "Share your export shape, current routing workflow, review constraints, and what the first pilot should prove.",
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
      submitLabel: "Open pilot request",
      subject: "Pilot discussion request | imLayer"
    }
  },
  footer: {
    oneLine:
      "imLayer is the core technology. support_v1 is the first product and the first pilot wedge."
  }
};

const skContent: SiteLocaleContent = {
  ...enContent,
  brand: {
    expandedName: PUBLIC_BRAND_EXPANDED_NAME,
    subtitle: "Zakladna decision-memory technologia"
  },
  nav: {
    items: [
      { label: "Technologia", href: "#technology" },
      { label: "Prva aplikacia", href: "#first-application" },
      { label: "Dokazy", href: "#evidence" },
      { label: "Roadmap", href: "#roadmap" },
      { label: "Kontakt", href: "#contact" }
    ],
    cta: "Prediskutovat pilot"
  },
  hero: {
    ...enContent.hero,
    eyebrow: "Zakladna technologia",
    primaryCta: "Prediskutovat pilot",
    secondaryCta: "Pozriet prvu aplikaciu",
    proofLabel: "Prehlad"
  },
  technology: {
    ...enContent.technology,
    eyebrow: "Co je imLayer"
  },
  whyNow: {
    ...enContent.whyNow,
    eyebrow: "Preco tato vrstva prave teraz"
  },
  productTransition: {
    ...enContent.productTransition,
    eyebrow: "Prvy produkt"
  },
  supportFirst: {
    ...enContent.supportFirst,
    eyebrow: "Preco support_v1 zacina tu"
  },
  firstApplication: {
    ...enContent.firstApplication,
    eyebrow: "Prva aplikacia",
    builtLabel: "Uz v stacku"
  },
  evidence: {
    ...enContent.evidence,
    eyebrow: "Aktualne dokazy a pripravenost na pilot",
    noteLabel: "Poctiva poznamka"
  },
  roadmap: {
    ...enContent.roadmap,
    eyebrow: "Roadmap"
  },
  beyondSupport: {
    ...enContent.beyondSupport,
    eyebrow: "Za hranicou supportu",
    examplesTitle: "Pravdepodobne dalsie use-cases"
  },
  pilotTrust: {
    ...enContent.pilotTrust,
    assetsBody:
      "Buyer-facing materialy sa mozu otvorit priamo, ked existuje public-safe dokument; citlivejsie pilotne materialy zostavaju za jednym krokom Poziadat o pristup.",
    openLabel: "Otvorit dokument",
    requestLabel: "Poziadat o pristup"
  },
  cta: {
    eyebrow: "Kontakt",
    title: "Prediskutujme ohraniceny prvy pilot.",
    body:
      "Ak mate support exporty a chcete vyhodnotit, ci imLayer vie zlepsit decision quality na ohranicenom workflow slice, dalsim krokom je pilot-fit diskusia.",
    guidance:
      "Poslite export shape, aktualny routing workflow, review constraints a to, co ma prvy pilot dokazat.",
    form: {
      nameLabel: "Meno",
      namePlaceholder: "Jana Novakova",
      emailLabel: "Pracovny e-mail",
      emailPlaceholder: "jana@firma.sk",
      companyLabel: "Firma",
      companyPlaceholder: "Nazov firmy",
      messageLabel: "Sprava",
      messagePlaceholder:
        "Support export shape, routing workflow, review constraints a to, co ma prvy pilot dokazat.",
      submitLabel: "Otvorit pilotnu ziadost",
      subject: "Pilotna diskusia | imLayer"
    }
  },
  footer: {
    oneLine:
      "imLayer je jadrova technologia. support_v1 je prvy produkt a prva pilotna wedge."
  }
};

export const siteContent: Record<Locale, SiteLocaleContent> = {
  en: enContent,
  sk: skContent
};

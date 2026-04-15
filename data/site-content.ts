export type Locale = "en" | "sk";

export const PUBLIC_BRAND_NAME = "Intuition Memory Layer";
export const CONTACT_EMAIL = "hello@example.com";

type NavItem = {
  label: string;
  href: string;
};

type Card = {
  title: string;
  body: string;
};

type AssetSlot = {
  label: string;
  title: string;
  body: string;
  path: string;
};

type WorkflowStep = {
  title: string;
  body: string;
};

type RoadmapStep = {
  stage: string;
  title: string;
  body: string;
};

type ExamplePath = {
  title: string;
  body: string;
};

type SiteLocaleContent = {
  brand: {
    subtitle: string;
  };
  nav: {
    items: NavItem[];
    cta: string;
  };
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
  technology: {
    eyebrow: string;
    title: string;
    body: string;
    cards: Card[];
    asset: AssetSlot;
  };
  whyNow: {
    eyebrow: string;
    title: string;
    body: string;
    cards: Card[];
  };
  productTransition: {
    eyebrow: string;
    title: string;
    body: string;
  };
  supportFirst: {
    eyebrow: string;
    title: string;
    body: string;
    cards: Card[];
  };
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
  roadmap: {
    eyebrow: string;
    title: string;
    body: string;
    steps: RoadmapStep[];
    asset: AssetSlot;
  };
  beyondSupport: {
    eyebrow: string;
    title: string;
    body: string;
    examplesTitle: string;
    examples: ExamplePath[];
    note: string;
  };
  cta: {
    eyebrow: string;
    title: string;
    body: string;
    guidance: string;
    directEmailLabel: string;
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
  footer: {
    oneLine: string;
  };
};

export const siteContent: Record<Locale, SiteLocaleContent> = {
  en: {
    brand: {
      subtitle: "Core decision-memory technology"
    },
    nav: {
      items: [
        { label: "Technology", href: "#technology" },
        { label: "First Application", href: "#first-application" },
        { label: "Evidence", href: "#evidence" },
        { label: "Roadmap", href: "#roadmap" },
        { label: "Contact", href: "#contact" }
      ],
      cta: "Discuss pilot fit"
    },
    hero: {
      eyebrow: "Core technology",
      headline: "Intuition Memory Layer",
      subheadline: "Turns fragmented workflow history into decision-ready context.",
      supportingLine:
        "Support_v1 is the first pilot-ready application of IML in a bounded support routing workflow.",
      primaryCta: "Discuss pilot fit",
      secondaryCta: "See the first application",
      proofLabel: "At a glance",
      proofStrip: [
        "IML is the core product thesis",
        "support_v1 is the first pilot-ready proving ground",
        "An internal eval and pilot-ready stack already exist",
        "Broader workflow paths follow only after first pilot evidence"
      ],
      asset: {
        label: "Hero brand asset",
        title: "Editorial brand visual for the IML thesis",
        body:
          "Premium hero artwork that communicates IML as a core technology layer, not as a support dashboard.",
        path: "/assets/iml/hero-environment-visual.png"
      }
    },
    technology: {
      eyebrow: "What IML is",
      title: "A layer for decisions that need more than raw memory recall.",
      body:
        "IML sits between memory systems and decisioning systems. It reconstructs historical context into a bounded, reviewable layer that a workflow can actually use at decision time.",
      cards: [
        {
          title: "Decision-memory, not generic memory",
          body:
            "The goal is not to store everything. The goal is to surface the parts of history that materially change a workflow decision."
        },
        {
          title: "Reviewable context, not blind automation",
          body:
            "IML is designed to keep decisions inspectable so a pilot can be evaluated with disciplined human review."
        },
        {
          title: "A core layer, not a narrow point tool",
          body:
            "support_v1 is the first applied vertical, but the underlying technology thesis is broader than support routing."
        }
      ],
      asset: {
        label: "Technology view",
        title: "Memory -> IML -> decisioning",
        body:
          "A concise view of IML as the layer that turns workflow history into bounded, usable decision context.",
        path: "/assets/iml/iml-conceptual-layer-visual.png"
      }
    },
    whyNow: {
      eyebrow: "Why this layer matters now",
      title: "Workflows have memory and models, but still lack a disciplined decision layer.",
      body:
        "Teams can now store history, retrieve fragments, and run models, but that still leaves a gap between raw recall and a reviewable operational decision. IML is meant to fill that gap.",
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
          title: "Proof needs bounded deployments",
          body:
            "A credible technology story starts with bounded evidence in a real workflow before it expands into broader platform claims."
        }
      ]
    },
    productTransition: {
      eyebrow: "First product",
      title: "First product built on imLayer",
      body:
        "The sections above describe the imLayer core technology. The sections below show its first applied product: support_v1."
    },
    supportFirst: {
      eyebrow: "Why support_v1 starts here",
      title: "support_v1 is the first applied workflow because support is verifiable, bounded, and commercially useful.",
      body:
        "As the first product built on imLayer, support_v1 gives the core layer a serious proving ground: real exports, visible decision points, constrained pilot scope, and a workflow where review quality can be examined directly.",
      cards: [
        {
          title: "Verifiable decision points",
          body:
            "Support routing creates concrete moments where better historical context can change whether a case follows a standard or careful path."
        },
        {
          title: "Real workflow data",
          body:
            "Exports, event history, timestamps, and case progression create the practical substrate needed for a disciplined pilot."
        },
        {
          title: "Pilot evidence before platform claims",
          body:
            "Support is the first beachhead because it allows claims to stay bounded while evidence compounds."
        },
        {
          title: "Commercial wedge",
          body:
            "A narrow first use-case creates a real entry point for partner conversations without pretending the full platform already exists."
        }
      ]
    },
    firstApplication: {
      eyebrow: "First application",
      title: "support_v1 is the first pilot-ready applied workflow built on imLayer.",
      body:
        "support_v1 applies the imLayer core technology to support routing workflows. It is not the whole technology. It is the first use case where the core layer is being shaped into a bounded pilot-ready implementation.",
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
            "Incoming data is checked for structure, ordering, coverage, and transformed into the working schema needed for evaluation."
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
        "The strongest current claim is that IML already has a serious internal eval layer and a pilot-ready support workflow. The evidence is meaningful enough for a first pilot conversation, while still bounded in scope.",
      highlight:
        "On the strongest current raw_ingest / combined_ab slice, calibrated IML reaches 92.31% versus 69.23% for the best non-calibrated baseline.",
      metrics: {
        calibratedLabel: "Calibrated IML",
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
            "The right claim is a bounded first pilot path with manual review, not a broad production rollout story."
        },
        {
          title: "Evidence remains uneven outside the strongest path",
          body:
            "The strongest slices support a pilot discussion, while weaker ingest paths still need more evidence before stronger claims should be made."
        }
      ],
      noteLabel: "Honest note",
      note:
        "Honest note: this page should not imply universal domain proof, broad deployment, or a fully production-ready platform. The current truth is a core technology thesis with a first pilot-ready application and a bounded evidence layer."
    },
    roadmap: {
      eyebrow: "Roadmap",
      title: "From core layer to broader workflow applications, one bounded step at a time.",
      body:
        "The roadmap should show expansion logic without skipping the pilot stage. Each step depends on evidence from the prior one rather than on abstract platform language.",
      steps: [
        {
          stage: "01",
          title: "Core technology: IML",
          body:
            "Continue hardening the decision-memory layer, evaluation logic, and reviewable decision framing that define the product thesis."
        },
        {
          stage: "02",
          title: "First applied vertical: support_v1",
          body:
            "Use support as the first proving ground where IML can be evaluated on real decision points and real export-derived context."
        },
        {
          stage: "03",
          title: "First real pilot / export onboarding",
          body:
            "Onboard a first partner on one bounded workflow slice, one export path, and one tightly reviewed pilot scope."
        },
        {
          stage: "04",
          title: "Second use-case after pilot",
          body:
            "Test a second applied workflow such as an e-commerce user-profile layer or a CRM entity workflow, first on synthetic data and then on 1-2 real cases."
        },
        {
          stage: "05",
          title: "Broader workflow / agent use-cases",
          body:
            "Only after compounding pilot evidence should IML expand into wider workflow and agent-oriented decision contexts."
        }
      ],
      asset: {
        label: "Roadmap view",
        title: "Evidence-led expansion",
        body:
          "A sequenced view from the core IML layer to the first pilot and only then to broader workflow applications.",
        path: "/assets/iml/platform-expansion-visual.png"
      }
    },
    beyondSupport: {
      eyebrow: "Beyond support",
      title: "The broader story starts after the first pilot proves out the layer.",
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
    cta: {
      eyebrow: "Contact",
      title: "Discuss a bounded first pilot.",
      body:
        "If you have support exports and want to evaluate whether IML can improve decision quality on a bounded workflow slice, the right next step is a pilot-fit conversation.",
      guidance:
        "Share your export shape, current routing workflow, review constraints, and what you want the first pilot to prove.",
      directEmailLabel: "Direct email",
      form: {
        nameLabel: "Name",
        namePlaceholder: "Jane Smith",
        emailLabel: "Work email",
        emailPlaceholder: "jane@company.com",
        companyLabel: "Company",
        companyPlaceholder: "Company name",
        messageLabel: "Message",
        messagePlaceholder:
          "Support export shape, routing workflow, review constraints, and what a first pilot should prove.",
        submitLabel: "Open pilot request",
        subject: "Pilot discussion request | Intuition Memory Layer"
      }
    },
    footer: {
      oneLine:
        "Intuition Memory Layer is the core technology. support_v1 is the first pilot-ready proving ground."
    }
  },
  sk: {
    brand: {
      subtitle: "Základná decision-memory technológia"
    },
    nav: {
      items: [
        { label: "Technológia", href: "#technology" },
        { label: "Prvá aplikácia", href: "#first-application" },
        { label: "Dôkazy", href: "#evidence" },
        { label: "Roadmap", href: "#roadmap" },
        { label: "Kontakt", href: "#contact" }
      ],
      cta: "Prediskutovať pilot"
    },
    hero: {
      eyebrow: "Základná technológia",
      headline: "Intuition Memory Layer",
      subheadline: "Premieňa fragmentovanú históriu workflow na kontext pripravený na rozhodovanie.",
      supportingLine:
        "support_v1 je prvá aplikácia IML pripravená na pilot v ohraničenom support routing workflow.",
      primaryCta: "Prediskutovať pilot",
      secondaryCta: "Pozrieť prvú aplikáciu",
      proofLabel: "Prehľad",
      proofStrip: [
        "IML je hlavná produktová téza",
        "support_v1 je prvé pilot-ready overenie v praxi",
        "Interný eval aj pilot-ready stack už existujú",
        "Širšie workflow cesty dávajú zmysel až po prvých pilotných dôkazoch"
      ],
      asset: {
        label: "Hero brand asset",
        title: "Brand vizuál pre tézu IML",
        body:
          "Prémiový hero vizuál, ktorý komunikuje IML ako základnú technologickú vrstvu, nie ako support dashboard.",
        path: "/assets/iml/hero-environment-visual.png"
      }
    },
    technology: {
      eyebrow: "Čo je IML",
      title: "Vrstva pre rozhodnutia, ktoré potrebujú viac než surový recall histórie.",
      body:
        "IML stojí medzi memory systémami a decisioning systémami. Rekonštruuje historický kontext do ohraničenej, kontrolovateľnej vrstvy, ktorú workflow vie reálne použiť v momente rozhodnutia.",
      cards: [
        {
          title: "Decision-memory, nie generická pamäť",
          body:
            "Cieľom nie je uložiť všetko. Cieľom je vytiahnuť tie časti histórie, ktoré reálne menia workflow rozhodnutie."
        },
        {
          title: "Kontrolovateľný kontext, nie slepá automatizácia",
          body:
            "IML je navrhnutý tak, aby pilot zostal kontrolovateľný a dal sa vyhodnocovať s disciplinovaným ľudským review."
        },
        {
          title: "Základná vrstva, nie úzky point tool",
          body:
            "support_v1 je prvá aplikovaná vertikála, ale základná technologická téza je širšia než samotný support routing."
        }
      ],
      asset: {
        label: "Pohľad na technológiu",
        title: "Pamäť -> IML -> rozhodovanie",
        body:
          "Stručný pohľad na IML ako vrstvu medzi historickou pamäťou a operatívnym rozhodovaním.",
        path: "/assets/iml/iml-conceptual-layer-visual.png"
      }
    },
    whyNow: {
      eyebrow: "Prečo táto vrstva práve teraz",
      title: "Workflow majú pamäť aj modely, no stále im chýba disciplinovaná rozhodovacia vrstva.",
      body:
        "Tímy už vedia ukladať históriu, vyťahovať fragmenty a spúšťať modely, ale stále chýba vrstva medzi raw recall a kontrolovateľným operatívnym rozhodnutím.",
      cards: [
        {
          title: "Samotná pamäť nerozhoduje",
          body:
            "Workflow potrebuje správny historický tvar, nie iba viac uložených dát alebo dlhšie context window."
        },
        {
          title: "Decisioning potrebuje štruktúru",
          body:
            "Operatívne voľby potrebujú vrstvu, ktorá vie rekonštruovať decision context opakovateľne a kontrolovateľne."
        },
        {
          title: "Proof potrebuje ohraničené nasadenie",
          body:
            "Dôveryhodný technologický príbeh sa začína ohraničeným dôkazom v reálnom workflow a až potom širšími platformovými tvrdeniami."
        }
      ]
    },
    productTransition: {
      eyebrow: "Prvý produkt",
      title: "Prvý produkt postavený na imLayer",
      body:
        "Sekcie vyššie popisujú jadrovú technológiu imLayer. Sekcie nižšie ukazujú jej prvý aplikovaný produkt: support_v1."
    },
    supportFirst: {
      eyebrow: "Prečo support_v1 začína tu",
      title: "support_v1 je prvý aplikovaný workflow, pretože support je overiteľný, ohraničený a komerčne užitočný.",
      body:
        "Ako prvý produkt postavený na imLayer dáva support_v1 jadrovej vrstve seriózne prvé proving ground: reálne exporty, viditeľné decision points, úzky pilot scope a workflow, kde sa dá review quality posudzovať priamo.",
      cards: [
        {
          title: "Overiteľné decision points",
          body:
            "Support routing vytvára konkrétne momenty, kde lepší historical context môže zmeniť, či prípad pôjde štandardnou alebo opatrnejšou cestou."
        },
        {
          title: "Reálne workflow dáta",
          body:
            "Exporty, event history, časové pečiatky a case progression tvoria praktický základ pre disciplinovaný pilot."
        },
        {
          title: "Pilot evidence pred platform claimmi",
          body:
            "Support je prvý beachhead preto, lebo drží tvrdenia ohraničené, kým evidence postupne rastie."
        },
        {
          title: "Komerčný wedge",
          body:
            "Úzky prvý use-case vytvára reálny vstup do partnerských diskusií bez predstierania, že celá platforma už existuje."
        }
      ]
    },
    firstApplication: {
      eyebrow: "Prvá aplikácia",
      title: "support_v1 je prvý aplikovaný workflow postavený na imLayer a pripravený na pilot.",
      body:
        "support_v1 aplikuje jadrovú technológiu imLayer na support routing workflow. Nie je to celá technológia. Je to prvý use case, kde sa jadrová vrstva mení na ohraničenú implementáciu pripravenú na pilot.",
      workflowLabel: "Workflow",
      workflowTitle: "Ako support_v1 aplikuje vrstvu",
      workflow: [
        {
          title: "Príjem exportu",
          body:
            "Workflow sa začína ohraničeným support exportom alebo kontrolovaným support slice vhodným na pilotnú evaluáciu."
        },
        {
          title: "Validácia a normalizácia",
          body:
            "Prichádzajúce dáta sa kontrolujú na štruktúru, ordering a coverage a transformujú sa do pracovnej schémy potrebnej na evaluáciu."
        },
        {
          title: "Rekonštrukcia histórie",
          body:
            "Viditeľná support história sa znovu skladá tak, aby sa routing decisions hodnotili proti reálnemu case contextu."
        },
        {
          title: "Vyhodnotenie routingu",
          body:
            "Vrstva porovnáva routing rozhodnutia na labeled points, aby sa otestovalo, či lepší decision context zlepšuje voľbu cesty."
        },
        {
          title: "Kontrolovateľný výstup pre pilot",
          body:
            "Výsledkom je kontrolovateľná routing vrstva pre bounded pilot, nie claim o bezobslužnej production automatizácii."
        }
      ],
      builtLabel: "Už v stacku",
      builtTitle: "Čo už v stacku pripravenom na pilot existuje",
      built: [
        "Interné eval cesty naprieč módmi labeled_support, raw_ingest, csv_ingest, mapped_ingest a zendesk_like",
        "Validačná logika pre použiteľnosť exportu ešte pred hlbšou evaluáciou",
        "Normalizácia do pracovnej schémy používanej súčasným stackom",
        "Event a case-history reconstruction pre support decision points",
        "Comparison a calibration logika pre bounded routing evaluation",
        "Pilot packaging a handoff materiály pre prvé externé onboardingy"
      ],
      asset: {
        label: "Aplikovaný workflow",
        title: "support_v1 v praxi",
        body:
          "Striedmy pohľad na tok support_v1 od intake exportu po kontrolovateľné vyhodnotenie routingu.",
        path: "/assets/iml/support-v1-workflow-visual.png"
      }
    },
    evidence: {
      eyebrow: "Aktuálne dôkazy a pripravenosť na pilot",
      title: "Dôkazy podporujú ohraničený pilotný príbeh, nie univerzálny proof.",
      body:
        "Najsilnejší súčasný claim je, že IML už má serióznu internú eval vrstvu a support workflow pripravený na pilot. Evidence je dosť silné na prvú pilotnú diskusiu, stále však ostáva ohraničené.",
      highlight:
        "Na najsilnejšom súčasnom raw_ingest / combined_ab slice dosahuje calibrated IML 92.31 % oproti 69.23 % pre najlepší non-calibrated baseline.",
      metrics: {
        calibratedLabel: "Calibrated IML",
        calibratedValue: "92.31%",
        baselineLabel: "Najlepší baseline",
        baselineValue: "69.23%",
        context: "Najsilnejší súčasný slice: raw_ingest / combined_ab",
        deltaLabel: "Pozorovaná delta",
        deltaValue: "+23.08 pp"
      },
      cards: [
        {
          title: "Interný eval stack existuje",
          body:
            "Aktuálny stack je viac než koncept. Už podporuje intake, validation, normalization, reconstruction, evaluation aj pilot packaging."
        },
        {
          title: "support_v1 je pripravený na pilot, nie na široké nasadenie",
          body:
            "Správny claim je ohraničená first-pilot path s manual review, nie story o širokom production rolloute."
        },
        {
          title: "Mimo najsilnejšej cesty zostávajú dôkazy nerovnomerné",
          body:
            "Najsilnejšie slices podporujú pilot conversation, ale slabšie ingest cesty ešte potrebujú viac evidence pred silnejšími tvrdeniami."
        }
      ],
      noteLabel: "Poctivá poznámka",
      note:
        "Poctivá poznámka: stránka nemá naznačovať univerzálny domain proof, broad deployment ani plne production-ready platformu. Aktuálna pravda je základná technologická téza s prvou aplikáciou pripravenou na pilot a s ohraničenou vrstvou dôkazov."
    },
    roadmap: {
      eyebrow: "Roadmap",
      title: "Od základnej vrstvy k širším workflow aplikáciám, krok po kroku.",
      body:
        "Roadmap má ukázať logiku expanzie bez preskočenia pilotnej fázy. Každý krok stojí na evidence z predchádzajúceho kroku, nie na abstraktnom platform jazyku.",
      steps: [
        {
          stage: "01",
          title: "Základná technológia: IML",
          body:
            "Ďalej spevňovať decision-memory vrstvu, evaluačnú logiku a kontrolovateľný decision framing, ktoré definujú produktovú tézu."
        },
        {
          stage: "02",
          title: "Prvá aplikovaná vertikála: support_v1",
          body:
            "Použiť support ako prvé proving ground, kde sa IML dá testovať na reálnych decision points a na reálnom export-derived contexte."
        },
        {
          stage: "03",
          title: "Prvý reálny pilot / export onboarding",
          body:
            "Onboardovať prvého partnera na jednom bounded workflow slice, jednej export ceste a jednom tesne reviewovanom pilot scope."
        },
        {
          stage: "04",
          title: "Druhý use-case po pilote",
          body:
            "Otestovať druhú aplikovanú workflow oblasť, napríklad e-commerce user-profile layer alebo CRM entity workflow, najprv na synthetic data a potom na 1-2 real cases."
        },
        {
          stage: "05",
          title: "Širšie workflow / agent use-cases",
          body:
            "Až po nahromadení pilot evidence má zmysel rozširovať IML do širších workflow a agent-oriented decision kontextov."
        }
      ],
      asset: {
        label: "Pohľad na roadmap",
        title: "Expanzia vedená dôkazmi",
        body:
          "Sekvenčný pohľad od jadra IML k prvému pilotu a až potom k širším workflow aplikáciám.",
        path: "/assets/iml/platform-expansion-visual.png"
      }
    },
    beyondSupport: {
      eyebrow: "Za hranicou supportu",
      title: "Širší príbeh sa začína až vtedy, keď prvý pilot potvrdí vrstvu.",
      body:
        "Ďalšia kapitola nie je okamžitý cross-domain rollout. Je to druhý bounded use-case, kde sa rovnaká decision-memory logika otestuje na inom type workflow.",
      examplesTitle: "Pravdepodobné ďalšie use-cases",
      examples: [
        {
          title: "E-commerce user-profile layer",
          body:
            "Decision-memory vrstva, ktorá rekonštruuje user history a profile state pred dôležitými service, risk alebo lifecycle rozhodnutiami."
        },
        {
          title: "CRM entity workflow",
          body:
            "Vrstva, ktorá drží account, contact a entity históriu použiteľnú presne v momente, keď workflow potrebuje rozhodnúť, ako routovať alebo konať."
        }
      ],
      note:
        "Očakávaný postup je synthetic data najprv a potom 1-2 real cases až po tom, čo prvý support pilot vytvorí dosť evidence pre druhú vertikálu."
    },
    cta: {
      eyebrow: "Kontakt",
      title: "Prediskutujme ohraničený prvý pilot.",
      body:
        "Ak máte support exporty a chcete vyhodnotiť, či IML vie zlepšiť decision quality na ohraničenom workflow slice, správnym ďalším krokom je pilot-fit diskusia.",
      guidance:
        "Pošlite export shape, aktuálny routing workflow, review constraints a to, čo má prvý pilot dokázať.",
      directEmailLabel: "Napísať priamo",
      form: {
        nameLabel: "Meno",
        namePlaceholder: "Jana Nováková",
        emailLabel: "Pracovný e-mail",
        emailPlaceholder: "jana@firma.sk",
        companyLabel: "Firma",
        companyPlaceholder: "Názov firmy",
        messageLabel: "Správa",
        messagePlaceholder:
          "Support export shape, routing workflow, review constraints a čo má prvý pilot dokázať.",
        submitLabel: "Otvoriť pilotnú žiadosť",
        subject: "Pilot diskusia | Intuition Memory Layer"
      }
    },
    footer: {
      oneLine:
        "Intuition Memory Layer je základná technológia. support_v1 je prvé prostredie pripravené na pilotné overenie."
    }
  }
};

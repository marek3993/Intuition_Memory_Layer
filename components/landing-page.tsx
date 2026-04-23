"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type FormEvent,
  type ReactNode
} from "react";
import {
  Locale,
  PageKey,
  PUBLIC_BRAND_EXPANDED_NAME,
  PUBLIC_BRAND_NAME,
  creatorLinkedInUrl,
  localeLabels,
  runtimeEvidenceSnapshot,
  siteContent
} from "@/data/site-content";

const emptyForm = {
  name: "",
  email: "",
  company: "",
  message: ""
};

const heroAssetByPage: Record<PageKey, string> = {
  home: "/assets/iml/hero-environment-visual.png",
  evidence: "/assets/iml/hero-environment-visual.png",
  support: "/assets/iml/hero-environment-visual.png"
};

const pagePathByKey: Record<PageKey, string> = {
  home: "/",
  evidence: "/evidence-and-validation",
  support: "/support-v1"
};

const archiveOrder = ["current", "heldout", "earlier", "support"] as const;
type ArchiveKey = (typeof archiveOrder)[number];
type ComparisonKey = "correctness" | "tokens" | "latency";
type MotionLevel = "minimal" | "subtle" | "moderate" | "strong";

export function LandingPage({
  page,
  initialLocale
}: {
  page: PageKey;
  initialLocale: Locale;
}) {
  const router = useRouter();
  const pathname = usePathname() || pagePathByKey[page];
  const searchParams = useSearchParams();
  const [locale, setLocale] = useState<Locale>(initialLocale);
  const [form, setForm] = useState(emptyForm);
  const [submitState, setSubmitState] = useState<"idle" | "loading" | "success" | "error">(
    "idle"
  );
  const [submitMessage, setSubmitMessage] = useState("");

  useEffect(() => {
    setLocale(initialLocale);
  }, [initialLocale]);

  useEffect(() => {
    document.documentElement.lang = locale;
    window.localStorage.setItem("imlayer-locale", locale);
  }, [locale]);

  useEffect(() => {
    if (searchParams.get("lang")) {
      return;
    }

    const storedLocale = window.localStorage.getItem("imlayer-locale");

    if ((storedLocale === "en" || storedLocale === "sk") && storedLocale !== locale) {
      setLocale(storedLocale);
      router.replace(
        buildLocalizedHref(pathname, storedLocale, window.location.hash.replace("#", "")),
        { scroll: false }
      );
    }
  }, [locale, pathname, router, searchParams]);

  const content = siteContent[locale];
  const currentRoute = pagePathByKey[page];
  const contactHref = localizedHref(locale, "/support-v1", "contact");

  const handleLocaleChange = (nextLocale: Locale) => {
    setLocale(nextLocale);
    router.replace(
      buildLocalizedHref(pathname, nextLocale, window.location.hash.replace("#", "")),
      { scroll: false }
    );
  };

  const handleFieldChange = (field: keyof typeof emptyForm, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));

    if (submitState !== "idle") {
      setSubmitState("idle");
      setSubmitMessage("");
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (submitState === "loading") {
      return;
    }

    const messages = content.formStatusMessages;

    setSubmitState("loading");
    setSubmitMessage("");

    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(form)
      });

      const result = (await response.json().catch(() => null)) as
        | { success?: boolean; error?: string }
        | null;

      if (!response.ok || !result?.success) {
        throw new Error(
          response.status === 400
            ? result?.error || messages.validationError
            : result?.error || messages.error
        );
      }

      setForm(emptyForm);
      setSubmitState("success");
      setSubmitMessage(messages.success);
    } catch (error) {
      setSubmitState("error");
      setSubmitMessage(
        error instanceof Error && error.message ? error.message : messages.error
      );
    }
  };

  return (
    <main lang={locale} className="relative overflow-x-clip bg-ink text-white">
      <BackgroundGlow />

      <header className="sticky top-0 z-50 border-b border-white/10 bg-[rgba(5,8,18,0.78)] backdrop-blur-2xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-2.5 sm:px-6">
          <Link href={localizedHref(locale, "/")} className="flex min-w-0 items-center gap-3">
            <Image
              src="/assets/iml/site-logo-navbar.png"
              alt="IML logo"
              width={518}
              height={562}
              priority
              sizes="64px"
              className="h-16 w-auto shrink-0 object-contain"
            />
            <div className="min-w-0">
              <div className="text-sm font-semibold tracking-[0.06em] text-white/96">
                {PUBLIC_BRAND_NAME}
              </div>
              <div className="truncate text-xs text-white/48">
                {PUBLIC_BRAND_EXPANDED_NAME} - {content.header.brandSubtitle}
              </div>
            </div>
          </Link>

          <nav className="hidden items-center gap-2 lg:flex">
            {content.header.routeLinks.map((item) => {
              const active = currentRoute === item.href;

              return (
                <Link
                  key={item.href}
                  href={localizedHref(locale, item.href)}
                  className={cx(
                    "rounded-full px-4 py-2 text-sm transition duration-300",
                    active
                      ? "bg-white/[0.08] text-white"
                      : "text-white/62 hover:bg-white/[0.04] hover:text-white"
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="flex items-center gap-3">
            <div
              role="group"
              aria-label="Language switcher"
              className="inline-grid grid-cols-2 rounded-full border border-white/10 bg-white/[0.035] p-1"
            >
              {(Object.keys(localeLabels) as Locale[]).map((option) => {
                const active = locale === option;

                return (
                  <button
                    key={option}
                    type="button"
                    onClick={() => handleLocaleChange(option)}
                    className={cx(
                      "rounded-full px-3 py-2 text-xs font-semibold tracking-[0.18em] transition duration-300",
                      active ? "bg-accent text-ink" : "text-white/62 hover:text-white"
                    )}
                  >
                    {localeLabels[option]}
                  </button>
                );
              })}
            </div>

            <Link href={contactHref} className={buttonStyles("primary", "hidden sm:inline-flex")}>
              {content.header.contactCta}
              <ArrowIcon />
            </Link>
          </div>
        </div>
      </header>

      {page === "home" ? (
        <HomePage locale={locale} />
      ) : page === "evidence" ? (
        <EvidencePage locale={locale} />
      ) : (
        <SupportPage
          locale={locale}
          form={form}
          submitState={submitState}
          submitMessage={submitMessage}
          onFieldChange={handleFieldChange}
          onSubmit={handleSubmit}
        />
      )}

      <footer className="border-t border-white/10 bg-[rgba(4,7,16,0.96)]">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-8 text-sm text-white/48 sm:px-6 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-col gap-2">
            <span>{PUBLIC_BRAND_NAME}</span>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-white/34">
              <span>{content.footer.creatorFooter}</span>
              <a
                href={creatorLinkedInUrl}
                target="_blank"
                rel="noreferrer"
                className="text-white/42 underline decoration-white/12 underline-offset-4 transition duration-300 hover:text-accent hover:decoration-accent/45"
              >
                {content.footer.creatorLinkLabel}
              </a>
            </div>
          </div>
          <span className="pretty-copy max-w-2xl text-left md:text-right">
            {content.footer.summary}
          </span>
        </div>
      </footer>
    </main>
  );

  function localizedHref(localeValue: Locale, path: string, hash?: string) {
    return buildLocalizedHref(path, localeValue, hash);
  }
}

function HomePage({ locale }: { locale: Locale }) {
  const content = siteContent[locale].home;
  const panelCopy =
    locale === "sk"
      ? {
          title: "Runtime štruktúra",
          layerLabel: "imLayer",
          layerBody: "Jadrový technologický príbeh a runtime decision-memory vrstva.",
          evidenceLabel: "Runtime dôkazy",
          evidenceBody: "Primárna interná dôkazová vrstva pre aktuálnu validáciu tézy.",
          supportLabel: "support_v1",
          supportBody: "Prvý produkt, prvý komerčný wedge a prvá externá validačná cesta."
        }
      : {
          title: "Runtime structure",
          layerLabel: "imLayer",
          layerBody: "Core technology story and runtime decision-memory layer.",
          evidenceLabel: "Runtime evidence",
          evidenceBody: "Primary internal proof layer for current thesis validation.",
          supportLabel: "support_v1",
          supportBody: "First product, first commercial wedge, and first external validation path."
        };

  return (
    <>
      <HeroSection
        assetPath={heroAssetByPage.home}
        aside={
          <Reveal motion="subtle" className="surface-strong hidden p-6 lg:block">
            <div className="text-[11px] font-medium uppercase tracking-[0.24em] text-accent/72">
              {panelCopy.title}
            </div>
            <div className="mt-5 grid gap-3">
              <CompactMessageCard
                label={panelCopy.layerLabel}
                body={panelCopy.layerBody}
              />
              <CompactMessageCard
                label={panelCopy.evidenceLabel}
                body={panelCopy.evidenceBody}
              />
              <CompactMessageCard
                label={panelCopy.supportLabel}
                body={panelCopy.supportBody}
              />
            </div>
          </Reveal>
        }
      >
        <Reveal motion="subtle" className="max-w-[42rem]">
          <span className="eyebrow">{content.hero.brandLabel}</span>
          <h1 className="balanced-heading mt-6 max-w-[14ch] text-[3.2rem] font-semibold leading-[0.9] tracking-[-0.065em] text-white sm:max-w-none sm:text-[4.45rem] lg:text-[5.2rem] xl:text-[5.9rem]">
            {content.hero.headline}
          </h1>
          <p className="pretty-copy mt-7 max-w-[35rem] text-[1.08rem] leading-8 text-white/78 sm:text-[1.18rem]">
            {content.hero.subheadline}
          </p>
          <p className="pretty-copy mt-3 max-w-[39rem] text-sm leading-7 text-white/52 sm:text-[0.96rem]">
            {content.hero.supportingLine}
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:mt-9 sm:flex-row">
            <Link href={buildLocalizedHref("/evidence-and-validation", locale)} className={buttonStyles("primary")}>
              {content.hero.primaryCta}
              <ArrowIcon />
            </Link>
            <Link href={buildLocalizedHref("/support-v1", locale)} className={buttonStyles("secondary")}>
              {content.hero.secondaryCta}
              <ArrowIcon />
            </Link>
          </div>
        </Reveal>
      </HeroSection>

      <Section tone="tone-charcoal-blue">
        <Intro eyebrow={content.whatChanges.eyebrow} title={content.whatChanges.eyebrow} body={content.whatChanges.intro} />
        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {content.whatChanges.cards.map((card, index) => (
            <Reveal key={card.title} motion="subtle" delay={index * 90}>
              <TextCard title={card.title} body={card.body} />
            </Reveal>
          ))}
        </div>
      </Section>

      <Section tone="tone-deep-navy">
        <Reveal motion="subtle">
          <span className="eyebrow">{content.proofHighlight.eyebrow}</span>
        </Reveal>
        <Reveal motion="subtle" delay={60} className="surface-strong mt-8 p-6 sm:p-8">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <StaticMetricCard label={runtimeEvidenceSnapshot.evaluatedLabel} value="2521 / 2521" />
            <StaticMetricCard label="packet accuracy" value="1.0000" />
            <StaticMetricCard label="raw accuracy" value="0.3455" />
            <StaticMetricCard label="lower input tokens" value="61.25%" />
          </div>
          <p className="pretty-copy mt-8 max-w-3xl text-base leading-8 text-white/74">
            {content.proofHighlight.interpretation}
          </p>
          <div className="mt-5 rounded-[24px] border border-accent/16 bg-accent/[0.07] px-5 py-4 text-sm text-white/72">
            {content.proofHighlight.qualification}
          </div>
          <div className="mt-7">
            <Link
              href={buildLocalizedHref("/evidence-and-validation", locale)}
              className={buttonStyles("primary")}
            >
              {content.proofHighlight.primaryCta}
              <ArrowIcon />
            </Link>
          </div>
        </Reveal>
      </Section>

      <Section tone="tone-charcoal-blue-soft">
        <Intro eyebrow={content.gateway.eyebrow} title={content.gateway.title} body="" />
        <div className="mt-10 grid gap-5 lg:grid-cols-2">
          {content.gateway.cards.map((card, index) => (
            <Reveal key={card.title} motion="subtle" delay={index * 100}>
              <article className="surface h-full p-6 sm:p-7">
                <h3 className="balanced-heading text-2xl font-semibold tracking-[-0.04em] text-white">
                  {card.title}
                </h3>
                <p className="pretty-copy mt-4 text-sm leading-7 text-white/62">{card.body}</p>
                <div className="mt-7">
                  <Link href={buildLocalizedHref(card.href, locale)} className={buttonStyles("secondary")}>
                    {card.cta}
                    <ArrowIcon />
                  </Link>
                </div>
              </article>
            </Reveal>
          ))}
        </div>
      </Section>

      <Section tone="tone-graphite">
        <Reveal motion="subtle">
          <Intro
            eyebrow={content.maturity.eyebrow}
            title={content.maturity.title}
            body=""
          />
        </Reveal>
        <div className="mt-10 grid gap-4">
          {content.maturity.items.map((item, index) => (
            <Reveal key={item} motion="subtle" delay={index * 70}>
              <div className="surface flex items-center justify-between gap-4 px-5 py-4 sm:px-6">
                <span className="pretty-copy text-sm leading-7 text-white/76 sm:text-base">
                  {item}
                </span>
                <span className="rounded-full border border-accent/16 bg-accent/[0.08] px-3 py-1 text-[10px] font-medium uppercase tracking-[0.2em] text-accent">
                  {String(index + 1).padStart(2, "0")}
                </span>
              </div>
            </Reveal>
          ))}
        </div>
      </Section>

      <Section tone="tone-steel-blue">
        <Reveal motion="minimal" className="surface-strong p-7 sm:p-9">
          <span className="eyebrow">Pilot path</span>
          <h2 className="balanced-heading mt-6 text-[2.2rem] font-semibold leading-[1.02] tracking-[-0.05em] text-white sm:text-[3.2rem]">
            {content.finalCta.headline}
          </h2>
          <p className="pretty-copy mt-5 max-w-3xl text-base leading-8 text-white/68 sm:text-[1.03rem]">
            {content.finalCta.supportingLine}
          </p>
          <div className="mt-8">
            <Link href={buildLocalizedHref("/support-v1", locale, "contact")} className={buttonStyles("primary")}>
              {content.finalCta.primaryCta}
              <ArrowIcon />
            </Link>
          </div>
        </Reveal>
      </Section>
    </>
  );
}

function EvidencePage({ locale }: { locale: Locale }) {
  const content = siteContent[locale].evidence;
  const [archiveKey, setArchiveKey] = useState<ArchiveKey>("current");
  const archiveItem = content.archive.items[archiveKey];
  const proofCopy =
    locale === "sk"
      ? {
          evaluatedCases: "Evaluované prípady",
          packetAccuracy: "Packet accuracy",
          rawAccuracy: "Raw accuracy",
          inputTokenReduction: "Zníženie vstupných tokenov",
          failedCases: "Zlyhané prípady",
          packetOnlyWins: "Packet-only wins",
          rawOnlyWins: "Raw-only wins",
          bothWrong: "Obe nesprávne",
          rawInputTokens: "Raw input tokens",
          packetInputTokens: "Packet input tokens",
          rawOutputTokens: "Raw output tokens",
          packetOutputTokens: "Packet output tokens",
          averageRawLatency: "Average raw latency",
          averagePacketLatency: "Average packet latency",
          averageLatencyDelta: "Average latency delta",
          medianRawLatency: "Median raw latency",
          medianPacketLatency: "Median packet latency",
          medianLatencyDelta: "Median latency delta",
          p95RawLatency: "p95 raw latency",
          p95PacketLatency: "p95 packet latency",
          p95LatencyDelta: "p95 latency delta"
        }
      : {
          evaluatedCases: "Evaluated cases",
          packetAccuracy: "Packet accuracy",
          rawAccuracy: "Raw accuracy",
          inputTokenReduction: "Input token reduction",
          failedCases: "Failed cases",
          packetOnlyWins: "Packet-only wins",
          rawOnlyWins: "Raw-only wins",
          bothWrong: "Both wrong",
          rawInputTokens: "Raw input tokens",
          packetInputTokens: "Packet input tokens",
          rawOutputTokens: "Raw output tokens",
          packetOutputTokens: "Packet output tokens",
          averageRawLatency: "Average raw latency",
          averagePacketLatency: "Average packet latency",
          averageLatencyDelta: "Average latency delta",
          medianRawLatency: "Median raw latency",
          medianPacketLatency: "Median packet latency",
          medianLatencyDelta: "Median latency delta",
          p95RawLatency: "p95 raw latency",
          p95PacketLatency: "p95 packet latency",
          p95LatencyDelta: "p95 latency delta"
        };
  const asideCopy =
    locale === "sk"
      ? {
          title: "Aktuálny signál",
          evaluated: proofCopy.evaluatedCases,
          packetAccuracy: proofCopy.packetAccuracy,
          inputReduction: proofCopy.inputTokenReduction
        }
      : {
          title: "Current signal",
          evaluated: proofCopy.evaluatedCases,
          packetAccuracy: proofCopy.packetAccuracy,
          inputReduction: proofCopy.inputTokenReduction
        };

  return (
    <>
      <HeroSection
        assetPath={heroAssetByPage.evidence}
        aside={
          <Reveal motion="moderate" className="surface-strong hidden p-6 lg:block">
            <div className="text-[11px] font-medium uppercase tracking-[0.24em] text-accent/72">
              {asideCopy.title}
            </div>
            <div className="mt-5 grid gap-3">
              <CompactMetricPanel
                title={asideCopy.evaluated}
                value={formatFraction(runtimeEvidenceSnapshot.evaluatedCompleted, runtimeEvidenceSnapshot.evaluatedTotal)}
              />
              <CompactMetricPanel
                title={asideCopy.packetAccuracy}
                value={formatFixed(runtimeEvidenceSnapshot.packetAccuracy, 4)}
              />
              <CompactMetricPanel
                title={asideCopy.inputReduction}
                value={formatPercent(runtimeEvidenceSnapshot.inputReductionPercent, 2)}
              />
            </div>
          </Reveal>
        }
      >
        <Reveal motion="moderate" className="max-w-[44rem]">
          <span className="eyebrow">{content.hero.eyebrow}</span>
          <h1 className="balanced-heading mt-6 max-w-[14ch] text-[3.2rem] font-semibold leading-[0.9] tracking-[-0.065em] text-white sm:max-w-none sm:text-[4.45rem] lg:text-[5rem]">
            {content.hero.headline}
          </h1>
          <p className="pretty-copy mt-7 max-w-[43rem] text-[1.08rem] leading-8 text-white/78 sm:text-[1.18rem]">
            {content.hero.subheadline}
          </p>
          <p className="pretty-copy mt-5 max-w-[36rem] text-sm leading-7 text-white/52">
            {content.hero.qualification}
          </p>
        </Reveal>
      </HeroSection>

      <Section tone="tone-charcoal-blue">
        <Reveal motion="moderate">
          <Intro
            eyebrow={content.currentEvidence.eyebrow}
            title={content.currentEvidence.eyebrow}
            body={content.currentEvidence.interpretation}
          />
        </Reveal>
        <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Reveal motion="strong" delay={0}>
            <StaticMetricCard
              label={proofCopy.evaluatedCases}
              value={formatFraction(
                runtimeEvidenceSnapshot.evaluatedCompleted,
                runtimeEvidenceSnapshot.evaluatedTotal
              )}
            />
          </Reveal>
          <Reveal motion="strong" delay={70}>
            <StaticMetricCard
              label={proofCopy.packetAccuracy}
              value={formatFixed(runtimeEvidenceSnapshot.packetAccuracy, 4)}
            />
          </Reveal>
          <Reveal motion="strong" delay={140}>
            <StaticMetricCard
              label={proofCopy.rawAccuracy}
              value={formatFixed(runtimeEvidenceSnapshot.rawAccuracy, 4)}
            />
          </Reveal>
          <Reveal motion="strong" delay={210}>
            <StaticMetricCard
              label={proofCopy.inputTokenReduction}
              value={formatPercent(runtimeEvidenceSnapshot.inputReductionPercent, 2)}
            />
          </Reveal>
        </div>
      </Section>

      <Section tone="tone-deep-navy">
        <Reveal motion="moderate">
          <Intro
            eyebrow={content.keyMetrics.eyebrow}
            title={content.keyMetrics.eyebrow}
            body=""
          />
        </Reveal>
        <div className="mt-10 grid gap-5 xl:grid-cols-3">
          <Reveal motion="strong">
            <MetricsGroupCard
              title={content.keyMetrics.coverageTitle}
              items={[
                `${proofCopy.evaluatedCases}: ${formatFraction(
                  runtimeEvidenceSnapshot.evaluatedCompleted,
                  runtimeEvidenceSnapshot.evaluatedTotal
                )}`,
                `${proofCopy.failedCases}: ${runtimeEvidenceSnapshot.failedCases}`
              ]}
            />
          </Reveal>
          <Reveal motion="strong" delay={90}>
            <MetricsGroupCard
              title={content.keyMetrics.correctnessTitle}
              items={[
                `${proofCopy.rawAccuracy}: ${formatFixed(runtimeEvidenceSnapshot.rawAccuracy, 4)}`,
                `${proofCopy.packetAccuracy}: ${formatFixed(
                  runtimeEvidenceSnapshot.packetAccuracy,
                  4
                )}`,
                `${proofCopy.rawOnlyWins}: ${runtimeEvidenceSnapshot.rawCorrectPacketWrong}`,
                `${proofCopy.packetOnlyWins}: ${runtimeEvidenceSnapshot.packetCorrectRawWrong}`,
                `${proofCopy.bothWrong}: ${runtimeEvidenceSnapshot.bothWrong}`
              ]}
            />
          </Reveal>
          <Reveal motion="strong" delay={180}>
            <MetricsGroupCard
              title={content.keyMetrics.runtimeEconomicsTitle}
              items={[
                `${proofCopy.rawInputTokens}: ${formatFixed(
                  runtimeEvidenceSnapshot.inputTokens.raw,
                  4
                )}`,
                `${proofCopy.packetInputTokens}: ${formatFixed(
                  runtimeEvidenceSnapshot.inputTokens.packet,
                  4
                )}`,
                `${proofCopy.inputTokenReduction}: ${formatPercent(
                  runtimeEvidenceSnapshot.inputReductionPercent,
                  2
                )}`,
                `${proofCopy.rawOutputTokens}: ${formatFixed(
                  runtimeEvidenceSnapshot.outputTokens.raw,
                  4
                )}`,
                `${proofCopy.packetOutputTokens}: ${formatFixed(
                  runtimeEvidenceSnapshot.outputTokens.packet,
                  4
                )}`,
                `${proofCopy.averageRawLatency}: ${formatMs(
                  runtimeEvidenceSnapshot.latencyAverageMs.raw,
                  2
                )}`,
                `${proofCopy.averagePacketLatency}: ${formatMs(
                  runtimeEvidenceSnapshot.latencyAverageMs.packet,
                  3
                )}`,
                `${proofCopy.averageLatencyDelta}: ${formatMs(
                  runtimeEvidenceSnapshot.latencyAverageMs.delta,
                  3
                )}`,
                `${proofCopy.medianRawLatency}: ${formatMs(
                  runtimeEvidenceSnapshot.latencyMedianMs.raw,
                  3
                )}`,
                `${proofCopy.medianPacketLatency}: ${formatMs(
                  runtimeEvidenceSnapshot.latencyMedianMs.packet,
                  3
                )}`,
                `${proofCopy.medianLatencyDelta}: ${formatMs(
                  runtimeEvidenceSnapshot.latencyMedianMs.delta,
                  3
                )}`,
                `${proofCopy.p95RawLatency}: ${formatMs(
                  runtimeEvidenceSnapshot.latencyP95Ms.raw,
                  3
                )}`,
                `${proofCopy.p95PacketLatency}: ${formatMs(
                  runtimeEvidenceSnapshot.latencyP95Ms.packet,
                  2
                )}`,
                `${proofCopy.p95LatencyDelta}: ${formatMs(
                  runtimeEvidenceSnapshot.latencyP95Ms.delta,
                  3
                )}`
              ]}
            />
          </Reveal>
        </div>
      </Section>

      <Section tone="tone-charcoal-blue-soft">
        <Reveal motion="moderate">
          <Intro
            eyebrow={content.comparisons.eyebrow}
            title={content.comparisons.title}
            body=""
          />
        </Reveal>
        <ComparisonTabs locale={locale} proofCopy={proofCopy} />
      </Section>

      <Section tone="tone-graphite">
        <Reveal motion="moderate">
          <Intro
            eyebrow={content.methodology.eyebrow}
            title={content.methodology.title}
            body=""
          />
        </Reveal>
        <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-5">
          {content.methodology.items.map((item, index) => (
            <Reveal key={item.title} motion="moderate" delay={index * 70}>
              <TextCard title={item.title} body={item.body} />
            </Reveal>
          ))}
        </div>
      </Section>

      <Section tone="tone-steel-blue">
        <Reveal motion="moderate">
          <Intro
            eyebrow={content.qualification.eyebrow}
            title={content.qualification.title}
            body=""
          />
        </Reveal>
        <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {content.qualification.items.map((item, index) => (
            <Reveal key={item} motion="moderate" delay={index * 60}>
              <div className="surface flex items-center gap-3 px-5 py-4">
                <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-accent shadow-[0_0_18px_rgba(137,180,255,0.38)]" />
                <span className="pretty-copy text-sm leading-7 text-white/72">{item}</span>
              </div>
            </Reveal>
          ))}
        </div>
      </Section>

      <Section tone="tone-charcoal-blue">
        <Reveal motion="moderate">
          <Intro eyebrow={content.archive.eyebrow} title={content.archive.title} body="" />
        </Reveal>
        <Reveal motion="strong" delay={50} className="surface-strong mt-10 p-6 sm:p-8">
          <div className="flex flex-wrap gap-2">
            {archiveOrder.map((key) => {
              const active = archiveKey === key;
              const item = content.archive.items[key];

              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => setArchiveKey(key)}
                  className={cx(
                    "rounded-full border px-4 py-2 text-sm transition duration-300",
                    active
                      ? "border-accent/25 bg-accent text-ink"
                      : "border-white/10 bg-white/[0.03] text-white/66 hover:border-accent/20 hover:text-white"
                  )}
                >
                  {item.label}
                </button>
              );
            })}
          </div>

          <div className="mt-8 grid gap-6 xl:grid-cols-[minmax(0,0.9fr)_minmax(280px,0.7fr)]">
            <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6">
              <div className="text-[11px] font-medium uppercase tracking-[0.24em] text-accent/72">
                {archiveItem.eyebrow}
              </div>
              <h3 className="balanced-heading mt-3 text-2xl font-semibold tracking-[-0.04em] text-white">
                {archiveItem.title}
              </h3>
              <p className="pretty-copy mt-4 text-sm leading-7 text-white/62">
                {archiveItem.body}
              </p>
              <div className="mt-6 rounded-[22px] border border-accent/16 bg-accent/[0.07] px-5 py-4 text-sm text-white/74">
                {archiveItem.note}
              </div>
            </div>

            <div className="grid gap-3">
              {archiveItem.metrics.map((metric, index) => (
                <div
                  key={metric}
                  className="rounded-[22px] border border-white/10 bg-white/[0.03] px-5 py-4"
                >
                  <div className="text-[10px] uppercase tracking-[0.22em] text-white/34">
                    {String(index + 1).padStart(2, "0")}
                  </div>
                  <p className="pretty-copy mt-2 text-sm leading-7 text-white/72">{metric}</p>
                </div>
              ))}
            </div>
          </div>
        </Reveal>
      </Section>

      <Section tone="tone-deep-navy">
        <Reveal motion="minimal" className="surface-strong p-7 sm:p-9">
          <span className="eyebrow">Next layer</span>
          <h2 className="balanced-heading mt-6 text-[2.2rem] font-semibold leading-[1.02] tracking-[-0.05em] text-white sm:text-[3.2rem]">
            {content.exitCta.headline}
          </h2>
          <div className="mt-8">
            <Link href={buildLocalizedHref("/support-v1", locale)} className={buttonStyles("primary")}>
              {content.exitCta.cta}
              <ArrowIcon />
            </Link>
          </div>
        </Reveal>
      </Section>
    </>
  );
}

function SupportPage({
  locale,
  form,
  submitState,
  submitMessage,
  onFieldChange,
  onSubmit
}: {
  locale: Locale;
  form: typeof emptyForm;
  submitState: "idle" | "loading" | "success" | "error";
  submitMessage: string;
  onFieldChange: (field: keyof typeof emptyForm, value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>;
}) {
  const content = siteContent[locale].support;
  const formContent = siteContent[locale].contactForm;
  const formStatusMessages = siteContent[locale].formStatusMessages;
  const asideCopy =
    locale === "sk"
      ? {
          title: "Prvý produkt",
          body:
            "support_v1 je prvý produktový povrch postavený na jadre imLayeru a prvá buyer-facing validačná cesta."
        }
      : {
          title: "First product",
          body:
            "support_v1 is the first product surface built on the imLayer core and the first buyer-facing validation path."
        };

  return (
    <>
      <HeroSection
        assetPath={heroAssetByPage.support}
        aside={
          <Reveal motion="moderate" className="surface-strong hidden p-5 lg:block">
            <div className="text-[11px] font-medium uppercase tracking-[0.24em] text-accent/72">
              {asideCopy.title}
            </div>
            <div className="asset-visual mt-4 asset-visual--workflow">
              <Image
                src="/assets/iml/support-v1-workflow-visual.png"
                alt="support_v1 workflow visual"
                width={1536}
                height={1024}
                sizes="(max-width: 1024px) 100vw, 34vw"
                className="asset-visual__image object-contain object-center"
              />
            </div>
            <p className="pretty-copy mt-4 text-sm leading-7 text-white/60">
              {asideCopy.body}
            </p>
          </Reveal>
        }
      >
        <Reveal motion="moderate" className="max-w-[42rem]">
          <span className="eyebrow">{content.hero.eyebrow}</span>
          <h1 className="balanced-heading mt-6 text-[3.6rem] font-semibold leading-[0.9] tracking-[-0.065em] text-white sm:text-[4.8rem] lg:text-[5.4rem]">
            {content.hero.headline}
          </h1>
          <p className="pretty-copy mt-7 max-w-[35rem] text-[1.08rem] leading-8 text-white/78 sm:text-[1.18rem]">
            {content.hero.subheadline}
          </p>
          <p className="pretty-copy mt-3 max-w-[39rem] text-sm leading-7 text-white/52 sm:text-[0.96rem]">
            {content.hero.supportingLine}
          </p>
          <div className="mt-8">
            <Link href={buildLocalizedHref("/support-v1", locale, "contact")} className={buttonStyles("primary")}>
              {content.hero.cta}
              <ArrowIcon />
            </Link>
          </div>
        </Reveal>
      </HeroSection>

      <Section tone="tone-charcoal-blue">
        <Reveal motion="moderate">
          <Intro eyebrow={content.whatIs.eyebrow} title={content.whatIs.title} body={content.whatIs.body} />
        </Reveal>
        <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {content.whatIs.cards.map((card, index) => (
            <Reveal key={card.title} motion="moderate" delay={index * 70}>
              <TextCard title={card.title} body={card.body} />
            </Reveal>
          ))}
        </div>
      </Section>

      <Section tone="tone-charcoal-blue-soft">
        <Reveal motion="moderate">
          <Intro eyebrow={content.whyWedge.eyebrow} title={content.whyWedge.title} body="" />
        </Reveal>
        <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-5">
          {content.whyWedge.cards.map((card, index) => (
            <Reveal key={card.title} motion="moderate" delay={index * 60}>
              <TextCard title={card.title} body={card.body} />
            </Reveal>
          ))}
        </div>
      </Section>

      <Section tone="tone-deep-navy">
        <Reveal motion="moderate">
          <Intro eyebrow={content.inPlace.eyebrow} title={content.inPlace.title} body="" />
        </Reveal>
        <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {content.inPlace.items.map((item, index) => (
            <Reveal key={item.title} motion="moderate" delay={index * 65}>
              <TextCard title={item.title} body={item.body} />
            </Reveal>
          ))}
        </div>
      </Section>

      <Section tone="tone-graphite">
        <Reveal motion="moderate">
          <Intro eyebrow={content.pilotFlow.eyebrow} title={content.pilotFlow.title} body="" />
        </Reveal>
        <div className="mt-10 grid gap-4">
          {content.pilotFlow.steps.map((step, index) => (
            <Reveal key={step.step} motion="moderate" delay={index * 80}>
              <div className="surface flex flex-col gap-4 p-5 sm:flex-row sm:items-start sm:p-6">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-accent/18 bg-accent/10 text-xs font-semibold tracking-[0.14em] text-accent">
                  {step.step}
                </span>
                <div>
                  <h3 className="balanced-heading text-lg font-semibold tracking-[-0.035em] text-white">
                    {step.title}
                  </h3>
                  <p className="pretty-copy mt-3 text-sm leading-7 text-white/62">{step.body}</p>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </Section>

      <Section tone="tone-charcoal-blue-soft">
        <Reveal motion="moderate">
          <Intro
            eyebrow={content.pilotExample.eyebrow}
            title={content.pilotExample.title}
            body={content.pilotExample.body}
          />
        </Reveal>
        <Reveal motion="moderate" delay={70} className="surface-strong mt-10 p-6 sm:p-8">
          <div className="grid gap-4 md:grid-cols-2">
            {content.pilotExample.items.map((item, index) => (
              <div
                key={item}
                className="rounded-[22px] border border-white/10 bg-white/[0.03] px-5 py-4"
              >
                <div className="text-[10px] uppercase tracking-[0.22em] text-accent/72">
                  {String(index + 1).padStart(2, "0")}
                </div>
                <p className="pretty-copy mt-2 text-sm leading-7 text-white/68">{item}</p>
              </div>
            ))}
          </div>
        </Reveal>
      </Section>

      <Section tone="tone-steel-blue">
        <Reveal motion="moderate">
          <Intro eyebrow={content.materials.eyebrow} title={content.materials.title} body={content.materials.body} />
        </Reveal>
        <div className="mt-10 grid gap-3">
          {content.materials.items.map((item, index) => (
            <Reveal key={item.title} motion="moderate" delay={index * 70}>
              <article className="surface flex flex-col gap-4 p-5 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <div className="text-[10px] uppercase tracking-[0.22em] text-accent/72">
                    {item.label}
                  </div>
                  <h3 className="balanced-heading mt-2 text-lg font-semibold tracking-[-0.035em] text-white">
                    {item.title}
                  </h3>
                  <p className="pretty-copy mt-3 max-w-3xl text-sm leading-7 text-white/62">
                    {item.body}
                  </p>
                </div>
                <div className="sm:shrink-0">
                  <Link
                    href={buildLocalizedHref("/support-v1", locale, "contact")}
                    className={buttonStyles("secondary", "min-w-[10.5rem]")}
                  >
                    {content.materials.requestLabel}
                    <ArrowIcon />
                  </Link>
                </div>
              </article>
            </Reveal>
          ))}
        </div>
      </Section>

      <Section id="contact" tone="tone-deep-navy">
        <Reveal motion="minimal" className="max-w-3xl">
          <Intro
            eyebrow={formContent.eyebrow}
            title={content.cta.headline}
            body={content.cta.supportingLine}
          />
          <p className="pretty-copy mt-6 max-w-2xl text-base leading-8 text-white/70">
            {formContent.guidance}
          </p>
        </Reveal>

        <Reveal motion="minimal" delay={80} className="mt-8 max-w-3xl">
          <form className="grid gap-4" onSubmit={onSubmit}>
            <div className="grid gap-4 md:grid-cols-2">
              <Field label={formContent.form.nameLabel}>
                <Input
                  value={form.name}
                  placeholder={formContent.form.namePlaceholder}
                  onChange={(event) => onFieldChange("name", event.target.value)}
                  disabled={submitState === "loading"}
                  required
                />
              </Field>
              <Field label={formContent.form.emailLabel}>
                <Input
                  type="email"
                  value={form.email}
                  placeholder={formContent.form.emailPlaceholder}
                  onChange={(event) => onFieldChange("email", event.target.value)}
                  disabled={submitState === "loading"}
                  required
                />
              </Field>
            </div>

            <Field label={formContent.form.companyLabel}>
              <Input
                value={form.company}
                placeholder={formContent.form.companyPlaceholder}
                onChange={(event) => onFieldChange("company", event.target.value)}
                disabled={submitState === "loading"}
              />
            </Field>

            <Field label={formContent.form.messageLabel}>
              <TextArea
                value={form.message}
                placeholder={formContent.form.messagePlaceholder}
                onChange={(event) => onFieldChange("message", event.target.value)}
                disabled={submitState === "loading"}
                required
              />
            </Field>

            <div className="flex flex-col gap-3">
              <button
                type="submit"
                disabled={submitState === "loading"}
                className={cx(
                  buttonStyles("primary"),
                  submitState === "loading" && "pointer-events-none opacity-80"
                )}
              >
                {submitState === "loading"
                  ? formStatusMessages.submitLoadingLabel
                  : formContent.form.submitLabel}
                <ArrowIcon />
              </button>
              <p
                aria-live="polite"
                className={cx(
                  "min-h-5 text-sm",
                  submitState === "success"
                    ? "text-accent"
                    : submitState === "error"
                      ? "text-[#ffb0b0]"
                      : "text-white/0"
                )}
              >
                {submitMessage}
              </p>
            </div>
          </form>
        </Reveal>
      </Section>
    </>
  );
}

function HeroSection({
  children,
  assetPath,
  aside
}: {
  children: ReactNode;
  assetPath: string;
  aside?: ReactNode;
}) {
  return (
    <section className="tone-deep-navy hero-section relative overflow-hidden px-5 pb-16 pt-12 sm:px-6 sm:pb-20 sm:pt-16 lg:pb-24 lg:pt-20">
      <HeroBackdrop path={assetPath} />
      <SectionGlow />
      <div className="mx-auto max-w-7xl">
        <div
          className={cx(
            "hero-content-shell",
            Boolean(aside) &&
              "lg:grid lg:grid-cols-[minmax(0,1fr)_minmax(320px,0.72fr)] lg:gap-8 lg:items-center"
          )}
        >
          {children}
          {aside}
        </div>
      </div>
    </section>
  );
}

function Section({
  children,
  tone,
  id
}: {
  children: ReactNode;
  tone: string;
  id?: string;
}) {
  return (
    <section id={id} className={cx("anchor-soft relative overflow-hidden", tone)}>
      <SectionGlow />
      <div className="mx-auto max-w-7xl px-5 py-20 sm:px-6 lg:py-24">{children}</div>
    </section>
  );
}

function Intro({
  eyebrow,
  title,
  body
}: {
  eyebrow: string;
  title: string;
  body: string;
}) {
  return (
    <div className="max-w-3xl">
      <span className="eyebrow">{eyebrow}</span>
      <h2 className="balanced-heading mt-5 text-[2.2rem] font-semibold leading-[1.02] tracking-[-0.05em] text-white sm:text-[3.2rem]">
        {title}
      </h2>
      {body ? (
        <p className="pretty-copy mt-5 text-base leading-8 text-white/68 sm:text-[1.03rem]">
          {body}
        </p>
      ) : null}
    </div>
  );
}

function TextCard({ title, body }: { title: string; body: string }) {
  return (
    <article className="surface h-full p-6 sm:p-7">
      <h3 className="balanced-heading text-xl font-semibold tracking-[-0.04em] text-white">
        {title}
      </h3>
      <p className="pretty-copy mt-3 text-sm leading-7 text-white/62">{body}</p>
    </article>
  );
}

function StaticMetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="surface h-full p-5 sm:p-6">
      <div className="text-[11px] uppercase tracking-[0.22em] text-white/34">{label}</div>
      <div className="mt-3 text-[2rem] font-semibold tracking-[-0.05em] text-white sm:text-[2.35rem]">
        {value}
      </div>
    </div>
  );
}

function CompactMessageCard({ label, body }: { label: string; body: string }) {
  return (
    <div className="rounded-[24px] border border-white/10 bg-white/[0.03] px-5 py-4">
      <div className="text-[10px] uppercase tracking-[0.22em] text-accent/72">{label}</div>
      <p className="pretty-copy mt-2 text-sm leading-7 text-white/66">{body}</p>
    </div>
  );
}

function CompactMetricPanel({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-[24px] border border-white/10 bg-white/[0.03] px-5 py-4">
      <div className="text-[10px] uppercase tracking-[0.22em] text-white/34">{title}</div>
      <div className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-white">{value}</div>
    </div>
  );
}

function MetricsGroupCard({ title, items }: { title: string; items: string[] }) {
  return (
    <article className="surface h-full p-6 sm:p-7">
      <h3 className="balanced-heading text-xl font-semibold tracking-[-0.04em] text-white">
        {title}
      </h3>
      <div className="mt-5 grid gap-3">
        {items.map((item) => (
          <div
            key={item}
            className="rounded-[20px] border border-white/10 bg-white/[0.03] px-4 py-3 text-sm leading-7 text-white/66"
          >
            {item}
          </div>
        ))}
      </div>
    </article>
  );
}

function ComparisonTabs({
  locale,
  proofCopy
}: {
  locale: Locale;
  proofCopy: {
    evaluatedCases: string;
    packetAccuracy: string;
    rawAccuracy: string;
    inputTokenReduction: string;
    failedCases: string;
    packetOnlyWins: string;
    rawOnlyWins: string;
    bothWrong: string;
    rawInputTokens: string;
    packetInputTokens: string;
    rawOutputTokens: string;
    packetOutputTokens: string;
    averageRawLatency: string;
    averagePacketLatency: string;
    averageLatencyDelta: string;
    medianRawLatency: string;
    medianPacketLatency: string;
    medianLatencyDelta: string;
    p95RawLatency: string;
    p95PacketLatency: string;
    p95LatencyDelta: string;
  };
}) {
  const content = siteContent[locale].evidence.comparisons;
  const [activeTab, setActiveTab] = useState<ComparisonKey>("correctness");
  const [ref, visible] = useInViewOnce<HTMLDivElement>(0.28);

  return (
    <div ref={ref} className="mt-10">
      <div className="flex flex-wrap gap-2">
        {(["correctness", "tokens", "latency"] as const).map((tab) => {
          const active = activeTab === tab;

          return (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab)}
              className={cx(
                "rounded-full border px-4 py-2 text-sm transition duration-300",
                active
                  ? "border-accent/25 bg-accent text-ink"
                  : "border-white/10 bg-white/[0.03] text-white/66 hover:border-accent/20 hover:text-white"
              )}
            >
              {content.tabs[tab]}
            </button>
          );
        })}
      </div>

      <div key={activeTab} className="mt-8">
        {activeTab === "correctness" ? (
          <CorrectnessPanel
            visible={visible}
            rawLabel={proofCopy.rawAccuracy}
            packetLabel={proofCopy.packetAccuracy}
            packetOnlyWinsLabel={proofCopy.packetOnlyWins}
            rawOnlyWinsLabel={proofCopy.rawOnlyWins}
            bothWrongLabel={proofCopy.bothWrong}
          />
        ) : activeTab === "tokens" ? (
          <TokensPanel
            visible={visible}
            inputReductionLabel={proofCopy.inputTokenReduction}
            rawInputLabel={proofCopy.rawInputTokens}
            packetInputLabel={proofCopy.packetInputTokens}
            rawOutputLabel={proofCopy.rawOutputTokens}
            packetOutputLabel={proofCopy.packetOutputTokens}
          />
        ) : (
          <LatencyPanel
            visible={visible}
            averageRawLabel={proofCopy.averageRawLatency}
            averagePacketLabel={proofCopy.averagePacketLatency}
            averageDeltaLabel={proofCopy.averageLatencyDelta}
            medianRawLabel={proofCopy.medianRawLatency}
            medianPacketLabel={proofCopy.medianPacketLatency}
            medianDeltaLabel={proofCopy.medianLatencyDelta}
            p95RawLabel={proofCopy.p95RawLatency}
            p95PacketLabel={proofCopy.p95PacketLatency}
            p95DeltaLabel={proofCopy.p95LatencyDelta}
          />
        )}
      </div>
    </div>
  );
}

function CorrectnessPanel({
  visible,
  rawLabel,
  packetLabel,
  packetOnlyWinsLabel,
  rawOnlyWinsLabel,
  bothWrongLabel
}: {
  visible: boolean;
  rawLabel: string;
  packetLabel: string;
  packetOnlyWinsLabel: string;
  rawOnlyWinsLabel: string;
  bothWrongLabel: string;
}) {
  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(280px,0.74fr)]">
      <div className="surface-strong p-6 sm:p-8">
        <div className="grid gap-6 md:grid-cols-2">
          <AnimatedMetricCard
            label={rawLabel}
            value={runtimeEvidenceSnapshot.rawAccuracy}
            decimals={4}
            visible={visible}
          />
          <AnimatedMetricCard
            label={packetLabel}
            value={runtimeEvidenceSnapshot.packetAccuracy}
            decimals={4}
            visible={visible}
          />
        </div>

        <div className="mt-8 grid gap-4">
          <BarRow
            label={rawLabel}
            value={runtimeEvidenceSnapshot.rawAccuracy}
            maxValue={1}
            decimals={4}
            visible={visible}
            durationMs={1200}
          />
          <BarRow
            label={packetLabel}
            value={runtimeEvidenceSnapshot.packetAccuracy}
            maxValue={1}
            decimals={4}
            visible={visible}
            accent
            durationMs={1200}
          />
        </div>
      </div>

      <div className="grid gap-4">
        <AnimatedSideStat
          label={packetOnlyWinsLabel}
          value={runtimeEvidenceSnapshot.packetCorrectRawWrong}
          visible={visible}
        />
        <AnimatedSideStat
          label={rawOnlyWinsLabel}
          value={runtimeEvidenceSnapshot.rawCorrectPacketWrong}
          visible={visible}
        />
        <AnimatedSideStat
          label={bothWrongLabel}
          value={runtimeEvidenceSnapshot.bothWrong}
          visible={visible}
        />
      </div>
    </div>
  );
}

function TokensPanel({
  visible,
  inputReductionLabel,
  rawInputLabel,
  packetInputLabel,
  rawOutputLabel,
  packetOutputLabel
}: {
  visible: boolean;
  inputReductionLabel: string;
  rawInputLabel: string;
  packetInputLabel: string;
  rawOutputLabel: string;
  packetOutputLabel: string;
}) {
  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(280px,0.74fr)]">
      <div className="surface-strong p-6 sm:p-8">
        <div className="text-[11px] uppercase tracking-[0.22em] text-accent/72">Average actual input tokens</div>
        <div className="mt-5 grid gap-4">
          <BarRow
            label={rawInputLabel}
            value={runtimeEvidenceSnapshot.inputTokens.raw}
            maxValue={runtimeEvidenceSnapshot.inputTokens.raw}
            decimals={4}
            visible={visible}
            durationMs={1200}
          />
          <BarRow
            label={packetInputLabel}
            value={runtimeEvidenceSnapshot.inputTokens.packet}
            maxValue={runtimeEvidenceSnapshot.inputTokens.raw}
            decimals={4}
            visible={visible}
            accent
            durationMs={1200}
          />
        </div>

        <div className="mt-8 text-[11px] uppercase tracking-[0.22em] text-accent/72">Average actual output tokens</div>
        <div className="mt-5 grid gap-4">
          <BarRow
            label={rawOutputLabel}
            value={runtimeEvidenceSnapshot.outputTokens.raw}
            maxValue={runtimeEvidenceSnapshot.outputTokens.raw}
            decimals={4}
            visible={visible}
            durationMs={1200}
          />
          <BarRow
            label={packetOutputLabel}
            value={runtimeEvidenceSnapshot.outputTokens.packet}
            maxValue={runtimeEvidenceSnapshot.outputTokens.raw}
            decimals={4}
            visible={visible}
            accent
            durationMs={1200}
          />
        </div>
      </div>

      <div className="grid gap-4">
        <AnimatedSideStat
          label={inputReductionLabel}
          value={runtimeEvidenceSnapshot.inputReductionPercent}
          decimals={2}
          suffix="%"
          visible={visible}
          accent
        />
        <AnimatedSideStat
          label={rawInputLabel}
          value={runtimeEvidenceSnapshot.inputTokens.raw}
          decimals={4}
          visible={visible}
        />
        <AnimatedSideStat
          label={packetInputLabel}
          value={runtimeEvidenceSnapshot.inputTokens.packet}
          decimals={4}
          visible={visible}
          accent
        />
      </div>
    </div>
  );
}

function LatencyPanel({
  visible,
  averageRawLabel,
  averagePacketLabel,
  averageDeltaLabel,
  medianRawLabel,
  medianPacketLabel,
  medianDeltaLabel,
  p95RawLabel,
  p95PacketLabel,
  p95DeltaLabel
}: {
  visible: boolean;
  averageRawLabel: string;
  averagePacketLabel: string;
  averageDeltaLabel: string;
  medianRawLabel: string;
  medianPacketLabel: string;
  medianDeltaLabel: string;
  p95RawLabel: string;
  p95PacketLabel: string;
  p95DeltaLabel: string;
}) {
  return (
    <div className="grid gap-4">
      <LatencyGroup
        title="average actual latency"
        rawLabel={averageRawLabel}
        packetLabel={averagePacketLabel}
        deltaLabel={averageDeltaLabel}
        rawValue={runtimeEvidenceSnapshot.latencyAverageMs.raw}
        packetValue={runtimeEvidenceSnapshot.latencyAverageMs.packet}
        deltaValue={runtimeEvidenceSnapshot.latencyAverageMs.delta}
        visible={visible}
        rawDecimals={2}
        packetDecimals={3}
        deltaDecimals={3}
      />
      <LatencyGroup
        title="median actual latency"
        rawLabel={medianRawLabel}
        packetLabel={medianPacketLabel}
        deltaLabel={medianDeltaLabel}
        rawValue={runtimeEvidenceSnapshot.latencyMedianMs.raw}
        packetValue={runtimeEvidenceSnapshot.latencyMedianMs.packet}
        deltaValue={runtimeEvidenceSnapshot.latencyMedianMs.delta}
        visible={visible}
        rawDecimals={3}
        packetDecimals={3}
        deltaDecimals={3}
      />
      <LatencyGroup
        title="p95 actual latency"
        rawLabel={p95RawLabel}
        packetLabel={p95PacketLabel}
        deltaLabel={p95DeltaLabel}
        rawValue={runtimeEvidenceSnapshot.latencyP95Ms.raw}
        packetValue={runtimeEvidenceSnapshot.latencyP95Ms.packet}
        deltaValue={runtimeEvidenceSnapshot.latencyP95Ms.delta}
        visible={visible}
        rawDecimals={3}
        packetDecimals={2}
        deltaDecimals={3}
      />
    </div>
  );
}

function LatencyGroup({
  title,
  rawLabel,
  packetLabel,
  deltaLabel,
  rawValue,
  packetValue,
  deltaValue,
  visible,
  rawDecimals,
  packetDecimals,
  deltaDecimals
}: {
  title: string;
  rawLabel: string;
  packetLabel: string;
  deltaLabel: string;
  rawValue: number;
  packetValue: number;
  deltaValue: number;
  visible: boolean;
  rawDecimals: number;
  packetDecimals: number;
  deltaDecimals: number;
}) {
  const maxValue = Math.max(rawValue, packetValue);

  return (
    <div className="surface-strong p-6 sm:p-7">
      <div className="text-[11px] uppercase tracking-[0.22em] text-accent/72">{title}</div>
      <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(220px,0.4fr)]">
        <div className="grid gap-4">
          <BarRow
            label={rawLabel}
            value={rawValue}
            maxValue={maxValue}
            decimals={rawDecimals}
            visible={visible}
            suffix=" ms"
            durationMs={1200}
          />
          <BarRow
            label={packetLabel}
            value={packetValue}
            maxValue={maxValue}
            decimals={packetDecimals}
            visible={visible}
            suffix=" ms"
            accent
            durationMs={1200}
          />
        </div>
        <div className="rounded-[22px] border border-white/10 bg-white/[0.03] px-5 py-4">
          <div className="text-[10px] uppercase tracking-[0.22em] text-white/34">{deltaLabel}</div>
          <div className="mt-3 text-[1.7rem] font-semibold tracking-[-0.05em] text-accent">
            <AnimatedNumber
              value={deltaValue}
              decimals={deltaDecimals}
              visible={visible}
              suffix=" ms"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function AnimatedMetricCard({
  label,
  value,
  decimals,
  visible,
  animate = true
}: {
  label: string;
  value: number;
  decimals: number;
  visible: boolean;
  animate?: boolean;
}) {
  return (
    <div className="rounded-[24px] border border-white/10 bg-white/[0.03] px-5 py-5">
      <div className="text-[10px] uppercase tracking-[0.22em] text-white/34">{label}</div>
      <div className="mt-3 text-[2.1rem] font-semibold tracking-[-0.05em] text-white">
        <AnimatedNumber value={value} decimals={decimals} visible={visible} animate={animate} />
      </div>
    </div>
  );
}

function AnimatedSideStat({
  label,
  value,
  visible,
  decimals = 0,
  suffix = "",
  accent = false,
  animate = true
}: {
  label: string;
  value: number;
  visible: boolean;
  decimals?: number;
  suffix?: string;
  accent?: boolean;
  animate?: boolean;
}) {
  return (
    <div className="surface h-full px-5 py-5">
      <div className="text-[10px] uppercase tracking-[0.22em] text-white/34">{label}</div>
      <div className={cx("mt-3 text-[2rem] font-semibold tracking-[-0.05em]", accent ? "text-accent" : "text-white")}>
        <AnimatedNumber
          value={value}
          decimals={decimals}
          visible={visible}
          animate={animate}
          suffix={suffix}
        />
      </div>
    </div>
  );
}

function BarRow({
  label,
  value,
  maxValue,
  decimals,
  visible,
  suffix = "",
  accent = false,
  durationMs = 1000,
  animate = true
}: {
  label: string;
  value: number;
  maxValue: number;
  decimals: number;
  visible: boolean;
  suffix?: string;
  accent?: boolean;
  durationMs?: number;
  animate?: boolean;
}) {
  const prefersReducedMotion = usePrefersReducedMotion();
  const width = maxValue === 0 ? 0 : (value / maxValue) * 100;

  return (
    <div className="rounded-[22px] border border-white/10 bg-white/[0.03] px-5 py-4">
      <div className="flex items-center justify-between gap-4">
        <span className="text-sm text-white/68">{label}</span>
        <span className={cx("text-sm font-semibold", accent ? "text-accent" : "text-white")}>
          <AnimatedNumber
            value={value}
            decimals={decimals}
            visible={visible}
            animate={animate}
            suffix={suffix}
          />
        </span>
      </div>
      <div className="mt-4 h-2.5 overflow-hidden rounded-full bg-white/[0.06]">
        <div
          className={cx(
            "h-full rounded-full transition-[width] ease-out",
            accent ? "bg-accent" : "bg-white/65"
          )}
          style={{
            width: prefersReducedMotion || visible ? `${width}%` : "0%",
            transitionDuration: `${prefersReducedMotion || !animate ? 10 : durationMs}ms`
          }}
        />
      </div>
    </div>
  );
}

function AnimatedNumber({
  value,
  decimals,
  visible,
  animate = true,
  suffix = ""
}: {
  value: number;
  decimals: number;
  visible: boolean;
  animate?: boolean;
  suffix?: string;
}) {
  const [displayValue, setDisplayValue] = useState(0);
  const prefersReducedMotion = usePrefersReducedMotion();
  const resolvedValue = visible && (prefersReducedMotion || !animate) ? value : displayValue;

  useEffect(() => {
    if (!visible) {
      return;
    }

    if (prefersReducedMotion || !animate) {
      setDisplayValue(value);
      return;
    }

    let frame = 0;
    let startTime = 0;
    const duration = 1100;

    const tick = (time: number) => {
      if (!startTime) {
        startTime = time;
      }

      const progress = Math.min((time - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(value * eased);

      if (progress < 1) {
        frame = window.requestAnimationFrame(tick);
      }
    };

    frame = window.requestAnimationFrame(tick);

    return () => {
      window.cancelAnimationFrame(frame);
    };
  }, [animate, prefersReducedMotion, value, visible]);

  return (
    <>
      {formatNumber(resolvedValue, decimals)}
      {suffix}
    </>
  );
}

function Reveal({
  children,
  className,
  delay = 0,
  motion = "subtle"
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
  motion?: MotionLevel;
}) {
  const [ref, visible] = useInViewOnce<HTMLDivElement>(0.18);
  const prefersReducedMotion = usePrefersReducedMotion();
  const config = motionConfig[motion];
  const style = {
    transitionDelay: `${prefersReducedMotion ? 0 : delay}ms`,
    transitionDuration: `${prefersReducedMotion ? 10 : config.duration}ms`,
    transform:
      visible || prefersReducedMotion ? "translateY(0px)" : `translateY(${config.distance}px)`
  } as CSSProperties;

  return (
    <div
      ref={ref}
      style={style}
      className={cx(
        "transition-[opacity,transform] ease-out",
        visible || prefersReducedMotion ? "opacity-100" : "opacity-0",
        className
      )}
    >
      {children}
    </div>
  );
}

function useInViewOnce<T extends HTMLElement>(threshold = 0.2) {
  const ref = useRef<T | null>(null);
  const [visible, setVisible] = useState(false);
  const prefersReducedMotion = usePrefersReducedMotion();

  useEffect(() => {
    if (prefersReducedMotion) {
      setVisible(true);
      return;
    }

    if (!ref.current || visible) {
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold }
    );

    observer.observe(ref.current);

    return () => {
      observer.disconnect();
    };
  }, [prefersReducedMotion, threshold, visible]);

  return [ref, visible] as const;
}

function usePrefersReducedMotion() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setPrefersReducedMotion(mediaQuery.matches);

    update();
    mediaQuery.addEventListener("change", update);

    return () => {
      mediaQuery.removeEventListener("change", update);
    };
  }, []);

  return prefersReducedMotion;
}

function HeroBackdrop({ path }: { path: string }) {
  return (
    <div className="hero-backdrop" aria-hidden="true">
      <Image
        src={path}
        alt=""
        fill
        priority
        sizes="100vw"
        className="hero-backdrop__image"
      />
      <div className="hero-backdrop__veil" />
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="grid gap-2">
      <span className="text-sm font-medium text-white/80">{label}</span>
      {children}
    </label>
  );
}

function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className="min-h-12 rounded-[18px] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white placeholder:text-white/34 disabled:cursor-not-allowed disabled:opacity-60"
    />
  );
}

function TextArea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      className="min-h-[148px] rounded-[18px] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white placeholder:text-white/34 disabled:cursor-not-allowed disabled:opacity-60"
    />
  );
}

function SectionGlow() {
  return (
    <>
      <div className="pointer-events-none absolute left-[-10rem] top-8 h-[20rem] w-[20rem] rounded-full bg-accent/[0.09] blur-3xl" />
      <div className="pointer-events-none absolute right-[-8rem] top-20 h-[18rem] w-[18rem] rounded-full bg-accent-strong/[0.08] blur-3xl" />
    </>
  );
}

function BackgroundGlow() {
  return (
    <>
      <div className="pointer-events-none absolute left-[-12rem] top-12 h-[28rem] w-[28rem] rounded-full bg-accent/[0.1] blur-3xl" />
      <div className="pointer-events-none absolute right-[-10rem] top-[32rem] h-[24rem] w-[24rem] rounded-full bg-accent-strong/[0.08] blur-3xl" />
    </>
  );
}

function ArrowIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 16 16"
      className="h-4 w-4"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M4 12L12 4M12 4H6M12 4V10"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function buttonStyles(variant: "primary" | "secondary", className = "") {
  const styles =
    variant === "primary"
      ? "border border-accent/25 bg-accent text-ink shadow-[0_12px_30px_rgba(79,140,255,0.24)] hover:bg-[#9fc2ff]"
      : "border border-white/10 bg-white/[0.03] text-white hover:border-accent/20 hover:bg-accent/[0.08]";

  return cx(
    "group inline-flex min-h-12 items-center justify-center gap-2 rounded-full px-6 py-3 text-sm font-medium transition duration-300 hover:-translate-y-0.5",
    styles,
    className
  );
}

function buildLocalizedHref(path: string, locale: Locale, hash?: string) {
  const normalizedPath = path || "/";
  const url = `${normalizedPath}?lang=${locale}`;
  return hash ? `${url}#${hash}` : url;
}

function formatNumber(value: number, decimals: number) {
  if (decimals === 0) {
    return Math.round(value).toString();
  }

  return value.toFixed(decimals);
}

function formatFixed(value: number, decimals: number) {
  return value.toFixed(decimals);
}

function formatPercent(value: number, decimals: number) {
  return `${value.toFixed(decimals)}%`;
}

function formatFraction(numerator: number, denominator: number) {
  return `${numerator} / ${denominator}`;
}

function formatMs(value: number, decimals: number) {
  return `${value.toFixed(decimals)} ms`;
}

const motionConfig: Record<MotionLevel, { duration: number; distance: number }> = {
  minimal: { duration: 480, distance: 6 },
  subtle: { duration: 560, distance: 10 },
  moderate: { duration: 620, distance: 14 },
  strong: { duration: 680, distance: 18 }
};

function cx(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

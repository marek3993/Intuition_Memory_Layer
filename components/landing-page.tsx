"use client";

import Image from "next/image";
import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Locale, PUBLIC_BRAND_NAME, siteContent } from "@/data/site-content";

const creatorLinkedInUrl = "https://www.linkedin.com/in/marek-benda-imlayer/";
const localeLabels: Record<Locale, string> = { en: "EN", sk: "SK" };
const emptyForm = {
  name: "",
  email: "",
  company: "",
  message: ""
};
const formStatusMessages: Record<
  Locale,
  {
    submitLoadingLabel: string;
    success: string;
    validationError: string;
    error: string;
  }
> = {
  en: {
    submitLoadingLabel: "Sending request...",
    success: "Your pilot request was sent. Expect a reply by email.",
    validationError: "Please complete the required fields with a valid work email.",
    error: "The form could not be sent. Please try again in a moment."
  },
  sk: {
    submitLoadingLabel: "Odosielam žiadosť...",
    success: "Pilotná žiadosť bola odoslaná. Odpoveď príde e-mailom.",
    validationError: "Vyplňte povinné polia a zadajte platný pracovný e-mail.",
    error: "Formulár sa nepodarilo odoslať. Skúste to ešte raz o chvíľu."
  }
};
const creatorAttribution: Record<
  Locale,
  { footer: string; linkLabel: string }
> = {
  en: {
    footer: "Created by Marek Benda",
    linkLabel: "LinkedIn"
  },
  sk: {
    footer: "Vytvoril Marek Benda",
    linkLabel: "LinkedIn"
  }
};

export function LandingPage() {
  const [locale, setLocale] = useState<Locale>("en");
  const [expandedAsset, setExpandedAsset] = useState<{
    path: string;
    title: string;
  } | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [submitState, setSubmitState] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [submitMessage, setSubmitMessage] = useState("");

  const content = siteContent[locale];

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  useEffect(() => {
    if (!expandedAsset) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setExpandedAsset(null);
      }
    };

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [expandedAsset]);

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

    const messages = formStatusMessages[locale];

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

  const roadmapExpandLabel =
    locale === "sk" ? "Otvoriť roadmap obrázok vo väčšom zobrazení" : "Open roadmap image in larger view";
  const roadmapDialogLabel =
    locale === "sk" ? "Zväčšený roadmap obrázok" : "Enlarged roadmap image";
  const closeLightboxLabel = locale === "sk" ? "Zavrieť zväčšený obrázok" : "Close enlarged image";

  return (
    <main lang={locale} className="relative overflow-x-clip bg-ink text-white">
      <BackgroundGlow />

      <header className="sticky top-0 z-50 border-b border-white/10 bg-[rgba(5,8,18,0.78)] backdrop-blur-2xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-2.5 sm:px-6">
          <a href="#top" className="flex min-w-0 items-center gap-3">
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
                {content.brand.expandedName} - {content.brand.subtitle}
              </div>
            </div>
          </a>

          <nav className="hidden items-center gap-2 lg:flex">
            {content.nav.items.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="rounded-full px-4 py-2 text-sm text-white/62 transition duration-300 hover:bg-white/[0.04] hover:text-white"
              >
                {item.label}
              </a>
            ))}
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
                    onClick={() => setLocale(option)}
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

            <a href="#contact" className={buttonStyles("primary", "hidden sm:inline-flex")}>
              {content.nav.cta}
              <ArrowIcon />
            </a>
          </div>
        </div>
      </header>

      <section
        id="top"
        className="tone-deep-navy hero-section relative overflow-hidden px-5 pb-16 pt-12 sm:px-6 sm:pb-20 sm:pt-16 lg:pb-24 lg:pt-20"
      >
        <HeroBackdrop path={content.hero.asset.path} />
        <SectionGlow />
        <div className="mx-auto max-w-7xl">
          <div className="hero-content-shell">
            <div className="max-w-[42rem]">
              <span className="eyebrow">{content.hero.eyebrow}</span>
              <h1 className="balanced-heading mt-6 max-w-[13ch] text-[3.2rem] font-semibold leading-[0.9] tracking-[-0.065em] text-white sm:max-w-none sm:text-[4.45rem] lg:text-[5.2rem] xl:text-[5.9rem]">
                {content.hero.headline}
              </h1>
              <p className="pretty-copy mt-7 max-w-[35rem] text-[1.08rem] leading-8 text-white/78 sm:text-[1.18rem]">
                {content.hero.subheadline}
              </p>
              <p className="pretty-copy mt-3 max-w-[39rem] text-sm leading-7 text-white/52 sm:text-[0.96rem]">
                {content.hero.supportingLine}
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:mt-9 sm:flex-row">
                <a href="#contact" className={buttonStyles("primary")}>
                  {content.hero.primaryCta}
                  <ArrowIcon />
                </a>
                <a href={content.hero.secondaryHref} className={buttonStyles("secondary")}>
                  {content.hero.secondaryCta}
                  <ArrowIcon />
                </a>
              </div>
            </div>
          </div>

          <div className="relative z-10 mt-12 max-w-7xl lg:mt-14">
            <div className="mb-3 text-[10px] font-medium uppercase tracking-[0.28em] text-white/20">
              {content.hero.proofLabel}
            </div>
            <div className="grid gap-2.5 md:grid-cols-2 xl:grid-cols-4">
              {content.hero.proofStrip.map((item, index) => (
                <HeroProofCard key={item} index={index + 1} body={item} />
              ))}
            </div>
          </div>
        </div>
      </section>

      <Section id="what-imlayer-is" tone="tone-charcoal-blue">
        <div className="grid gap-10 lg:grid-cols-[minmax(0,0.92fr)_minmax(340px,0.78fr)] lg:items-start lg:gap-12">
          <div>
            <Intro {...content.technology} />
            <div className="section-grid mt-10">
              {content.technology.cards.map((card) => (
                <Card key={card.title} {...card} />
              ))}
            </div>
          </div>
          <AssetCard asset={content.technology.asset} variant="layer" />
        </div>
      </Section>

      <Section id="why-now" tone="tone-charcoal-blue-soft">
        <Intro {...content.whyNow} />
        <div className="section-grid mt-10">
          {content.whyNow.cards.map((card) => (
            <Card key={card.title} {...card} />
          ))}
        </div>
      </Section>

      <Section id="evidence" tone="tone-deep-navy">
        <Intro {...content.evidence} />
        <div className="mt-10 grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(300px,0.74fr)]">
          <div className="surface-strong p-6 sm:p-8">
            <div className="rounded-[26px] border border-accent/16 bg-accent/[0.08] p-5 sm:p-6">
              <p className="pretty-copy text-base leading-7 text-white/82">
                {content.evidence.highlight}
              </p>
            </div>
            <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {content.evidence.metrics.map((metric) => (
                <Metric key={metric.label} label={metric.label} value={metric.value} />
              ))}
            </div>
          </div>

          <div className="surface p-6 sm:p-8">
            <div className="text-[11px] font-medium uppercase tracking-[0.24em] text-accent/72">
              {content.evidence.noteLabel}
            </div>
            <p className="pretty-copy mt-3 text-sm leading-7 text-white/66">
              {content.evidence.note}
            </p>
          </div>
        </div>
        <div className="section-grid mt-8">
          {content.evidence.cards.map((card) => (
            <Card key={card.title} {...card} />
          ))}
        </div>
      </Section>

      <Section id="first-product" tone="tone-graphite">
        <div className="grid gap-10 lg:grid-cols-[minmax(0,0.92fr)_minmax(340px,0.78fr)] lg:items-start lg:gap-12">
          <Intro {...content.firstProduct} />
          <AssetCard
            asset={content.firstProduct.asset}
            variant="workflow"
            onExpand={setExpandedAsset}
            expandLabel={roadmapExpandLabel}
          />
        </div>

        <div className="section-grid mt-10">
          {content.firstProduct.cards.map((card) => (
            <Card key={card.title} {...card} />
          ))}
        </div>

        <div className="mt-12 grid gap-6 xl:grid-cols-[minmax(0,1.05fr)_minmax(300px,0.72fr)]">
          <div className="surface-strong p-6 sm:p-8">
            <div className="text-[11px] font-medium uppercase tracking-[0.24em] text-accent/72">
              {content.firstProduct.workflowLabel}
            </div>
            <h3 className="balanced-heading mt-3 text-2xl font-semibold tracking-[-0.04em] text-white">
              {content.firstProduct.workflowTitle}
            </h3>
            <div className="mt-8 grid gap-4">
              {content.firstProduct.workflow.map((step, index) => (
                <div key={step.title} className="rounded-[24px] border border-white/10 bg-white/[0.04] p-5">
                  <div className="flex items-center gap-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-full border border-accent/18 bg-accent/10 text-xs font-semibold tracking-[0.12em] text-accent">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <h4 className="text-base font-semibold text-white">{step.title}</h4>
                  </div>
                  <p className="pretty-copy mt-3 text-sm leading-7 text-white/60">
                    {step.body}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div className="surface p-6 sm:p-8">
            <div className="text-[11px] font-medium uppercase tracking-[0.24em] text-accent/72">
              {content.firstProduct.builtLabel}
            </div>
            <h3 className="balanced-heading mt-3 text-2xl font-semibold tracking-[-0.04em] text-white">
              {content.firstProduct.builtTitle}
            </h3>
            <div className="mt-6 grid gap-3">
              {content.firstProduct.built.map((item) => (
                <div key={item} className="rounded-[22px] border border-white/10 bg-white/[0.03] px-4 py-4 text-sm leading-7 text-white/64">
                  <div className="flex items-start gap-3">
                    <span className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full bg-accent shadow-[0_0_18px_rgba(137,180,255,0.38)]" />
                    <span className="pretty-copy">{item}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-8 rounded-[24px] border border-accent/16 bg-accent/[0.07] p-5">
              <div className="text-[11px] font-medium uppercase tracking-[0.24em] text-accent/72">
                {content.firstProduct.proofLabel}
              </div>
              <h4 className="balanced-heading mt-3 text-lg font-semibold tracking-[-0.035em] text-white">
                {content.firstProduct.proofTitle}
              </h4>
              <div className="mt-5 grid gap-3">
                {content.firstProduct.proofItems.map((item) => (
                  <div key={item} className="flex items-start gap-3">
                    <span className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full bg-accent shadow-[0_0_18px_rgba(137,180,255,0.34)]" />
                    <p className="pretty-copy text-sm leading-7 text-white/70">{item}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </Section>

      <Section id="pilot" tone="tone-steel-blue">
        <div className="grid gap-10 xl:grid-cols-[minmax(0,0.96fr)_minmax(320px,0.84fr)] xl:items-start">
          <div>
            <Intro {...content.firstPilot} />
            <div className="section-grid mt-10">
              {content.firstPilot.cards.map((card) => (
                <Card key={card.title} {...card} />
              ))}
            </div>
          </div>

          <PilotAssetPanel
            assetsLabel={content.firstPilot.assetsLabel}
            title={content.firstPilot.assetsTitle}
            body={content.firstPilot.assetsBody}
            assets={content.firstPilot.assets}
            openLabel={content.firstPilot.openLabel}
            requestLabel={content.firstPilot.requestLabel}
          />
        </div>
      </Section>

      <Section id="roadmap" tone="tone-charcoal-blue">
        <div className="grid gap-10 xl:grid-cols-[minmax(0,0.94fr)_minmax(360px,1.02fr)] xl:items-start">
          <div>
            <Intro {...content.roadmap} />
            <div className="mt-10 grid gap-4">
              {content.roadmap.steps.map((step) => (
                <div key={step.stage} className="surface flex gap-4 p-5 sm:p-6">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-accent/18 bg-accent/10 text-sm font-semibold tracking-[0.12em] text-accent">
                    {step.stage}
                  </div>
                  <div>
                    <h3 className="balanced-heading text-lg font-semibold tracking-[-0.035em] text-white">
                      {step.title}
                    </h3>
                    <p className="pretty-copy mt-3 text-sm leading-7 text-white/62">
                      {step.body}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <AssetCard
            asset={content.roadmap.asset}
            variant="sequence"
            onExpand={setExpandedAsset}
            expandLabel={roadmapExpandLabel}
          />
        </div>
      </Section>

      <Section id="contact" tone="tone-deep-navy">
        <div className="max-w-3xl">
          <Intro {...content.cta} />
          <p className="pretty-copy mt-6 max-w-2xl text-base leading-8 text-white/70">
            {content.cta.guidance}
          </p>
          <form className="mt-8 grid gap-4" onSubmit={handleSubmit}>
            <div className="grid gap-4 md:grid-cols-2">
              <Field label={content.cta.form.nameLabel}>
                <Input
                  value={form.name}
                  placeholder={content.cta.form.namePlaceholder}
                  onChange={(event) => handleFieldChange("name", event.target.value)}
                  disabled={submitState === "loading"}
                  required
                />
              </Field>
              <Field label={content.cta.form.emailLabel}>
                <Input
                  type="email"
                  value={form.email}
                  placeholder={content.cta.form.emailPlaceholder}
                  onChange={(event) => handleFieldChange("email", event.target.value)}
                  disabled={submitState === "loading"}
                  required
                />
              </Field>
            </div>
            <Field label={content.cta.form.companyLabel}>
              <Input
                value={form.company}
                placeholder={content.cta.form.companyPlaceholder}
                onChange={(event) => handleFieldChange("company", event.target.value)}
                disabled={submitState === "loading"}
              />
            </Field>
            <Field label={content.cta.form.messageLabel}>
              <TextArea
                value={form.message}
                placeholder={content.cta.form.messagePlaceholder}
                onChange={(event) => handleFieldChange("message", event.target.value)}
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
                  ? formStatusMessages[locale].submitLoadingLabel
                  : content.cta.form.submitLabel}
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
        </div>
      </Section>

      {expandedAsset ? (
        <ImageLightbox
          asset={expandedAsset}
          closeLabel={closeLightboxLabel}
          dialogLabel={roadmapDialogLabel}
          onClose={() => setExpandedAsset(null)}
        />
      ) : null}

      <footer className="border-t border-white/10 bg-[rgba(4,7,16,0.96)]">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-8 text-sm text-white/48 sm:px-6 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-col gap-2">
            <span>{PUBLIC_BRAND_NAME}</span>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-white/34">
              <span>{creatorAttribution[locale].footer}</span>
              <a
                href={creatorLinkedInUrl}
                target="_blank"
                rel="noreferrer"
                className="text-white/42 underline decoration-white/12 underline-offset-4 transition duration-300 hover:text-accent hover:decoration-accent/45"
              >
                {creatorAttribution[locale].linkLabel}
              </a>
            </div>
          </div>
          <span className="pretty-copy max-w-2xl text-left md:text-right">{content.footer.oneLine}</span>
        </div>
      </footer>
    </main>
  );
}

function Section({
  id,
  tone,
  children
}: {
  id?: string;
  tone: string;
  children: ReactNode;
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
      <p className="pretty-copy mt-5 text-base leading-8 text-white/68 sm:text-[1.03rem]">
        {body}
      </p>
    </div>
  );
}

function Card({ title, body }: { title: string; body: string }) {
  return (
    <article className="surface h-full p-6 sm:p-7">
      <h3 className="balanced-heading text-xl font-semibold tracking-[-0.04em] text-white">
        {title}
      </h3>
      <p className="pretty-copy mt-3 text-sm leading-7 text-white/62">{body}</p>
    </article>
  );
}

function PilotAssetPanel({
  assetsLabel,
  title,
  body,
  assets,
  openLabel,
  requestLabel
}: {
  assetsLabel: string;
  title: string;
  body: string;
  assets: Array<{
    label: string;
    title: string;
    body: string;
    access: "public" | "request";
    href?: string;
  }>;
  openLabel: string;
  requestLabel: string;
}) {
  return (
    <div className="surface-strong p-6 sm:p-8">
      <div className="text-[11px] font-medium uppercase tracking-[0.24em] text-accent/72">
        {assetsLabel}
      </div>
      <h3 className="balanced-heading mt-3 text-2xl font-semibold tracking-[-0.04em] text-white">
        {title}
      </h3>
      <p className="pretty-copy mt-3 text-sm leading-7 text-white/64">{body}</p>
      <div className="mt-7 grid gap-3">
        {assets.map((asset) => (
          <PilotAssetRow
            key={asset.title}
            asset={asset}
            openLabel={openLabel}
            requestLabel={requestLabel}
          />
        ))}
      </div>
    </div>
  );
}

function PilotAssetRow({
  asset,
  openLabel,
  requestLabel
}: {
  asset: {
    label: string;
    title: string;
    body: string;
    access: "public" | "request";
    href?: string;
  };
  openLabel: string;
  requestLabel: string;
}) {
  const actionHref = asset.access === "public" && asset.href ? asset.href : "#contact";
  const actionLabel = asset.access === "public" ? openLabel : requestLabel;

  return (
    <article className="rounded-[24px] border border-white/10 bg-white/[0.03] p-4 sm:p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="text-[10px] font-medium uppercase tracking-[0.24em] text-accent/72">
            {asset.label}
          </div>
          <h4 className="balanced-heading mt-2 text-base font-semibold text-white">
            {asset.title}
          </h4>
          <p className="pretty-copy mt-2 text-sm leading-7 text-white/60">{asset.body}</p>
        </div>

        <div className="flex shrink-0 items-start sm:items-end">
          <a href={actionHref} className={buttonStyles("secondary", "min-w-[9.5rem]")}>
            {actionLabel}
            <ArrowIcon />
          </a>
        </div>
      </div>
    </article>
  );
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

function HeroProofCard({ index, body }: { index: number; body: string }) {
  return (
    <div className="hero-proof-card">
      <div className="hero-proof-card__index">{String(index).padStart(2, "0")}</div>
      <p className="pretty-copy mt-1.5 text-sm leading-6 text-white/54">{body}</p>
    </div>
  );
}

function AssetCard({
  asset,
  variant,
  onExpand,
  expandLabel
}: {
  asset: { label: string; title: string; body: string; path: string };
  variant: "layer" | "workflow" | "sequence";
  onExpand?: (asset: { path: string; title: string }) => void;
  expandLabel?: string;
}) {
  return (
    <div className={assetCardClass(variant)}>
      <span className="text-[11px] uppercase tracking-[0.22em] text-white/42">
        {asset.label}
      </span>
      <div className={cx("asset-visual", assetVisualSpacing(variant), `asset-visual--${variant}`)}>
        {onExpand ? (
          <button
            type="button"
            className="asset-visual__button"
            aria-haspopup="dialog"
            aria-label={expandLabel ?? asset.title}
            onClick={() => onExpand({ path: asset.path, title: asset.title })}
          >
            <Image
              src={asset.path}
              alt={asset.title}
              width={1536}
              height={1024}
              sizes={assetSizes(variant)}
              className={cx("asset-visual__image", assetImageClass(variant))}
            />
          </button>
        ) : (
          <Image
            src={asset.path}
            alt={asset.title}
            width={1536}
            height={1024}
            sizes={assetSizes(variant)}
            className={cx("asset-visual__image", assetImageClass(variant))}
          />
        )}
      </div>
      <div className="mt-5 max-w-sm">
        <div className="text-[11px] uppercase tracking-[0.22em] text-white/42">
          {asset.title}
        </div>
        <p className="pretty-copy mt-3 text-sm leading-7 text-white/62">{asset.body}</p>
      </div>
    </div>
  );
}

function ImageLightbox({
  asset,
  closeLabel,
  dialogLabel,
  onClose
}: {
  asset: { path: string; title: string };
  closeLabel: string;
  dialogLabel: string;
  onClose: () => void;
}) {
  return (
    <div
      className="image-lightbox"
      role="dialog"
      aria-modal="true"
      aria-label={dialogLabel}
      onClick={onClose}
    >
      <div className="image-lightbox__panel" onClick={(event) => event.stopPropagation()}>
        <button
          type="button"
          className="image-lightbox__close"
          aria-label={closeLabel}
          onClick={onClose}
          autoFocus
        >
          <span aria-hidden="true">&times;</span>
        </button>
        <div className="image-lightbox__frame">
          <Image
            src={asset.path}
            alt={asset.title}
            width={1536}
            height={1024}
            sizes="100vw"
            className="image-lightbox__image"
          />
        </div>
      </div>
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

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[22px] border border-white/10 bg-white/[0.04] p-5">
      <div className="text-[11px] uppercase tracking-[0.22em] text-white/40">{label}</div>
      <div className="mt-3 text-[2rem] font-semibold tracking-[-0.05em] text-white">
        {value}
      </div>
    </div>
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

function assetImageClass(variant: "layer" | "workflow" | "sequence") {
  if (variant === "sequence") {
    return "object-contain object-center scale-[1.04]";
  }

  if (variant === "workflow") {
    return "object-contain object-center scale-[1]";
  }

  return "object-contain object-center scale-[1.04]";
}

function assetCardClass(variant: "layer" | "workflow" | "sequence") {
  return cx(
    "surface relative overflow-hidden",
    variant === "sequence" ? "p-4 sm:p-5" : "p-5 sm:p-6"
  );
}

function assetVisualSpacing(variant: "layer" | "workflow" | "sequence") {
  return variant === "sequence" ? "mt-4" : "mt-5";
}

function assetSizes(variant: "layer" | "workflow" | "sequence") {
  if (variant === "sequence") {
    return "(max-width: 1279px) 100vw, 42vw";
  }

  return "(max-width: 1024px) 100vw, 34vw";
}

function cx(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}


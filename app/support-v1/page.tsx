import { LandingPage } from "@/components/landing-page";
import { resolveLocale } from "@/data/site-content";

type SearchParams = Promise<{ lang?: string | string[] } | undefined>;

export default async function SupportV1Page({
  searchParams
}: {
  searchParams?: SearchParams;
}) {
  const params = await searchParams;
  return <LandingPage page="support" initialLocale={resolveLocale(params?.lang)} />;
}

import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service",
  description:
    "The terms governing use of the African Intelligence Cloud (AIC) research and policy-intelligence platform.",
  alternates: { canonical: "/terms" },
};

const UPDATED = "24 July 2026";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="text-xl font-bold text-aic-dark">{title}</h2>
      <div className="space-y-3 text-sm leading-relaxed text-slate-600">{children}</div>
    </section>
  );
}

export default function TermsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <p className="section-label">Legal</p>
      <h1 className="mt-2 text-4xl font-bold text-aic-dark">Terms of Service</h1>
      <p className="mt-3 text-sm text-slate-400">Last updated: {UPDATED}</p>

      <div className="mt-10 space-y-10">
        <Section title="Acceptance of terms">
          <p>
            By accessing or using African Intelligence Cloud (&quot;AIC&quot;, the
            &quot;platform&quot;) at aic.hyrin.org, you agree to these Terms of Service. If you do not
            agree, please do not use the platform.
          </p>
        </Section>

        <Section title="The service">
          <p>
            AIC provides tools to discover, analyse, visualize, and interpret African development
            data — including macroeconomic indicators, household survey microdata, geospatial layers,
            and AI-assisted research features. Some features require a registered account.
          </p>
        </Section>

        <Section title="Accounts and eligibility">
          <p>
            You are responsible for maintaining the confidentiality of your account credentials and
            for all activity under your account. You agree to provide accurate registration
            information and to keep it current. New accounts may require review before activation.
          </p>
        </Section>

        <Section title="Acceptable use">
          <ul className="list-disc space-y-1 pl-5">
            <li>Do not upload data you are not licensed or authorized to use.</li>
            <li>Do not attempt to re-identify individuals in de-identified microdata.</li>
            <li>Do not disrupt, reverse-engineer, or attempt to gain unauthorized access to the platform.</li>
            <li>Do not use the platform for unlawful purposes or to infringe others&apos; rights.</li>
          </ul>
        </Section>

        <Section title="Your data and content">
          <p>
            You retain ownership of datasets you upload. You grant AIC a limited licence to store and
            process that content solely to provide the service to you. You are responsible for
            complying with the licences and data-protection obligations attached to any data you
            upload or analyse.
          </p>
        </Section>

        <Section title="Third-party and public data">
          <p>
            The platform incorporates public data from third-party providers (for example, the World
            Bank, WHO, FAO, DHS Program, HDX, and IPUMS). Such data remains subject to the terms and
            licences of its original providers, and is provided &quot;as is&quot; without warranty as
            to accuracy or completeness.
          </p>
        </Section>

        <Section title="Disclaimers and limitation of liability">
          <p>
            The platform and its analytical outputs are provided for research and informational
            purposes and are offered &quot;as is&quot; without warranties of any kind. Analytical
            results depend on the data and parameters you provide and should be independently
            verified before being relied upon for policy or operational decisions. To the maximum
            extent permitted by law, AIC is not liable for indirect or consequential losses arising
            from use of the platform.
          </p>
        </Section>

        <Section title="Changes and termination">
          <p>
            We may update these terms or modify features over time; material changes will be
            reflected by the &quot;last updated&quot; date above. We may suspend or terminate access
            for violations of these terms. You may stop using the platform at any time.
          </p>
        </Section>

        <Section title="Contact">
          <p>
            Questions about these terms? Email{" "}
            <a href="mailto:aluqman@hyrin.org" className="text-aic-green hover:underline">
              aluqman@hyrin.org
            </a>
            .
          </p>
        </Section>
      </div>
    </div>
  );
}

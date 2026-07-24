import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description:
    "How African Intelligence Cloud (AIC) collects, uses, protects, and retains data — including account information and uploaded microdata.",
  alternates: { canonical: "/privacy" },
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

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <p className="section-label">Legal</p>
      <h1 className="mt-2 text-4xl font-bold text-aic-dark">Privacy Policy</h1>
      <p className="mt-3 text-sm text-slate-400">Last updated: {UPDATED}</p>

      <div className="mt-10 space-y-10">
        <Section title="Overview">
          <p>
            African Intelligence Cloud (&quot;AIC&quot;, &quot;we&quot;, &quot;us&quot;) is a
            research and policy-intelligence platform for African development data. This policy
            explains what information we collect, how we use it, and the choices you have. It applies
            to the platform available at aic.hyrin.org.
          </p>
        </Section>

        <Section title="Information we collect">
          <p>
            <strong>Account information.</strong> When you register, we collect your name, email
            address, and an encrypted (hashed) password. We never store passwords in plain text.
          </p>
          <p>
            <strong>Uploaded datasets.</strong> If you upload household survey microdata or other
            files, we store them in private, access-controlled storage associated with your account.
            Uploaded microdata is not public and is not shared with other users unless you explicitly
            grant access.
          </p>
          <p>
            <strong>Usage data.</strong> We collect standard technical logs (such as request times
            and error diagnostics) to operate, secure, and improve the platform.
          </p>
        </Section>

        <Section title="How we use information">
          <ul className="list-disc space-y-1 pl-5">
            <li>To provide, maintain, and secure the platform and your account.</li>
            <li>To run the analyses you request on data you provide or select.</li>
            <li>To communicate with you about your account, support requests, and service updates.</li>
            <li>To detect, prevent, and address technical issues, abuse, and security incidents.</li>
          </ul>
          <p>We do not sell your personal information or your uploaded datasets.</p>
        </Section>

        <Section title="Public and third-party data">
          <p>
            The platform surfaces aggregated public data from sources such as the World Bank, WHO,
            FAO, DHS Program, HDX, and IPUMS. That data is governed by the licences of its original
            providers. Analyses of your privately uploaded microdata are performed within your
            account and are not added to any public dataset.
          </p>
        </Section>

        <Section title="Data retention and deletion">
          <p>
            We retain account information for as long as your account is active. You may request
            deletion of your account and associated uploaded datasets by emailing us. We will action
            verified deletion requests within a reasonable period, subject to legal and operational
            requirements.
          </p>
        </Section>

        <Section title="Security">
          <p>
            We use industry-standard measures — encrypted transport (HTTPS), hashed credentials,
            access-controlled storage, and cloud infrastructure security — to protect your data. No
            method of transmission or storage is completely secure, but we work to protect your
            information and to disclose material incidents promptly.
          </p>
        </Section>

        <Section title="Your rights">
          <p>
            Depending on your jurisdiction, you may have rights to access, correct, export, or delete
            your personal data, and to object to or restrict certain processing. To exercise these
            rights, contact us at the address below.
          </p>
        </Section>

        <Section title="Contact">
          <p>
            Questions about this policy or your data? Email{" "}
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

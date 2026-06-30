"use client";

interface Citation {
  doi: string | null;
  title: string | null;
  year: number | null;
}

interface Props {
  citations: Citation[];
}

export function CitationPanel({ citations }: Props) {
  if (citations.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <h3 className="text-sm font-semibold text-slate-700 mb-2">References</h3>
        <p className="text-sm text-slate-400">No citation data available.</p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-3">
      <h3 className="text-sm font-semibold text-slate-700">
        References ({citations.length})
      </h3>
      <ol className="space-y-2 list-decimal list-inside">
        {citations.map((c, i) => (
          <li key={i} className="text-sm text-slate-600 leading-snug">
            {c.title ? (
              <>
                <span className="font-medium">{c.title}</span>
                {c.year && <span className="text-slate-400 ml-1">({c.year})</span>}
                {c.doi && (
                  <a
                    href={`https://doi.org/${c.doi}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-2 text-xs text-green-700 hover:underline"
                  >
                    DOI
                  </a>
                )}
              </>
            ) : c.doi ? (
              <a
                href={`https://doi.org/${c.doi}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-green-700 hover:underline break-all"
              >
                {c.doi}
              </a>
            ) : (
              <span className="text-slate-400 italic">Unknown reference</span>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}

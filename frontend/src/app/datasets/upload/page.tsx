"use client";

import { useRef, useState, DragEvent, ChangeEvent } from "react";
import { useRouter } from "next/navigation";
import { uploadDataset } from "@/lib/api";

const ALLOWED_EXTENSIONS = ["csv", "xlsx", "xls", "json", "parquet"];
const MAX_MB = 50;

function getExtension(filename: string) {
  return filename.split(".").pop()?.toLowerCase() ?? "";
}

export default function UploadDatasetPage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [privacy, setPrivacy] = useState<"private" | "organization" | "public">("private");
  const [tags, setTags] = useState("");
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);

  function validateFile(f: File): string {
    const ext = getExtension(f.name);
    if (!ALLOWED_EXTENSIONS.includes(ext))
      return `File type .${ext} is not supported. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`;
    if (f.size > MAX_MB * 1_048_576)
      return `File exceeds ${MAX_MB} MB limit.`;
    return "";
  }

  function setCheckedFile(f: File) {
    const err = validateFile(f);
    if (err) { setError(err); setFile(null); return; }
    setError("");
    setFile(f);
    if (!name) setName(f.name.replace(/\.[^.]+$/, ""));
  }

  function onInputChange(e: ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) setCheckedFile(f);
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) setCheckedFile(f);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) { setError("Please select a file."); return; }
    if (!name.trim()) { setError("Dataset name is required."); return; }

    const fd = new FormData();
    fd.append("file", file);
    fd.append("name", name.trim());
    if (description.trim()) fd.append("description", description.trim());
    fd.append("privacy", privacy);
    if (tags.trim()) fd.append("tags", tags.trim());

    setUploading(true);
    setError("");
    try {
      const ds = await uploadDataset(fd);
      router.push(`/datasets/${ds.id}`);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
        "Upload failed. Please try again.";
      setError(msg);
      setUploading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Upload Dataset</h1>
        <p className="text-sm text-slate-500 mt-1">
          Supported formats: {ALLOWED_EXTENSIONS.join(", ")} — up to {MAX_MB} MB
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5 bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        {/* Drop zone */}
        <div
          role="button"
          tabIndex={0}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition ${
            dragging
              ? "border-green-500 bg-green-50"
              : file
              ? "border-green-400 bg-green-50"
              : "border-slate-300 hover:border-slate-400"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ALLOWED_EXTENSIONS.map((e) => `.${e}`).join(",")}
            className="hidden"
            onChange={onInputChange}
          />
          {file ? (
            <div className="space-y-1">
              <div className="text-green-700 font-medium">{file.name}</div>
              <div className="text-sm text-slate-500">
                {(file.size / 1_048_576).toFixed(2)} MB — click to change
              </div>
            </div>
          ) : (
            <div className="space-y-1">
              <div className="text-slate-600 font-medium">Drag & drop or click to select</div>
              <div className="text-sm text-slate-400">
                {ALLOWED_EXTENSIONS.join(", ")} up to {MAX_MB} MB
              </div>
            </div>
          )}
        </div>

        {/* Name */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Dataset name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Nigeria GDP 2024"
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            placeholder="Brief description of this dataset…"
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 resize-none"
          />
        </div>

        {/* Privacy */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Privacy</label>
          <select
            value={privacy}
            onChange={(e) => setPrivacy(e.target.value as typeof privacy)}
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            <option value="private">Private — only you</option>
            <option value="organization">Organization — your org members</option>
            <option value="public">Public — anyone</option>
          </select>
        </div>

        {/* Tags */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Tags <span className="text-slate-400 font-normal">(comma-separated)</span>
          </label>
          <input
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="e.g. economy, nigeria, gdp"
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div className="flex gap-3 pt-1">
          <button
            type="submit"
            disabled={uploading}
            className="flex-1 py-2.5 bg-green-700 text-white font-medium rounded-lg hover:bg-green-800 transition disabled:opacity-60 text-sm"
          >
            {uploading ? "Uploading…" : "Upload Dataset"}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="px-5 py-2.5 border border-slate-300 text-slate-600 font-medium rounded-lg hover:bg-slate-50 transition text-sm"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

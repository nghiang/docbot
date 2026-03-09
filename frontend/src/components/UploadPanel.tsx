import { useCallback, useRef, useState } from "react";
import { uploadFile } from "../api";
import type { UploadedFile } from "../types";

interface Props {
    onFileUploaded: (file: UploadedFile) => void;
}

export default function UploadPanel({ onFileUploaded }: Props) {
    const [dragging, setDragging] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const ALLOWED = [".pdf", ".docx"];

    const handleFiles = useCallback(
        async (files: FileList | null) => {
            if (!files || files.length === 0) return;
            const file = files[0];

            const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
            if (!ALLOWED.includes(ext)) {
                setError(`Unsupported file type "${ext}". Only PDF and DOCX allowed.`);
                return;
            }

            setError(null);
            setUploading(true);
            try {
                const res = await uploadFile(file);
                onFileUploaded({
                    fileName: res.file_name,
                    taskId: res.task_id,
                    status: "PENDING",
                });
            } catch (e: unknown) {
                setError(e instanceof Error ? e.message : "Upload failed");
            } finally {
                setUploading(false);
                if (inputRef.current) inputRef.current.value = "";
            }
        },
        [onFileUploaded]
    );

    const onDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault();
            setDragging(false);
            handleFiles(e.dataTransfer.files);
        },
        [handleFiles]
    );

    return (
        <div className="mb-6">
            <h2 className="text-lg font-semibold mb-3 text-gray-800">
                Upload Document
            </h2>

            <div
                onDragOver={(e) => {
                    e.preventDefault();
                    setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={onDrop}
                onClick={() => inputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${dragging
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-300 hover:border-blue-400 hover:bg-gray-50"
                    }`}
            >
                {uploading ? (
                    <div className="flex flex-col items-center gap-2">
                        <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                        <span className="text-sm text-gray-600">Uploading…</span>
                    </div>
                ) : (
                    <>
                        <svg
                            className="mx-auto h-10 w-10 text-gray-400 mb-2"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={1.5}
                                d="M12 16V4m0 0l-4 4m4-4 4 4M4 14v4a2 2 0 002 2h12a2 2 0 002-2v-4"
                            />
                        </svg>
                        <p className="text-sm text-gray-600">
                            Drag & drop a <strong>PDF</strong> or <strong>DOCX</strong> file
                            here, or click to browse
                        </p>
                    </>
                )}
            </div>

            <input
                ref={inputRef}
                type="file"
                accept=".pdf,.docx"
                className="hidden"
                onChange={(e) => handleFiles(e.target.files)}
            />

            {error && (
                <p className="mt-2 text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">
                    {error}
                </p>
            )}
        </div>
    );
}

import { useEffect, useRef } from "react";
import { getTaskStatus } from "../api";
import type { UploadedFile } from "../types";

interface Props {
    files: UploadedFile[];
    onUpdate: (index: number, file: UploadedFile) => void;
}

const STEP_LABELS: Record<string, string> = {
    downloading: "Downloading file",
    extracting: "Extracting text",
    ocr: "Running OCR",
    chunking: "Chunking text",
    embedding: "Generating embeddings",
    storing: "Storing in Qdrant",
};

const STATUS_COLORS: Record<string, string> = {
    PENDING: "bg-gray-400",
    STARTED: "bg-blue-400",
    PROGRESS: "bg-blue-500",
    SUCCESS: "bg-green-500",
    FAILURE: "bg-red-500",
    RETRY: "bg-yellow-500",
};

export default function ProcessingStatus({ files, onUpdate }: Props) {
    const intervals = useRef<Map<number, ReturnType<typeof setInterval>>>(new Map());

    useEffect(() => {
        files.forEach((f, i) => {
            if (["SUCCESS", "FAILURE"].includes(f.status)) {
                const existing = intervals.current.get(i);
                if (existing) {
                    clearInterval(existing);
                    intervals.current.delete(i);
                }
                return;
            }

            if (intervals.current.has(i)) return;

            const id = setInterval(async () => {
                try {
                    const s = await getTaskStatus(f.taskId);
                    onUpdate(i, {
                        ...f,
                        status: s.status,
                        progress: s.progress,
                    });
                    if (["SUCCESS", "FAILURE"].includes(s.status)) {
                        clearInterval(id);
                        intervals.current.delete(i);
                    }
                } catch {
                    // ignore transient errors
                }
            }, 2000);

            intervals.current.set(i, id);
        });

        return () => {
            intervals.current.forEach((id) => clearInterval(id));
        };
    }, [files, onUpdate]);

    if (files.length === 0) return null;

    return (
        <div>
            <h2 className="text-lg font-semibold mb-3 text-gray-800">
                Processing Status
            </h2>
            <ul className="space-y-3">
                {files.map((f, i) => (
                    <li
                        key={`${f.taskId}-${i}`}
                        className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm"
                    >
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-gray-700 truncate max-w-[70%]">
                                {f.fileName}
                            </span>
                            <span
                                className={`text-xs text-white px-2 py-0.5 rounded-full ${STATUS_COLORS[f.status] ?? "bg-gray-400"}`}
                            >
                                {f.status}
                            </span>
                        </div>

                        {f.progress?.step && (
                            <p className="text-xs text-gray-500">
                                {STEP_LABELS[f.progress.step] ?? f.progress.step}
                                {f.progress.detail && ` — ${f.progress.detail}`}
                            </p>
                        )}

                        {f.progress?.percent != null && (
                            <div className="mt-2 w-full bg-gray-200 rounded-full h-1.5">
                                <div
                                    className="bg-blue-500 h-1.5 rounded-full transition-all"
                                    style={{ width: `${f.progress.percent}%` }}
                                />
                            </div>
                        )}

                        {f.status === "SUCCESS" && (
                            <p className="text-xs text-green-600 mt-1">
                                Indexing complete
                            </p>
                        )}
                        {f.status === "FAILURE" && (
                            <p className="text-xs text-red-600 mt-1">
                                Indexing failed
                            </p>
                        )}
                    </li>
                ))}
            </ul>
        </div>
    );
}

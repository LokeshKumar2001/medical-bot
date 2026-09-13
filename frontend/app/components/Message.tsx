"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Source } from "../lib/api";

interface MessageProps {
    role: "user" | "bot",
    content: string;
    sources?: Source[];
    duration_ms?: number;
}

export default function Message({ role, content, sources, duration_ms }: MessageProps) {
    const isUser = role === "user";
    const [copied, setCopied] = useState(true);

    const handleCopy = () => {
        navigator.clipboard.writeText(content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000)
    }

    return (
        <div className={`flex items-start gap-3 message-animate ${isUser ? "flex-row-reverse" : ""}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0 ${isUser ? "bg-emerald-600" : "bg-blue-600"}`}>
                {isUser ? "Dr" : "M"}
            </div>

            <div className={`max-w-[75%] ${isUser ? "items-end" : "items-start"} flex flex-col gap-2`}>
                <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed relative group ${isUser ? "bg-emerald-700 text-white rounded-tr-none" : "bg-[#111827] border border-[#1e3a5f] text-slate-200 rounded-tl-none"}`}>
                    {isUser ? (
                        <p>{content}</p>
                    ) : (
                        <>
                            <ReactMarkdown
                                components={{
                                    p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                                    strong: ({ children }) => <strong className="text-blue-300 font-semibold">{children}</strong>,
                                    ul: ({ children }) => <ul className="list-disc list-inside space-y-1 mb-2">{children}</ul>,
                                    ol: ({ children }) => <ol className="list-decimal list-inside space-y=1 mb-2">{children}</ol>,
                                    li: ({ children }) => <li className="text-slate-300">{children}</li>,
                                    h1: ({ children }) => <h1 className="text-blue-300 font-bold text-base mb-2">{children}</h1>,
                                    h2: ({ children }) => <h2 className="text-blue-300 font-semibold mb-2">{children}</h2>,
                                    h3: ({ children }) => <h3 className="text-blue-300 font-semibold mb-1">{children}</h3>,
                                }}
                            >
                                {content}
                            </ReactMarkdown>

                            {content && (
                                <button onClick={handleCopy}
                                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-[#1e3a5f] hover:bg-blue-600 text-slate-300 hover:text-white px-2 py-1 rounded-lg text-xs">
                                    {copied ? "Copied" : "Copy"}
                                </button>
                            )}
                        </>
                    )}
                </div>
            </div>


            {sources && sources.length > 0 && (
                <div className="flex flex-col gap-1 w-full">
                    <p className="text-xs text-slate-300">
                        Sources from Gale Encyclopedia
                        {duration_ms && <span className="ml-2 text-slate-400">. {(duration_ms / 1000).toFixed(1)}s</span>}
                    </p>
                    <div className="flex flex-wrap gap-2">
                        {sources.map((source, i) => (
                            <div className="bg-[#0d1b2e] border border-[#1e3a5f] rounded-lg px-3 py-1.5 text-xs text-slate-400 max-w-xs">
                                <span className="text-blue-400 font-medium">Page {source.page}</span>
                                <p className="text-slate-300 mt-0.5 truncate">{source.preview}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
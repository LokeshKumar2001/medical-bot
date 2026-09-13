'use client';
import { useRouter } from "next/navigation";
import React, { useEffect, useRef, useState } from "react";
import { ChatMessage, checkHealth, createSession, deleteSession, fetchMessages, fetchSession, Session, streamMessage } from "./lib/api";
import { getUser, isLoggedIn, logout } from "./lib/auth";
import { Menu, Send } from 'lucide-react';
import TypingIndicator from "./components/TypingIndicator";
import Message from "./components/Message";

const SUGGESTED_QUESTIONS = [
  "What are the symptoms of malaria?",
  "How is hypertension diagnosed and treated?",
  "What is the difference between Type 1 and Type 2 diabetes?",
  "What are the causes and treatment of kidney failure?",
  "What is myocardial infarction and how is it treated?"
]

export default function Home() {
  const router = useRouter();
  const [user, setUser] = useState<{ full_name: string; email: string } | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.push("/login");
      return;
    }
    const u = getUser();
    setUser(u);
    checkHealth().then(setHealthy);
    loadSessions();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, loading])

  const loadSessions = async () => {
    const data = await fetchSession();
    setSessions(data);
  }

  const handleSelectSession = async (session: Session) => {
    setActiveSession(session);
    const msgs = await fetchMessages(session.id);
    setMessages(msgs);
  }

  const handleNewChat = async () => {
    const session = await createSession("New Chat");
    if (!session) return;
    setSessions((prev) => [session, ...prev])
    setActiveSession(session);
    setMessages([]);
    inputRef?.current?.focus();
  }

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    await deleteSession(sessionId);
    setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    if (activeSession?.id === sessionId) {
      setActiveSession(null);
      setMessages([])
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  const handleSend = async (question?: string) => {
    const q = (question || input).trim()
    if (!q || loading) return;

    let session = activeSession;
    if (!session) {
      const newSession = await createSession("New Chat");
      if (!newSession) return;
      session = newSession;
      setSessions((prev) => [newSession, ...prev]);
      setActiveSession(newSession);
    }

    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setInput("");
    setLoading(true);
    setMessages((prev) => [...prev, { role: "bot", content: "" }])

    const startTime = Date.now();

    await streamMessage(
      q,
      session.id,
      (token) => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "bot") {
            updated[updated.length - 1] = { ...last, content: last.content + token };
          }
          return updated;
        })
      },
      (sources) => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "bot") {
            updated[updated.length - 1] = {
              ...last,
              sources,
              duration_ms: Date.now() - startTime,
            };
          }
          return updated;
        });
        //Refresh sessions to update titles
        loadSessions();
      },
      () => {
        setLoading(false);
        inputRef.current?.focus();
      },
      (err) => {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: "bot", content: `x Error: ${err}` }
          return updated;
        });
        setLoading(false);
      }
    )
  }

  const handleLogout = () => {
    logout();
    router.push("/login");
  }

  const showWelcome = messages.length === 0;

  return (
    <div className="flex h-screen bg-[#0a0f1e] overflow-hidden">
      {sidebarOpen && (
        <aside className="w-64 bg-[#0d1b2e] border-r border-[#1e3a5f] flex flex-col shrink-0">
          <div className="p-4 border-b border-[#1e3a5f]">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-xs">
                M
              </div>
              <span className="text-white font-semibold text-sm">MedBot</span>
            </div>
            <button className="w-full bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium py-2 px-3 rounded-xl transition-all flex items-center gap-2" onClick={handleNewChat}>
              <span className="text-lg leading-none">+</span>
              New Chat
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {sessions.length === 0 && (
              <p className="text-slate-500 text-xs text-center mt-4">No Chats yet</p>
            )}
            {sessions.map((session) => (
              <div
                key={session.id}
                onClick={() => handleSelectSession(session)}
                className={`group flex item-center justify-between px-3 py-2 rounded-xl cursor-pointer transition-all ${activeSession?.id === session.id ? "bg-[#1e3a5f] text-white" : "text-slate-400 hover:bg-[#111827] hover:text-white"}`}
              >
                <span className="text-xs truncate flex-1">{session.title}</span>
                <button
                  onClick={(e) => handleDeleteSession(e, session.id)}
                  className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400 ml-2 text-xs transition-all"
                >
                  x
                </button>
              </div>
            ))}
          </div>

          <div className="p-4 border-t border-[#1e3a5f]">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-[#111827] border border-[#1e3a5f] flex items-center justify-center text-white text-xs font-bold shrink-0">
                {user?.full_name ? user.full_name[0].toUpperCase() : "N"}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-white text-xs font-medium truncate">{user?.full_name || "Sujan Anand"}</p>
                <p className="text-slate-400 text-xs truncate">{user?.email || "sujanand0@gmail.com"}</p>
              </div>
            </div>
          </div>
        </aside>
      )}

      <div className="flex flex-col flex-1 overflow-hidden">
        <header className="flex items-center justify-between px-6 py-3.5 border-b border-[#1e3a5f] bg-[#0d1b2e] shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen((prev) => !prev)}
              className="text-slate-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-[#1e3a5f]/40 flex items-center justify-center focus:outline-none"
              aria-label="Toggle sidebar"
            >
              <Menu size={18} />
            </button>
            <div className="flex flex-col justify-center">
              <h1 className="text-white font-semibold text-[15px] leading-tight">
                {activeSession ? activeSession.title : "MedBot"}
              </h1>
              <p className="text-slate-400 text-xs mt-0.5 leading-tight">
                Gale Encyclopedia of Medicine · GPT-4o
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${healthy === null
                ? "bg-amber-400 animate-pulse"
                : healthy
                  ? "bg-emerald-400"
                  : "bg-red-400"
                }`}
            />
            <span className="text-xs text-slate-300 font-medium">
              {healthy === null ? "Connecting..." : healthy ? "Online" : "Offline"}
            </span>
          </div>
        </header>

        {/* Main Content Area (Messages & Welcome) */}
        <main className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-3xl mx-auto space-y-6">
            {showWelcome && (
              <div className="flex flex-col items-center justify-center text-center px-4 py-4">
                <div className="w-14 h-14 rounded-2xl bg-blue-600 flex items-center justify-center text-white font-bold text-2xl shadow-lg shadow-blue-600/25 mx-auto mb-4">
                  M
                </div>
                <h2 className="text-2xl font-bold text-white tracking-tight mb-2">
                  Hello, {user?.full_name ? user.full_name.split(" ")[0] : "Sujan"} 👋
                </h2>
                <p className="text-slate-400 text-xs sm:text-sm max-w-md text-center leading-relaxed">
                  AI-powered medical assistant trained on the Gale Encyclopedia of Medicine (3rd Edition).
                </p>

                <div className="w-full max-w-xl mx-auto mt-7 text-left">
                  <p className="text-xs text-slate-400 font-medium mb-2.5">Suggested Questions</p>
                  <div className="flex flex-col gap-2.5">
                    {SUGGESTED_QUESTIONS.map((q, i) => (
                      <button
                        key={i}
                        onClick={() => {
                          setInput(q);
                          inputRef.current?.focus();
                          handleSend(q)
                        }}
                        className="w-full text-left px-4 py-3 rounded-xl bg-[#0c1527] border border-[#1e3a5f] hover:border-blue-500 hover:bg-[#0f1d36] text-slate-300 hover:text-white text-xs sm:text-sm transition-all duration-150 cursor-pointer"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {messages?.map((msg, id) => {
              const isLastMessage = (id == messages.length - 1);
              const isEmptyBot = isLastMessage && msg.role == "bot" && msg.content === "" && loading;
              if (isEmptyBot) return <TypingIndicator key={id} />

              return (
                <Message key={id} role={msg.role} content={msg.content} sources={msg.sources} duration_ms={msg.duration_ms} />
              )
            })}
            <div ref={bottomRef} />
          </div>
        </main>

        {/* Footer (Input Section anchored at the bottom) */}
        <footer className="px-6 py-4 border-t border-[#1e3a5f] bg-[#0d1b2e] shrink-0">
          <div className="max-w-3xl mx-auto">
            <div className="flex items-center gap-3 bg-[#111827] border border-[#1e3a5f] rounded-2xl px-4 py-2.5 focus-within:border-blue-500 transition-colors shadow-sm">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a medical question... (Enter to send)"
                rows={1}
                className="flex-1 bg-transparent text-slate-200 placeholder-slate-400 text-sm resize-none outline-none leading-relaxed"
                onInput={(e) => {
                  const t = e.target as HTMLTextAreaElement;
                  t.style.height = "auto";
                  t.style.height = t.scrollHeight + "px";
                }}
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || loading}
                className="w-8 h-8 rounded-full bg-[#1e293b] hover:bg-blue-600 disabled:opacity-40 disabled:hover:bg-[#1e293b] text-white flex items-center justify-center transition-colors shrink-0"
                aria-label="Send question"
              >
                <Send size={15} className="translate-x-0.5 text-slate-200" />
              </button>
            </div>
            <p className="text-center text-xs text-slate-400 mt-2.5">
              MedBot can make mistakes. Always verify with clinical judgment.
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
}

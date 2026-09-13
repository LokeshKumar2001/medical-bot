export default function TypingIndicator() {
    return (
        <div className="flex items-start gap-3 message-animate">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
                M
            </div>

            <div className="bg-[#111827] border border-[#1e3a5f] rounded-2xl rounded-tl-none px-4 py-3">
                <div className="flex items-center gap-1.5">
                    <span className="typing-dot w-2 h-2 rounded-full bg-blue-400 inline-block" />
                    <span className="typing-dot w-2 h-2 rounded-full bg-blue-400 inline-block" />
                    <span className="typing-dot w-2 h-2 rounded-full bg-blue-400 inline-block" />
                </div>
            </div>
        </div>
    )
}
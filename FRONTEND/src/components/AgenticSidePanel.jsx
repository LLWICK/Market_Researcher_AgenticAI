import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Bot, Send } from "lucide-react";

// Simpler Agentic AI Side Panel
// Features:
// - Slide-in/out panel
// - Agent header
// - Chat-style interface
// - Minimal abilities

export default function AgenticSidePanel() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { id: 1, role: "assistant", text: "Hello! How can I help you today?" },
  ]);
  const [input, setInput] = useState("");

  function handleSend(e) {
    e.preventDefault();
    if (!input.trim()) return;
    const text = input.trim();
    setMessages((prev) => [...prev, { id: Date.now(), role: "user", text }]);
    setInput("");
    // Simulate assistant response
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { id: Date.now(), role: "assistant", text: `I heard: ${text}` },
      ]);
    }, 600);
  }

  return (
    <>
      {/* Toggle Button */}
      <div className="fixed bottom-6 right-6 z-50">
        <button
          onClick={() => setOpen(true)}
          className="flex items-center gap-2 px-4 py-3 rounded-full shadow-md bg-white border"
        >
          <Bot className="w-5 h-5" />
          <span className="text-sm font-medium">Astra</span>
        </button>
      </div>

      <AnimatePresence>
        {open && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/40 z-40"
              onClick={() => setOpen(false)}
            />

            {/* Panel */}
            <motion.aside
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="fixed right-0 top-0 z-50 h-full w-[360px] bg-white border-l shadow-xl flex flex-col"
            >
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b">
                <div className="flex items-center gap-2">
                  <div className="w-10 h-10 rounded-lg bg-indigo-500 flex items-center justify-center text-white font-semibold">
                    A
                  </div>
                  <div>
                    <div className="font-semibold">Astra</div>
                    <div className="text-xs text-zinc-500">Assistant</div>
                  </div>
                </div>
                <button
                  onClick={() => setOpen(false)}
                  className="p-2 hover:bg-zinc-100 rounded-md"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-auto p-4 space-y-3">
                {messages.map((m) => (
                  <div
                    key={m.id}
                    className={`flex ${
                      m.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`rounded-lg p-3 max-w-[80%] ${
                        m.role === "user"
                          ? "bg-indigo-600 text-white"
                          : "bg-zinc-100"
                      }`}
                    >
                      <div className="text-sm whitespace-pre-wrap">
                        {m.text}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Input */}
              <form onSubmit={handleSend} className="flex gap-2 p-3 border-t">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Type a message..."
                  className="flex-1 rounded-md border p-2 text-sm"
                />
                <button
                  type="submit"
                  className="px-3 py-2 bg-indigo-600 text-white rounded-md flex items-center gap-1"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

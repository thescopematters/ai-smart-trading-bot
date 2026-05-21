/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable no-unused-vars */
import React, { useEffect, useRef, useState, useCallback, memo } from "react";
import clsx from "clsx";
import ReactMarkdown from "react-markdown";
import cryptobotAvatar from "../../assets/cryptobot_avatar_cute_1.png";
import { ArrowDown } from "lucide-react";
import remarkGfm from "remark-gfm";
import { motion, AnimatePresence } from "framer-motion";

// ─── Stable ReactMarkdown components (defined OUTSIDE to prevent re-mount) ───
const markdownComponents = {
  p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
  ul: ({ node, ...props }) => <ul className="list-disc pl-4 mb-2" {...props} />,
  ol: ({ node, ...props }) => (
    <ol className="list-decimal pl-4 mb-2" {...props} />
  ),
  li: ({ node, ...props }) => <li className="mb-1" {...props} />,
  a: ({ node, ...props }) => (
    <a
      className="text-neon-blue hover:underline"
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    />
  ),
  code: ({ node, inline, className, children, ...props }) => {
    return inline ? (
      <code
        className="bg-indigo-50 px-1.5 py-0.5 rounded text-indigo-900 font-mono text-xs border border-indigo-100 font-semibold"
        {...props}
      >
        {children}
      </code>
    ) : (
      <code
        className="block bg-slate-800 text-slate-200 p-3 rounded-xl text-xs font-mono my-2 whitespace-pre-wrap shadow-inner"
        {...props}
      >
        {children}
      </code>
    );
  },
  table: ({ node, ...props }) => (
    <div className="w-full overflow-x-auto my-3 rounded-xl border border-slate-200 bg-white shadow-sm pb-1 custom-scrollbar">
      <table className="w-max min-w-full divide-y divide-slate-200 text-left border-collapse" {...props} />
    </div>
  ),
  thead: ({ node, ...props }) => <thead className="bg-slate-50/80" {...props} />,
  th: ({ node, ...props }) => (
    <th
      className="px-3 py-2 sm:px-4 sm:py-3 text-left text-[10px] sm:text-xs font-extrabold text-slate-500 uppercase tracking-wider whitespace-nowrap"
      {...props}
    />
  ),
  td: ({ node, ...props }) => (
    <td
      className="px-3 py-2 sm:px-4 sm:py-3 text-[11px] sm:text-sm text-slate-700 border-t border-slate-100/60 font-medium whitespace-nowrap"
      {...props}
    />
  ),
  tr: ({ node, ...props }) => (
    <tr className="hover:bg-slate-50/50 transition-colors" {...props} />
  ),
};

// Stable remarkPlugins array (prevents re-mount on every render)
const remarkPluginsArray = [remarkGfm];

// ─── Memoized Message Row ────────────────────────────────────────────────────
// Each message row only re-renders when its own text/timestamp/error changes,
// NOT when a different message (e.g. the streaming last message) updates.
const MessageRow = memo(({ msg }) => (
  <div
    className={clsx(
      "flex w-full min-w-0",
      msg.isUser ? "justify-end" : "justify-start",
    )}
  >
    {!msg.isUser && (
      <div className="w-8 h-8 rounded-full overflow-hidden shrink-0 shadow-md bg-white mr-3">
        <img
          src={cryptobotAvatar}
          alt="CryptoBot"
          className="w-full h-full object-cover"
        />
      </div>
    )}

    <div
      className={clsx(
        "flex flex-col min-w-0",
        msg.isUser ? "items-end max-w-[80%]" : "items-start max-w-[95%] sm:max-w-[90%]",
      )}
    >
      <div
        className={clsx(
          "rounded-2xl px-5 py-3 text-sm shadow-sm min-w-0 max-w-full",
          msg.isUser
            ? "bg-[#072042] text-white rounded-br-none shadow-[#072042]/20"
            : msg.isError
              ? "bg-red-50 text-red-900 border border-red-200 shadow-sm rounded-bl-none"
              : "bg-slate-200 text-gray-900 shadow-sm rounded-bl-none border border-slate-200",
        )}
      >
        {msg.isUser ? (
          msg.text
        ) : (
          <div className="prose prose-slate prose-sm text-gray-900 min-w-0 max-w-full w-full">
            <ReactMarkdown
              remarkPlugins={remarkPluginsArray}
              components={markdownComponents}
            >
              {msg.text || ""}
            </ReactMarkdown>
          </div>
        )}
      </div>
      {msg.timestamp && msg.id !== "greeting" && (
        <span
          className={clsx(
            "text-[10px] text-slate-800 font-semibold mt-1 px-1",
            msg.isUser ? "text-right" : "text-left",
          )}
        >
          {msg.timestamp}
        </span>
      )}
    </div>
  </div>
));

MessageRow.displayName = "MessageRow";

// ─── Main Component ──────────────────────────────────────────────────────────

const ChatMessages = ({ messages, isTyping }) => {
  const messagesEndRef = useRef(null);
  const scrollContainerRef = useRef(null);
  const [isNearBottom, setIsNearBottom] = useState(true);
  const isSelectingRef = useRef(false);

  // Track selection lifecycle: mousedown → mouseup
  // This prevents auto-scroll from firing while the user is dragging to select text
  useEffect(() => {
    const onMouseDown = () => {
      isSelectingRef.current = true;
    };
    const onMouseUp = () => {
      // Small delay so the auto-scroll effect doesn't fire
      // in the same tick the user releases the mouse
      setTimeout(() => {
        isSelectingRef.current = false;
      }, 200);
    };
    document.addEventListener("mousedown", onMouseDown);
    document.addEventListener("mouseup", onMouseUp);
    return () => {
      document.removeEventListener("mousedown", onMouseDown);
      document.removeEventListener("mouseup", onMouseUp);
    };
  }, []);

  const scrollToBottom = useCallback((behavior = "smooth") => {
    messagesEndRef.current?.scrollIntoView({ behavior });
    setIsNearBottom(true);
  }, []);

  // Detect if user is near bottom
  const handleScroll = useCallback(() => {
    if (!scrollContainerRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } =
      scrollContainerRef.current;
    // If user is within 100px of the bottom, we consider them "at bottom"
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;
    setIsNearBottom(isAtBottom);
  }, []);

  // Only auto-scroll if user is already looking at the bottom
  useEffect(() => {
    // Block scroll if user is mid-select OR has an active selection
    const hasSelection = window.getSelection().toString().length > 0;
    if (isNearBottom && !isSelectingRef.current && !hasSelection) {
      scrollToBottom();
    }
  }, [messages, isNearBottom, scrollToBottom]);

  // Initial scroll
  useEffect(() => {
    scrollToBottom("auto");
  }, []);

  return (
    <div className="flex-1 relative overflow-hidden flex flex-col min-h-0 w-full">
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto overflow-x-hidden w-full p-4 space-y-6 custom-scrollbar overscroll-contain"
      >
        {messages.map((msg) => (
          <MessageRow key={msg.id} msg={msg} />
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="w-8 h-8 mr-3 shrink-0 rounded-full overflow-hidden shadow-sm border border-slate-200 bg-white">
              <img
                src={cryptobotAvatar}
                alt="CryptoBot"
                className="w-full h-full object-cover opacity-60"
              />
            </div>
            <div className="bg-white rounded-2xl rounded-bl-none px-4 py-3 flex gap-1 items-center shadow-sm border border-slate-100">
              <span
                className="w-2 h-2 bg-[#072042] rounded-full animate-bounce"
                style={{ animationDelay: "0s" }}
              ></span>
              <span
                className="w-2 h-2 bg-[#072042] rounded-full animate-bounce"
                style={{ animationDelay: "0.2s" }}
              ></span>
              <span
                className="w-2 h-2 bg-[#072042] rounded-full animate-bounce"
                style={{ animationDelay: "0.4s" }}
              ></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Floating Jump to Bottom / Typing Indicator Button */}
      <AnimatePresence>
        {!isNearBottom && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.8 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.8 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20"
          >
            <motion.button
              whileHover={{ y: -2, scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => scrollToBottom()}
              className={clsx(
                "w-12 h-12 rounded-full shadow-2xl backdrop-blur-md flex items-center justify-center transition-colors duration-300 overflow-hidden",
                "bg-white/80 border border-slate-200 text-slate-900 hover:bg-white",
              )}
            >
              <AnimatePresence mode="wait">
                {isTyping ? (
                  <motion.div
                    key="typing"
                    initial={{ opacity: 0, scale: 0.5 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.5 }}
                    className="flex gap-1"
                  >
                    <span
                      className="w-1.5 h-1.5 bg-slate-900 rounded-full animate-bounce"
                      style={{ animationDelay: "0s" }}
                    ></span>
                    <span
                      className="w-1.5 h-1.5 bg-slate-900 rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    ></span>
                    <span
                      className="w-1.5 h-1.5 bg-slate-900 rounded-full animate-bounce"
                      style={{ animationDelay: "0.4s" }}
                    ></span>
                  </motion.div>
                ) : (
                  <motion.div
                    key="arrow"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    <ArrowDown className="w-6 h-6" />
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ChatMessages;

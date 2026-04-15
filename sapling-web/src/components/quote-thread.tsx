"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Send, Check, CheckCheck, Mail, MailOpen } from "lucide-react";

interface QuoteMessage {
  id: string;
  sender_id: string;
  sender_name?: string;
  sender_role: string;
  message_type: string;
  content: string | null;
  metadata: Record<string, unknown> | null;
  read_at: string | null;
  email_sent_at: string | null;
  email_opened_at: string | null;
  created_at: string;
}

const TYPE_LABELS: Record<string, string> = {
  request: "Quote Requested",
  quote_sent: "Quote Sent",
  accepted: "Quote Accepted",
  declined: "Quote Declined",
  revision_requested: "Revision Requested",
  note: "Message",
  price_update: "Price Updated",
  status_change: "Status Changed",
};

const TYPE_COLORS: Record<string, string> = {
  request: "bg-blue-100 text-blue-700",
  quote_sent: "bg-purple-100 text-purple-700",
  accepted: "bg-green-100 text-green-700",
  declined: "bg-red-100 text-red-700",
  revision_requested: "bg-orange-100 text-orange-700",
  note: "bg-gray-100 text-gray-700",
  price_update: "bg-purple-100 text-purple-700",
  status_change: "bg-gray-100 text-gray-700",
};

function formatTime(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleDateString("en-ZA", {
    day: "numeric", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export function QuoteThread({
  messages,
  quoteId,
  currentUserId,
  onMessageSent,
}: {
  messages: QuoteMessage[];
  quoteId: string;
  currentUserId: string;
  onMessageSent?: () => void;
}) {
  const [newMessage, setNewMessage] = useState("");
  const [sending, setSending] = useState(false);

  async function handleSend() {
    if (!newMessage.trim()) return;
    setSending(true);
    try {
      await api.post(`/api/quotes/${quoteId}/message`, { content: newMessage.trim() });
      setNewMessage("");
      onMessageSent?.();
    } catch {
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex flex-col">
      {/* Messages */}
      <div className="space-y-3 pb-4">
        {messages.map((msg) => {
          const isOwn = msg.sender_id === currentUserId;
          const isSystem = ["accepted", "declined", "revision_requested", "status_change"].includes(msg.message_type);
          const isQuoteSent = msg.message_type === "quote_sent";

          // System/status messages — centered
          if (isSystem) {
            return (
              <div key={msg.id} className="flex flex-col items-center gap-1 py-2">
                <span className={`rounded-full px-3 py-1 text-xs font-medium ${TYPE_COLORS[msg.message_type] || TYPE_COLORS.note}`}>
                  {TYPE_LABELS[msg.message_type] || msg.message_type}
                </span>
                {msg.content && (
                  <p className="text-xs text-muted-foreground">{msg.content}</p>
                )}
                <span className="text-[10px] text-muted-foreground">{formatTime(msg.created_at)}</span>
              </div>
            );
          }

          // Price quote message — highlighted
          if (isQuoteSent) {
            const meta = (msg.metadata || {}) as Record<string, unknown>;
            const price = meta.quoted_price as number | undefined;
            const unit = String(meta.price_unit || "");
            const validUntil = meta.valid_until as string | undefined;
            return (
              <div key={msg.id} className="rounded-lg border-2 border-purple-200 bg-purple-50 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-purple-600">Quote Sent</span>
                  <span className="text-[10px] text-muted-foreground">{formatTime(msg.created_at)}</span>
                </div>
                {price != null && (
                  <p className="mt-2 text-xl font-bold text-purple-800">
                    R{Number(price).toLocaleString("en-ZA", { minimumFractionDigits: 2 })} <span className="text-sm font-normal">{String(unit)}</span>
                  </p>
                )}
                {validUntil && (
                  <p className="mt-1 text-xs text-purple-600">Valid until: {String(validUntil)}</p>
                )}
                {msg.content && (
                  <p className="mt-2 text-sm text-purple-700">{msg.content}</p>
                )}
                <ReadReceipts msg={msg} />
              </div>
            );
          }

          // Regular messages — chat style
          return (
            <div key={msg.id} className={`flex ${isOwn ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] rounded-lg px-4 py-2.5 ${
                isOwn
                  ? "bg-[var(--sapling-orange)] text-white"
                  : "bg-gray-100 text-[var(--sapling-dark)]"
              }`}>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold">
                    {msg.sender_name || (isOwn ? "You" : msg.sender_role === "admin" ? "Admin" : "Agent")}
                  </span>
                  {msg.message_type !== "note" && (
                    <span className={`rounded-full px-1.5 py-0.5 text-[9px] font-medium ${
                      isOwn ? "bg-white/20 text-white" : TYPE_COLORS[msg.message_type] || ""
                    }`}>
                      {TYPE_LABELS[msg.message_type] || ""}
                    </span>
                  )}
                </div>
                {msg.content && (
                  <p className="mt-1 text-sm">{msg.content}</p>
                )}
                <div className={`mt-1 flex items-center justify-end gap-1 text-[10px] ${
                  isOwn ? "text-white/70" : "text-muted-foreground"
                }`}>
                  <span>{formatTime(msg.created_at)}</span>
                  {isOwn && <ReadReceipts msg={msg} light />}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Input */}
      <div className="flex gap-2 border-t pt-3">
        <input
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
          placeholder="Type a message..."
          className="flex-1 rounded-lg border border-input bg-transparent px-3 py-2 text-sm outline-none focus-visible:border-ring"
        />
        <Button
          size="sm"
          onClick={handleSend}
          disabled={sending || !newMessage.trim()}
          className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
        >
          <Send className="size-3.5" />
        </Button>
      </div>
    </div>
  );
}

function ReadReceipts({ msg, light }: { msg: QuoteMessage; light?: boolean }) {
  const color = light ? "text-white/70" : "text-muted-foreground";
  return (
    <span className={`inline-flex items-center gap-0.5 ${color}`}>
      {msg.email_sent_at && (
        <Mail className="size-2.5" />
      )}
      {msg.email_opened_at && (
        <MailOpen className="size-2.5 text-blue-400" />
      )}
      {msg.read_at ? (
        <CheckCheck className="size-3 text-blue-400" />
      ) : (
        <Check className="size-3" />
      )}
    </span>
  );
}

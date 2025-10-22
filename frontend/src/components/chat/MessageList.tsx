/**
 * MessageList Component
 *
 * Displays conversation messages with proper formatting
 */

import React, { useEffect, useRef } from "react";
import { MessageResponse } from "@/types/api";
import { Card } from "@/components/ui";

export interface MessageListProps {
  messages: MessageResponse[];
  loading?: boolean;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  loading = false,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0 && !loading) {
    return (
      <div className="flex h-full items-center justify-center text-gray-500">
        <div className="text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
          <p className="mt-4 text-sm">새로운 대화를 시작하세요</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-4 overflow-y-auto p-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${
            message.role === "user" ? "justify-end" : "justify-start"
          }`}
        >
          <Card
            variant={message.role === "user" ? "outlined" : "default"}
            padding="md"
            className={`max-w-[80%] ${
              message.role === "user"
                ? "bg-blue-50 border-blue-200"
                : "bg-white"
            }`}
          >
            <div className="mb-1 flex items-center gap-2">
              <span
                className={`text-xs font-semibold ${
                  message.role === "user" ? "text-blue-700" : "text-gray-700"
                }`}
              >
                {message.role === "user" ? "나" : "AI 어시스턴트"}
              </span>
              <span className="text-xs text-gray-500">
                {new Date(message.created_at).toLocaleTimeString("ko-KR", {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
            <div className="whitespace-pre-wrap text-sm text-gray-900">
              {message.content}
            </div>
            {message.char_count > 3900 && (
              <div className="mt-2 text-xs text-yellow-600">
                ⚠️ 응답이 길이 제한으로 잘렸을 수 있습니다
              </div>
            )}
          </Card>
        </div>
      ))}

      {loading && (
        <div className="flex justify-start">
          <Card variant="default" padding="md" className="max-w-[80%]">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-gray-700">
                AI 어시스턴트
              </span>
            </div>
            <div className="mt-2 flex items-center gap-2">
              <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.3s]"></div>
              <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.15s]"></div>
              <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400"></div>
            </div>
          </Card>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
};

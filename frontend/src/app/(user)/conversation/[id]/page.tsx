"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Trash2 } from "lucide-react";
import { useState } from "react";

interface Message {
  id: string;
  role: string;
  content: string;
  created_at: string;
}

interface Conversation {
  id: string;
  title: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  messages: Message[];
}

async function fetchConversation(id: string): Promise<Conversation> {
  const response = await fetch(`/api/conversations/${id}`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch conversation");
  }

  return response.json();
}

export default function ConversationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const conversationId = params.id as string;
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const { data: conversation, isLoading, error } = useQuery({
    queryKey: ["conversation", conversationId],
    queryFn: () => fetchConversation(conversationId),
  });

  const handleDelete = async () => {
    try {
      const response = await fetch(`/api/conversations/${conversationId}`, {
        method: "DELETE",
        credentials: "include",
      });

      if (response.ok) {
        router.push("/history");
      }
    } catch (err) {
      console.error("Failed to delete conversation:", err);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">로딩 중...</div>
      </div>
    );
  }

  if (error || !conversation) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-red-600">대화를 불러올 수 없습니다.</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => router.push("/history")}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>대화 목록으로</span>
        </button>

        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              {conversation.title}
            </h1>
            {conversation.tags && conversation.tags.length > 0 && (
              <div className="flex gap-2">
                {conversation.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-1 bg-blue-100 text-blue-700 text-sm rounded"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>

          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="p-2 text-red-600 hover:bg-red-50 rounded"
            title="대화 삭제"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>

        <div className="mt-2 text-sm text-gray-500">
          생성: {new Date(conversation.created_at).toLocaleString("ko-KR")} |
          메시지 수: {conversation.messages.length}
        </div>
      </div>

      {/* Messages */}
      <div className="space-y-4">
        {conversation.messages.map((message) => (
          <div
            key={message.id}
            className={`p-4 rounded-lg ${
              message.role === "user"
                ? "bg-blue-50 ml-8"
                : "bg-gray-50 mr-8"
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="font-semibold text-sm">
                {message.role === "user" ? "사용자" : "AI"}
              </span>
              <span className="text-xs text-gray-500">
                {new Date(message.created_at).toLocaleString("ko-KR")}
              </span>
            </div>
            <div className="text-gray-800 whitespace-pre-wrap">
              {message.content}
            </div>
          </div>
        ))}
      </div>

      {/* Resume Chat Button */}
      <div className="mt-6 text-center">
        <button
          onClick={() => router.push(`/chat?conversation=${conversationId}`)}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          이 대화 이어서 하기
        </button>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold mb-2">대화 삭제</h3>
            <p className="text-gray-600 mb-4">
              이 대화를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
              >
                취소
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                삭제
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

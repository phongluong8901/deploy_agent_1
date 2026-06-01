"use client"

import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';

export default function Home() {
  const [idea, setIdea] = useState<string>('Đang kết nối tới Gemini...');

  useEffect(() => {
    // const eventSource = new EventSource('http://127.0.0.1:8000/api-be');
    const eventSource = new EventSource('/api-be');
    let buffer = "";

    eventSource.onmessage = (event) => {
      buffer += event.data;
      setIdea(buffer);
    };

    eventSource.onerror = () => {
      // Nếu có lỗi, thông báo cho người dùng thay vì chỉ đóng kết nối im lặng
      if (buffer === 'Đang kết nối tới Gemini...') {
        setIdea('❌ Lỗi: Không thể kết nối tới server. Vui lòng kiểm tra lại API Key hoặc mạng.');
      }
      eventSource.close();
    };

    return () => eventSource.close();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-purple-50 to-blue-100 flex items-center justify-center p-6">
      <div className="bg-white/80 backdrop-blur-xl border border-white/50 shadow-2xl rounded-3xl p-8 max-w-2xl w-full">
        <h1 className="text-3xl font-extrabold mb-8 text-center bg-gradient-to-r from-indigo-600 to-blue-500 bg-clip-text text-transparent">
          Business Idea Generator
        </h1>

        <div className="markdown-content p-6 bg-white/50 rounded-2xl text-left text-gray-800 leading-relaxed min-h-[200px] border border-gray-100 shadow-inner">
          <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>
            {idea}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
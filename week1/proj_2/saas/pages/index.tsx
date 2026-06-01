"use client"

import { useEffect, useState } from 'react';

export default function Home() {
  const [idea, setIdea] = useState<string>('Đang chờ lấy ý tưởng từ Gemini...');

  useEffect(() => {
    // local
    // fetch('http://127.0.0.1:8000/api-be')

    // cloud vercel
    fetch('/api-be')
      .then(async (res) => {
        // Lấy nội dung phản hồi
        const text = await res.text();

        // Kiểm tra xem phản hồi có phải là lỗi 429 không
        if (text.includes("429")) {
          throw new Error('Đã hết lượt miễn phí trong hôm nay. Vui lòng quay lại vào ngày mai!');
        }

        if (!res.ok) throw new Error('Không lấy được data');
        return text;
      })
      .then((data) => setIdea(data))
      .catch((err) => setIdea('Lỗi rồi: ' + err.message));
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 p-8">
      <div className="bg-white p-10 rounded-2xl shadow-lg max-w-xl w-full text-center">
        <h1 className="text-2xl font-bold mb-6">Business Idea Generator</h1>
        <div className="p-4 bg-gray-50 rounded-lg text-left whitespace-pre-wrap text-gray-700">
          {idea}
        </div>
      </div>
    </div>
  );
}
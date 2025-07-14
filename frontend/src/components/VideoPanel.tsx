// src/components/VideoPanel.tsx
import React from "react";

const VideoPanel: React.FC = () => {
  return (
    <div className="bg-black rounded-lg overflow-hidden shadow h-[360px] flex items-center justify-center text-white">
      <p className="text-sm text-gray-300">🎥 Streaming en vivo aparecerá aquí</p>
    </div>
  );
};

export default VideoPanel;

/**
 * @file LoadingScreen.tsx
 * @description Initial full-screen pulsing loader displayed while initializing market overview data.
 */

"use client";

import React from "react";

export interface LoadingScreenProps {
  message?: string;
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({
  message = "Đang khởi tạo dữ liệu thị trường...",
}) => {
  return (
    <div className="flex items-center justify-center h-screen bg-[#0E1117]">
      <div className="animate-pulse flex flex-col items-center">
        <div className="h-10 w-10 bg-blue-600 rounded-full mb-4 animate-ping"></div>
        <div className="text-gray-300 font-medium">{message}</div>
      </div>
    </div>
  );
};

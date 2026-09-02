/**
 * @file LoginScreen.tsx
 * @description Secure, modern login screen component for authenticating users
 * directly against the database with credential validation and session bootstrap.
 */

"use client";

import React, { useState } from "react";
import { Lock, User, TrendingUp, ShieldCheck, Eye, EyeOff, LogIn, AlertCircle } from "lucide-react";
import { authApi } from "@/lib/api";

export interface LoginScreenProps {
  onLoginSuccess: (user: any) => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setErrorMsg("Vui lòng điền đầy đủ tên đăng nhập và mật khẩu.");
      return;
    }

    try {
      setLoading(true);
      setErrorMsg(null);
      const res = await authApi.login(username.trim(), password);
      if (res && res.success && res.user) {
        onLoginSuccess(res.user);
      } else {
        setErrorMsg("Đăng nhập không thành công.");
      }
    } catch (err: any) {
      console.error("Login failed:", err);
      const detail = err?.response?.data?.detail || "Không thể kết nối đến máy chủ xác thực.";
      setErrorMsg(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#0D1117] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Subtle Background Glow Elements */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[350px] bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/3 w-[300px] h-[300px] bg-emerald-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Main Login Card */}
      <div className="w-full max-w-md bg-[#161B22] border border-[#30363D] rounded-2xl p-6 sm:p-8 shadow-2xl relative z-10 space-y-6">
        {/* Header Branding */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 shadow-lg shadow-blue-500/25 mb-1">
            <TrendingUp className="text-white w-6 h-6" />
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-100 tracking-tight">
            AI Finance Pro
          </h1>
          <p className="text-xs text-gray-400">
            Hệ thống phân tích tài chính & khuyến nghị định lượng
          </p>
        </div>

        {/* Security Badge */}
        <div className="flex items-center justify-center gap-1.5 px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg text-blue-400 text-xs font-medium">
          <ShieldCheck size={14} />
          <span>Xác thực bảo mật tài khoản Database</span>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="flex items-start gap-2.5 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs animate-shake">
            <AlertCircle size={16} className="shrink-0 text-rose-400 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-gray-300">Tên đăng nhập</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                <User size={15} />
              </div>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Nhập username (VD: admin)"
                autoComplete="username"
                disabled={loading}
                className="w-full pl-9 pr-3 py-2.5 bg-[#0D1117] border border-[#30363D] rounded-xl text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all disabled:opacity-50"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-gray-300">Mật khẩu</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                <Lock size={15} />
              </div>
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Nhập mật khẩu"
                autoComplete="current-password"
                disabled={loading}
                className="w-full pl-9 pr-10 py-2.5 bg-[#0D1117] border border-[#30363D] rounded-xl text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all disabled:opacity-50"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-200 transition-colors"
              >
                {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-2.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {loading ? (
              <span className="inline-flex items-center gap-2">
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Đang xác thực...
              </span>
            ) : (
              <span className="inline-flex items-center gap-2">
                <LogIn size={15} />
                Đăng Nhập
              </span>
            )}
          </button>
        </form>

        {/* Footer Note */}
        <div className="pt-2 border-t border-[#30363D]/60 text-center">
          <p className="text-[11px] text-gray-500 leading-relaxed">
            Hệ thống quản lý nội bộ. Tài khoản chỉ được khởi tạo trực tiếp từ Database bởi Quản Trị Viên.
          </p>
        </div>
      </div>
    </div>
  );
};

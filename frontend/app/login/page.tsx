'use client';

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiLogin } from "../lib/api";
import { saveAuth } from "../lib/auth";

export default function LoginPage() {
    const router = useRouter();
    const [fullName, setFullName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);


    const handleLogin = async () => {
        setError("");
        if (!email || !password) {
            setError("Please fill in all fields");
            return;
        }
        setLoading(true);
        try {
            const res = await apiLogin(email, password);
            if (!res.success) {
                setError(res.error || "Login failed");
                return;
            }
            saveAuth(res.token, res.user);
            router.push("/");
        } catch (error) {
            setError("Something went wrong. Try again")
        } finally {
            setLoading(false);
        }
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key == "Enter") handleLogin();
    }

    return (
        <div className="min-h-screen bg-[#020f1e] flex items-center justify-center px-4">
            <div className="w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="w-14 h-14 rounded-2xl bg-blue-600 flex items-center justify-center text-white font-bold text-xl mx-auto mb-4">
                        <div>M</div>
                    </div>
                    <h1 className="text-2xl font-bold text-white">Welcome back</h1>
                    <p className="text-slate-400 text-sm mt-1">Sign In to Medbot</p>
                </div>

                <div className="bg-[#0d1b2e] border-[#1e3a5f] rounded-2xl p-8 space-y-5">
                    {error && (
                        <div className="bg-red-500/10 border-red-500/30 text-red-400 text-sm px-4 py-3 rounded-xl">
                            {error}
                        </div>
                    )}

                    <div>
                        <label className="text-slate-300 text-sm font-medium block mb-2">Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="doctor@hospital.com"
                            className="w-full bg-[#111827] border-[#1e3a5f] focus:border-blue-500 text-slate-200 placeholder-slate-500 rounded-xl px-4 py-3 text-sm outline-none transition-colors "
                        />
                    </div>
                    <div>
                        <label className="text-slate-300 text-sm font-medium block mb-2">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Min 8 Characters"
                            className="w-full bg-[#111827] border-[#1e3a5f] focus:border-blue-500 text-slate-200 placeholder-slate-500 rounded-xl px-4 py-3 text-sm outline-none transition-colors "
                        />
                    </div>

                    <button
                        onClick={handleLogin}
                        disabled={loading}
                        className="w-full bg-blue-600 hover:bg-blue-500 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-all text-sm"
                    >
                        {loading ? "Creating account..." : "Create account"}
                    </button>


                    <p className="text-slate-400 text-sm">
                        Don't have an account?{" "}
                        <Link href={"/register"} className="text-blue-400 hover:text-blue-300 font-medium"> Register</Link>
                    </p>

                </div>
                <p className="text-center text-slate-600 text-xs mt-6">Medbot -Powered by Gale Encyclopedia of Medicine </p>
            </div>
        </div>
    )
}
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  Lock,
  Mail,
  User,
  KeyRound,
  ArrowRight,
  Fingerprint,
  Eye,
  EyeOff,
  Terminal,
  AlertCircle,
} from 'lucide-react';
import { api } from '../api/client';
import { useToast } from '../context/ToastContext';

function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" className="shrink-0">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      />
    </svg>
  );
}

export default function SignUp() {
  const navigate = useNavigate();
  const { addToast } = useToast();

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Form Field States
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('Threat Intelligence Lead');
  const [clearance, setClearance] = useState('LEVEL_4_RESTRICTED');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleGoogleSignIn = () => {
    addToast({
      title: 'SSO Authentication',
      message: 'Redirecting to Enterprise Identity Provider...',
      type: 'info',
    });
  };

  const handleEnroll = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (!username.trim()) {
      setErrorMessage('Operator Handle is required.');
      return;
    }
    if (!email.trim()) {
      setErrorMessage('Enterprise Email is required.');
      return;
    }
    if (!password) {
      setErrorMessage('Master Key is required.');
      return;
    }
    if (password !== confirmPassword) {
      setErrorMessage('Master Key and Verify Master Key do not match.');
      return;
    }

    setLoading(true);
    try {
      const cleanUsername = username.trim();
      const generatedUserId = `usr-${cleanUsername.toLowerCase().replace(/[^a-z0-9]/g, '') || 'operator'}`;

      await api.signUp({
        user_id: generatedUserId,
        username: cleanUsername,
        email: email.trim(),
        role: role || 'Threat Intelligence Lead',
        is_active: true,
      });

      addToast({
        title: 'Operator Enrolled Successfully',
        message: `Credentials provisioned for ${cleanUsername}. Redirecting to SOC Dashboard...`,
        type: 'success',
      });

      setTimeout(() => {
        navigate('/');
      }, 1000);
    } catch (err) {
      setErrorMessage(err?.message || 'Failed to enroll Sec-Ops operator account.');
      addToast({
        title: 'Enrollment Error',
        message: err?.message || 'Failed to enroll Sec-Ops operator account.',
        type: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-void flex flex-col items-center justify-center p-4 relative overflow-hidden font-sans">
      {/* Background Cyber Grid & Glow Orbs */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f293d15_1px,transparent_1px),linear-gradient(to_bottom,#1f293d15_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] pointer-events-none"></div>
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-red-600/10 rounded-full blur-3xl pointer-events-none animate-pulse-slow"></div>
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none animate-pulse-slow"></div>

      {/* Main Container Card */}
      <div className="w-full max-w-xl z-10 animate-slideDown">
        {/* Header Branding */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-red-950/80 border border-red-500/50 shadow-glow-red mb-3">
            <ShieldAlert className="w-7 h-7 text-red-400 animate-pulse" />
          </div>
          <h1 className="text-2xl font-bold tracking-wider font-mono text-slate-100 uppercase flex items-center justify-center gap-2">
            MODEL<span className="text-red-500">VAULT</span>
          </h1>
          <p className="text-xs font-mono text-slate-400 mt-1 uppercase tracking-widest flex items-center justify-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
            <span>SEC-OPS OPERATOR ENROLLMENT // ACCESS LEVEL 4</span>
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-panel/90 border border-socBorder shadow-2xl rounded-xl p-6 sm:p-8 backdrop-blur-md relative overflow-hidden">
          {/* Top subtle glow line */}
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-red-500 to-transparent"></div>

          {/* Google Sign-In */}
          <button
            type="button"
            onClick={handleGoogleSignIn}
            className="w-full py-2.5 px-4 rounded-md bg-white hover:bg-slate-50 border border-slate-200 text-slate-800 text-xs font-mono font-semibold tracking-wide shadow-sm transition-all flex items-center justify-center gap-3 active:scale-[0.99]"
          >
            <GoogleIcon />
            <span>Sign up with Google</span>
          </button>

          {/* Divider */}
          <div className="relative my-5">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-socBorder" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-panel/90 px-3 font-mono text-slate-400 uppercase tracking-wider">or</span>
            </div>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div className="mb-4 p-3 bg-red-950/40 border border-red-500/50 rounded-md text-xs font-mono text-red-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleEnroll} className="space-y-4">
            {/* Username & Email Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5 flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Operator Handle *</span>
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. j.reese"
                  required
                  className="w-full px-3.5 py-2 bg-surface border border-socBorder rounded-md text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-red-500/60 focus:ring-1 focus:ring-red-500/30 transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5 flex items-center gap-1.5">
                  <Mail className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Enterprise Email *</span>
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="operator@modelvault.io"
                  required
                  className="w-full px-3.5 py-2 bg-surface border border-socBorder rounded-md text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-red-500/60 focus:ring-1 focus:ring-red-500/30 transition-all"
                />
              </div>
            </div>

            {/* Role & Department Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5 flex items-center gap-1.5">
                  <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Operational Role</span>
                </label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full px-3.5 py-2 bg-surface border border-socBorder rounded-md text-xs font-mono text-slate-200 focus:outline-none focus:border-red-500/60 focus:ring-1 focus:ring-red-500/30 transition-all cursor-pointer"
                >
                  <option value="Threat Intelligence Lead">Threat Intelligence Lead</option>
                  <option value="MLOps Security Engineer">MLOps Security Engineer</option>
                  <option value="Incident Response Commander">Incident Response Commander</option>
                  <option value="AI Safety Auditor">AI Safety Auditor</option>
                  <option value="Principal ML Scientist">Principal ML Scientist</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5 flex items-center gap-1.5">
                  <Fingerprint className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Security Clearance</span>
                </label>
                <select
                  value={clearance}
                  onChange={(e) => setClearance(e.target.value)}
                  className="w-full px-3.5 py-2 bg-surface border border-socBorder rounded-md text-xs font-mono text-slate-200 focus:outline-none focus:border-red-500/60 focus:ring-1 focus:ring-red-500/30 transition-all cursor-pointer"
                >
                  <option value="LEVEL_4_RESTRICTED">Level 4 (Threat Response)</option>
                  <option value="LEVEL_5_TOP_SECRET">Level 5 (Model Custodian)</option>
                  <option value="LEVEL_3_ANALYST">Level 3 (Read-Only Telemetry)</option>
                </select>
              </div>
            </div>

            {/* Password & Confirm Password */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Lock className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Master Key *</span>
                  </span>
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-slate-400 hover:text-slate-200 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                  </button>
                </label>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  className="w-full px-3.5 py-2 bg-surface border border-socBorder rounded-md text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-red-500/60 focus:ring-1 focus:ring-red-500/30 transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5 flex items-center gap-1.5">
                  <KeyRound className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Verify Master Key *</span>
                </label>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  className="w-full px-3.5 py-2 bg-surface border border-socBorder rounded-md text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-red-500/60 focus:ring-1 focus:ring-red-500/30 transition-all"
                />
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-4">
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 px-4 rounded-md bg-gradient-to-r from-red-600 to-rose-700 hover:from-red-500 hover:to-rose-600 border border-red-500/40 text-slate-100 text-xs font-mono font-bold uppercase tracking-wider shadow-glow-red hover:shadow-red-500/50 transition-all flex items-center justify-center gap-2 active:scale-[0.99] disabled:opacity-50"
              >
                <span>{loading ? 'PROVISIONING CREDENTIALS...' : 'ENROLL SEC-OPS OPERATOR'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </form>

          {/* Footer inside Card */}
          <div className="mt-6 pt-4 border-t border-socBorder/80 flex items-center justify-between text-xs font-mono text-slate-400">
            <span>Already credentialed?</span>
            <Link
              to="/"
              className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1 transition-colors"
            >
              <span>Access SOC Dashboard</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Security Warning Notice */}
        <p className="text-[11px] font-mono text-center text-slate-400 mt-4 leading-relaxed">
          UNAUTHORIZED ACCESS PROHIBITED &bull; ALL ACTIONS AUDITED TO IMMUTABLE LOGS (RFC 5424)
        </p>
      </div>
    </div>
  );
}

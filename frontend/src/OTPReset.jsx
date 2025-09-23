import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';
import './forgot.css';

const API_BASE = 'http://localhost:5000';

const formatPhoneForServer = (raw) => {
  if (!raw) return '';
  const s = String(raw).trim();
  if (s.startsWith('+')) return s;
  const digits = s.replace(/\D/g, '');
  if (digits.length === 10) return '+91' + digits;
  return '+' + digits;
};

const OTPReset = () => {
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const sendOtp = async () => {
    const digits = phone.replace(/\D/g, '');
    if (!/^\d{10}$/.test(digits)) {
      toast.error('Enter a valid 10-digit phone number');
      return;
    }
    const phoneToSend = formatPhoneForServer(phone);
    try {
      setLoading(true);
      const res = await axios.post(
        `${API_BASE}/send-otp`,
        { phone: phoneToSend },
        { headers: { 'Content-Type': 'application/json' } }
      );
      if (res.data?.status === 'success') {
        toast.success('OTP sent (check server console in dev).');
        setStep(2);
      } else {
        toast.error(res.data?.message || 'Failed to send OTP');
      }
    } catch (err) {
      console.error('sendOtp error', err);
      toast.error(err?.response?.data?.message || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const verifyOtp = async () => {
    const phoneToSend = formatPhoneForServer(phone);
    if (!otp) {
      toast.error('Enter the OTP');
      return;
    }
    try {
      setLoading(true);
      const res = await axios.post(
        `${API_BASE}/verify-otp`,
        { phone: phoneToSend, otp },
        { headers: { 'Content-Type': 'application/json' } }
      );
      if (res.data?.status === 'success') {
        toast.success('OTP verified');
        setStep(3);
      } else {
        toast.error(res.data?.message || 'OTP verification failed');
      }
    } catch (err) {
      console.error('verifyOtp error', err);
      toast.error(err?.response?.data?.message || 'OTP verification failed');
    } finally {
      setLoading(false);
    }
  };

  const updatePassword = async () => {
    const phoneToSend = formatPhoneForServer(phone);
    if (!newPassword) {
      toast.error('Enter a new password');
      return;
    }
    try {
      setLoading(true);
      const res = await axios.post(
        `${API_BASE}/forgot-password`,
        { phone: phoneToSend, otp, newPassword },
        { headers: { 'Content-Type': 'application/json' } }
      );
      if (res.data?.status === 'success') {
        toast.success(res.data.message || 'Password updated!');
        navigate('/login', { replace: true });
      } else {
        toast.error(res.data?.message || 'Password update failed');
      }
    } catch (err) {
      console.error('updatePassword error', err);
      toast.error(err?.response?.data?.message || 'Password update failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="forgot-page-body">
      <div className="forgot-container">
        <h2>Reset Password</h2>

        {step === 1 && (
          <>
            <input type="text" placeholder="Enter Phone Number (10 digits)" value={phone} onChange={(e)=>setPhone(e.target.value)} />
            <button className="reset-btn" onClick={sendOtp} disabled={loading}>{loading? 'Sending...':'Send OTP'}</button>
          </>
        )}

        {step === 2 && (
          <>
            <input type="text" placeholder="Enter OTP" value={otp} onChange={(e)=>setOtp(e.target.value)} />
            <div style={{display:'flex', gap:8}}>
              <button className="reset-btn" onClick={verifyOtp} disabled={loading}>{loading? 'Verifying...':'Verify OTP'}</button>
              <button className="reset-btn" onClick={sendOtp} disabled={loading}>Resend OTP</button>
            </div>
          </>
        )}

        {step === 3 && (
          <>
            <input type="password" placeholder="Enter New Password" value={newPassword} onChange={(e)=>setNewPassword(e.target.value)} />
            <button className="reset-btn" onClick={updatePassword} disabled={loading}>{loading? 'Updating...':'Update Password'}</button>
          </>
        )}

        <div style={{ marginTop: 12, color:'#9aa' }}>
          Tip: In dev mode the OTP is printed to the Flask console as <code>[DEV OTP] phone=... otp=...</code>.
        </div>
      </div>
    </div>
  );
};

export default OTPReset;

/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from 'react';
import { balancesAPI } from '../services/api';
import { useExchangeStore } from '../store/useExchangeStore';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

const CURRENCIES = [
  { symbol: 'USDT', label: 'Tether (USDT)', color: '#22c55e', preset: [1000, 5000, 10000, 50000] },
  { symbol: 'BTC',  label: 'Bitcoin (BTC)',  color: '#f59e0b', preset: [0.1, 0.5, 1, 5] },
  { symbol: 'ETH',  label: 'Ethereum (ETH)', color: '#6366f1', preset: [1, 5, 10, 50] },
];

export default function AddFundsModal({ isOpen, onClose }: Props) {
  const { setBalances } = useExchangeStore();
  const [selectedCurrency, setSelectedCurrency] = useState('USDT');
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const currency = CURRENCIES.find((c) => c.symbol === selectedCurrency)!;

  const handleTopUp = async () => {
    const amt = parseFloat(amount);
    if (!amt || amt <= 0) {
      setError('Please enter a valid amount');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await balancesAPI.topUp(selectedCurrency, amt);

      // Refresh balances from DB
      const res = await balancesAPI.getAll();
      setBalances(res.data);

      setSuccess(`✅ ${amt} ${selectedCurrency} added successfully!`);
      setAmount('');

      // Auto close after 1.5s
      setTimeout(() => {
        setSuccess('');
        onClose();
      }, 1500);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Top up failed');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setAmount('');
    setError('');
    setSuccess('');
    onClose();
  };

  return (
    <div
      onClick={handleClose}
      style={{
        position: 'fixed', inset: 0,
        background: 'rgba(0,0,0,0.65)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: '#1e293b',
          border: '0.5px solid #334155',
          borderRadius: '14px',
          padding: '24px',
          width: '100%',
          maxWidth: '420px',
          margin: '0 16px',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#e2e8f0' }}>
              Add Funds
            </h3>
            <p style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
              Add dummy funds to your account
            </p>
          </div>
          <button
            onClick={handleClose}
            style={{
              background: 'transparent', border: 'none',
              color: '#64748b', fontSize: '20px', cursor: 'pointer',
              lineHeight: 1, padding: '4px',
            }}
          >
            ×
          </button>
        </div>

        {/* Currency selector */}
        <div style={{ marginBottom: '16px' }}>
          <label style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: '8px' }}>
            Select Currency
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
            {CURRENCIES.map((c) => (
              <button
                key={c.symbol}
                onClick={() => { setSelectedCurrency(c.symbol); setAmount(''); }}
                style={{
                  padding: '10px 8px',
                  borderRadius: '8px',
                  border: `1px solid ${selectedCurrency === c.symbol ? c.color : '#334155'}`,
                  background: selectedCurrency === c.symbol ? `${c.color}18` : 'transparent',
                  color: selectedCurrency === c.symbol ? c.color : '#64748b',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                {c.symbol}
              </button>
            ))}
          </div>
        </div>

        {/* Preset amounts */}
        <div style={{ marginBottom: '16px' }}>
          <label style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: '8px' }}>
            Quick Select
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
            {currency.preset.map((p) => (
              <button
                key={p}
                onClick={() => setAmount(String(p))}
                style={{
                  padding: '7px 4px',
                  borderRadius: '6px',
                  border: `0.5px solid ${amount === String(p) ? currency.color : '#334155'}`,
                  background: amount === String(p) ? `${currency.color}18` : '#0f172a',
                  color: amount === String(p) ? currency.color : '#94a3b8',
                  fontSize: '12px',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Custom amount input */}
        <div style={{ marginBottom: '16px' }}>
          <label style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: '8px' }}>
            Custom Amount
          </label>
          <div style={{
            display: 'flex', alignItems: 'center',
            background: '#0f172a', border: '0.5px solid #334155',
            borderRadius: '8px', overflow: 'hidden',
          }}>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleTopUp()}
              placeholder="Enter amount"
              style={{
                flex: 1, background: 'transparent', border: 'none',
                outline: 'none', padding: '10px 12px',
                fontSize: '14px', color: '#e2e8f0',
                fontFamily: 'inherit',
              }}
            />
            <span style={{
              padding: '0 12px', fontSize: '12px',
              color: '#64748b', borderLeft: '0.5px solid #334155',
            }}>
              {selectedCurrency}
            </span>
          </div>
        </div>

        {/* Success / Error messages */}
        {success && (
          <div style={{
            background: 'rgba(34,197,94,0.1)', border: '0.5px solid rgba(34,197,94,0.3)',
            borderRadius: '8px', padding: '10px 12px',
            fontSize: '13px', color: '#22c55e', marginBottom: '12px',
          }}>
            {success}
          </div>
        )}
        {error && (
          <div style={{
            background: 'rgba(239,68,68,0.1)', border: '0.5px solid rgba(239,68,68,0.3)',
            borderRadius: '8px', padding: '10px 12px',
            fontSize: '13px', color: '#ef4444', marginBottom: '12px',
          }}>
            {error}
          </div>
        )}

        {/* Buttons */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
          <button
            onClick={handleClose}
            style={{
              padding: '11px', borderRadius: '8px', fontSize: '13px',
              fontWeight: 500, border: '0.5px solid #334155',
              background: 'transparent', color: '#94a3b8', cursor: 'pointer',
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleTopUp}
            disabled={loading || !amount}
            style={{
              padding: '11px', borderRadius: '8px', fontSize: '13px',
              fontWeight: 600, border: 'none',
              background: loading || !amount ? '#334155' : currency.color,
              color: loading || !amount ? '#64748b' : '#fff',
              cursor: loading || !amount ? 'not-allowed' : 'pointer',
              transition: 'all 0.15s',
            }}
          >
            {loading ? 'Adding...' : `Add ${selectedCurrency}`}
          </button>
        </div>
      </div>
    </div>
  );
}
import { useEffect, useRef } from 'react';
import { ScanLine } from 'lucide-react';

type Props = {
  value: string;
  onChange: (value: string) => void;
  onScan: (value: string) => void | Promise<void>;
  placeholder?: string;
  autoFocus?: boolean;
  disabled?: boolean;
  className?: string;
};

/** Keyboard-wedge friendly barcode field — Enter submits the scan. */
export default function BarcodeScanInput({
  value,
  onChange,
  onScan,
  placeholder = 'Scan barcode or type item code…',
  autoFocus = false,
  disabled = false,
  className = '',
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus();
    }
  }, [autoFocus]);

  const submit = async () => {
    const code = value.trim();
    if (!code || disabled) return;
    await onScan(code);
    onChange('');
    inputRef.current?.focus();
  };

  return (
    <div className={`relative ${className}`}>
      <ScanLine className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" aria-hidden />
      <input
        ref={inputRef}
        type="text"
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            void submit();
          }
        }}
        placeholder={placeholder}
        className="input-field w-full pl-10 font-mono text-sm"
        autoComplete="off"
        spellCheck={false}
      />
    </div>
  );
}

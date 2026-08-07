import { useState } from 'react'

interface PasswordFieldProps {
  value: string
  onChange: (value: string) => void
  disabled?: boolean
  placeholder?: string
  id?: string
}

const PASSWORD_ALPHABET =
  'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%^&*'

function generatePassword(length = 16): string {
  const values = new Uint32Array(length)
  crypto.getRandomValues(values)
  let out = ''
  for (let i = 0; i < length; i++) {
    out += PASSWORD_ALPHABET[values[i] % PASSWORD_ALPHABET.length]
  }
  return out
}

/** Text input for a password with client-side generate and copy helpers. */
export function PasswordField({
  value,
  onChange,
  disabled,
  placeholder,
  id,
}: PasswordFieldProps) {
  const [show, setShow] = useState(false)
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    if (!value) return
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* clipboard unavailable — ignore */
    }
  }

  return (
    <div className="flex items-center gap-2">
      <input
        id={id}
        type={show ? 'text' : 'password'}
        value={value}
        onChange={e => onChange(e.target.value)}
        disabled={disabled}
        placeholder={placeholder ?? 'Password'}
        autoComplete="new-password"
        className="flex-1 bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-gray-200 font-mono text-sm disabled:opacity-40 focus:outline-none focus:border-indigo-500"
      />
      <button
        type="button"
        onClick={() => setShow(s => !s)}
        disabled={disabled}
        className="px-2 py-1.5 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors disabled:opacity-50"
        title={show ? 'Hide password' : 'Show password'}
      >
        {show ? 'Hide' : 'Show'}
      </button>
      <button
        type="button"
        onClick={() => onChange(generatePassword())}
        disabled={disabled}
        className="px-2 py-1.5 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors disabled:opacity-50"
        title="Generate a strong password"
      >
        Generate
      </button>
      <button
        type="button"
        onClick={handleCopy}
        disabled={disabled || !value}
        className="px-2 py-1.5 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors disabled:opacity-50"
        title="Copy password to clipboard"
      >
        {copied ? 'Copied' : 'Copy'}
      </button>
    </div>
  )
}

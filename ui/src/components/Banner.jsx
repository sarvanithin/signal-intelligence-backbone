import React from 'react'

export default function Banner({ kind = 'error', text }) {
  const bgColor = kind === 'error' ? 'bg-red-900 border-red-700' : 'bg-yellow-900 border-yellow-700';
  const textColor = kind === 'error' ? 'text-red-100' : 'text-yellow-100';

  return (
    <div className={`border rounded-lg p-3 ${bgColor} ${textColor} text-sm`}>
      {kind === 'error' ? '⚠️' : 'ℹ️'} {text}
    </div>
  )
}

import { useState, useEffect, useCallback } from 'react'
import { apiFetch } from '../api/client'

export interface WorkbookSheet {
  name: string
  headers: string[]
  rows: (string | number | null)[][]
}

interface Props {
  sheets: WorkbookSheet[]
  networkId: string
  onSaved?: (sheets: WorkbookSheet[]) => void
}

type SheetEdits = Record<string, (string | number | null)[][]>

export function WorkbookGrid({ sheets, networkId, onSaved }: Props) {
  const [activeSheet, setActiveSheet] = useState(0)
  // edits[sheetName] = full 2-d array of current cell values (initially clone of rows)
  const [edits, setEdits] = useState<SheetEdits>(() => initEdits(sheets))
  // dirty[sheetName][rowIdx][colIdx] = true if user changed that cell
  const [dirty, setDirty] = useState<Record<string, boolean[][]>>(() => initDirty(sheets))
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [saveError, setSaveError] = useState<string | null>(null)

  // Re-initialise if sheets prop changes (e.g. after upload)
  useEffect(() => {
    setEdits(initEdits(sheets))
    setDirty(initDirty(sheets))
    setActiveSheet(0)
    setSaveStatus('idle')
    setSaveError(null)
  }, [sheets])

  const handleCellChange = useCallback(
    (sheetName: string, rowIdx: number, colIdx: number, value: string) => {
      setEdits(prev => {
        const rows = prev[sheetName].map(r => [...r])
        rows[rowIdx][colIdx] = value
        return { ...prev, [sheetName]: rows }
      })
      setDirty(prev => {
        const d = prev[sheetName].map(r => [...r])
        d[rowIdx][colIdx] = true
        return { ...prev, [sheetName]: d }
      })
      setSaveStatus('idle')
    },
    []
  )

  const handleSave = async () => {
    setSaveStatus('saving')
    setSaveError(null)
    const data = sheets.map(sheet => ({
      name: sheet.name,
      headers: sheet.headers,
      rows: edits[sheet.name],
    }))
    try {
      await apiFetch(`/api/v1/networks/${networkId}/workbook/save/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data }),
      })
      // Clear dirty flags — edits are now the saved baseline
      setDirty(
        Object.fromEntries(
          sheets.map(sheet => [
            sheet.name,
            sheet.rows.map(row => row.map(() => false)),
          ])
        )
      )
      setSaveStatus('saved')
      if (onSaved) {
        onSaved(
          sheets.map(sheet => ({
            name: sheet.name,
            headers: sheet.headers,
            rows: edits[sheet.name],
          }))
        )
      }
    } catch {
      setSaveStatus('error')
      setSaveError('Failed to save changes. Please try again.')
    }
  }

  const handleDiscard = () => {
    setEdits(initEdits(sheets))
    setDirty(initDirty(sheets))
    setSaveStatus('idle')
    setSaveError(null)
  }

  const hasEdits = sheets.some(sheet =>
    (dirty[sheet.name] ?? []).some(row => row.some(Boolean))
  )

  if (sheets.length === 0) return null

  const sheet = sheets[activeSheet]
  const currentRows = edits[sheet.name] ?? []
  const currentDirty = dirty[sheet.name] ?? []

  return (
    <div className="flex flex-col gap-3">
      {/* Sheet tab bar */}
      {sheets.length > 1 && (
        <div className="flex gap-1 border-b border-gray-700 pb-0">
          {sheets.map((s, idx) => (
            <button
              key={s.name}
              onClick={() => setActiveSheet(idx)}
              className={`px-3 py-1.5 text-sm rounded-t border-b-2 ${
                idx === activeSheet
                  ? 'border-blue-500 text-white bg-gray-800'
                  : 'border-transparent text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              {s.name}
            </button>
          ))}
        </div>
      )}

      {/* Grid */}
      <div className="overflow-x-auto rounded border border-gray-700">
        <table className="min-w-full text-sm text-left">
          <thead className="bg-gray-800 text-gray-300">
            <tr>
              {sheet.headers.map(h => (
                <th key={h} className="px-3 py-2 font-medium whitespace-nowrap border-b border-gray-700">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {currentRows.map((row, rowIdx) => (
              <tr
                key={rowIdx}
                className={rowIdx % 2 === 0 ? 'bg-gray-900' : 'bg-gray-850'}
              >
                {row.map((cell, colIdx) => {
                  const isDirty = currentDirty[rowIdx]?.[colIdx] ?? false
                  return (
                    <td key={colIdx} className="px-1 py-0.5 border-b border-gray-800">
                      <input
                        type="text"
                        value={cell ?? ''}
                        onChange={e =>
                          handleCellChange(sheet.name, rowIdx, colIdx, e.target.value)
                        }
                        className={`w-full bg-transparent px-2 py-1 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 ${
                          isDirty
                            ? 'ring-1 ring-yellow-400 bg-yellow-900/20'
                            : 'hover:bg-gray-700'
                        }`}
                      />
                    </td>
                  )
                })}
              </tr>
            ))}
            {currentRows.length === 0 && (
              <tr>
                <td
                  colSpan={sheet.headers.length}
                  className="px-3 py-4 text-center text-gray-500"
                >
                  No data rows
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Save / Discard toolbar */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleSave}
          disabled={!hasEdits || saveStatus === 'saving'}
          className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm rounded"
        >
          {saveStatus === 'saving' ? 'Saving…' : 'Save changes'}
        </button>
        <button
          onClick={handleDiscard}
          disabled={!hasEdits || saveStatus === 'saving'}
          className="px-4 py-1.5 bg-gray-600 hover:bg-gray-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm rounded"
        >
          Discard
        </button>
        {saveStatus === 'saved' && (
          <span className="text-green-400 text-sm">Saved</span>
        )}
        {saveStatus === 'error' && (
          <span className="text-red-400 text-sm">{saveError}</span>
        )}
      </div>
    </div>
  )
}

function initEdits(sheets: WorkbookSheet[]): SheetEdits {
  return Object.fromEntries(
    sheets.map(sheet => [sheet.name, sheet.rows.map(row => [...row])])
  )
}

function initDirty(sheets: WorkbookSheet[]): Record<string, boolean[][]> {
  return Object.fromEntries(
    sheets.map(sheet => [
      sheet.name,
      sheet.rows.map(row => row.map(() => false)),
    ])
  )
}

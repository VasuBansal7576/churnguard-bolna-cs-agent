'use client'

import { useRef, useState, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { uploadCSV } from '@/lib/api'
import type { UploadResult } from '@/types'

interface UploadCSVProps {
  onUploadComplete: () => void
}

export function UploadCSV({ onUploadComplete }: UploadCSVProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [result, setResult] = useState<UploadResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.endsWith('.csv')) {
      setError('Please upload a .csv file')
      return
    }

    setIsUploading(true)
    setError(null)
    setResult(null)

    try {
      const uploadResult = await uploadCSV(file)
      setResult(uploadResult)
      onUploadComplete()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }, [onUploadComplete])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }, [handleFile])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    e.target.value = '' // Reset so same file can be re-uploaded
  }, [handleFile])

  return (
    <Card className="bg-zinc-900/50 border-zinc-800 p-6">
      <div
        className={`
          relative rounded-xl border-2 border-dashed transition-all duration-200 p-8 cursor-pointer
          ${isDragging
            ? 'border-blue-500 bg-blue-500/5'
            : 'border-zinc-700 hover:border-zinc-600 bg-zinc-900/30'
          }
        `}
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="rounded-full bg-zinc-800 p-3">
            <svg className="h-6 w-6 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-medium text-zinc-300">
              {isUploading ? 'Uploading...' : 'Drop your CSV here, or click to browse'}
            </p>
            <p className="text-xs text-zinc-500 mt-1">
              Required columns: name, email, phone (E.164)
            </p>
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
            disabled={isUploading}
            onClick={(e) => {
              e.stopPropagation()
              fileInputRef.current?.click()
            }}
          >
            {isUploading ? 'Uploading...' : 'Choose File'}
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleFileInput}
            disabled={isUploading}
          />
        </div>
      </div>

      {/* Upload result */}
      {result && (
        <div className="mt-4 rounded-lg bg-emerald-500/5 border border-emerald-500/20 p-3">
          <p className="text-sm text-emerald-400">
            ✓ {result.created} customer{result.created !== 1 ? 's' : ''} created
            {result.skipped > 0 && (
              <span className="text-amber-400 ml-2">
                ({result.skipped} skipped)
              </span>
            )}
          </p>
          {result.errors.length > 0 && (
            <div className="mt-2 text-xs text-zinc-500">
              {result.errors.map((err, i) => (
                <p key={i}>{err}</p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mt-4 rounded-lg bg-red-500/5 border border-red-500/20 p-3">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}
    </Card>
  )
}

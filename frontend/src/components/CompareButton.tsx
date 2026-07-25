import { useState, useEffect } from 'react'
import { Scale, Check } from 'lucide-react'
import { 
  addToComparison, 
  removeFromComparison, 
  isInComparison,
  getComparisonCount
} from '../lib/compareStore'
import type { Institution } from '../lib/api'

interface CompareButtonProps {
  institution: Institution
  size?: 'sm' | 'md' | 'lg'
  variant?: 'icon' | 'button'
  onToggle?: (isAdded: boolean) => void
}

export default function CompareButton({ 
  institution, 
  size = 'md', 
  variant = 'button',
  onToggle 
}: CompareButtonProps) {
  const [isAdded, setIsAdded] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [showMessage, setShowMessage] = useState(false)

  useEffect(() => {
    setIsAdded(isInComparison(institution.id))
  }, [institution.id])

  const handleClick = () => {
    if (isAdded) {
      removeFromComparison(institution.id)
      setIsAdded(false)
      onToggle?.(false)
      showToast('Removed from comparison')
    } else {
      const result = addToComparison(institution)
      if (result.success) {
        setIsAdded(true)
        onToggle?.(true)
        const count = getComparisonCount()
        showToast(`Added! (${count}/3 in comparison)`)
      } else {
        showToast(result.message || 'Cannot add')
      }
    }
  }

  const showToast = (msg: string) => {
    setMessage(msg)
    setShowMessage(true)
    setTimeout(() => setShowMessage(false), 2000)
  }

  const sizeClasses = {
    sm: 'w-7 h-7',
    md: 'w-8 h-8',
    lg: 'w-10 h-10'
  }

  const iconSizes = {
    sm: 'w-3.5 h-3.5',
    md: 'w-4 h-4',
    lg: 'w-5 h-5'
  }

  if (variant === 'icon') {
    return (
      <div className="relative">
        <button
          onClick={handleClick}
          className={`${sizeClasses[size]} rounded-lg flex items-center justify-center transition-colors duration-200 ${
            isAdded 
              ? 'bg-indigo-100 text-indigo-600 hover:bg-indigo-200' 
              : 'bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-700'
          }`}
          title={isAdded ? 'Remove from comparison' : 'Add to compare'}
        >
          {isAdded ? (
            <Check className={iconSizes[size]} />
          ) : (
            <Scale className={iconSizes[size]} />
          )}
        </button>
        
        {/* Toast Message */}
        {showMessage && (
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-gray-900 text-white text-xs rounded-lg whitespace-nowrap z-50 animate-fade-in">
            {message}
            <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="relative">
      <button
        onClick={handleClick}
        className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
          isAdded 
            ? 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200' 
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        }`}
      >
        {isAdded ? (
          <>
            <Check className="w-4 h-4" />
            <span>In Comparison</span>
          </>
        ) : (
          <>
            <Scale className="w-4 h-4" />
            <span>Compare</span>
          </>
        )}
      </button>

      {/* Toast Message */}
      {showMessage && (
        <div className="absolute bottom-full left-0 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg whitespace-nowrap z-50 shadow-lg">
          {message}
          <div className="absolute top-full left-4 border-4 border-transparent border-t-gray-900" />
        </div>
      )}
    </div>
  )
}

import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  type ReactNode,
} from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { cn } from '../../lib/cn'

export const ADD_EXERCISE_PAGE_KEY = 'add'

export interface ExercisePagerPage {
  id: string
  content: ReactNode
  label?: string
}

export interface ExercisePagerHandle {
  goToExercise: (id: string) => void
  goToAddExercise: () => void
  goToPrevious: () => void
  goToNext: () => void
}

export interface ExercisePagerProps {
  pages: ExercisePagerPage[]
  activeId: string
  onActiveChange: (id: string) => void
}

function prefersReducedMotion(): boolean {
  return typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
}

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  const tag = target.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true
  if (target.isContentEditable) return true
  if (target.closest('[role="dialog"]')) return true
  return false
}

export const ExercisePager = forwardRef<ExercisePagerHandle, ExercisePagerProps>(
  function ExercisePager({ pages, activeId, onActiveChange }, ref) {
    const containerRef = useRef<HTMLDivElement>(null)
    const pageRefs = useRef(new Map<string, HTMLDivElement>())
    const lastScrolledId = useRef<string | null>(null)
    const activeIndex = Math.max(
      0,
      pages.findIndex((page) => page.id === activeId),
    )

    const scrollToId = useCallback(
      (id: string) => {
        const el = pageRefs.current.get(id)
        if (el) {
          lastScrolledId.current = id
          el.scrollIntoView({
            behavior: prefersReducedMotion() ? 'auto' : 'smooth',
            inline: 'start',
            block: 'nearest',
          })
        }
      },
      [],
    )

    useImperativeHandle(
      ref,
      () => ({
        goToExercise: (id: string) => {
          onActiveChange(id)
          scrollToId(id)
        },
        goToAddExercise: () => {
          onActiveChange(ADD_EXERCISE_PAGE_KEY)
          scrollToId(ADD_EXERCISE_PAGE_KEY)
        },
        goToPrevious: () => {
          const idx = pages.findIndex((page) => page.id === activeId)
          if (idx > 0) {
            const id = pages[idx - 1]!.id
            onActiveChange(id)
            scrollToId(id)
          }
        },
        goToNext: () => {
          const idx = pages.findIndex((page) => page.id === activeId)
          if (idx >= 0 && idx < pages.length - 1) {
            const id = pages[idx + 1]!.id
            onActiveChange(id)
            scrollToId(id)
          }
        },
      }),
      [pages, activeId, onActiveChange, scrollToId],
    )

    useEffect(() => {
      if (lastScrolledId.current === activeId) return
      scrollToId(activeId)
    }, [activeId, scrollToId])

    useEffect(() => {
      const container = containerRef.current
      if (!container || typeof IntersectionObserver === 'undefined') return

      const observer = new IntersectionObserver(
        (entries) => {
          const mostVisible = entries
            .filter((entry) => entry.isIntersecting)
            .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0]
          if (mostVisible) {
            const id = mostVisible.target.getAttribute('data-page-id')
            if (id && id !== activeId) {
              lastScrolledId.current = id
              onActiveChange(id)
            }
          }
        },
        { root: container, threshold: [0.5, 0.6, 0.7] },
      )

      pageRefs.current.forEach((el) => observer.observe(el))
      return () => observer.disconnect()
    }, [pages, activeId, onActiveChange])

    useEffect(() => {
      const onKeyDown = (event: KeyboardEvent) => {
        if (isEditableTarget(event.target)) return
        if (event.key === 'ArrowLeft' && activeIndex > 0) {
          event.preventDefault()
          const id = pages[activeIndex - 1]!.id
          onActiveChange(id)
          scrollToId(id)
        }
        if (event.key === 'ArrowRight' && activeIndex < pages.length - 1) {
          event.preventDefault()
          const id = pages[activeIndex + 1]!.id
          onActiveChange(id)
          scrollToId(id)
        }
      }
      window.addEventListener('keydown', onKeyDown)
      return () => window.removeEventListener('keydown', onKeyDown)
    }, [activeIndex, pages, onActiveChange, scrollToId])

    const showDots = pages.length <= 7

    return (
      <div className="flex min-h-0 flex-1 flex-col">
        <div
          ref={containerRef}
          className="exercise-pager flex min-h-0 w-full flex-1 snap-x snap-mandatory overflow-x-auto overscroll-x-contain [-webkit-overflow-scrolling:touch] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        >
          {pages.map((page) => (
            <div
              key={page.id}
              data-page-id={page.id}
              ref={(el) => {
                if (el) {
                  pageRefs.current.set(page.id, el)
                } else {
                  pageRefs.current.delete(page.id)
                }
              }}
              className="exercise-page h-full w-full shrink-0 snap-start [scroll-snap-stop:always]"
              aria-label={page.label}
            >
              {page.content}
            </div>
          ))}
        </div>

        <div className="flex items-center justify-center gap-3 border-t border-border px-4 py-2">
          <Button
            size="sm"
            variant="ghost"
            aria-label="Previous exercise"
            disabled={activeIndex <= 0}
            onClick={() => {
              const id = pages[activeIndex - 1]?.id
              if (!id) return
              onActiveChange(id)
              scrollToId(id)
            }}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>

          {showDots ? (
            <div className="flex items-center gap-2" role="tablist" aria-label="Exercise pages">
              {pages.map((page, index) => (
                <button
                  key={page.id}
                  type="button"
                  role="tab"
                  aria-selected={index === activeIndex}
                  aria-label={page.label ?? `Page ${index + 1}`}
                  className={cn(
                    'h-2.5 w-2.5 rounded-full transition-colors',
                    index === activeIndex ? 'bg-primary' : 'bg-border hover:bg-primary/40',
                  )}
                  onClick={() => {
                    onActiveChange(page.id)
                    scrollToId(page.id)
                  }}
                />
              ))}
            </div>
          ) : (
            <p className="text-sm tabular-nums text-textMuted">
              {activeIndex + 1} of {pages.length}
            </p>
          )}

          <Button
            size="sm"
            variant="ghost"
            aria-label="Next exercise"
            disabled={activeIndex >= pages.length - 1}
            onClick={() => {
              const id = pages[activeIndex + 1]?.id
              if (!id) return
              onActiveChange(id)
              scrollToId(id)
            }}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    )
  },
)

ExercisePager.displayName = 'ExercisePager'

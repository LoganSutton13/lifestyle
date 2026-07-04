import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { UtensilsCrossed } from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { EmptyState } from '../../components/ui/EmptyState'
import { Spinner } from '../../components/ui/Spinner'
import { getErrorMessage } from '../../lib/errors'
import type { MealCategoryKey } from '../../lib/constants'
import { fetchMeals } from './api'
import { MealCard } from './MealCard'
import { MealFilterTabs } from './MealFilterTabs'

export function MealPlanPage() {
  const [category, setCategory] = useState<MealCategoryKey>('all')
  const [page, setPage] = useState(1)

  const query = useQuery({
    queryKey: ['meals', category, page],
    queryFn: () => fetchMeals({ category, page }),
  })

  const handleCategoryChange = (nextCategory: MealCategoryKey) => {
    setCategory(nextCategory)
    setPage(1)
  }

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-text">Meal Plan</h1>

      <MealFilterTabs value={category} onChange={handleCategoryChange} />

      {query.isLoading ? <Spinner label="Loading meals..." /> : null}

      {query.isError ? (
        <p className="rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger">
          {getErrorMessage(query.error)}
        </p>
      ) : null}

      {query.isSuccess && query.data.items.length === 0 ? (
        <EmptyState
          title="No meals assigned"
          description="Your coach has not assigned any meals yet."
          icon={<UtensilsCrossed className="h-8 w-8" />}
        />
      ) : null}

      {query.isSuccess && query.data.items.length > 0 ? (
        <div className="space-y-3">
          {query.data.items.map((meal) => (
            <MealCard key={meal.id} meal={meal} />
          ))}
        </div>
      ) : null}

      {query.isSuccess && query.data.total > 0 ? (
        <div className="flex items-center justify-between gap-3 pt-2">
          <Button
            variant="secondary"
            disabled={page <= 1}
            onClick={() => setPage((current) => Math.max(1, current - 1))}
          >
            Previous
          </Button>
          <span className="text-sm text-textMuted">
            Page {query.data.page} of {Math.max(1, Math.ceil(query.data.total / query.data.pageSize))}
          </span>
          <Button
            variant="secondary"
            disabled={!query.data.hasNextPage}
            onClick={() => setPage((current) => current + 1)}
          >
            Next
          </Button>
        </div>
      ) : null}
    </div>
  )
}

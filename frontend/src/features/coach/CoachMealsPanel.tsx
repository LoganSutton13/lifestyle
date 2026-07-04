import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { Select } from '../../components/ui/Select'
import { Spinner } from '../../components/ui/Spinner'
import { useToast } from '../../components/ui/Toast'
import { MEAL_CATEGORIES } from '../../lib/constants'
import { getErrorMessage } from '../../lib/errors'
import * as coachApi from './api'

const categoryOptions = MEAL_CATEGORIES.filter((c) => c.key !== 'all').map((c) => ({
  value: c.key,
  label: c.label,
}))

export function CoachMealsPanel({ clientId }: { clientId: string }) {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [name, setName] = useState('')
  const [category, setCategory] = useState('breakfast')
  const [description, setDescription] = useState('')

  const query = useQuery({
    queryKey: ['coach-client-meals', clientId],
    queryFn: () => coachApi.fetchClientMeals(clientId, { page: 1 }),
  })

  const createMutation = useMutation({
    mutationFn: () => coachApi.createClientMeal(clientId, { name, category, description }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['coach-client-meals', clientId] })
      setName('')
      setDescription('')
      showToast('Meal assigned')
    },
    onError: (error) => showToast(getErrorMessage(error), 'error'),
  })

  const deleteMutation = useMutation({
    mutationFn: (mealId: string) => coachApi.deleteClientMeal(clientId, mealId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['coach-client-meals', clientId] })
      showToast('Meal removed')
    },
    onError: (error) => showToast(getErrorMessage(error), 'error'),
  })

  return (
    <div className="space-y-4">
      <Card className="space-y-3">
        <h3 className="font-semibold text-text">Assign meal</h3>
        <Input label="Meal name" value={name} onChange={(e) => setName(e.target.value)} />
        <Select label="Category" options={categoryOptions} value={category} onChange={(e) => setCategory(e.target.value)} />
        <label className="flex flex-col gap-1.5 text-sm font-medium text-text">
          Description
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="rounded-xl border border-border px-3 py-2.5 font-normal"
          />
        </label>
        <Button type="button" onClick={() => createMutation.mutate()} loading={createMutation.isPending}>
          Assign meal
        </Button>
      </Card>

      {query.isLoading ? <Spinner label="Loading meals..." /> : null}

      {query.isSuccess ? (
        <div className="space-y-2">
          {query.data.items.map((meal) => (
            <Card key={meal.id} className="flex items-start justify-between gap-3">
              <div>
                <p className="font-medium text-text">{meal.name}</p>
                <p className="text-xs text-primaryDark">{meal.categoryLabel}</p>
                {meal.description ? (
                  <p className="mt-1 whitespace-pre-wrap text-sm text-textMuted">{meal.description}</p>
                ) : null}
              </div>
              <Button
                type="button"
                variant="danger"
                size="sm"
                onClick={() => deleteMutation.mutate(meal.id)}
              >
                Remove
              </Button>
            </Card>
          ))}
        </div>
      ) : null}
    </div>
  )
}

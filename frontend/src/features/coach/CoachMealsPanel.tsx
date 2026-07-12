import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { Modal } from '../../components/ui/Modal'
import { Select } from '../../components/ui/Select'
import { Spinner } from '../../components/ui/Spinner'
import { Textarea } from '../../components/ui/Textarea'
import { useToast } from '../../components/ui/Toast'
import { MEAL_CATEGORIES } from '../../lib/constants'
import { getErrorMessage } from '../../lib/errors'
import * as coachApi from './api'
import type { CoachMealItem } from './api'

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
  const [editingMeal, setEditingMeal] = useState<CoachMealItem | null>(null)
  const [editName, setEditName] = useState('')
  const [editCategory, setEditCategory] = useState('breakfast')
  const [editDescription, setEditDescription] = useState('')

  const query = useQuery({
    queryKey: ['coach-client-meals', clientId],
    queryFn: () => coachApi.fetchClientMeals(clientId, { page: 1 }),
  })

  useEffect(() => {
    if (editingMeal) {
      setEditName(editingMeal.name)
      setEditCategory(editingMeal.category)
      setEditDescription(editingMeal.description)
    }
  }, [editingMeal])

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

  const updateMutation = useMutation({
    mutationFn: () =>
      coachApi.updateClientMeal(clientId, editingMeal!.id, {
        name: editName,
        category: editCategory,
        description: editDescription,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['coach-client-meals', clientId] })
      setEditingMeal(null)
      showToast('Meal updated')
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
        <Textarea
          label="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
        />
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
              <div className="flex shrink-0 gap-2">
                <Button type="button" variant="secondary" size="sm" onClick={() => setEditingMeal(meal)}>
                  Edit
                </Button>
                <Button
                  type="button"
                  variant="danger"
                  size="sm"
                  onClick={() => deleteMutation.mutate(meal.id)}
                >
                  Remove
                </Button>
              </div>
            </Card>
          ))}
        </div>
      ) : null}

      <Modal open={editingMeal !== null} onClose={() => setEditingMeal(null)} title="Edit meal">
        <div className="flex flex-col gap-4">
          <Input label="Meal name" value={editName} onChange={(e) => setEditName(e.target.value)} />
          <Select
            label="Category"
            options={categoryOptions}
            value={editCategory}
            onChange={(e) => setEditCategory(e.target.value)}
          />
          <Textarea
            label="Description"
            value={editDescription}
            onChange={(e) => setEditDescription(e.target.value)}
            rows={3}
          />
          <div className="flex gap-3 pt-2">
            <Button
              type="button"
              variant="secondary"
              className="flex-1"
              onClick={() => setEditingMeal(null)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              className="flex-1"
              disabled={!editName.trim()}
              loading={updateMutation.isPending}
              onClick={() => updateMutation.mutate()}
            >
              Save
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

import { Card } from '../../components/ui/Card';
import type { MealItem } from './api';

interface MealCardProps {
  meal: MealItem;
}

export function MealCard({ meal }: MealCardProps) {
  return (
    <Card>
      <div className="mb-2 flex items-start justify-between gap-2">
        <h3 className="font-semibold text-text">{meal.name}</h3>
        <span className="shrink-0 rounded-full bg-primarySoft px-2 py-0.5 text-xs font-medium text-primaryDark">
          {meal.categoryLabel}
        </span>
      </div>
      <p className="whitespace-pre-wrap text-sm text-textMuted">{meal.description}</p>
    </Card>
  );
}

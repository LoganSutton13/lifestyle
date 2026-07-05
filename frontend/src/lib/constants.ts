import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export type UserRole = 'client' | 'coach' | 'admin'

export interface User {
  id: string
  username: string
  firstName: string
  lastName: string
  role: UserRole
  avatarKey: string
  timezone: string
}

export interface UserWithCreated extends User {
  createdAt: string
}

export const AVATAR_KEYS = [
  'avocado',
  'banana',
  'carrot',
  'guava',
  'kiwi',
  'lemon',
  'lettuce',
  'orange',
  'pepper',
  'pineapple',
  'redpepper',
  'watermelon',
] as const

export type AvatarKey = (typeof AVATAR_KEYS)[number]

const AVATAR_FILES: Record<AvatarKey, string> = {
  avocado: 'cute_avocado',
  banana: 'cute_banana',
  carrot: 'cute_carrot',
  guava: 'cute_guava',
  kiwi: 'cute_kiwi',
  lemon: 'cute_lemon',
  lettuce: 'cute_lettuce',
  orange: 'cute_orange',
  pepper: 'cute_pepper',
  pineapple: 'cute_pineapple',
  redpepper: 'cute_red_pepper',
  watermelon: 'cuter_watermelon',
}

export const MEAL_CATEGORIES = [
  { key: 'all', label: 'All' },
  { key: 'breakfast', label: 'Breakfast' },
  { key: 'lunch', label: 'Lunch' },
  { key: 'dinner', label: 'Dinner' },
  { key: 'dessert', label: 'Dessert' },
] as const

export type MealCategoryKey = (typeof MEAL_CATEGORIES)[number]['key']

export const RANGE_PRESETS = [
  { key: '1M', label: '1M', months: 1 },
  { key: '3M', label: '3M', months: 3 },
  { key: '6M', label: '6M', months: 6 },
  { key: '1Y', label: '1Y', months: 12 },
  { key: '3Y', label: '3Y', months: 36 },
] as const

export type RangePresetKey = (typeof RANGE_PRESETS)[number]['key']

export const MAX_MEASUREMENT_RANGE_DAYS = 1095

export const DEFAULT_PAGE_SIZE = 10

export const COACH_PAGE_SIZE = 20

export function avatarUrl(key: string): string {
  const file = AVATAR_FILES[key as AvatarKey] ?? key
  return `/avatars/${file}.svg`
}

export function getDefaultRedirect(role: UserRole): string {
  switch (role) {
    case 'admin':
      return '/admin'
    case 'coach':
      return '/coach'
    default:
      return '/app/checklist'
  }
}

import type { Layout } from 'react-grid-layout'

export interface DashboardCard {
  cardId: string
  x: number
  y: number
  w: number
  h: number
}

/**
 * Dashboard cards形式をreact-grid-layoutのLayout形式に変換
 */
export function toGridLayout(cards: DashboardCard[]): Layout[] {
  return cards.map((card) => ({
    i: card.cardId,
    x: card.x,
    y: card.y,
    w: card.w,
    h: card.h,
  }))
}

/**
 * react-grid-layoutのLayout形式をDashboard cards形式に変換
 */
export function fromGridLayout(layout: Layout[]): DashboardCard[] {
  return layout.map((item) => ({
    cardId: item.i,
    x: item.x,
    y: item.y,
    w: item.w,
    h: item.h,
  }))
}

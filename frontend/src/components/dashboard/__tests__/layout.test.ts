import { describe, it, expect } from 'vitest'
import { toGridLayout, fromGridLayout } from '../layout'
import type { Layout } from 'react-grid-layout'

describe('layout helpers', () => {
  describe('toGridLayout', () => {
    it('converts dashboard cards to RGL layout', () => {
      const cards = [
        { cardId: 'card1', x: 0, y: 0, w: 4, h: 2 },
        { cardId: 'card2', x: 4, y: 0, w: 4, h: 2 },
      ]

      const layout = toGridLayout(cards)

      expect(layout).toHaveLength(2)
      expect(layout[0]).toMatchObject({
        i: 'card1',
        x: 0,
        y: 0,
        w: 4,
        h: 2,
      })
      expect(layout[1]).toMatchObject({
        i: 'card2',
        x: 4,
        y: 0,
        w: 4,
        h: 2,
      })
    })

    it('handles empty cards array', () => {
      const layout = toGridLayout([])
      expect(layout).toEqual([])
    })
  })

  describe('fromGridLayout', () => {
    it('converts RGL layout back to dashboard cards', () => {
      const layout: Layout[] = [
        { i: 'card1', x: 0, y: 0, w: 4, h: 2 },
        { i: 'card2', x: 4, y: 0, w: 4, h: 2 },
      ]

      const cards = fromGridLayout(layout)

      expect(cards).toHaveLength(2)
      expect(cards[0]).toMatchObject({
        cardId: 'card1',
        x: 0,
        y: 0,
        w: 4,
        h: 2,
      })
      expect(cards[1]).toMatchObject({
        cardId: 'card2',
        x: 4,
        y: 0,
        w: 4,
        h: 2,
      })
    })

    it('handles empty layout array', () => {
      const cards = fromGridLayout([])
      expect(cards).toEqual([])
    })

    it('preserves card order', () => {
      const layout: Layout[] = [
        { i: 'card2', x: 4, y: 0, w: 4, h: 2 },
        { i: 'card1', x: 0, y: 0, w: 4, h: 2 },
      ]

      const cards = fromGridLayout(layout)

      expect(cards[0].cardId).toBe('card2')
      expect(cards[1].cardId).toBe('card1')
    })
  })
})

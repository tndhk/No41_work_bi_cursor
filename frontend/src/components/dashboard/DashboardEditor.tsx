import { useState, useMemo } from 'react'
import GridLayout, { Layout } from 'react-grid-layout'
import 'react-grid-layout/css/styles.css'
import 'react-resizable/css/styles.css'
import { toGridLayout, fromGridLayout, type DashboardCard } from './layout'
import CardContainer from './CardContainer'

interface DashboardEditorProps {
  cards: DashboardCard[]
  onLayoutCommit: (cards: DashboardCard[]) => void
}

export default function DashboardEditor({ cards, onLayoutCommit }: DashboardEditorProps) {
  const [currentLayout, setCurrentLayout] = useState<Layout[]>(() => toGridLayout(cards))

  const handleLayoutChange = (layout: Layout[]) => {
    setCurrentLayout(layout)
  }

  const handleDragStop = (layout: Layout[]) => {
    const updatedCards = fromGridLayout(layout)
    onLayoutCommit(updatedCards)
  }

  const handleResizeStop = (layout: Layout[]) => {
    const updatedCards = fromGridLayout(layout)
    onLayoutCommit(updatedCards)
  }

  return (
    <div className="dashboard-editor">
      <GridLayout
        className="layout"
        layout={currentLayout}
        cols={12}
        rowHeight={60}
        width={1200}
        onLayoutChange={handleLayoutChange}
        onDragStop={handleDragStop}
        onResizeStop={handleResizeStop}
        draggableHandle=".drag-handle"
      >
        {cards.map((card) => (
          <div key={card.cardId} className="bg-white border border-gray-300 rounded-sm">
            <div className="drag-handle cursor-move p-2 border-b border-gray-200 bg-gray-50 text-xs text-gray-600">
              {card.cardId}
            </div>
            <div className="p-4">
              <CardContainer cardId={card.cardId} filters={{}} />
            </div>
          </div>
        ))}
      </GridLayout>
      {cards.length === 0 && (
        <div className="text-center text-gray-500 py-12 border border-dashed border-gray-300 rounded-sm">
          カードがありません
        </div>
      )}
    </div>
  )
}

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dashboardSharesApi } from '../../lib/dashboardShares'
import { api } from '../../lib/api'
import type { DashboardShareCreateRequest } from '../../lib/dashboardShares'

interface User {
  user_id: string
  email: string
  name: string
}

interface Group {
  group_id: string
  name: string
}

interface DashboardShareDialogProps {
  dashboardId: string
  isOpen: boolean
  onClose: () => void
}

export default function DashboardShareDialog({ dashboardId, isOpen, onClose }: DashboardShareDialogProps) {
  const [shareType, setShareType] = useState<'user' | 'group'>('user')
  const [selectedId, setSelectedId] = useState('')
  const [permission, setPermission] = useState<'viewer' | 'editor' | 'owner'>('viewer')
  const queryClient = useQueryClient()

  const { data: shares = [] } = useQuery({
    queryKey: ['dashboard-shares', dashboardId],
    queryFn: () => dashboardSharesApi.list(dashboardId),
    enabled: isOpen,
  })

  const { data: referencedDatasets = [] } = useQuery({
    queryKey: ['referenced-datasets', dashboardId],
    queryFn: () => dashboardSharesApi.getReferencedDatasets(dashboardId),
    enabled: isOpen,
  })

  const { data: users = [] } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await api.get('users').json<{ data: User[] }>()
      return response.data
    },
    enabled: isOpen && shareType === 'user',
  })

  const { data: groups = [] } = useQuery({
    queryKey: ['groups'],
    queryFn: async () => {
      const response = await api.get('groups').json<{ data: Group[] }>()
      return response.data
    },
    enabled: isOpen && shareType === 'group',
  })

  const createMutation = useMutation({
    mutationFn: (data: DashboardShareCreateRequest) => dashboardSharesApi.create(dashboardId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-shares', dashboardId] })
      setSelectedId('')
      setPermission('viewer')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (shareId: string) => dashboardSharesApi.delete(dashboardId, shareId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-shares', dashboardId] })
    },
  })

  const handleShare = () => {
    if (!selectedId) {
      alert('ユーザーまたはグループを選択してください')
      return
    }
    createMutation.mutate({
      shared_to_type: shareType,
      shared_to_id: selectedId,
      permission,
    })
  }

  const handleDelete = (shareId: string) => {
    if (confirm('この共有を削除しますか？')) {
      deleteMutation.mutate(shareId)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        <h3 className="text-lg font-semibold mb-4">Dashboard共有</h3>

        {referencedDatasets.length > 0 && (
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
            <p className="text-sm font-medium text-yellow-800 mb-2">このDashboardが参照しているDataset:</p>
            <ul className="text-sm text-yellow-700 list-disc list-inside">
              {referencedDatasets.map((ds) => (
                <li key={ds.dataset_id}>{ds.name}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">共有タイプ</label>
          <div className="flex gap-4">
            <label className="flex items-center">
              <input
                type="radio"
                value="user"
                checked={shareType === 'user'}
                onChange={(e) => {
                  setShareType(e.target.value as 'user')
                  setSelectedId('')
                }}
                className="mr-2"
              />
              ユーザー
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="group"
                checked={shareType === 'group'}
                onChange={(e) => {
                  setShareType(e.target.value as 'group')
                  setSelectedId('')
                }}
                className="mr-2"
              />
              グループ
            </label>
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {shareType === 'user' ? 'ユーザー' : 'グループ'}を選択
          </label>
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="">選択してください</option>
            {shareType === 'user'
              ? users.map((user) => (
                  <option key={user.user_id} value={user.user_id}>
                    {user.name} ({user.email})
                  </option>
                ))
              : groups.map((group) => (
                  <option key={group.group_id} value={group.group_id}>
                    {group.name}
                  </option>
                ))}
          </select>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">権限</label>
          <select
            value={permission}
            onChange={(e) => setPermission(e.target.value as 'viewer' | 'editor' | 'owner')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="viewer">閲覧のみ</option>
            <option value="editor">編集可</option>
            <option value="owner">所有者</option>
          </select>
        </div>

        <div className="flex justify-end gap-2 mb-6">
          <button
            onClick={handleShare}
            disabled={!selectedId || createMutation.isPending}
            className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
          >
            {createMutation.isPending ? '共有中...' : '共有'}
          </button>
        </div>

        <div className="border-t pt-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">共有一覧</h4>
          {shares.length === 0 ? (
            <p className="text-sm text-gray-500">共有がありません</p>
          ) : (
            <div className="space-y-2">
              {shares.map((share) => (
                <div key={share.share_id} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                  <div>
                    <span className="text-sm font-medium">{share.shared_to_name || share.shared_to_id}</span>
                    <span className="text-xs text-gray-500 ml-2">
                      ({share.shared_to_type === 'user' ? 'ユーザー' : 'グループ'})
                    </span>
                    <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded ml-2">
                      {share.permission === 'viewer' ? '閲覧' : share.permission === 'editor' ? '編集' : '所有者'}
                    </span>
                  </div>
                  <button
                    onClick={() => handleDelete(share.share_id)}
                    className="text-sm text-red-600 hover:text-red-700"
                  >
                    削除
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="flex justify-end mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
          >
            閉じる
          </button>
        </div>
      </div>
    </div>
  )
}

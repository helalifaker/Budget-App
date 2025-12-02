/**
 * CellCommentDialog Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CellCommentDialog } from '@/components/CellCommentDialog'
import { useCellComments } from '@/hooks/api/useCellComments'

// Mock hooks
vi.mock('@/hooks/api/useCellComments', () => ({
  useCellComments: vi.fn(() => ({
    comments: [
      {
        id: '1',
        cell_id: 'cell-1',
        comment_text: 'This is a test comment',
        created_by: 'test@efir.sa',
        created_at: '2025-01-01T10:00:00Z',
        is_resolved: false,
      },
      {
        id: '2',
        cell_id: 'cell-1',
        comment_text: 'Resolved comment',
        created_by: 'user2@efir.sa',
        created_at: '2025-01-01T09:00:00Z',
        is_resolved: true,
        resolved_by: 'admin@efir.sa',
        resolved_at: '2025-01-01T11:00:00Z',
      },
    ],
    addComment: vi.fn().mockResolvedValue({}),
    resolveComment: vi.fn().mockResolvedValue({}),
    isLoading: false,
  })),
}))

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

describe('CellCommentDialog', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = createTestQueryClient()
  })

  it('renders dialog when open', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <CellCommentDialog cellId="cell-1" open={true} onOpenChange={() => {}} />
      </QueryClientProvider>
    )

    expect(screen.getByText('Commentaires de cellule')).toBeInTheDocument()
    expect(screen.getByText('This is a test comment')).toBeInTheDocument()
  })

  it('displays comments correctly', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <CellCommentDialog cellId="cell-1" open={true} onOpenChange={() => {}} />
      </QueryClientProvider>
    )

    expect(screen.getByText('This is a test comment')).toBeInTheDocument()
    expect(screen.getByText('Resolved comment')).toBeInTheDocument()
  })

  it('shows resolved status', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <CellCommentDialog cellId="cell-1" open={true} onOpenChange={() => {}} />
      </QueryClientProvider>
    )

    expect(screen.getByText(/Résolu par admin@efir.sa/)).toBeInTheDocument()
  })

  it('allows adding new comment', async () => {
    const user = userEvent.setup()
    const { useCellComments } = await import('@/hooks/api/useCellComments')
    const mockAddComment = vi.fn().mockResolvedValue({})

    vi.mocked(useCellComments).mockReturnValue({
      comments: [],
      addComment: mockAddComment,
      resolveComment: vi.fn(),
      isLoading: false,
    })

    render(
      <QueryClientProvider client={queryClient}>
        <CellCommentDialog cellId="cell-1" open={true} onOpenChange={() => {}} />
      </QueryClientProvider>
    )

    const textarea = screen.getByPlaceholderText('Ajouter un commentaire...')
    await user.type(textarea, 'New comment text')

    const addButton = screen.getByText('Ajouter')
    await user.click(addButton)

    await waitFor(() => {
      expect(mockAddComment).toHaveBeenCalledWith('New comment text')
    })
  })

  it('shows empty state when no comments', () => {
    vi.mocked(useCellComments).mockReturnValue({
      comments: [],
      addComment: vi.fn(),
      resolveComment: vi.fn(),
      isLoading: false,
    })

    render(
      <QueryClientProvider client={queryClient}>
        <CellCommentDialog cellId="cell-1" open={true} onOpenChange={() => {}} />
      </QueryClientProvider>
    )

    expect(screen.getByText('Aucun commentaire')).toBeInTheDocument()
  })
})

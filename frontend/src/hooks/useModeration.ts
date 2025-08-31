import { useState, useCallback } from 'react';

interface Review {
  id?: string;
  content_id: string;
  ai_confidence?: number;
  action: string;
  reviewer_id?: string;
  notes?: string;
  created_at?: string;
}

interface ModerationResult {
  content_id: string;
  ai_confidence: number;
  action: string;
  reason?: string;
}

export function useModeration() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const enqueueForModeration = useCallback(async (contentId: string): Promise<Review> => {
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('content_id', contentId);

      const response = await fetch('/api/moderation/enqueue', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to enqueue for moderation with status ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to enqueue for moderation';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const listQueue = useCallback(async (): Promise<Review[]> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/moderation/queue');

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to list queue with status ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to list queue';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const postDecision = useCallback(async (
    reviewId: string,
    decision: string,
    reviewerId?: string,
    notes?: string
  ): Promise<Review> => {
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('decision', decision);
      if (reviewerId) formData.append('reviewer_id', reviewerId);
      if (notes) formData.append('notes', notes);

      const response = await fetch(`/api/moderation/${reviewId}/decision`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to post decision with status ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to post decision';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const postDecisionByContentId = useCallback(async (
    contentId: string,
    decision: string,
    reviewerId?: string,
    notes?: string
  ): Promise<Review> => {
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('decision', decision);
      if (reviewerId) formData.append('reviewer_id', reviewerId);
      if (notes) formData.append('notes', notes);

      const response = await fetch(`/api/moderation/content/${contentId}/decision`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to post decision with status ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to post decision';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const simulateModeration = useCallback(async (contentId: string): Promise<ModerationResult> => {
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('content_id', contentId);

      const response = await fetch('/api/content/moderation/simulate', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to simulate moderation with status ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to simulate moderation';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const getPendingReviews = useCallback(async (): Promise<Review[]> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/moderation/pending');

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to get pending reviews with status ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get pending reviews';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    enqueueForModeration,
    listQueue,
    postDecision,
    postDecisionByContentId,
    simulateModeration,
    getPendingReviews,
  };
}

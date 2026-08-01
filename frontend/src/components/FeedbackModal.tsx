import React, { useState } from 'react';
import { useFeedback } from '../hooks/useFeedback';
import { FeedbackType, FeedbackRating } from '../api/feedback';

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialType?: FeedbackType;
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
  isOpen,
  onClose,
  initialType,
}) => {
  const { createFeedback, loading, error } = useFeedback();
  const [type, setType] = useState<FeedbackType>(initialType || 'general');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [rating, setRating] = useState<FeedbackRating | undefined>();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);

    if (!title.trim() || !description.trim()) {
      setSubmitError('Please fill in all required fields');
      return;
    }

    try {
      await createFeedback({
        type,
        title,
        description,
        rating,
        public: true,
      });
      setSubmitSuccess(true);
      setTimeout(() => {
        resetForm();
        onClose();
      }, 2000);
    } catch (err) {
      setSubmitError((err as Error).message);
      console.error('[v0] Error submitting feedback:', err);
    }
  };

  const resetForm = () => {
    setType(initialType || 'general');
    setTitle('');
    setDescription('');
    setRating(undefined);
    setSubmitError(null);
    setSubmitSuccess(false);
  };

  return (
    <div className="feedback-modal-overlay" onClick={onClose}>
      <div
        className="feedback-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2>Send Feedback</h2>
          <button
            className="btn-close"
            onClick={onClose}
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {submitSuccess ? (
          <div className="modal-success">
            <div className="success-icon">✓</div>
            <h3>Thank you!</h3>
            <p>Your feedback has been submitted successfully.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="feedback-form">
            {(submitError || error) && (
              <div className="error-alert">
                {submitError || error}
              </div>
            )}

            <div className="form-group">
              <label htmlFor="feedback-type">Feedback Type</label>
              <select
                id="feedback-type"
                value={type}
                onChange={(e) =>
                  setType(e.target.value as FeedbackType)
                }
              >
                <option value="bug_report">Bug Report</option>
                <option value="feature_request">Feature Request</option>
                <option value="improvement">Improvement</option>
                <option value="general">General Feedback</option>
                <option value="complaint">Complaint</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="feedback-title">Title *</label>
              <input
                id="feedback-title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Brief summary of your feedback"
                maxLength={100}
              />
              <span className="char-count">
                {title.length} / 100
              </span>
            </div>

            <div className="form-group">
              <label htmlFor="feedback-description">
                Description *
              </label>
              <textarea
                id="feedback-description"
                value={description}
                onChange={(e) =>
                  setDescription(e.target.value)
                }
                placeholder="Please provide detailed feedback..."
                rows={5}
                maxLength={1000}
              />
              <span className="char-count">
                {description.length} / 1000
              </span>
            </div>

            {type === 'bug_report' && (
              <div className="form-group">
                <label htmlFor="feedback-rating">
                  How severely does this affect you?
                </label>
                <div className="rating-options">
                  {(['very_poor', 'poor', 'average', 'good', 'excellent'] as FeedbackRating[]).map(
                    (r) => (
                      <label key={r} className="rating-label">
                        <input
                          type="radio"
                          name="rating"
                          value={r}
                          checked={rating === r}
                          onChange={() => setRating(r)}
                        />
                        <span className="rating-text">
                          {r === 'very_poor'
                            ? '🔴 Critical'
                            : r === 'poor'
                            ? '🟠 High'
                            : r === 'average'
                            ? '🟡 Medium'
                            : r === 'good'
                            ? '🟢 Low'
                            : '✅ Minor'}
                        </span>
                      </label>
                    )
                  )}
                </div>
              </div>
            )}

            <div className="form-actions">
              <button
                type="button"
                onClick={onClose}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="btn btn-primary"
              >
                {loading ? 'Submitting...' : 'Submit Feedback'}
              </button>
            </div>
          </form>
        )}
      </div>

      <style jsx>{`
        .feedback-modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 2000;
        }

        .feedback-modal {
          background: white;
          border-radius: 12px;
          box-shadow: 0 20px 25px rgba(0, 0, 0, 0.15);
          max-width: 500px;
          width: 90%;
          max-height: 90vh;
          overflow-y: auto;
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-bottom: 1px solid #e5e7eb;
        }

        .modal-header h2 {
          margin: 0;
          font-size: 20px;
          font-weight: 600;
        }

        .btn-close {
          background: none;
          border: none;
          font-size: 24px;
          color: #9ca3af;
          cursor: pointer;
          padding: 0;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .btn-close:hover {
          color: #374151;
        }

        .feedback-form {
          padding: 20px;
        }

        .form-group {
          margin-bottom: 20px;
          display: flex;
          flex-direction: column;
        }

        .form-group label {
          margin-bottom: 8px;
          font-size: 14px;
          font-weight: 500;
          color: #374151;
        }

        .form-group input[type="text"],
        .form-group textarea,
        .form-group select {
          padding: 10px 12px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          font-size: 14px;
          font-family: inherit;
          resize: vertical;
        }

        .form-group input[type="text"]:focus,
        .form-group textarea:focus,
        .form-group select:focus {
          outline: none;
          border-color: #2563eb;
          box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }

        .char-count {
          margin-top: 4px;
          font-size: 12px;
          color: #9ca3af;
        }

        .rating-options {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
        }

        .rating-label {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px;
          border: 1px solid #e5e7eb;
          border-radius: 6px;
          cursor: pointer;
          font-size: 14px;
        }

        .rating-label input[type="radio"] {
          cursor: pointer;
        }

        .rating-label:hover {
          border-color: #d1d5db;
          background: #f9fafb;
        }

        .rating-text {
          flex: 1;
        }

        .form-actions {
          display: flex;
          gap: 12px;
          margin-top: 24px;
        }

        .btn {
          padding: 10px 16px;
          border: none;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          flex: 1;
        }

        .btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-primary {
          background: #2563eb;
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          background: #1d4ed8;
        }

        .btn-secondary {
          background: #f3f4f6;
          color: #374151;
        }

        .btn-secondary:hover:not(:disabled) {
          background: #e5e7eb;
        }

        .error-alert {
          padding: 12px;
          background: #fee2e2;
          color: #dc2626;
          border-radius: 6px;
          font-size: 14px;
          margin-bottom: 16px;
        }

        .modal-success {
          padding: 40px 20px;
          text-align: center;
        }

        .success-icon {
          font-size: 48px;
          margin-bottom: 16px;
          color: #059669;
        }

        .modal-success h3 {
          margin: 0 0 8px 0;
          font-size: 18px;
          font-weight: 600;
          color: #059669;
        }

        .modal-success p {
          margin: 0;
          color: #6b7280;
          font-size: 14px;
        }
      `}</style>
    </div>
  );
};

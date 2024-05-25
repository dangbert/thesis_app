import React, { useState } from 'react';
import {
  Typography,
  TextField,
  Button,
  CircularProgress,
  Checkbox,
  FormControlLabel,
  Box,
} from '@mui/material';
import { FeedbackPublic, FeedbackData, FeedbackCreate } from '../models';
import * as courseApi from '../api/courses';
import { useUserContext } from '../providers';

import { FEEDBACK_MAX_ROWS, FEEDBACK_MIN_ROWS } from '../constants';

interface FeedbackViewProps {
  attemptId: string;
  feedback?: FeedbackPublic;
  readOnly: boolean;
  onClose: () => void;
  onCreate?: (feedback: FeedbackPublic) => void;
}

/**
 * View or create feedback on an Attempt.
 */
const FeedbackView: React.FC<FeedbackViewProps> = ({
  attemptId,
  feedback,
  readOnly,
  onClose,
  onCreate,
}) => {
  const DEFAULT_FEEDBACK: FeedbackData = {
    feedback: '',
    other_comments: '',
    approved: false,
    score: undefined,
  };

  const [feedbackData, setFeedbackData] = useState<FeedbackData>(
    feedback?.data || DEFAULT_FEEDBACK
  );
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const userCtx = useUserContext();

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = event.target;
    setFeedbackData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async () => {
    if (!userCtx.user) {
      setError('User not logged in');
      return;
    }
    setSubmitting(true);
    const feedbackToCreate: FeedbackCreate = {
      attempt_id: attemptId,
      data: feedbackData,
    };

    const res = await courseApi.createFeedback(feedbackToCreate);
    if (res.error) {
      setError(res.error);
    } else {
      // Handle success (refresh data, close modal, etc.)
      console.log('Feedback successfully created:', res.data);
      onCreate?.(res.data);
    }
    setSubmitting(false);
  };

  const canSubmit = !submitting && feedbackData.feedback.trim() !== '';

  return (
    <>
      {/* TODO: start textfield short, and support it growing up to maxlines? */}
      <TextField
        label="Feedback"
        name="feedback"
        value={feedbackData.feedback}
        onChange={handleInputChange}
        fullWidth
        margin="dense"
        InputProps={{ readOnly }}
        multiline
        minRows={FEEDBACK_MIN_ROWS}
        maxRows={FEEDBACK_MAX_ROWS}
      />
      <TextField
        label="Other Comments"
        name="other_comments"
        value={feedbackData.other_comments || ''}
        onChange={handleInputChange}
        fullWidth
        margin="dense"
        InputProps={{ readOnly }}
        multiline
        minRows={FEEDBACK_MIN_ROWS}
        maxRows={FEEDBACK_MAX_ROWS}
      />
      <FormControlLabel
        control={
          <Checkbox
            checked={feedbackData.approved}
            onChange={handleInputChange}
            name="approved"
            color="primary"
            disabled={readOnly}
          />
        }
        label="Approve Work"
      />
      {error && <Typography color="error">{error}</Typography>}
      {!readOnly && (
        <Box display="flex" justifyContent="flex-end" mt={2}>
          <Button onClick={onClose} color="primary">
            Cancel
          </Button>
          <Button onClick={handleSubmit} color="primary" disabled={!canSubmit}>
            {submitting ? <CircularProgress size={24} /> : 'Submit Feedback'}
          </Button>
        </Box>
      )}
    </>
  );
};

export default FeedbackView;

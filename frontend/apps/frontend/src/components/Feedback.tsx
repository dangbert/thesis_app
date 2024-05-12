import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  CircularProgress,
} from '@mui/material';
import { FeedbackPublic, FeedbackData, FeedbackCreate } from '../models';
import * as courseApi from '../api/courses';

interface FeedbackViewProps {
  attemptId: string;
  feedback?: FeedbackPublic;
  readOnly: boolean;
}

const FeedbackView: React.FC<FeedbackViewProps> = ({
  attemptId,
  feedback,
  readOnly,
}) => {
  const [feedbackData, setFeedbackData] = useState<FeedbackData>({
    feedback: feedback?.data.feedback || '',
    plan: feedback?.data.plan || '',
  });
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setFeedbackData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async () => {
    let cancelled = false;
    setSubmitting(true);
    const feedbackToCreate: FeedbackCreate = {
      attempt_id: attemptId,
      user_id: '', // User ID should be provided as required or obtained from context
      data: feedbackData,
    };

    const res = await courseApi.createFeedback(feedbackToCreate);
    if (cancelled) return;

    if (res.error) {
      setError(res.error);
    } else {
      // handle success (refresh data, close modal, etc.)
      console.log('Feedback successfully created:', res.data);
    }
    setSubmitting(false);
    return () => (cancelled = true);
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Feedback Details
        </Typography>
        <TextField
          label="Feedback"
          name="feedback"
          value={feedbackData.feedback}
          onChange={handleInputChange}
          fullWidth
          margin="dense"
          InputProps={{ readOnly }}
          multiline
          rows={4}
        />
        <TextField
          label="Plan"
          name="plan"
          value={feedbackData.plan}
          onChange={handleInputChange}
          fullWidth
          margin="dense"
          InputProps={{ readOnly }}
          multiline
          rows={4}
        />
        {!readOnly && (
          <>
            {error && <Typography color="error">{error}</Typography>}
            <Button
              onClick={handleSubmit}
              color="primary"
              variant="contained"
              disabled={submitting}
            >
              {submitting ? <CircularProgress size={24} /> : 'Submit Feedback'}
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default FeedbackView;

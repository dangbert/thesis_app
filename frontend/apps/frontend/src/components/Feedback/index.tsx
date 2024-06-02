import React, { useState } from 'react';
import {
  Typography,
  TextField,
  Button,
  CircularProgress,
  Checkbox,
  Box,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Paper,
} from '@mui/material';

import {
  FeedbackPublic,
  FeedbackData,
  FeedbackCreate,
  AssignmentPublic,
  EvalMetrics,
} from '../../models';
import * as courseApi from '../../api';
import { useUserContext } from '../../providers';
import EvalControls from './EvalControls';

import { FEEDBACK_MAX_ROWS, FEEDBACK_MIN_ROWS } from '../../constants';

interface FeedbackViewProps {
  attemptId: string;
  asData: AssignmentPublic;
  priorFeedback?: FeedbackPublic; // existing feedback (if any)
  readOnly: boolean;
  isTeacher: boolean;
  onClose: () => void;
  onCreate?: (feedback: FeedbackPublic) => void;
}

/**
 * View or create feedback on an Attempt.
 */
const FeedbackView: React.FC<FeedbackViewProps> = ({
  attemptId,
  asData,
  priorFeedback,
  readOnly,
  isTeacher,
  onClose,
  onCreate,
}) => {
  const DEFAULT_FEEDBACK: FeedbackData = {
    // default to provided feedback (e.g. if using AI feedback as starting point)
    feedback: priorFeedback?.data.feedback || '',
    other_comments: '',
    approved: false,
    score: null,
    eval_metrics: null,
  };

  const [feedbackData, setFeedbackData] = useState<FeedbackData>(
    priorFeedback?.data || DEFAULT_FEEDBACK
  );
  // when to make the approve button blank...
  const [needsApprovalResponse, setNeedsApprovalResponse] = useState<boolean>(
    !readOnly
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

  const handleEvalChange = (evalData: EvalMetrics) => {
    setFeedbackData((prev) => ({
      ...prev,
      eval_metrics: evalData,
    }));
  };

  const handleSubmit = async () => {
    if (!userCtx.user) {
      setError('User not logged in');
      return;
    }
    setSubmitting(true);
    setError('');
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

  let canSubmit =
    !submitting &&
    feedbackData.feedback.trim() !== '' &&
    !needsApprovalResponse;

  if (asData.scorable && feedbackData.score === undefined) {
    canSubmit = false;
  }

  let approvalStr = feedbackData.approved ? 'approve' : 'resubmit';
  if (needsApprovalResponse) approvalStr = ''; // make the button blank

  return (
    <>
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
        maxRows={FEEDBACK_MAX_ROWS + 2}
        variant={readOnly ? 'filled' : 'outlined'}
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
        minRows={2}
        maxRows={FEEDBACK_MAX_ROWS}
        variant={readOnly ? 'filled' : 'outlined'}
      />

      <br />
      <br />
      <Paper variant="outlined" style={{ padding: '14px' }}>
        <FormControl component="fieldset">
          <FormLabel component="legend">Goal/Plan:</FormLabel>
          <RadioGroup
            row
            name="goal"
            value={approvalStr}
            onChange={(event) => {
              if (readOnly) return;
              setNeedsApprovalResponse(false);
              setFeedbackData((prev) => ({
                ...prev,
                approved: event.target.value === 'approve',
              }));
            }}
          >
            <FormControlLabel
              value="approve"
              control={<Radio />}
              label="Approved"
              // disabled={readOnly}
            />
            <FormControlLabel
              value="resubmit"
              control={<Radio />}
              label="Needs resubmission"
              // disabled={readOnly}
            />
          </RadioGroup>
        </FormControl>

        <br />
        {/* Reflection Score Section */}
        {asData.scorable && (
          <FormControl component="fieldset">
            <FormLabel component="legend">Reflection Score:</FormLabel>
            <RadioGroup
              row
              name="score"
              value={feedbackData.score?.toString() || ''}
              onChange={(event) => {
                if (readOnly) return;
                setFeedbackData((prev) => ({
                  ...prev,
                  score: parseInt(event.target.value),
                }));
              }}
            >
              {[0, 1, 2, 3].map((score) => (
                <FormControlLabel
                  key={score}
                  // disabled={readOnly}
                  value={score.toString()}
                  control={<Radio />}
                  label={score.toString()}
                />
              ))}
            </RadioGroup>
          </FormControl>
        )}
      </Paper>

      {isTeacher && (
        <EvalControls
          evalData={feedbackData.eval_metrics || ({} as EvalMetrics)}
          onChange={handleEvalChange}
          readOnly={readOnly}
        />
      )}

      {error && <Typography color="error">{error}</Typography>}
      <Box display="flex" justifyContent="flex-end" mt={2}>
        <Button onClick={onClose} color="primary">
          {readOnly ? 'Close' : 'Cancel'}
        </Button>
        {!readOnly && (
          <Button onClick={handleSubmit} color="primary" disabled={!canSubmit}>
            {submitting ? <CircularProgress size={24} /> : 'Submit Feedback'}
          </Button>
        )}
      </Box>
    </>
  );
};

export default FeedbackView;

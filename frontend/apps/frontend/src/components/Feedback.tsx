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
} from '@mui/material';
import {
  FeedbackPublic,
  FeedbackData,
  FeedbackCreate,
  AssignmentPublic,
} from '../models';
import * as courseApi from '../api/courses';
import { useUserContext } from '../providers';

import { FEEDBACK_MAX_ROWS, FEEDBACK_MIN_ROWS } from '../constants';

interface FeedbackViewProps {
  attemptId: string;
  asData: AssignmentPublic;
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
  asData,
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

  let canSubmit =
    !submitting &&
    feedbackData.feedback.trim() !== '' &&
    !needsApprovalResponse;

  if (asData.scorable && feedbackData.score === undefined) {
    canSubmit = false;
  }

  let approvalStr = feedbackData.approved ? 'approve' : 'resubmit';
  if (needsApprovalResponse) approvalStr = ''; // make the button blank

  console.log(`approvalStr = ${approvalStr}`);
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

      <br />
      <br />
      <FormControl component="fieldset">
        <FormLabel component="legend">Goal/Plan:</FormLabel>
        <RadioGroup
          row
          name="goal"
          value={approvalStr}
          onChange={(event) => {
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
            label="Approve"
          />
          <FormControlLabel
            value="resubmit"
            control={<Radio />}
            label="Needs resubmission"
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
            onChange={(event) =>
              setFeedbackData((prev) => ({
                ...prev,
                score: parseInt(event.target.value),
              }))
            }
          >
            <FormControlLabel value="0" control={<Radio />} label="0" />
            <FormControlLabel value="1" control={<Radio />} label="1" />
            <FormControlLabel value="2" control={<Radio />} label="2" />
            <FormControlLabel value="3" control={<Radio />} label="3" />
          </RadioGroup>
        </FormControl>
      )}

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

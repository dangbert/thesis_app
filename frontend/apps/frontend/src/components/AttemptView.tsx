import React from 'react';
import {
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  Grid,
  Box,
} from '@mui/material';
import FeedbackView from './Feedback'; // Make sure this component is properly imported
import { FIELD_ROWS } from './AttemptCreateModal';

import * as models from '../models';
import * as constants from '../constants';

interface AttemptViewProps {
  attempt: models.AttemptPublic;
  open: boolean;
  onClose: () => void;
  onCreateFeedback?: (feedback: models.FeedbackPublic) => void;
  mode: 'view' | 'createFeedback';
  feedback?: models.FeedbackPublic;
}

const AttemptView: React.FC<AttemptViewProps> = ({
  attempt,
  open,
  onClose,
  onCreateFeedback,
  mode,
  feedback,
}) => {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      aria-labelledby="attempt-view-title"
      fullWidth={true}
      maxWidth="xl"
      // PaperProps={{ style: { minHeight: '70vh' } }}
    >
      <DialogContent>
        <Grid container spacing={2}>
          <Grid
            item
            xs={12}
            md={6}
            style={{
              paddingRight: 16,
            }}
          >
            <Typography variant="h6" gutterBottom>
              Attempt Details
            </Typography>
            <TextField
              label="SMART Goal"
              value={attempt.data.goal}
              fullWidth
              margin="dense"
              InputProps={{ readOnly: true }}
              // disabled={true}
              multiline
              minRows={constants.ATTEMPT_MIN_ROWS}
              maxRows={constants.ATTEMPT_MAX_ROWS}
            />
            <TextField
              label="Action Plan"
              value={attempt.data.plan}
              fullWidth
              margin="dense"
              InputProps={{ readOnly: true }}
              // disabled={true}
              multiline
              minRows={constants.ATTEMPT_MIN_ROWS}
              maxRows={constants.ATTEMPT_MAX_ROWS}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="h6" gutterBottom>
              Feedback
            </Typography>
            {mode === 'view' ? (
              feedback ? (
                <FeedbackView
                  attemptId={attempt.id}
                  feedback={feedback}
                  readOnly={true}
                  onClose={onClose}
                />
              ) : (
                <Typography>No feedback available yet.</Typography>
              )
            ) : (
              <FeedbackView
                attemptId={attempt.id}
                feedback={feedback}
                readOnly={false}
                onClose={onClose}
                onCreate={onCreateFeedback}
              />
            )}
          </Grid>
        </Grid>
      </DialogContent>
    </Dialog>
  );
};

export default AttemptView;

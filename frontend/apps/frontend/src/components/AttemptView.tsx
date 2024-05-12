import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  useTheme,
  useMediaQuery,
  Grid,
} from '@mui/material';
import FeedbackView from './Feedback'; // Make sure to create this component

import * as models from '../models';

interface AttemptViewProps {
  attempt: models.AttemptPublic;
  open: boolean;
  onClose: () => void;
  mode: 'view' | 'createFeedback';
  feedback?: models.FeedbackPublic;
}

const AttemptView: React.FC<AttemptViewProps> = ({
  attempt,
  open,
  onClose,
  mode,
  feedback,
}) => {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('lg'));

  return (
    <Dialog
      open={open}
      onClose={onClose}
      aria-labelledby="attempt-view-title"
      fullWidth={true}
      maxWidth="md"
    >
      <DialogTitle id="attempt-view-title">Attempt Details</DialogTitle>
      <DialogContent>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              label="SMART Goal"
              value={attempt.data.goal}
              fullWidth
              margin="dense"
              InputProps={{ readOnly: true }}
              multiline
              rows={4}
            />
            <TextField
              label="Action Plan"
              value={attempt.data.plan}
              fullWidth
              margin="dense"
              InputProps={{ readOnly: true }}
              multiline
              rows={4}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            {mode === 'view' ? (
              feedback ? (
                <FeedbackView
                  attemptId={attempt.id}
                  feedback={feedback}
                  readOnly={true}
                />
              ) : (
                <div>No feedback available yet.</div>
              )
            ) : (
              <FeedbackView
                attemptId={attempt.id}
                feedback={feedback}
                readOnly={false}
              />
            )}
          </Grid>
        </Grid>
      </DialogContent>
    </Dialog>
  );
};

export default AttemptView;

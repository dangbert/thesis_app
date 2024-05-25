import React from 'react';
import {
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  Grid,
  List,
  ListItem,
  Alert,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import FeedbackView from './Feedback';
import FileView from './Files';

import * as models from '../models';
import * as constants from '../constants';

interface AttemptViewProps {
  attempt: models.AttemptPublic;
  asData: models.AssignmentPublic;
  open: boolean;
  onClose: () => void;
  onCreateFeedback?: (feedback: models.FeedbackPublic) => void;
  mode: 'view' | 'createFeedback';
  feedback?: models.FeedbackPublic;
}

const AttemptView: React.FC<AttemptViewProps> = ({
  attempt,
  asData,
  open,
  onClose,
  onCreateFeedback,
  mode,
  feedback,
}) => {
  const canCreateFeedback = mode === 'createFeedback' && !feedback;
  return (
    <Dialog
      open={open}
      onClose={onClose}
      aria-labelledby="attempt-view"
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

            <br />
            <br />
            <Typography variant="subtitle1" gutterBottom>
              File Attachments ({attempt.files.length}):
            </Typography>
            {attempt.files.length === 0 && (
              <Typography sx={{ fontStyle: 'italic' }}>
                No files attached.
              </Typography>
            )}
            <List dense>
              {attempt.files.map((file, index) => (
                <ListItem key={index}>
                  <FileView filename={file.filename} read_url={file.read_url} />
                </ListItem>
              ))}
            </List>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="h6" gutterBottom>
              {canCreateFeedback ? 'Create Feedback' : 'View Feedback'}
            </Typography>
            {mode === 'view' ? (
              feedback ? (
                <FeedbackView
                  attemptId={attempt.id}
                  asData={asData}
                  feedback={feedback}
                  readOnly={true}
                  onClose={onClose}
                />
              ) : (
                <>
                  <Alert severity="info">
                    No feedback available yet, stay tuned...
                  </Alert>
                </>
              )
            ) : (
              <FeedbackView
                attemptId={attempt.id}
                asData={asData}
                feedback={feedback}
                readOnly={!canCreateFeedback}
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

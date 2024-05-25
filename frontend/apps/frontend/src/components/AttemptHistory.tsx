import React, { useState, useEffect } from 'react';
import { Paper, Typography, Button, Snackbar } from '@mui/material';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineDot,
  TimelineConnector,
  TimelineContent,
} from '@mui/lab';
import TimelineOppositeContent, {
  timelineOppositeContentClasses,
} from '@mui/lab/TimelineOppositeContent';
import { friendlyDate } from '../utils';
import AttemptView from './AttemptView';
import * as models from '../models';
import * as constants from '../constants';

interface AttemptHistoryProps {
  attempts: models.AttemptPublic[]; // Now receives an array of attempts
  asData: models.AssignmentPublic;
  isInstructor: boolean;
}

const AttemptHistory: React.FC<AttemptHistoryProps> = ({
  attempts,
  asData,
  isInstructor,
}) => {
  const [viewAttemptIdx, setViewAttemptIdx] = useState(-1);
  const [snackbarTxt, setSnackbarTxt] = useState('');

  console.log('history attempts', attempts);
  return (
    <>
      <Snackbar
        open={snackbarTxt !== ''}
        autoHideDuration={constants.SNACKBAR_DUR_MS}
        onClose={() => setSnackbarTxt('')}
        message={snackbarTxt}
      />
      {attempts.length > 0 &&
        viewAttemptIdx > -1 &&
        viewAttemptIdx < attempts.length && (
          <AttemptView
            attempt={attempts[viewAttemptIdx]}
            asData={asData}
            open={true}
            onClose={() => setViewAttemptIdx(-1)}
            mode={isInstructor ? 'createFeedback' : 'view'}
            onCreateFeedback={(feedback: models.FeedbackPublic) => {
              setSnackbarTxt('Feedback submitted ✅');
              setViewAttemptIdx(-1);
            }}
          />
        )}
      <Timeline
        // position="left"
        sx={{
          [`& .${timelineOppositeContentClasses.root}`]: {
            flex: 0.3,
          },
        }}
      >
        {/* iterate backwards so newest attempts are at top of page */}
        {attempts
          .slice(0)
          .reverse()
          .map((attempt, attemptIndex) => {
            const realIndex = attempts.length - attemptIndex - 1;

            return (
              <React.Fragment key={attempt.id}>
                {/* Timeline for each Attempt */}
                <TimelineItem>
                  <TimelineOppositeContent color="textSecondary">
                    {friendlyDate(attempt.created_at)}
                  </TimelineOppositeContent>
                  <TimelineSeparator>
                    <TimelineDot color="primary" />
                    {attemptIndex < attempts.length - 1 && (
                      <TimelineConnector />
                    )}
                  </TimelineSeparator>
                  <TimelineContent>
                    <Paper elevation={3} style={{ padding: '6px 16px' }}>
                      <Typography variant="h6" component="h1">
                        Submission {realIndex + 1}
                      </Typography>
                      <Typography>
                        Created at:{' '}
                        {new Date(attempt.created_at).toLocaleString()}
                      </Typography>
                      <Button
                        variant="outlined"
                        style={{ marginTop: '8px' }}
                        onClick={() => setViewAttemptIdx(realIndex)}
                      >
                        View
                      </Button>
                    </Paper>
                  </TimelineContent>
                </TimelineItem>

                {/* Timeline for each feedback entry within the attempt */}
                {/* {attempt.feedback.map((feedback: FeedbackPublic, index: number) => (
            <TimelineItem key={feedback.id}>
              <TimelineSeparator>
                <TimelineDot
                  color={feedback.data.approved ? 'secondary' : 'grey'}
                />
                {index < attempt.feedback.length - 1 ||
                  (attemptIndex < attempts.length - 1 && <TimelineConnector />)}
              </TimelineSeparator>
              <TimelineContent>
                <Paper elevation={3} style={{ padding: '6px 16px' }}>
                  <Typography variant="h6" component="h1">
                    {feedback.data.approved
                      ? 'Feedback Approved'
                      : 'Feedback Pending'}
                  </Typography>
                  <Typography>
                    Feedback from{' '}
                    {new Date(feedback.created_at).toLocaleString()}
                  </Typography>
                  <Typography variant="body2">
                    {feedback.data.feedback}
                  </Typography>
                  {feedback.data.approved && (
                    <Typography color="secondary">Approval received</Typography>
                  )}
                </Paper>
              </TimelineContent>
            </TimelineItem>
          ))} */}
              </React.Fragment>
            );
          })}
      </Timeline>
    </>
  );
};

export default AttemptHistory;

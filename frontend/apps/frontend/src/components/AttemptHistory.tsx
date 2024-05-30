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
  isTeacher: boolean;
  refreshAttempts: () => void;
}

const AttemptHistory: React.FC<AttemptHistoryProps> = ({
  attempts,
  asData,
  isTeacher,
  refreshAttempts,
}) => {
  const [viewAttemptIdx, setViewAttemptIdx] = useState(-1);
  const [snackbarTxt, setSnackbarTxt] = useState('');

  let curAttempt = undefined;
  let curFeedback = undefined;
  if (
    attempts.length > 0 &&
    viewAttemptIdx > -1 &&
    viewAttemptIdx < attempts.length
  ) {
    curAttempt = attempts[viewAttemptIdx];
    if (curAttempt.feedbacks.length > 0) {
      // TODO: get latest feedback (preferring human feedback if available)
      curFeedback = curAttempt.feedbacks[curAttempt.feedbacks.length - 1];
    }
  }

  return (
    <>
      <Snackbar
        open={snackbarTxt !== ''}
        autoHideDuration={constants.SNACKBAR_DUR_MS}
        onClose={() => setSnackbarTxt('')}
        message={snackbarTxt}
      />
      {curAttempt && (
        <AttemptView
          attempt={curAttempt}
          feedback={curFeedback}
          asData={asData}
          open={true}
          onClose={() => setViewAttemptIdx(-1)}
          mode={isTeacher && !curFeedback ? 'createFeedback' : 'view'}
          onCreateFeedback={(feedback: models.FeedbackPublic) => {
            setSnackbarTxt('Feedback submitted ✅');
            setViewAttemptIdx(-1);
            refreshAttempts();
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
            let status = isTeacher
              ? 'awaiting AI feedback'
              : 'awaiting teacher review';
            if (attempt.feedbacks.length > 0) {
              const hasHumanFeedback = attempt.feedbacks.some((x) => !x.is_ai);
              const hasAiFeedback = attempt.feedbacks.some((x) => x.is_ai);
              if (hasHumanFeedback) {
                status = 'feedback available';
              } else if (hasAiFeedback) {
                status = 'awaiting teacher review';
              }
            }

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
                        {attemptIndex === 0 ? ' (latest)' : ''}
                      </Typography>
                      {/* TODO: create a <FeedbackStatus> component with an icon (also for user table) */}
                      <Typography style={{ marginTop: '8px' }}>
                        Status: {status}
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

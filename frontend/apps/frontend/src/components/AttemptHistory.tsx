import React, { useState, useEffect } from 'react';
import { Paper, Typography, Button, Snackbar, Alert } from '@mui/material';
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
  let curHumanFeedback;
  let curAiFeedback;
  if (
    attempts.length > 0 &&
    viewAttemptIdx > -1 &&
    viewAttemptIdx < attempts.length
  ) {
    curAttempt = attempts[viewAttemptIdx];
    [curHumanFeedback, curAiFeedback] = splitAttemptFeedback(curAttempt);
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
          humanFeedback={curHumanFeedback}
          aiFeedback={curAiFeedback}
          asData={asData}
          open={true}
          onClose={() => setViewAttemptIdx(-1)}
          isTeacher={isTeacher}
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
            let mustResubmit = false;
            if (attempt.feedbacks.length > 0) {
              const [humanFeedback, aiFeedback] = splitAttemptFeedback(attempt);
              if (humanFeedback && !humanFeedback.data.approved)
                mustResubmit = true;
            }

            const isLatestAttempt = attemptIndex === 0;
            let publicStatus = attempt.status;
            if (
              publicStatus ===
                models.AssignmentAttemptStatus.AWAITING_AI_FEEDBACK &&
              !isTeacher
            ) {
              publicStatus =
                models.AssignmentAttemptStatus.AWAITING_TEACHER_FEEDBACK;
            }
            return (
              <React.Fragment key={attempt.id}>
                {/* Timeline for each Attempt */}
                <TimelineItem>
                  <TimelineOppositeContent color="textSecondary">
                    {friendlyDate(attempt.created_at)}
                  </TimelineOppositeContent>
                  <TimelineSeparator>
                    <TimelineDot color={isLatestAttempt ? 'primary' : 'grey'} />
                    {attemptIndex < attempts.length - 1 && (
                      <TimelineConnector />
                    )}
                  </TimelineSeparator>
                  <TimelineContent sx={{ opacity: isLatestAttempt ? 1 : 0.75 }}>
                    <Paper elevation={3} style={{ padding: '6px 16px' }}>
                      <Typography variant="h6" component="h1">
                        Submission {realIndex + 1}
                        {isLatestAttempt ? ' (latest)' : ''}
                      </Typography>
                      {/* TODO: create a <FeedbackStatus> component with an icon (also for user table) */}
                      <Typography style={{ marginTop: '8px' }}>
                        {isLatestAttempt &&
                          (mustResubmit ? (
                            <Alert
                              severity="warning"
                              style={{ marginTop: '8px' }}
                            >
                              <>
                                <b>Resubmission requested</b> (view feedback
                                below)
                              </>
                            </Alert>
                          ) : (
                            <b>{publicStatus}</b>
                          ))}
                        {!isLatestAttempt && `${publicStatus}`}
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
              </React.Fragment>
            );
          })}
      </Timeline>
    </>
  );
};

/**
 * Given an attempt return [humanFeedback, aiFeedback] (where either or both can be undefined).
 * Helps determinstically handle edge cause of multiple feedbacks of the same type (by taking the latest).
 */
function splitAttemptFeedback(attempt: models.AttemptPublic) {
  if (attempt.feedbacks.length === 0) return [undefined, undefined];

  const humanFeedbacks = attempt.feedbacks.filter((x) => !x.is_ai);
  const aiFeedbacks = attempt.feedbacks.filter((x) => x.is_ai);

  return [humanFeedbacks.at(-1), aiFeedbacks.at(-1)];
}

export default AttemptHistory;

import React from 'react';
import { Paper, Typography, Button } from '@mui/material';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineDot,
  TimelineConnector,
  TimelineContent,
} from '@mui/lab';
import { AttemptPublic, FeedbackPublic } from '../models';

interface AttemptHistoryProps {
  attempts: AttemptPublic[]; // Now receives an array of attempts
}

const AttemptHistory: React.FC<AttemptHistoryProps> = ({ attempts }) => {
  return (
    <Timeline position="alternate">
      {attempts.map((attempt, attemptIndex) => (
        <React.Fragment key={attempt.id}>
          {/* Timeline for each Attempt */}
          <TimelineItem>
            <TimelineSeparator>
              <TimelineDot color="primary" />
              {attempt.feedback.length > 0 && <TimelineConnector />}
            </TimelineSeparator>
            <TimelineContent>
              <Paper elevation={3} style={{ padding: '6px 16px' }}>
                <Typography variant="h6" component="h1">
                  Submission {attempt.id}
                </Typography>
                <Typography>
                  Created at: {new Date(attempt.created_at).toLocaleString()}
                </Typography>
                <Button variant="outlined" style={{ marginTop: '8px' }}>
                  View
                </Button>
              </Paper>
            </TimelineContent>
          </TimelineItem>

          {/* Timeline for each feedback entry within the attempt */}
          {attempt.feedback.map((feedback: FeedbackPublic, index: number) => (
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
          ))}
        </React.Fragment>
      ))}
    </Timeline>
  );
};

export default AttemptHistory;

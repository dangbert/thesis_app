import { Paper, Typography } from '@mui/material';
import * as models from '../../models';
import { LikertStars, MultiSelect } from './FormHelpers';
import { isUndefined } from '../../utils';

const PROBLEM_CHOICES = [
  'Accuracy/relevance',
  'Feedback style/tone',
  'Structure',
  'Grammar',
  'Too wordy',
  'Too short',
  'Other',
];

interface EvalControlsProps {
  evalData: models.EvalMetrics;
  onChange: (evalData: models.EvalMetrics) => void;
  readOnly: boolean;
}

/**
 * Form controls for teacher to optionally critique the AI feedback (for research purposes).
 */
const EvalControls: React.FC<EvalControlsProps> = ({
  evalData,
  onChange,
  readOnly,
}) => {
  return (
    <Paper variant="outlined" style={{ padding: '14px', marginTop: '7px' }}>
      <Typography variant="h6">AI Feedback Evaluation</Typography>
      <LikertStars
        title="Overall Quality"
        value={evalData.rating || undefined}
        readOnly={readOnly}
        setValue={(newRating) => {
          onChange({ ...evalData, rating: newRating || null });
        }}
      />

      <br />
      <MultiSelect
        title={
          readOnly ? 'AI Feedback Problems' : 'Select all AI Feedback Problems'
        }
        choices={PROBLEM_CHOICES}
        readOnly={readOnly}
        selected={
          isUndefined(evalData.problems)
            ? undefined
            : (evalData.problems as string[])
        }
        setSelected={(newProblems) => {
          onChange({ ...evalData, problems: newProblems || null });
        }}
      />
    </Paper>
  );
};

export default EvalControls;

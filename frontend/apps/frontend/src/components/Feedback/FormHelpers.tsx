import * as React from 'react';
import Rating from '@mui/material/Rating';
import Box from '@mui/material/Box';
import StarIcon from '@mui/icons-material/Star';
import { Theme, useTheme } from '@mui/material/styles';
import OutlinedInput from '@mui/material/OutlinedInput';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import Chip from '@mui/material/Chip';

const STAR_LABELS: { [index: string]: string } = {
  1: 'Very dissatisfied',
  2: 'Dissatisfied',
  3: 'Unsure',
  4: 'Satisfied',
  5: 'Very satisfied',
};

function getLabelText(value: number) {
  return `${value} Star${value !== 1 ? 's' : ''}, ${STAR_LABELS[value]}`;
}

interface LikertStarsProps {
  value?: number;
  setValue(value?: number): void;
  readOnly: boolean;
}

// https://mui.com/material-ui/react-rating/#hover-feedback

export const LikertStars: React.FC<LikertStarsProps> = ({
  value,
  setValue,
  readOnly,
}) => {
  const [hover, setHover] = React.useState(-1);

  // const curLabel = STAR_LABELS.hasOwnProperty(value || '') ? STAR_LABELS[value] : '';
  // let curLabel = 'not specified';
  // if (value !== undefined && value in STAR_LABELS) {
  //   curLabel = STAR_LABELS[value];
  // }
  const curLabel =
    value !== undefined
      ? STAR_LABELS[value] ?? 'Not specified'
      : 'Not specified';
  console.log(`value=${value}`);

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
      }}
    >
      <Rating
        name="hover-feedback"
        value={value}
        precision={1.0}
        getLabelText={getLabelText}
        readOnly={readOnly}
        onChange={(event, newValue) => {
          setValue(newValue || undefined);
        }}
        onChangeActive={(event, newHover) => {
          setHover(newHover);
        }}
        emptyIcon={<StarIcon style={{ opacity: 0.55 }} fontSize="inherit" />}
      />
      {value !== null && <Box sx={{ ml: 2 }}>{curLabel}</Box>}
    </Box>
  );
};

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
  PaperProps: {
    style: {
      maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
      width: 250,
    },
  },
};

const SELECTION_OPTIONS = ['Grammar', 'Assignment Relevance', ''];

function getStyles(name: string, personName: readonly string[], theme: Theme) {
  return {
    fontWeight:
      personName.indexOf(name) === -1
        ? theme.typography.fontWeightRegular
        : theme.typography.fontWeightMedium,
  };
}

export function MultipleSelectChip() {
  const theme = useTheme();
  const [personName, setPersonName] = React.useState<string[]>([]);

  const handleChange = (event: SelectChangeEvent<typeof personName>) => {
    const {
      target: { value },
    } = event;
    setPersonName(
      // On autofill we get a stringified value.
      typeof value === 'string' ? value.split(',') : value
    );
  };

  return (
    <div>
      <FormControl sx={{ m: 1, width: 300 }}>
        <InputLabel id="demo-multiple-chip-label">
          Select all AI Feedback Problems
        </InputLabel>
        <Select
          labelId="demo-multiple-chip-label"
          id="demo-multiple-chip"
          multiple
          value={personName}
          onChange={handleChange}
          input={<OutlinedInput id="select-multiple-chip" label="Chip" />}
          renderValue={(selected) => (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {selected.map((value) => (
                <Chip key={value} label={value} />
              ))}
            </Box>
          )}
          MenuProps={MenuProps}
        >
          {SELECTION_OPTIONS.map((name) => (
            <MenuItem
              key={name}
              value={name}
              style={getStyles(name, personName, theme)}
            >
              {name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </div>
  );
}

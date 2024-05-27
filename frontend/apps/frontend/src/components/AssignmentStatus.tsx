import React from 'react';
import { useEffect, useState } from 'react';
import {
  Snackbar,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TableSortLabel,
  Toolbar,
  Typography,
  Paper,
  Checkbox,
  IconButton,
  Tooltip,
  FormControlLabel,
  Switch,
  Box,
} from '@mui/material';
import { visuallyHidden } from '@mui/utils';
import { alpha } from '@mui/material/styles';
import DeleteIcon from '@mui/icons-material/Delete';
import FilterListIcon from '@mui/icons-material/FilterList';
import { LoadingButton } from '@mui/lab';

import AttemptCreateModal from './AttemptCreateModal';
import AttemptView from './AttemptView';
import AttemptHistory from './AttemptHistory';
import Markdown from 'react-markdown';

import { AssignmentPublic } from '../models';
import * as models from '../models';
import * as API from '../api';
import * as constants from '../constants';
import { useUserContext } from '../providers';

interface AssignmentStatusProps {
  asData: AssignmentPublic;
  // dueDate: string;
}

function descendingComparator<T>(a: T, b: T, orderBy: keyof T) {
  if (b[orderBy] < a[orderBy]) {
    return -1;
  }
  if (b[orderBy] > a[orderBy]) {
    return 1;
  }
  return 0;
}

function getComparator<Key extends keyof any>(
  order: Order,
  orderBy: Key
): (
  a: { [key in Key]: number | string },
  b: { [key in Key]: number | string }
) => number {
  return order === 'desc'
    ? (a, b) => descendingComparator(a, b, orderBy)
    : (a, b) => -descendingComparator(a, b, orderBy);
}

type Order = 'asc' | 'desc';

interface RowData {
  id: string; // user id
  name: string;
  email: string;
  group: number;
  submissions: number;
  status: string;
  role: string;
}

interface HeadCell {
  disablePadding: boolean;
  id: keyof RowData;
  label: string;
  numeric: boolean;
}

const headCells: readonly HeadCell[] = [
  {
    id: 'name',
    numeric: false,
    disablePadding: true,
    label: 'Name',
  },
  {
    id: 'email',
    numeric: false,
    disablePadding: false,
    label: 'Email',
  },
  {
    id: 'group',
    numeric: true,
    disablePadding: false,
    label: 'Group',
  },
  {
    id: 'role',
    numeric: false,
    disablePadding: false,
    label: 'role',
  },
  {
    id: 'submissions',
    numeric: true,
    disablePadding: false,
    label: 'Submissions',
  },
  {
    id: 'status',
    numeric: false,
    disablePadding: false,
    label: 'Assignment Status',
  },
];

interface EnhancedTableProps {
  onRequestSort: (
    event: React.MouseEvent<unknown>,
    property: keyof RowData
  ) => void;
  order: Order;
  orderBy: string;
  rowCount: number;
}

// https://mui.com/material-ui/react-table/#sorting-amp-selecting
function EnhancedTableHead(props: EnhancedTableProps) {
  const { order, orderBy, rowCount, onRequestSort } = props;
  const createSortHandler =
    (property: keyof RowData) => (event: React.MouseEvent<unknown>) => {
      onRequestSort(event, property);
    };

  return (
    <TableHead>
      <TableRow>
        {headCells.map((headCell) => (
          <TableCell
            key={headCell.id}
            // align={headCell.numeric ? 'right' : 'left'}
            align={'left'}
            padding={headCell.disablePadding ? 'none' : 'normal'}
            sortDirection={orderBy === headCell.id ? order : false}
          >
            <TableSortLabel
              active={orderBy === headCell.id}
              direction={orderBy === headCell.id ? order : 'asc'}
              onClick={createSortHandler(headCell.id)}
            >
              {headCell.label}
              {orderBy === headCell.id ? (
                <Box component="span" sx={visuallyHidden}>
                  {order === 'desc' ? 'sorted descending' : 'sorted ascending'}
                </Box>
              ) : null}
            </TableSortLabel>
          </TableCell>
        ))}
      </TableRow>
    </TableHead>
  );
}

const AssignmentStatus: React.FC<AssignmentStatusProps> = ({ asData }) => {
  const [statusData, setStatusData] = useState<
    models.AssignmentStudentStatus[]
  >([]);
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [reloadTime, setReloadTime] = useState<number>(Date.now() / 1000);
  const userCtx = useUserContext();

  useEffect(() => {
    let cancel = false;
    (async () => {
      if (!userCtx.user) return;
      console.log(`requesting assignment status ${asData.id}`);

      setLoading(true);
      const res = await API.getAssignmentStatus(asData.course_id, asData.id);
      if (cancel) return;
      if (res.error) {
        console.error(res.error);
        setStatusData([]);
      } else {
        setStatusData(res.data);
      }
      setLoading(false);

      return () => (cancel = true);
    })();
  }, [asData.id, userCtx.user?.id, reloadTime]);

  const [order, setOrder] = React.useState<Order>('asc');
  const [orderBy, setOrderBy] = React.useState<keyof RowData>('name');
  const [page, setPage] = React.useState(0);
  const [dense, setDense] = React.useState(false);
  const [rowsPerPage, setRowsPerPage] = React.useState(100);

  const rows = statusData.map((s) => ({
    id: s.student.id,
    name: s.student.name,
    email: s.student.email,
    role: s.role,
    group: -1, // TODO todo for now
    submissions: s.attempt_count,
    status: s.status,
  }));

  const handleRequestSort = (
    event: React.MouseEvent<unknown>,
    property: keyof RowData
  ) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleChangeDense = (event: React.ChangeEvent<HTMLInputElement>) => {
    setDense(event.target.checked);
  };

  // Avoid a layout jump when reaching the last page with empty rows.
  const emptyRows =
    page > 0 ? Math.max(0, (1 + page) * rowsPerPage - rows.length) : 0;

  const visibleRows = React.useMemo(
    () =>
      rows
        .slice()
        .sort(getComparator(order, orderBy))
        .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage),
    [JSON.stringify(statusData), order, orderBy, page, rowsPerPage]
  );

  // TODO: use MIT DataGrid! https://mui.com/x/react-data-grid/#mit-version-free-forever
  if (!userCtx.user) return null;
  return (
    <div>
      {error && <Alert severity="error">{error}</Alert>}
      <Box sx={{ width: '100%' }}>
        <Paper sx={{ width: '100%', mb: 2 }}>
          <Toolbar
            sx={{
              pl: { sm: 2 },
              pr: { xs: 1, sm: 1 },
            }}
          >
            <Typography
              sx={{ flex: '1 1 100%' }}
              variant="h6"
              id="tableTitle"
              component="div"
            >
              Course Members
            </Typography>
            <>
              <Tooltip title="Filter list">
                <IconButton>
                  <FilterListIcon />
                </IconButton>
              </Tooltip>

              <Tooltip title="Filter list">
                <span>
                  <LoadingButton
                    onClick={() => setReloadTime(Date.now() / 1000)}
                    color="primary"
                    loading={loading}
                    disabled={loading}
                  >
                    Refresh Table
                  </LoadingButton>
                </span>
              </Tooltip>
            </>
          </Toolbar>
          <TableContainer>
            <Table
              sx={{ minWidth: 750 }}
              aria-labelledby="tableTitle"
              size={dense ? 'small' : 'medium'}
              stickyHeader
            >
              <EnhancedTableHead
                order={order}
                orderBy={orderBy}
                onRequestSort={handleRequestSort}
                rowCount={rows.length}
              />
              <TableBody>
                {visibleRows.map((row, index) => {
                  return (
                    <TableRow
                      hover
                      tabIndex={-1}
                      key={row.id}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell align="left">{row.name}</TableCell>
                      <TableCell align="left">
                        <a href={'mailto:' + row.email}>{row.email}</a>
                      </TableCell>
                      <TableCell align="left">{row.group}</TableCell>
                      <TableCell align="left">{row.role}</TableCell>
                      <TableCell align="left">{row.submissions}</TableCell>
                      <TableCell align="left">{row.status}</TableCell>
                    </TableRow>
                  );
                })}
                {emptyRows > 0 && (
                  <TableRow
                    style={{
                      height: (dense ? 33 : 53) * emptyRows,
                    }}
                  >
                    <TableCell colSpan={6} />
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={rows.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </Paper>
        <FormControlLabel
          control={<Switch checked={dense} onChange={handleChangeDense} />}
          label="Dense padding"
        />
      </Box>
    </div>
  );
};

export default AssignmentStatus;

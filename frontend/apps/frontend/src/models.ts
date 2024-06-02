/**
 * Date fields as shown in backend/app/models/base.py:Base
 */
interface BaseFields {
  id: string;
  created_at: string;
  updated_at: string | null;
}

/* must match backend/app/hardcoded.py */
export interface SMARTData {
  goal: string;
  plan: string;
}

export interface FeedbackData {
  feedback: string;
  other_comments: string | null;
  approved: boolean;
  score: number | null;
  metrics: EvalMetrics | null;
}

export interface EvalMetrics {
  problems: string[];
  rating: number;
}

/* must match backend/app/models/schemas.py */
export interface UserPublic extends BaseFields {
  sub: string;
  name: string;
  email: string;
  // TODO: store in DB
  picture?: string | null;
}

export enum CourseRole {
  STUDENT = 'student',
  TEACHER = 'teacher',
}

export interface CourseCreate {
  name: string;
  about: string;
}

export interface CoursePublic extends CourseCreate, BaseFields {
  your_role: CourseRole | null;
  invite_role: CourseRole | null;
  your_group: number | null;
}

export interface AssignmentCreate {
  name: string;
  about: string;
  scorable: boolean;
}

export interface AssignmentPublic extends AssignmentCreate, BaseFields {
  course_id: string;
}

export interface AttemptCreate {
  assignment_id: string;
  /* eslint-disable  @typescript-eslint/no-explicit-any */
  data: SMARTData; // | { [key: string]: any };
  file_ids: string[];
}

export interface AttemptPublic extends BaseFields {
  assignment_id: string;
  user_id: string;
  data: SMARTData;
  feedbacks: FeedbackPublic[];
  files: FilePublic[];
  status: AssignmentAttemptStatus;
}

export enum AssignmentAttemptStatus {
  NOT_STARTED = 'not started',
  AWAITING_AI_FEEDBACK = 'awaiting AI feedback',
  AWAITING_TEACHER_FEEDBACK = 'awaiting teacher feedback',
  RESUBMISSION_REQUESTED = 'resubmission requested',
  COMPLETE = 'complete',
}

export interface AssignmentStudentStatus {
  student: UserPublic;
  role: CourseRole;
  group_num: number | null;
  attempt_count: number;
  last_attempt_date: string | null;
  status: AssignmentAttemptStatus;
}

export interface FilePublic extends BaseFields {
  filename: string;
  read_url: string;
}

export interface FeedbackCreate {
  attempt_id: string;
  data: FeedbackData;
}

export interface FeedbackPublic extends BaseFields {
  attempt_id: string;
  user_id: string | null;
  is_ai: boolean;
  data: FeedbackData;
}

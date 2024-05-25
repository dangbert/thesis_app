/**
 * Date fields as shown in backend/app/models/base.py:Base
 */
interface BaseFields {
  id: string;
  created_at: string;
  updated_at?: string; // TODO: maybe should be string | null
}

/* must match backend/app/hardcoded.py */
export interface SMARTData {
  goal: string;
  plan: string;
}

export interface FeedbackData {
  feedback: string;
  other_comments?: string;
  approved: boolean;
  score?: number;
  metrics?: EvalMetrics;
}

export interface EvalMetrics {
  problems: string[];
}

/* must match backend/app/models/schemas.py */
export interface UserPublic extends BaseFields {
  sub: string;
  name: string;
  email: string;
  // TODO: store in DB
  picture?: string;
}

export interface CourseCreate {
  name: string;
  about: string;
}

export interface CoursePublic extends CourseCreate, BaseFields {}

export interface AssignmentCreate {
  name: string;
  about: string;
  scorable: boolean;
}

export interface AssignmentPublic extends AssignmentCreate, BaseFields {}

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
  user_id?: string;
  is_ai: boolean;
  data: FeedbackData;
}

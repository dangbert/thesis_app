/**
 * Date fields as shown in backend/app/models/base.py:Base
 */
interface DateFields {
  created_at: string;
  updated_at?: string;
}

/* must match backend/app/hardcoded.py */
export interface SMARTData {
  goal: string;
  plan: string;
}

export interface FeedbackData {
  feedback: string;
  plan: string;
}

/* must match backend/app/models/user.py */
export interface UserPublic extends DateFields {
  sub: string;
  name: string;
  email: string;
  id: string;
}

/* must match backend/app/models/course_partials.py */

export interface CourseCreate {
  name: string;
  about: string;
}

export interface CoursePublic extends CourseCreate, DateFields {
  id: string;
}

export interface AssignmentCreate {
  name: string;
  about: string;
}

export interface AssignmentPublic extends AssignmentCreate, DateFields {
  id: string;
}

export interface AttemptCreate {
  assignment_id: string;
  // TODO: no need to store user_id it should be in the cookie
  user_id: string;
  /* eslint-disable  @typescript-eslint/no-explicit-any */
  data: SMARTData | { [key: string]: any };
}

export interface AttemptPublic extends AttemptCreate, DateFields {
  id: string;
  feedback: FeedbackPublic[];
}

export interface FilePublic extends DateFields {
  id: string;
  filename: string;
  read_url: string;
}

export interface FeedbackPublic extends DateFields {
  id: string;
  attempt_id: string;
  user_id?: string;
  is_ai: boolean;
  data: FeedbackData;
}

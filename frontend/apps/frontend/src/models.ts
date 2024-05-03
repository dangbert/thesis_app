/* must match backend/app/hardcoded.py */
export interface SMARTData {
  goal: string;
  plan: string;
}

/* must match backend/app/models/course_partials.py */

export interface CourseCreate {
  name: string;
  about: string;
}

export interface CoursePublic extends CourseCreate {
  id: string;
}

export interface AssignmentCreate {
  name: string;
  about: string;
}

export interface AssignmentPublic extends AssignmentCreate {
  id: string;
}

export interface AttemptCreate {
  assignment_id: string;
  user_id: string;
  /* eslint-disable  @typescript-eslint/no-explicit-any */
  data: SMARTData | { [key: string]: any };
}

export interface AttemptPublic extends AttemptCreate {
  id: string;
}

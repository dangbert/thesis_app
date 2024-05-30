export const API_PATH = '/api/v1';
export interface APIResult {
  data?: any; // json data
  error: string; // error (or '')
  timeMs: number; // time API call took
  status?: number; // status code
}

/**
 * wrapper for any API call, returns the json result or an error string.
 * @param promise Promise for pending API call
 * @param getText: whether to get result as text instead of json.
 * @retuns APIResult
 */
export const jsonOrError = async (
  promise: Promise<Response>,
  getText = false
) => {
  const result: APIResult = {
    timeMs: new Date().getTime(),
    error: '',
  };
  try {
    const res = await promise;
    result.status = res.status;
    if (!res.ok) {
      result.error = res.statusText;
    }
    if (getText) {
      result.data = await res.text();
    } else {
      result.data = await res.json();
    }
  } catch (caughtError) {
    result.error = `API error: "${caughtError}"`;
  } finally {
    if (result.data?.detail) result.error = result.data.detail; // use this error message if available
  }
  result.timeMs = new Date().getTime() - result.timeMs;
  return result;
};
